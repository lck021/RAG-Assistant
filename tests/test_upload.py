from fastapi.testclient import TestClient
from io import BytesIO
from main import app

client = TestClient(app)

def test_correct_upload(monkeypatch):
    # skips the lengthy embedding process
    monkeypatch.setattr("main.embed_chunks",
                        lambda chunks: [[0.0] * 1024 for _ in chunks])

    file = BytesIO(b"Hello world!")
    response = client.post(
        "/api/upload",
        files={"file": ("test.txt", file, "text/plain")}
    )

    assert response.status_code == 201

    data = response.json()
    assert "id" in data
    assert data["filename"] == "test.txt"
    assert data["chunk_count"] > 0

def test_incorrect_type():
    response = client.post(
                "/api/upload",
                files={"file": ("test.pdf", b"pdf file contents", "application/pdf")}
            )

    assert response.status_code == 422
    assert response.json()["detail"] == "Incorrect file type"