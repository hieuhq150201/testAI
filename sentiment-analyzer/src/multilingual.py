"""
🌐 Sprint 9 — Enhanced Multilingual Support
- Confidence-based language blending (từ arXiv 2412.09317)
  → khi langdetect không chắc (< 0.7 confidence) → run cả EN+VI → weighted merge
- Dynamic weighting: nếu EN conf < VI conf → ưu tiên VI dù text có từ Anh
"""
import re
from typing import Tuple

# ── Language Detection ─────────────────────────────────────────────
def detect_language(text: str) -> Tuple[str, float]:
    """
    Return (lang, confidence): 'vi'/'en'/'unknown', 0.0–1.0
    langdetect không trả confidence → ước lượng từ ký tự đặc trưng
    """
    try:
        from langdetect import detect_langs
        results = detect_langs(text)
        if not results:
            return 'unknown', 0.0
        top = results[0]
        lang = top.lang if top.lang in ('vi', 'en') else 'unknown'
        return lang, round(top.prob, 3)
    except Exception:
        return 'unknown', 0.0

def detect_language_simple(text: str) -> str:
    """Legacy compat: chỉ trả lang string"""
    lang, _ = detect_language(text)
    return lang

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
    'ấn tượng','chất lượng','đáng','recommend','xứng đáng',
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


# ── Emoji Sentiment ───────────────────────────────────────────────
EMOJI_POSITIVE = {'😍','❤️','🔥','✨','😊','🥰','💯','👍','🎉','💪','🙌','⭐','🌟','💖','😄'}
EMOJI_NEGATIVE = {'💀','😭','😤','🤮','😡','👎','💔','😢','🤬','😠','🙄','😒','😞','💩','🤢'}

def emoji_score(text: str) -> float:
    """Return +1.0 (very positive) to -1.0 (very negative), 0 if no emoji"""
    pos = sum(1 for c in text if c in EMOJI_POSITIVE)
    neg = sum(1 for c in text if c in EMOJI_NEGATIVE)
    total = pos + neg
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 3)

def _apply_emoji_blend(result: dict, text: str) -> dict:
    """Blend emoji score (20%) with model result (80%)"""
    e = emoji_score(text)
    if e == 0.0:
        return result
    adj_pos = result["positive_prob"] * 0.8 + (0.5 + e * 0.5) * 0.2
    adj_neg = round(1.0 - adj_pos, 4)
    adj_pos = round(adj_pos, 4)
    result = dict(result)
    result.update({
        "positive_prob": adj_pos,
        "negative_prob": adj_neg,
        "sentiment": "positive" if adj_pos >= 0.5 else "negative",
        "confidence": round(max(adj_pos, adj_neg), 4),
        "emoji_score": e,
    })
    return result

def preprocess_vi(text: str) -> str:
    text = text.lower()
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[^\w\s]', ' ', text, flags=re.UNICODE)
    tokens = [w for w in text.split() if w not in VI_STOPWORDS and len(w) > 1]
    return ' '.join(tokens)

def predict_vi_lexicon(text: str) -> dict:
    text_lower = text.lower()
    pos_score = sum(1 for w in VI_POSITIVE_WORDS if w in text_lower)
    neg_score = sum(1 for w in VI_NEGATIVE_WORDS if w in text_lower)
    negations = ['không', 'chẳng', 'chả', 'ko', 'k ']
    for neg in negations:
        if neg in text_lower:
            pos_score, neg_score = neg_score, pos_score
            break
    total = pos_score + neg_score
    if total == 0:
        return {"sentiment": "neutral", "confidence": 0.5,
                "positive_prob": 0.5, "negative_prob": 0.5,
                "method": "lexicon_vi", "note": "Không đủ từ khóa"}
    pos_prob = pos_score / total
    neg_prob = neg_score / total
    sentiment = "positive" if pos_prob >= 0.5 else "negative"
    confidence = max(pos_prob, neg_prob)
    return {"sentiment": sentiment, "confidence": round(confidence, 4),
            "positive_prob": round(pos_prob, 4), "negative_prob": round(neg_prob, 4),
            "method": "lexicon_vi"}

# ── VI trained model ───────────────────────────────────────────────
_VI_MODEL = None

def _load_vi_model():
    global _VI_MODEL
    if _VI_MODEL is not None:
        return
    import os, pickle
    vi_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'vi_model.pkl')
    if os.path.exists(vi_path):
        with open(vi_path, 'rb') as f:
            _VI_MODEL = pickle.load(f)

