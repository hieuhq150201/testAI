"""
💻 Agent-D1: FastAPI — v2 với Cache + Observability
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import pickle, re, os, time, sys, nltk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
nltk.download('stopwords', quiet=True)
from nltk.corpus import stopwords
from src.cache import prediction_cache
from src.observability import log_prediction, get_stats

app = FastAPI(title="Sentiment Analyzer API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MODEL_PATH = os.path.join(os.path.dirname(__file__), '../models/best_model_v2.pkl')
stop_words = set(stopwords.words('english'))

with open(MODEL_PATH, 'rb') as f:
    model = pickle.load(f)

def preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[^a-z\s]', ' ', text)
    tokens = [w for w in text.split() if w not in stop_words and len(w) > 1]
    return ' '.join(tokens) if tokens else "empty"

def _predict_raw(text: str) -> dict:
    """Core prediction — no cache, no logging"""
    pred  = model.predict([preprocess(text)])[0]
    proba = model.predict_proba([preprocess(text)])[0]
    return {
        "sentiment": "positive" if pred == 1 else "negative",
        "confidence": round(float(proba[pred]), 4),
        "positive_prob": round(float(proba[1]), 4),
        "negative_prob": round(float(proba[0]), 4),
    }

class TextInput(BaseModel):
    text: str

class BatchInput(BaseModel):
    texts: List[str]

@app.get("/")
def root():
    return {"status": "ok", "service": "Sentiment Analyzer API", "version": "2.0.0"}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model": "LR+TF-IDF",
        "accuracy": 0.8937,
        "model_loaded": model is not None,
        "cache": prediction_cache.stats
    }

@app.post("/predict")
def predict(input: TextInput):
    if not input.text.strip():
        raise HTTPException(400, "Text cannot be empty")

    t0 = time.time()

    # Cache check
    cached = prediction_cache.get(input.text)
    if cached:
        return {**cached, "cached": True, "latency_ms": round((time.time()-t0)*1000, 2)}

    result = _predict_raw(input.text)
    latency = round((time.time()-t0)*1000, 2)

    prediction_cache.set(input.text, result)
    log_prediction(input.text, result, source="api", latency_ms=latency)

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
            r = _predict_raw(text)
            prediction_cache.set(text, r)
            log_prediction(text, r, source="batch")
            results.append({"index": i, **r, "cached": False})

    elapsed = round((time.time()-t0)*1000, 2)
    return {
        "results": results,
        "count": len(results),
        "cache_hits": cache_hits,
        "elapsed_ms": elapsed
    }

@app.get("/stats")
def stats():
    """📊 Prediction history & model observability"""
    return {
        "cache": prediction_cache.stats,
        "predictions": get_stats()
    }
