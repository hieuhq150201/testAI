"""
🔍 Agent-QA2: Integration Tests v2 — Cache + Observability + API
"""
import pytest, sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

# ── Health ─────────────────────────────────────────────────────────
class TestHealthEndpoints:
    def test_root_ok(self):
        r = client.get("/")
        assert r.status_code == 200
        assert r.json()["version"] == "2.0.0"

    def test_health_fields(self):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] == True
        assert "cache" in data
        assert "hit_rate" in data["cache"]

# ── /predict ──────────────────────────────────────────────────────
class TestPredictEndpoint:
    def test_positive(self):
        r = client.post("/predict", json={"text": "This movie was absolutely amazing!"})
        assert r.status_code == 200
        assert r.json()["sentiment"] == "positive"

    def test_negative(self):
        r = client.post("/predict", json={"text": "Terrible film, complete waste of time."})
        assert r.status_code == 200
        assert r.json()["sentiment"] == "negative"

    def test_response_has_v2_fields(self):
        r = client.post("/predict", json={"text": "Some review."})
        data = r.json()
        for field in ["sentiment","confidence","positive_prob","negative_prob","cached","latency_ms"]:
            assert field in data, f"Missing field: {field}"

    def test_empty_text_400(self):
        assert client.post("/predict", json={"text": ""}).status_code == 400

    def test_whitespace_400(self):
        assert client.post("/predict", json={"text": "   "}).status_code == 400

    def test_missing_field_422(self):
        assert client.post("/predict", json={"wrong": "x"}).status_code == 422

    def test_html_handled(self):
        assert client.post("/predict", json={"text": "<b>Great movie!</b>"}).status_code == 200

    def test_long_text_handled(self):
        assert client.post("/predict", json={"text": "great " * 500}).status_code == 200

# ── Cache ─────────────────────────────────────────────────────────
class TestCacheBehavior:
    def test_second_request_is_cached(self):
        text = f"unique test text for cache validation {time.time()}"
        r1 = client.post("/predict", json={"text": text})
        r2 = client.post("/predict", json={"text": text})
        assert r1.json()["cached"] == False
        assert r2.json()["cached"] == True

    def test_cached_result_consistent(self):
        text = f"consistency test {time.time()}"
        r1 = client.post("/predict", json={"text": text})
        r2 = client.post("/predict", json={"text": text})
        assert r1.json()["sentiment"] == r2.json()["sentiment"]
        assert r1.json()["confidence"] == r2.json()["confidence"]

    def test_cache_faster_than_fresh(self):
        text = f"speed test {time.time()}"
        client.post("/predict", json={"text": text})  # warm up
        t1 = time.time()
        client.post("/predict", json={"text": text})
        cached_time = time.time() - t1
        assert cached_time < 0.05  # cached should be <50ms

# ── /predict/batch ────────────────────────────────────────────────
class TestBatchEndpoint:
    def test_basic_batch(self):
        r = client.post("/predict/batch", json={"texts": ["Great!", "Terrible.", "Okay."]})
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 3
        assert "cache_hits" in data

    def test_batch_empty_400(self):
        assert client.post("/predict/batch", json={"texts": []}).status_code == 400

    def test_batch_over_100_400(self):
        assert client.post("/predict/batch", json={"texts": ["x"]*101}).status_code == 400

    def test_batch_exactly_100(self):
        r = client.post("/predict/batch", json={"texts": ["good movie"]*100})
        assert r.status_code == 200
        assert r.json()["count"] == 100

    def test_batch_cache_hits_counted(self):
        texts = [f"batch cache test {time.time()}"] * 3
        client.post("/predict/batch", json={"texts": texts[:1]})  # cache first
        r = client.post("/predict/batch", json={"texts": texts})
        assert r.json()["cache_hits"] >= 1

# ── /stats ────────────────────────────────────────────────────────
class TestStatsEndpoint:
    def test_stats_accessible(self):
        r = client.get("/stats")
        assert r.status_code == 200

    def test_stats_has_cache_and_predictions(self):
        data = client.get("/stats").json()
        assert "cache" in data
        assert "predictions" in data

    def test_stats_cache_fields(self):
        data = client.get("/stats").json()
        for field in ["hits","misses","hit_rate","size"]:
            assert field in data["cache"], f"Missing: {field}"

# ── Performance ───────────────────────────────────────────────────
class TestPerformance:
    def test_single_under_100ms(self):
        times = [(lambda t=time.time(): (client.post("/predict", json={"text":"great movie"}), time.time()-t)[1])() for _ in range(20)]
        assert sum(times)/len(times)*1000 < 100

    def test_batch_50_under_500ms(self):
        t = time.time()
        client.post("/predict/batch", json={"texts": ["good movie"]*50})
        assert (time.time()-t)*1000 < 500
