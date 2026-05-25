import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_job():
    return {
        "title_raw": "아파트 경비원 모집",
        "job_category_norm": None,
        "work_type_norm": "PART_TIME",
        "salary_min": 2000000,
        "physical_level": "LOW",
        "senior_tag": "SENIOR_PREFERRED",
    }
