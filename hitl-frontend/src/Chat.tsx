
import { useState } from "react";
import "./Chat.css";

type Decision = "approve" | "reject";

type Action = {
  name: string;
  args: Record<string, unknown>;
  allowed_decisions: string[];
};

type Message = {
  type: string;
  content: string;
  name?: string | null;
};

type ApiResult = {
  thread_id?: string;
  status?: string;
  detail?: string;
  pending_actions?: Action[];
  messages?: Message[];
};

export default function Chat() {
  const [task, setTask] = useState("");
  const [threadId, setThreadId] = useState("");
  const [status, setStatus] = useState("ready");
  const [actions, setActions] = useState<Action[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [selected, setSelected] = useState<Record<number, Decision>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function apiRequest(
    endpoint: string,
    body: Record<string, unknown>
  ): Promise<ApiResult> {
    const response = await fetch(`/api${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || `Request failed (${response.status})`);
    }

    return data;
  }

  function applyResult(data: ApiResult) {
    setStatus(data.status || "unknown");
    setActions(data.pending_actions || []);
    setMessages(data.messages || []);
    setSelected({});
  }

  async function startTask(event: React.FormEvent) {
    event.preventDefault();
    if (!task.trim() || loading) return;

    setLoading(true);
    setError("");
    setMessages([]);
    setActions([]);
    setSelected({});

    const id =
      typeof crypto !== "undefined" && crypto.randomUUID
        ? crypto.randomUUID()
        : `thread-${Date.now()}`;

    setThreadId(id);
    setStatus("running");

    try {
      const data = await apiRequest("/hitl/run", {
        message: task.trim(),
        thread_id: id,
      });
      applyResult(data);
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Unable to run the agent.");
    } finally {
      setLoading(false);
    }
  }

  async function submitDecisions(decisions: Decision[]) {
    if (!threadId || loading || decisions.length !== actions.length) return;

    setLoading(true);
    setError("");

    try {
      const data = await apiRequest("/hitl/respond", {
        thread_id: threadId,
        decisions: decisions.map((decision) => ({ decision })),
      });
      applyResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to submit decision.");
    } finally {
      setLoading(false);
    }
  }

  function chooseDecision(index: number, decision: Decision) {
    if (actions.length === 1) {
      void submitDecisions([decision]);
      return;
    }

    setSelected((previous) => ({ ...previous, [index]: decision }));
  }

  const assistantMessages = messages.filter(
    (message) => message.type === "ai" && message.content.trim()
  );

  return (
    <main className="workspace">
      <header className="topbar">
        <div className="brand-mark">W</div>
        <div>
          <h1>AI Workspace</h1>
          <p>Human-in-the-loop assistant</p>
        </div>
        <span className={`status-pill status-${status}`}>
          {status.replaceAll("_", " ")}
        </span>
      </header>

      <section className="main-panel">
        <div className="intro">
          <span className="eyebrow">AGENT CONTROL CENTER</span>
          <h2>What should I work on?</h2>
          <p>
            The agent will pause before protected actions so you can review
            and decide what happens next.
          </p>
        </div>

        <form className="task-form" onSubmit={startTask}>
          <label htmlFor="task">Your task</label>
          <textarea
            id="task"
            value={task}
            onChange={(event) => setTask(event.target.value)}
            placeholder="Example: Create a project notes file with three sections..."
            rows={4}
            disabled={loading || actions.length > 0}
          />
          <div className="form-footer">
            <span>Protected actions require your approval.</span>
            <button
              className="primary-button"
              type="submit"
              disabled={loading || !task.trim() || actions.length > 0}
            >
              {loading ? "Working..." : "Run agent"}
            </button>
          </div>
        </form>

        {error && (
          <div className="error-box" role="alert">
            <strong>Request failed</strong>
            <p>{error}</p>
          </div>
        )}

        {actions.length > 0 && (
          <section className="approval-section">
            <div className="section-heading">
              <span className="approval-icon">!</span>
              <div>
                <h3>Approval required</h3>
                <p>Review the requested action before proceeding.</p>
              </div>
            </div>

            {actions.map((action, index) => (
              <article className="action-card" key={`${action.name}-${index}`}>
                <div className="action-title-row">
                  <div>
                    <span className="eyebrow">REQUESTED TOOL</span>
                    <h4>{action.name}</h4>
                  </div>
                  <span className="review-label">Needs review</span>
                </div>

                <p className="field-label">Arguments</p>
                <pre className="arguments">
                  {JSON.stringify(action.args, null, 2)}
                </pre>

                <p className="field-label">Allowed decisions</p>
                <div className="decision-buttons">
                  {(["approve", "reject"] as Decision[]).map((decision) => {
                    const allowed = action.allowed_decisions.includes(decision);
                    return (
                      <button
                        key={decision}
                        type="button"
                        className={
                          `decision-button ${decision}` +
                          (selected[index] === decision ? " selected" : "")
                        }
                        disabled={!allowed || loading}
                        onClick={() => chooseDecision(index, decision)}
                      >
                        {decision === "approve" ? "Approve" : "Reject"}
                      </button>
                    );
                  })}
                </div>

                {actions.length > 1 && (
                  <p className="selection-note">
                    Selected: {selected[index] || "No decision yet"}
                  </p>
                )}
              </article>
            ))}

            {actions.length > 1 && (
              <button
                className="primary-button submit-decisions"
                disabled={
                  loading ||
                  actions.some((_, index) => !selected[index])
                }
                onClick={() =>
                  void submitDecisions(
                    actions.map((_, index) => selected[index])
                  )
                }
              >
                {loading ? "Submitting..." : "Submit all decisions"}
              </button>
            )}

            <p className="safety-note">
              Nothing should execute until the relevant approval is submitted.
            </p>
          </section>
        )}

        {assistantMessages.length > 0 && (
          <section className="result-section">
            <h3>Agent response</h3>
            {assistantMessages.map((message, index) => (
              <div className="message-card" key={index}>
                {message.content}
              </div>
            ))}
          </section>
        )}

        {threadId && (
          <div className="thread-info">
            <span>Thread ID</span>
            <code>{threadId}</code>
          </div>
        )}

        <div className="bottom-actions">
          <button
            type="button"
            className="secondary-button"
            disabled={loading}
            onClick={() => {
              setTask("");
              setThreadId("");
              setStatus("ready");
              setActions([]);
              setMessages([]);
              setSelected({});
              setError("");
            }}
          >
            Clear interface
          </button>
          <span>AI Workspace · Development mode</span>
        </div>
      </section>
    </main>
  );
}
