"""
🇻🇳 Sprint 5 — Multilingual Support
- Language detection (vi / en / other)
- Vietnamese preprocessing (no stopword lib needed — rule-based)
- Vietnamese sentiment: lexicon-based fallback khi chưa có PhoBERT
- English: route sang model LR+TF-IDF đã train
"""
import re
from typing import Tuple

# ── Language Detection ─────────────────────────────────────────────
def detect_language(text: str) -> str:
    """Return 'vi', 'en', hoặc 'unknown'"""
    try:
        from langdetect import detect
        lang = detect(text)
        return lang if lang in ('vi', 'en') else 'unknown'
    except Exception:
        return 'unknown'

# ── Vietnamese Preprocessing ───────────────────────────────────────
VI_STOPWORDS = {
    'và','của','là','có','trong','cho','với','các','được','này',
    'một','những','không','tôi','bạn','mình','thì','đã','đang',
    'sẽ','hay','hoặc','nhưng','vì','nên','cũng','rất','quá','lắm',
    'ở','từ','theo','về','lên','ra','vào','đến','qua','tại','như'
}

VI_POSITIVE_WORDS = {
    'tuyệt','hay','đỉnh','ngon','tốt','xuất sắc','tuyệt vời','thích',
    'yêu','đẹp','hoàn hảo','tuyệt đỉnh','ổn','hài lòng','vui','thú vị',
    'ấn tượng','chất lượng','đáng','recommend','recommend','xứng đáng',
    'amazing','perfect','great','good','love','excellent','wonderful',
    'tốt lắm','hay lắm','đỉnh lắm','quá hay','quá tốt','siêu hay',
    'đáng xem','đáng tiền','không tệ','ổn áp'
}

VI_NEGATIVE_WORDS = {
    'tệ','dở','chán','thất vọng','tồi','kém','nhàm','buồn','dở tệ',
    'phí tiền','lãng phí','không hay','không tốt','rác','kinh','ghê',
    'awful','terrible','bad','worst','boring','waste','disappointing',
    'tệ lắm','dở lắm','chán lắm','quá tệ','quá chán','siêu tệ',
    'không đáng','không xứng','phí thời gian','thất vọng hoàn toàn'
}

def preprocess_vi(text: str) -> str:
    text = text.lower()
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[^\w\s]', ' ', text, flags=re.UNICODE)
    tokens = [w for w in text.split() if w not in VI_STOPWORDS and len(w) > 1]
    return ' '.join(tokens)

def predict_vi_lexicon(text: str) -> dict:
    """
    Lexicon-based sentiment cho tiếng Việt.
    Fallback đến khi PhoBERT được tích hợp (Sprint 5b).
    """
    text_lower = text.lower()
    pos_score = sum(1 for w in VI_POSITIVE_WORDS if w in text_lower)
    neg_score = sum(1 for w in VI_NEGATIVE_WORDS if w in text_lower)

    # Negation handling: "không hay" → flip
    negations = ['không', 'chẳng', 'chả', 'ko', 'k ']
    for neg in negations:
        if neg in text_lower:
            pos_score, neg_score = neg_score, pos_score
            break

    total = pos_score + neg_score
    if total == 0:
        return {"sentiment": "neutral", "confidence": 0.5,
                "positive_prob": 0.5, "negative_prob": 0.5,
                "method": "lexicon_vi", "note": "Không đủ từ khóa để phân tích"}

    pos_prob = pos_score / total
    neg_prob = neg_score / total
    sentiment = "positive" if pos_prob >= 0.5 else "negative"
    confidence = max(pos_prob, neg_prob)

    return {
        "sentiment": sentiment,
        "confidence": round(confidence, 4),
        "positive_prob": round(pos_prob, 4),
        "negative_prob": round(neg_prob, 4),
        "method": "lexicon_vi"
    }


# ── Vietnamese Trained Model ──────────────────────────────────────
import os as _os, pickle as _pickle, re as _re

def _load_vi_model():
    path = _os.path.join(_os.path.dirname(__file__), '../models/vi_model.pkl')
    if _os.path.exists(path):
        with open(path, 'rb') as f:
            return _pickle.load(f)
    return None

_VI_MODEL = _load_vi_model()

def _preprocess_vi_ml(text: str) -> str:
    text = text.lower()
    text = _re.sub(r'https?://\S+', '', text)
    text = _re.sub(r'[^\w\s]', ' ', text, flags=_re.UNICODE)
    return text.strip()

def predict_vi_trained(text: str) -> dict:
    """Dùng trained TF-IDF model cho tiếng Việt"""
    if _VI_MODEL is None:
        return predict_vi_lexicon(text)
    t = _preprocess_vi_ml(text)
    if isinstance(_VI_MODEL, dict):
        from scipy.sparse import hstack
        fw = _VI_MODEL['word_vec'].transform([t])
        fc = _VI_MODEL['char_vec'].transform([t])
        pred  = _VI_MODEL['clf'].predict(hstack([fw,fc]))[0]
        proba = _VI_MODEL['clf'].predict_proba(hstack([fw,fc]))[0]
    else:
        pred  = _VI_MODEL.predict([t])[0]
        proba = _VI_MODEL.predict_proba([t])[0]
    return {
        "sentiment": "positive" if pred==1 else "negative",
        "confidence": round(float(proba[pred]), 4),
        "positive_prob": round(float(proba[1]), 4),
        "negative_prob": round(float(proba[0]), 4),
        "method": "tfidf_vi_trained_v2"
    }

# ── Router ─────────────────────────────────────────────────────────
def predict_multilingual(text: str, en_model) -> dict:
    """Route text sang đúng model theo ngôn ngữ detect được"""
    import re as _re, nltk
    nltk.download('stopwords', quiet=True)
    from nltk.corpus import stopwords as _sw
    en_stopwords = set(_sw.words('english'))

    lang = detect_language(text)

    if lang == 'vi':
        result = predict_vi_trained(text)
        result["language"] = "vi"
        return result

    # English or unknown → dùng LR model
    def _preprocess_en(t):
        t = t.lower()
        t = _re.sub(r'<[^>]+>', ' ', t)
        t = _re.sub(r'[^a-z\s]', ' ', t)
        tokens = [w for w in t.split() if w not in en_stopwords and len(w) > 1]
        return ' '.join(tokens) if tokens else "empty"

    clean = _preprocess_en(text)
    pred = en_model.predict([clean])[0]
    proba = en_model.predict_proba([clean])[0]
    return {
        "sentiment": "positive" if pred==1 else "negative",
        "confidence": round(float(proba[pred]), 4),
        "positive_prob": round(float(proba[1]), 4),
        "negative_prob": round(float(proba[0]), 4),
        "language": lang,
        "method": "lr_tfidf_en"
    }
