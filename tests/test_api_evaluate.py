from fastapi.testclient import TestClient

from app.deps import get_evaluator
from app.main import app
from app.services.evaluator import RAGEvaluator
from tests.fakes import FakeEmbedder

client = TestClient(app)


def setup_module(module):
    app.dependency_overrides[get_evaluator] = lambda: RAGEvaluator(FakeEmbedder())


def teardown_module(module):
    app.dependency_overrides.clear()


def test_evaluate_without_ground_truth():
    resp = client.post(
        "/api/evaluate",
        json={
            "question": "What is gradient descent?",
            "answer": (
                "Gradient descent is an optimization algorithm that minimizes "
                "a function by iteratively moving in the direction of steepest descent. "
                "The learning rate controls the step size during optimization."
            ),
            "context": [
                "Gradient descent minimizes a loss function by iteratively moving "
                "in the steepest descent direction. The learning rate controls the step size."
            ],
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "faithfulness" in data
    assert "answer_relevancy" in data
    assert data["context_recall"] is None
    assert "overall_score" in data
    assert "metrics_detail" in data
    assert data["evaluation_ms"] >= 0


def test_evaluate_with_ground_truth():
    resp = client.post(
        "/api/evaluate",
        json={
            "question": "What is gradient descent?",
            "answer": (
                "Gradient descent is an optimization algorithm that minimizes a function. "
                "The learning rate controls the step size during optimization."
            ),
            "context": [
                "Gradient descent minimizes a loss function by iteratively moving "
                "in the steepest descent direction. The learning rate controls the step size."
            ],
            "ground_truth": (
                "Gradient descent is a first-order optimization algorithm. "
                "The learning rate controls the step size during optimization."
            ),
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["context_recall"] is not None
    assert "context_recall" in data["metrics_detail"]


def test_evaluate_scores_in_range():
    resp = client.post(
        "/api/evaluate",
        json={
            "question": "What is gradient descent?",
            "answer": "Gradient descent is an optimization algorithm.",
            "context": ["Gradient descent is an optimization algorithm."],
        },
    )
    data = resp.json()
    for key in ("faithfulness", "answer_relevancy", "overall_score"):
        assert 0.0 <= data[key] <= 1.0


def test_evaluate_requires_context():
    resp = client.post(
        "/api/evaluate",
        json={"question": "q", "answer": "a", "context": []},
    )
    # Pydantic min_length=1 -> validation error -> 422 envelope
    assert resp.status_code == 422
