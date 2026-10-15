
from threading import Lock
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from langgraph.types import Command

from workspace.agents.engine import agent, run_agent


app = FastAPI(
    title="AI Workspace API",
    version="0.2.0",
    description="AI Workspace with validated HITL approvals",
)

# Development-only registry. Cleared when this process restarts.
pending_approvals: dict[str, dict[str, Any]] = {}
approval_lock = Lock()


class RunRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)
    thread_id: str | None = None


class DecisionItem(BaseModel):
    decision: Literal["approve", "reject"]
    message: str | None = Field(default=None, max_length=2000)


class RespondRequest(BaseModel):
    thread_id: str = Field(min_length=1, max_length=200)
    # Use "decision" for one action, or "decisions" for multiple actions.
    decision: Literal["approve", "reject"] | None = None
    message: str | None = Field(default=None, max_length=2000)
    decisions: list[DecisionItem] | None = Field(
        default=None, min_length=1, max_length=20
    )


def serialize_result(result: dict[str, Any]) -> dict[str, Any]:
    messages = []

    for msg in result.get("messages", []):
        messages.append({
            "type": getattr(msg, "type", type(msg).__name__),
            "content": str(getattr(msg, "content", "")),
            "name": getattr(msg, "name", None),
            "tool_calls": jsonable_encoder(
                getattr(msg, "tool_calls", []) or []
            ),
        })

    interrupts = []

    for item in result.get("__interrupt__", []):
        value = getattr(item, "value", {}) or {}

        interrupts.append({
            "interrupt_id": getattr(item, "id", None),
            "action_requests": jsonable_encoder(
                value.get("action_requests", [])
            ),
            "review_configs": jsonable_encoder(
                value.get("review_configs", [])
            ),
        })

    return {
        "messages": messages,
        "interrupts": interrupts,
    }


def get_pending_actions(
    result: dict[str, Any],
) -> list[dict[str, Any]]:
    actions = []

    for interrupt in result.get("__interrupt__", []):
        value = getattr(interrupt, "value", {}) or {}
        configs = value.get("review_configs", [])

        allowed_by_name = {
            config.get("action_name"): config.get(
                "allowed_decisions", []
            )
            for config in configs
        }

        for action in value.get("action_requests", []):
            name = action.get("name")
            actions.append({
                "name": name,
                "args": action.get("args", {}),
                "allowed_decisions": allowed_by_name.get(name, []),
            })

    return actions


def response_payload(
    thread_id: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    data = serialize_result(result)
    actions = get_pending_actions(result)

    status = "approval_required" if actions else "completed"

    return {
        "thread_id": thread_id,
        "status": status,
        "pending_actions": actions,
        "messages": data["messages"],
        "interrupts": data["interrupts"],
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ai-workspace",
    }


@app.post("/hitl/run")
def hitl_run(request: RunRequest):
    thread_id = request.thread_id or str(uuid4())

    # Prevent a new request from reusing an active API thread.
    with approval_lock:
        if thread_id in pending_approvals:
            raise HTTPException(
                status_code=409,
                detail="This thread is already active or awaiting approval.",
            )
        pending_approvals[thread_id] = {"status": "running"}

    try:
        result = run_agent(
            message=request.message,
            thread_id=thread_id,
        )

        actions = get_pending_actions(result)

        with approval_lock:
            if actions:
                pending_approvals[thread_id] = {
                    "status": "pending",
                    "actions": actions,
                }
            else:
                pending_approvals.pop(thread_id, None)

        return response_payload(thread_id, result)

    except Exception as exc:
        with approval_lock:
            pending_approvals.pop(thread_id, None)

        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {type(exc).__name__}: {exc}",
        ) from exc


@app.post("/hitl/respond")
def hitl_respond(request: RespondRequest):
    # Validate the request shape.
    if request.decisions is not None and request.decision is not None:
        raise HTTPException(
            status_code=422,
            detail="Provide either decision or decisions, not both.",
        )

    if request.decisions is None and request.decision is None:
        raise HTTPException(
            status_code=422,
            detail="A decision or decisions list is required.",
        )

    with approval_lock:
        pending = pending_approvals.get(request.thread_id)

        if pending is None:
            raise HTTPException(
                status_code=409,
                detail="No pending approval exists for this thread.",
            )

        if pending["status"] != "pending":
            raise HTTPException(
                status_code=409,
                detail="This thread is already being processed.",
            )

        actions = pending["actions"]

        if request.decisions is not None:
            submitted = [
                item.model_dump(exclude_none=True)
                for item in request.decisions
            ]
        else:
            # The single-decision format is accepted only for one action.
            if len(actions) != 1:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "This thread has multiple pending actions. "
                        "Submit one decision per action using 'decisions'."
                    ),
                )

            submitted = [{
                "decision": request.decision,
                **({"message": request.message} if request.message else {}),
            }]

        if len(submitted) != len(actions):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Expected {len(actions)} decision(s), "
                    f"received {len(submitted)}."
                ),
            )

        # Check every decision against the middleware's allowed choices.
        for action, item in zip(actions, submitted):
            if item["decision"] not in action["allowed_decisions"]:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Decision '{item['decision']}' is not allowed "
                        f"for tool '{action['name']}'."
                    ),
                )

        # Reserve the thread to prevent concurrent double-resume attempts.
        pending_approvals[request.thread_id]["status"] = "processing"

    langgraph_decisions = [
        {
            "type": item["decision"],
            **({"message": item["message"]} if item.get("message") else {}),
        }
        for item in submitted
    ]

    try:
        result = agent.invoke(
            Command(resume={"decisions": langgraph_decisions}),
            config={
                "configurable": {
                    "thread_id": request.thread_id,
                }
            },
        )

        new_actions = get_pending_actions(result)

        with approval_lock:
            if new_actions:
                pending_approvals[request.thread_id] = {
                    "status": "pending",
                    "actions": new_actions,
                }
            else:
                pending_approvals.pop(request.thread_id, None)

        return response_payload(request.thread_id, result)

    except Exception as exc:
        with approval_lock:
            current = pending_approvals.get(request.thread_id)
            if current and current["status"] == "processing":
                current["status"] = "pending"

        raise HTTPException(
            status_code=500,
            detail=f"Agent resume failed: {type(exc).__name__}: {exc}",
        ) from exc
