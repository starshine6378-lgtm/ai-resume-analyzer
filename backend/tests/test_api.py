import fitz
from fastapi.testclient import TestClient

from app.main import app


def make_pdf_bytes() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        "Zhang San\nEmail: zhangsan@example.com\nPhone: 13800138000\n"
        "4 years work experience\nSkills: Python FastAPI Redis Docker MySQL\n"
        "Bachelor degree\nProject: order API platform",
    )
    data = document.tobytes()
    document.close()
    return data


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_analyze_and_match_without_ai_key() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analyze-and-match",
            files={"file": ("resume.pdf", make_pdf_bytes(), "application/pdf")},
            data={
                "job_description": (
                    "Python backend engineer. Requires 3 years experience, "
                    "FastAPI, Redis, MySQL and Docker. Kubernetes preferred."
                ),
                "use_ai_review": "false",
            },
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["analysis"]["candidate"]["email"] == "zhangsan@example.com"
        assert payload["match"]["score"] > 50
