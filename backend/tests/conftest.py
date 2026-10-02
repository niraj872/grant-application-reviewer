import os, tempfile
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/t.db"; os.environ["AI_PROVIDER"] = "demo"
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import engine
from app.models import Base
@pytest.fixture()
def client():
    Base.metadata.drop_all(engine); Base.metadata.create_all(engine); return TestClient(app)