def _preprocess_vi_ml(text: str) -> str:
    text = text.lower()
    text = re.sub(r'http\S+', ' ', text)
    text = re.sub(r'[^\w\s]', ' ', text, flags=re.UNICODE)
    tokens = [w for w in text.split() if w not in VI_STOPWORDS and len(w) > 1]
    return ' '.join(tokens) if tokens else 'empty'

_load_vi_model()

def predict_vi_trained(text: str) -> dict:
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

# ── English predict helper ─────────────────────────────────────────
def _predict_en(text: str, en_model) -> dict:
    import re as _re, nltk
    nltk.download('stopwords', quiet=True)
    from nltk.corpus import stopwords as _sw
    en_stopwords = set(_sw.words('english'))
    def _prep(t):
        t = t.lower()
        t = _re.sub(r'<[^>]+>', ' ', t)
        t = _re.sub(r'[^a-z\s]', ' ', t)
        tokens = [w for w in t.split() if w not in en_stopwords and len(w) > 1]
        return ' '.join(tokens) if tokens else "empty"
    clean = _prep(text)
    pred = en_model.predict([clean])[0]
    proba = en_model.predict_proba([clean])[0]
    return {
        "sentiment": "positive" if pred==1 else "negative",
        "confidence": round(float(proba[pred]), 4),
        "positive_prob": round(float(proba[1]), 4),
        "negative_prob": round(float(proba[0]), 4),
        "method": "lr_tfidf_en"
    }

# ── Confidence-based blending (arXiv 2412.09317) ──────────────────
LANG_CONF_THRESHOLD = 0.70  # Nếu langdetect < 70% → blend cả 2

def _blend_results(en_res: dict, vi_res: dict, lang_conf: float) -> dict:
    """
    Blend EN + VI predictions dựa trên confidence của từng model + lang detection confidence.
    Dynamic weighting: w_en = lang_conf * en_model_conf; w_vi = (1-lang_conf) * vi_model_conf
    """
    # Nếu en_conf >> vi_conf → EN thắng và ngược lại
    w_en = lang_conf * en_res["confidence"]
    w_vi = (1.0 - lang_conf) * vi_res["confidence"]
    total_w = w_en + w_vi if (w_en + w_vi) > 0 else 1.0

    blended_pos = (w_en * en_res["positive_prob"] + w_vi * vi_res["positive_prob"]) / total_w
    blended_neg = (w_en * en_res["negative_prob"] + w_vi * vi_res["negative_prob"]) / total_w

    sentiment = "positive" if blended_pos >= 0.5 else "negative"
    confidence = round(max(blended_pos, blended_neg), 4)

    return {
        "sentiment": sentiment,
        "confidence": confidence,
        "positive_prob": round(blended_pos, 4),
        "negative_prob": round(blended_neg, 4),
        "method": "confidence_blend_en_vi",
        "blend_weights": {"en": round(w_en/total_w, 3), "vi": round(w_vi/total_w, 3)},
        "en_result": {"sentiment": en_res["sentiment"], "confidence": en_res["confidence"]},
        "vi_result": {"sentiment": vi_res["sentiment"], "confidence": vi_res["confidence"]},
    }

# ── Main router ────────────────────────────────────────────────────
def predict_multilingual(text: str, en_model) -> dict:
    """
    Route text sang đúng model:
    - lang_conf >= 0.70 → single model (vi hoặc en)
    - lang_conf < 0.70  → blend cả 2 với dynamic weighting
    """
    lang, lang_conf = detect_language(text)

    if lang == 'vi' and lang_conf >= LANG_CONF_THRESHOLD:
        result = predict_vi_trained(text)
        result["language"] = "vi"
        result["lang_confidence"] = lang_conf
        return _apply_emoji_blend(result, text)

    if lang == 'en' and lang_conf >= LANG_CONF_THRESHOLD:
        result = _predict_en(text, en_model)
        result["language"] = "en"
        result["lang_confidence"] = lang_conf
        return _apply_emoji_blend(result, text)

    # Ambiguous (mixed VI/EN, code-switching, short text) → blend
    en_res = _predict_en(text, en_model)
    vi_res = predict_vi_trained(text)

    # Nếu không detect được gì → dùng 50/50
    if lang == 'unknown':
        lang_conf = 0.5

    # EN detected nhưng low confidence → adjust: treat as vi_leaning nếu vi_conf > en_conf
    effective_lang_conf = lang_conf if lang == 'en' else (1.0 - lang_conf)

    blended = _blend_results(en_res, vi_res, effective_lang_conf)
    blended["language"] = lang if lang != 'unknown' else 'mixed'
    blended["lang_confidence"] = lang_conf
    return _apply_emoji_blend(blended, text)
