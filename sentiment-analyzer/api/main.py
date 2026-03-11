"""
💻 FastAPI Sentiment Analyzer — v3.0
Features: Cache (Redis/LRU), Observability, Multilingual (vi/en), Model Registry
"""
import os
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

# ── Sprint 7: Source Analyzers ─────────────────────────────────────
from fastapi import UploadFile, File as FastAPIFile
from src.analyzers import analyze_url, analyze_youtube, analyze_file_content
from src.multilingual import predict_multilingual

def _predict_auto(text: str) -> dict:
    """Wrapper: multilingual predict dùng active model"""
    return predict_multilingual(text, registry.get_active())

class URLInput(BaseModel):
    url: str
    max_items: Optional[int] = 500

@app.post("/analyze/url")
def analyze_url_endpoint(input: URLInput):
    """🔗 Crawl URL → extract paragraphs → phân tích sentiment"""
    if not input.url.strip():
        raise HTTPException(400, "URL cannot be empty")
    try:
        result = analyze_url(input.url, _predict_auto)
        log_prediction(input.url, {"sentiment": result["overall_sentiment"],
                                   "confidence": result["avg_confidence"]}, source="url")
        return result
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(500, f"Lỗi phân tích URL: {e}")

@app.post("/analyze/youtube")
def analyze_youtube_endpoint(input: URLInput):
    """🎬 YouTube URL → lấy comments → phân tích sentiment"""
    if not input.url.strip():
        raise HTTPException(400, "URL cannot be empty")
    try:
        result = analyze_youtube(input.url, _predict_auto,
                                 max_comments=min(input.max_items or 500, 1000))
        log_prediction(input.url, {"sentiment": result["overall_sentiment"],
                                   "confidence": result["avg_confidence"]}, source="youtube")
        return result
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(500, f"Lỗi phân tích YouTube: {e}")

@app.post("/analyze/file")
async def analyze_file_endpoint(file: UploadFile = FastAPIFile(...)):
    """📄 Upload file CSV/TXT → phân tích từng dòng"""
    allowed = {"csv", "txt"}
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed:
        raise HTTPException(400, f"Chỉ hỗ trợ: {allowed}. Nhận được: {ext}")
    content_bytes = await file.read()
    if len(content_bytes) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(400, "File quá lớn (max 5MB)")
    try:
        content = content_bytes.decode("utf-8", errors="ignore")
        result = analyze_file_content(content, file.filename, _predict_auto)
        return result
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(500, f"Lỗi phân tích file: {e}")


# ── POST /analyze/video ────────────────────────────────────────────
@app.post("/analyze/video")
async def analyze_video_endpoint(
    file: UploadFile = FastAPIFile(...),
):
    """
    Upload video file → facial emotion analysis → sentiment.
    Supported: mp4, avi, mov, mkv, webm (max 50MB)
    """
    MAX_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}

    ext = os.path.splitext(file.filename or '')[1].lower()
    if ext not in ALLOWED:
        raise HTTPException(400, f"Định dạng không hỗ trợ: {ext}. Cho phép: {', '.join(ALLOWED)}")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(413, f"File quá lớn ({len(content)//1024//1024}MB). Tối đa 50MB.")

    try:
        result = analyze_video_bytes(content, file.filename or 'upload.mp4')
        log_prediction(
            text=f"[VIDEO:{file.filename}]",
            result={
                "sentiment": result.get("sentiment", "neutral"),
                "confidence": result.get("confidence", 0.5),
                "positive_prob": result.get("positive_prob", 0.5),
                "negative_prob": result.get("negative_prob", 0.5),
                "method": result.get("method", "facial_emotion_deepface"),
                "language": "video",
            },
            source="video"
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"Lỗi phân tích video: {str(e)}")
