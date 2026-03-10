"""
💻 FastAPI Sentiment Analyzer — v3.0
Features: Cache (Redis/LRU), Observability, Multilingual (vi/en), Model Registry
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import re, os, time, sys, nltk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
nltk.download('stopwords', quiet=True)
from nltk.corpus import stopwords
from src.cache import prediction_cache
from src.observability import log_prediction, get_stats
from src.multilingual import predict_multilingual
from src.model_registry import registry

app = FastAPI(title="Sentiment Analyzer API", version="3.0.0",
              description="Phân tích cảm xúc đa ngôn ngữ (vi/en) với cache + observability")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

stop_words = set(stopwords.words('english'))

def preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[^a-z\s]', ' ', text)
    tokens = [w for w in text.split() if w not in stop_words and len(w) > 1]
    return ' '.join(tokens) if tokens else "empty"

def _predict_en(text: str) -> dict:
    model = registry.get_active()
    pred  = model.predict([preprocess(text)])[0]
    proba = model.predict_proba([preprocess(text)])[0]
    return {"sentiment": "positive" if pred==1 else "negative",
            "confidence": round(float(proba[pred]), 4),
            "positive_prob": round(float(proba[1]), 4),
            "negative_prob": round(float(proba[0]), 4),
            "language": "en", "method": "lr_tfidf_en"}

class TextInput(BaseModel):
    text: str

class BatchInput(BaseModel):
    texts: List[str]

class ActivateModel(BaseModel):
    version: str

# ── Endpoints ─────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "Sentiment Analyzer API", "version": "3.0.0"}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "active_model": registry.active_version,
        "model_metadata": registry.active_metadata,
        "model_loaded": registry.get_active() is not None,
        "cache": prediction_cache.stats
    }

@app.post("/predict")
def predict(input: TextInput):
    if not input.text.strip():
        raise HTTPException(400, "Text cannot be empty")
    t0 = time.time()
    cached = prediction_cache.get(input.text)
    if cached:
        return {**cached, "cached": True, "latency_ms": round((time.time()-t0)*1000, 2)}
    result = _predict_en(input.text)
    latency = round((time.time()-t0)*1000, 2)
    prediction_cache.set(input.text, result)
    log_prediction(input.text, result, source="api", latency_ms=latency)
    return {**result, "cached": False, "latency_ms": latency}

@app.post("/predict/multilingual")
def predict_multi(input: TextInput):
    """🌏 Auto-detect ngôn ngữ → route đúng model"""
    if not input.text.strip():
        raise HTTPException(400, "Text cannot be empty")
    t0 = time.time()
    cached = prediction_cache.get(f"ml:{input.text}")
    if cached:
        return {**cached, "cached": True, "latency_ms": round((time.time()-t0)*1000, 2)}
    result = predict_multilingual(input.text, registry.get_active())
    latency = round((time.time()-t0)*1000, 2)
    prediction_cache.set(f"ml:{input.text}", result)
    log_prediction(input.text, result, source="multilingual", latency_ms=latency)
    return {**result, "cached": False, "latency_ms": latency}

@app.post("/predict/batch")
def predict_batch(input: BatchInput):
    if not input.texts:
        raise HTTPException(400, "Texts list cannot be empty")
    if len(input.texts) > 100:
        raise HTTPException(400, "Max 100 texts per batch")
    t0 = time.time()
    results = []
    cache_hits = 0
    for i, text in enumerate(input.texts):
        cached = prediction_cache.get(text)
        if cached:
            results.append({"index": i, **cached, "cached": True})
            cache_hits += 1
        else:
            r = _predict_en(text)
            prediction_cache.set(text, r)
            log_prediction(text, r, source="batch")
            results.append({"index": i, **r, "cached": False})
    return {"results": results, "count": len(results),
            "cache_hits": cache_hits, "elapsed_ms": round((time.time()-t0)*1000, 2)}

@app.get("/stats")
def stats():
    return {"cache": prediction_cache.stats, "predictions": get_stats()}

@app.get("/models")
def list_models():
    """📦 Danh sách model versions"""
    return {"versions": registry.list_versions(), "active": registry.active_version}

@app.post("/models/activate")
def activate_model(body: ActivateModel):
    """🔄 Switch active model không cần restart"""
    try:
        registry.activate(body.version)
        prediction_cache.clear()  # clear cache khi đổi model
        return {"status": "ok", "active": body.version, "cache": "cleared"}
    except ValueError as e:
        raise HTTPException(400, str(e))
