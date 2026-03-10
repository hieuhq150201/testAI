"""
Sprint 9 — Context-aware sentiment (ScienceDirect 2026)
Dùng comment xung quanh (reply thread, nearby comments) làm context
để điều chỉnh sentiment của target comment.

Ý tưởng autofilter:
- Lấy N comment gần nhất cùng author hoặc replies → context window
- Nếu context majority negative → downweight target positive (và ngược lại)
- Không thay đổi model — chỉ post-process confidence
"""

from typing import List, Dict, Optional

CONTEXT_WINDOW = 3        # Số comment xung quanh xét
CONTEXT_INFLUENCE = 0.15  # Tối đa 15% điều chỉnh confidence từ context

def build_reply_threads(comments: List[Dict]) -> Dict[str, List[str]]:
    """
    Group comments thành threads dựa trên @mention pattern.
    Key: author name; Value: list of texts mentioning/replying to them.
    """
    threads: Dict[str, List[str]] = {}
    mention_re = __import__('re').compile(r'@(\w[\w\s]*?)(?:\s|$|[,:!?])')
    for c in comments:
        text = c.get('text', '')
        for match in mention_re.finditer(text):
            mentioned = match.group(1).strip()
            threads.setdefault(mentioned, []).append(text)
    return threads

def get_context_window(
    idx: int,
    comments: List[Dict],
    predict_fn,
    window: int = CONTEXT_WINDOW
) -> Optional[float]:
    """
    Tính sentiment của context window quanh comment tại idx.
    Trả về avg positive_prob của các comment lân cận (bỏ chính nó).
    """
    start = max(0, idx - window)
    end   = min(len(comments), idx + window + 1)
    neighbors = [comments[i] for i in range(start, end) if i != idx]
    if not neighbors:
        return None
    probs = []
    for nb in neighbors:
        try:
            r = predict_fn(nb.get('text', ''))
            probs.append(r.get('positive_prob', 0.5))
        except Exception:
            probs.append(0.5)
    return sum(probs) / len(probs) if probs else None

def adjust_with_context(
    result: Dict,
    context_pos_avg: Optional[float]
) -> Dict:
    """
    Điều chỉnh confidence dựa trên context:
    - Nếu context majority positive (avg > 0.65) và target cũng positive → boost nhẹ
    - Nếu context majority negative (avg < 0.35) và target positive → giảm nhẹ
    - Thay đổi tối đa CONTEXT_INFLUENCE (15%)
    """
    if context_pos_avg is None:
        result['context_adjusted'] = False
        return result

    pos_prob = result.get('positive_prob', 0.5)
    neg_prob = result.get('negative_prob', 0.5)
    sentiment = result.get('sentiment', 'positive')

    # Tính delta từ context
    context_signal = context_pos_avg - 0.5  # -0.5..+0.5
    delta = context_signal * CONTEXT_INFLUENCE  # tối đa ±0.075

    new_pos = max(0.01, min(0.99, pos_prob + delta))
    new_neg = 1.0 - new_pos
    new_sentiment = 'positive' if new_pos >= 0.5 else 'negative'
    new_conf = round(max(new_pos, new_neg), 4)

    out = dict(result)
    out.update({
        'positive_prob': round(new_pos, 4),
        'negative_prob': round(new_neg, 4),
        'confidence': new_conf,
        'sentiment': new_sentiment,
        'context_adjusted': True,
        'context_pos_avg': round(context_pos_avg, 3),
        'original_sentiment': sentiment,
        'original_confidence': result.get('confidence', new_conf),
    })
    return out

def analyze_with_context(
    comments: List[Dict],
    predict_fn,
    use_context: bool = True
) -> List[Dict]:
    """
    Phân tích toàn bộ comments với context-awareness.
    predict_fn: fn(text) -> {sentiment, confidence, positive_prob, negative_prob, ...}
    """
    results = []
    for idx, comment in enumerate(comments):
        text = comment.get('text', '')
        try:
            base = predict_fn(text)
        except Exception:
            base = {'sentiment': 'neutral', 'confidence': 0.5,
                    'positive_prob': 0.5, 'negative_prob': 0.5}

        if use_context and len(comments) > 1:
            ctx_avg = get_context_window(idx, comments, predict_fn)
            base = adjust_with_context(base, ctx_avg)
        else:
            base['context_adjusted'] = False

        base['author'] = comment.get('author', '')
        base['text']   = text
        base['votes']  = comment.get('votes', 0)
        results.append(base)

    return results
