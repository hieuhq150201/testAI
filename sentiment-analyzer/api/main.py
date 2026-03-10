from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import pickle, re, os, time, nltk

nltk.download('stopwords', quiet=True)
from nltk.corpus import stopwords

app = FastAPI(title="Sentiment Analyzer API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MODEL_PATH = os.path.join(os.path.dirname(__file__), '../models/best_model_v2.pkl')
stop_words = set(stopwords.words('english'))

with open(MODEL_PATH, 'rb') as f:
    model = pickle.load(f)

def preprocess(text):
    text = text.lower()
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[^a-z\s]', '', text)
    return ' '.join(w for w in text.split() if w not in stop_words)

class TextInput(BaseModel):
    text: str

class BatchInput(BaseModel):
    texts: List[str]

@app.get("/")
def root():
    return {"status": "ok", "service": "Sentiment Analyzer API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy", "model": "LR+TF-IDF", "accuracy": 0.8937, "model_loaded": model is not None}

@app.post("/predict")
def predict(input: TextInput):
    if not input.text.strip():
        raise HTTPException(400, "Text cannot be empty")
    pred = model.predict([preprocess(input.text)])[0]
    proba = model.predict_proba([preprocess(input.text)])[0]
    return {
        "sentiment": "positive" if pred == 1 else "negative",
        "confidence": round(float(proba[pred]), 4),
        "positive_prob": round(float(proba[1]), 4),
        "negative_prob": round(float(proba[0]), 4)
    }

@app.post("/predict/batch")
def predict_batch(input: BatchInput):
    if not input.texts:
        raise HTTPException(400, "Texts list cannot be empty")
    if len(input.texts) > 100:
        raise HTTPException(400, "Max 100 texts")
    start = time.time()
    cleaned = [preprocess(t) for t in input.texts]
    preds = model.predict(cleaned)
    probas = model.predict_proba(cleaned)
    results = [{"index": i, "sentiment": "positive" if p==1 else "negative",
                "confidence": round(float(pb[p]),4)} for i,(p,pb) in enumerate(zip(preds,probas))]
    return {"results": results, "count": len(results), "elapsed_ms": round((time.time()-start)*1000,2)}
