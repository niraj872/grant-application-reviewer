import hashlib, os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./grant.db")  # swap for postgresql+psycopg://... later
def ai_provider(): return os.getenv("AI_PROVIDER", "demo")  # demo | anthropic
def sha256(t: str) -> str: return hashlib.sha256(t.encode()).hexdigest()
DISCLAIMER = ("AI findings are suggestions for human review. This tool is an evidence-review and completeness aid; "
              "it does not make legal, compliance, or funding-eligibility decisions.")
