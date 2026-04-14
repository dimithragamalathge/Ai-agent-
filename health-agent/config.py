"""
Centralised configuration — every module imports from here.
All values come from the .env file via python-dotenv.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (same folder as this file)
load_dotenv(dotenv_path=Path(__file__).parent / ".env")


def _require(key: str) -> str:
    """Return env var value or raise a clear error if missing."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Missing required environment variable: {key}\n"
            f"Copy .env.example → .env and fill in your credentials."
        )
    return value


# ─── Brand ────────────────────────────────────────────────────────────────────
INSTAGRAM_HANDLE: str = os.getenv("INSTAGRAM_HANDLE", "@YourHandle")
BRAND_NAME: str = os.getenv("BRAND_NAME", "YourBrandName")

# ─── Claude API ───────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL: str = "claude-sonnet-4-6"

# ─── Canva Connect API ────────────────────────────────────────────────────────
CANVA_CLIENT_ID: str = os.getenv("CANVA_CLIENT_ID", "")
CANVA_CLIENT_SECRET: str = os.getenv("CANVA_CLIENT_SECRET", "")
CANVA_SINGLE_POST_TEMPLATE_ID: str = os.getenv("CANVA_SINGLE_POST_TEMPLATE_ID", "")
CANVA_CAROUSEL_TEMPLATE_ID: str = os.getenv("CANVA_CAROUSEL_TEMPLATE_ID", "")
CANVA_ACCESS_TOKEN: str = os.getenv("CANVA_ACCESS_TOKEN", "")
CANVA_REFRESH_TOKEN: str = os.getenv("CANVA_REFRESH_TOKEN", "")
CANVA_API_BASE: str = "https://api.canva.com/rest/v1"
CANVA_AUTH_URL: str = "https://www.canva.com/api/oauth/authorize"
CANVA_TOKEN_URL: str = "https://api.canva.com/rest/v1/oauth/token"
# Set this to https://yourusername.pythonanywhere.com/canva/callback on PythonAnywhere
CANVA_REDIRECT_URI: str = os.getenv("CANVA_REDIRECT_URI", "http://localhost:8080/canva/callback")

# ─── Instagram Graph API ──────────────────────────────────────────────────────
INSTAGRAM_USER_ID: str = os.getenv("INSTAGRAM_USER_ID", "")
INSTAGRAM_ACCESS_TOKEN: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_API_BASE: str = "https://graph.instagram.com/v22.0"

# ─── PubMed ───────────────────────────────────────────────────────────────────
PUBMED_API_KEY: str = os.getenv("PUBMED_API_KEY", "")
PUBMED_BASE_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# ─── Scheduler ────────────────────────────────────────────────────────────────
SCHEDULE_DAYS: str = os.getenv("SCHEDULE_DAYS", "mon,wed,fri")
SCHEDULE_TIME: str = os.getenv("SCHEDULE_TIME", "08:00")

# ─── App ──────────────────────────────────────────────────────────────────────
FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")
DASHBOARD_PASSWORD: str = os.getenv("DASHBOARD_PASSWORD", "")
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///health_agent.db")
OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "./output/images"))
