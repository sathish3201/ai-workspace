
import os
from pathlib import Path
from dotenv import load_dotenv


class Settings:
    """Central settings and path management for AI Workspace."""

    # ------------------------------------------
    # Project paths
    # ------------------------------------------

    CONFIG_DIR = Path(__file__).resolve().parent
    PROJECT_DIR = CONFIG_DIR.parent

    FRONTEND_DIR = PROJECT_DIR / "hitl-frontend"
    BACKEND_DIR = PROJECT_DIR / "workspace"
    API_DIR = PROJECT_DIR / "api"
    LOG_DIR = PROJECT_DIR / "logs"
    TEST_DIR = PROJECT_DIR / "tests"
    UNIT_TEST_DIR = TEST_DIR / "unit"
    INTEGRATION_TEST_DIR = TEST_DIR / "integration"

    ENV_FILE = PROJECT_DIR / ".env"

    # ------------------------------------------
    # Initialize environment
    # ------------------------------------------

    @classmethod
    def initialize(cls):
        """Create directories and load environment variables."""

        # Create directories if they don't exist
        for directory in (
            cls.CONFIG_DIR,
            cls.FRONTEND_DIR,
            cls.BACKEND_DIR,
            cls.API_DIR,
            cls.LOG_DIR,
        ):
            directory.mkdir(parents=True, exist_ok=True)

        # Load variables from the project .env file
        load_dotenv(dotenv_path=cls.ENV_FILE, override=False)

    # ------------------------------------------
    # Environment variable helpers
    # ------------------------------------------

    @classmethod
    def get_env(cls, key: str, default=None):
        """Read an environment variable."""
        return os.getenv(key, default)

    @classmethod
    def get_secret(cls, key: str, default=None):
        """
        Read a secret from environment variables first,
        then Google Colab Secrets if available.
        """
        value = os.getenv(key)

        if value:
            return value

        try:
            from google.colab import userdata
            return userdata.get(key) or default
        except Exception:
            return default

    @classmethod
    def require_env(cls, key: str) -> str:
        """Return a required environment variable."""
        value = cls.get_secret(key)

        if not value:
            raise ValueError(
                f"Missing required environment variable or secret: {key}"
            )

        return value

    # ------------------------------------------
    # API credentials
    # ------------------------------------------

    @classmethod
    def groq_api_key(cls):
        return cls.get_secret("GROQ_API_KEY")

    @classmethod
    def ngrok_auth_token(cls):
        return cls.get_secret("NGROK_AUTH_TOKEN")

    # ------------------------------------------
    # Application configuration
    # ------------------------------------------

    APP_ENV = "development"
    API_HOST = "0.0.0.0"
    API_PORT = 8000

    # ------------------------------------------
    # Logging paths
    # ------------------------------------------

    @classmethod
    def log_file(cls, filename="app.log"):
        """Return a path for a log file."""
        return cls.LOG_DIR / filename

    # ------------------------------------------
    # Display configuration
    # ------------------------------------------

    @classmethod
    def show_paths(cls):
        """Print all configured directories."""
        print(f"Config  : {cls.CONFIG_DIR}")
        print(f"Project : {cls.PROJECT_DIR}")
        print(f"Frontend: {cls.FRONTEND_DIR}")
        print(f"Backend : {cls.BACKEND_DIR}")
        print(f"API     : {cls.API_DIR}")
        print(f"Logs    : {cls.LOG_DIR}")

    @classmethod
    def validate(cls):
        """Check required configuration."""
        missing = []

        if not cls.groq_api_key():
            missing.append("GROQ_API_KEY")

        if missing:
            raise ValueError(
                "Missing configuration: " + ", ".join(missing)
            )


# Initialize paths and environment when imported
Settings.initialize()
