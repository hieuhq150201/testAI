"""
🔍 Agent-QA2: Integration Tests (FastAPI via TestClient)
"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

# ── Health / Root ──────────────────────────────────────────────────
class TestHealthEndpoints:
    def test_root_status_ok(self):
        r = client.get("/")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_returns_healthy(self):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] == True

# ── /predict ──────────────────────────────────────────────────────
class TestPredictEndpoint:
    def test_positive_review(self):
        r = client.post("/predict", json={"text": "This movie was absolutely amazing!"})
        assert r.status_code == 200
        data = r.json()
        assert data["sentiment"] == "positive"
        assert 0 < data["confidence"] <= 1

    def test_negative_review(self):
        r = client.post("/predict", json={"text": "Terrible film, I wasted my time completely."})
        assert r.status_code == 200
        assert r.json()["sentiment"] == "negative"

    def test_response_has_all_fields(self):
        r = client.post("/predict", json={"text": "Some movie review here."})
        data = r.json()
        assert "sentiment" in data
        assert "confidence" in data
        assert "positive_prob" in data
        assert "negative_prob" in data

    def test_empty_text_returns_400(self):
        r = client.post("/predict", json={"text": ""})
        assert r.status_code == 400

    def test_whitespace_only_returns_400(self):
        r = client.post("/predict", json={"text": "   "})
        assert r.status_code == 400

    def test_missing_text_field_returns_422(self):
        r = client.post("/predict", json={"wrong_field": "test"})
        assert r.status_code == 422

    def test_html_text_handled(self):
        r = client.post("/predict", json={"text": "<b>Great</b> movie <br/>"})
        assert r.status_code == 200

    def test_long_text_handled(self):
        r = client.post("/predict", json={"text": "great movie " * 500})
        assert r.status_code == 200

# ── /predict/batch ────────────────────────────────────────────────
class TestBatchEndpoint:
    def test_batch_basic(self):
        r = client.post("/predict/batch", json={"texts": [
            "Great film!", "Terrible movie.", "It was okay."
        ]})
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 3
        assert len(data["results"]) == 3

    def test_batch_indexes_correct(self):
        r = client.post("/predict/batch", json={"texts": ["good", "bad", "okay"]})
        indexes = [item["index"] for item in r.json()["results"]]
        assert indexes == [0, 1, 2]

    def test_batch_has_elapsed_ms(self):
        r = client.post("/predict/batch", json={"texts": ["test1", "test2"]})
        assert "elapsed_ms" in r.json()
        assert r.json()["elapsed_ms"] >= 0

    def test_batch_empty_list_returns_400(self):
        r = client.post("/predict/batch", json={"texts": []})
        assert r.status_code == 400

    def test_batch_over_limit_returns_400(self):
        r = client.post("/predict/batch", json={"texts": ["text"] * 101})
        assert r.status_code == 400

    def test_batch_exactly_100_allowed(self):
        r = client.post("/predict/batch", json={"texts": ["good movie"] * 100})
        assert r.status_code == 200
        assert r.json()["count"] == 100

# ── Performance ────────────────────────────────────────────────────
class TestPerformance:
    def test_single_latency_under_100ms(self):
        import time
        times = []
        for _ in range(20):
            t = time.time()
            client.post("/predict", json={"text": "This was a great movie experience."})
            times.append((time.time() - t) * 1000)
        avg = sum(times) / len(times)
        assert avg < 100, f"Avg latency {avg:.1f}ms exceeds 100ms threshold"

    def test_batch_50_under_500ms(self):
        import time
        t = time.time()
        client.post("/predict/batch", json={"texts": ["good movie"] * 50})
        elapsed = (time.time() - t) * 1000
        assert elapsed < 500, f"Batch 50 took {elapsed:.1f}ms, exceeds 500ms"
