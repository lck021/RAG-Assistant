from pathlib import Path

import pytest
from fastapi import responses
from fastapi.testclient import TestClient
from main import app

TEST_FILE = Path(__file__).parent/"test.txt"

CASES = [
    ("How long does a Kestrel-4 run on one charge?", "11"),
    ("How many days of annual leave do employees get?", "25"),
    ("Who founded Aurelia Robotics?", "Marta Sousa"),
    ("How close can a person get before the robots stop?", "1.5"),
]

UNANSWERABLE = [
    "What is Aurelia's stock price?",
    "Who is the CEO of Aurelia Robotics?",
    "How many Kestrel-4 units were sold in 2024?",
]

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def uploaded_document():
    with open(TEST_FILE, "rb") as file:
        response = client.post(
                    "/upload",
                    files={"file": ("test.txt", file, "text/plain")}
                )
    assert response.status_code == 201, response.text
    document = response.json()

    yield
    client.delete(f"/delete/{document['id']}")


def test_basic_response():
    response = client.post(
        "/ask",
        json={"question": "What is this document about?"}
    )

    assert response.status_code == 200

    data = response.json()
    assert "response" in data
    assert "context" in data


@pytest.mark.parametrize("question, answer", CASES)
def test_correct_response(question: str, answer: str):
    response = client.post(
                "/ask",
                json={"question": question}
            )

    assert response.status_code == 200

    data = response.json()
    assert answer in data["response"], f"{answer} not found in {data['response']}"

    context = data["context"]
    assert any(answer in chunk["content"] for chunk in context), (
        f"{answer} not found in context: {[c['content'] for c in context]}"
        )


@pytest.mark.parametrize("question", UNANSWERABLE)
def test_refuses_unanswerable(question):
    response = client.post(
                    "/ask",
                    json={"question": question}
                )
    
    answer = response.json()["response"]
    assert ("NOT_FOUND" in answer), answer


def test_null_request():
    response = client.post(
            "/ask",
            json={"question": None}
        )
    
    assert response.status_code == 422


def test_empty_question():
    response = client.post(
            "/ask",
            json={"question": ""}
        )
    
    assert response.status_code == 422


def test_invalid_type():
    response = client.post(
                "/ask",
                json={"question": 123}
            )
        
    assert response.status_code == 422