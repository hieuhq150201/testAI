"""
Bot/Spam detector cho YouTube comments
Dựa trên các dấu hiệu nhận biết không cần API:
- Lặp text giống nhau
- Emoji/ký tự spam
- Link/quảng cáo
- Comment quá ngắn vô nghĩa
- Username pattern bất thường
"""
import re
from collections import Counter
from typing import List, Dict, Tuple
import unicodedata

# ── Spam patterns ─────────────────────────────────────────────────
PROMO_PATTERNS = re.compile(
    r'(sub.{0,5}back|sub4sub|follow.{0,5}back|f4f|l4l|check.{0,10}channel|'
    r'free.{0,10}(robux|vbucks|gift|money)|bit\.ly|tinyurl|t\.me|'
    r'telegram|whatsapp.{0,10}group|discord\.gg|join.{0,10}now|'
    r'click.{0,10}link|link.{0,10}bio|dm.{0,5}me|inbox.{0,5}me)',
    re.IGNORECASE
)

BOT_USERNAME_PATTERN = re.compile(
    r'^[A-Za-z]+\d{4,}$|^User\d+$|^\w{3,6}\d{6,}$'
)

def count_emoji(text: str) -> int:
    return sum(1 for c in text if unicodedata.category(c) in ('So', 'Sm') or ord(c) > 0x1F300)

def is_spam(comment: dict) -> Tuple[bool, str]:
    """
    Trả về (is_spam, reason)
    comment: {"text": str, "author": str, "votes": int}
    """
    text = comment.get("text", "").strip()
    author = comment.get("author", "")

    if not text or len(text) < 3:
        return True, "quá ngắn"

    # Link/promo
    if PROMO_PATTERNS.search(text):
        return True, "quảng cáo/link"

    # Emoji spam (>60% là emoji)
    emoji_count = count_emoji(text)
    if len(text) > 0 and emoji_count / len(text) > 0.6 and len(text) < 30:
        return True, "emoji spam"

    # Lặp ký tự (aaaaaaa, !!!!!!)
    if re.search(r'(.)\1{6,}', text):
        return True, "lặp ký tự"

    # ALL CAPS dài (thường là spam/bot)
    words = text.split()
    if len(words) >= 3 and sum(1 for w in words if w.isupper() and len(w) > 2) / len(words) > 0.7:
        return True, "all caps spam"

    # Username pattern bot
    if BOT_USERNAME_PATTERN.match(author):
        return True, "username bot"

    return False, ""


def detect_duplicate_spam(comments: List[dict], threshold: float = 0.85) -> List[dict]:
    """
    Đánh dấu các comment gần giống nhau (copy-paste bot farm)
    """
    def normalize(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        return re.sub(r'\s+', ' ', text)

    seen: Dict[str, int] = {}
    for c in comments:
        key = normalize(c.get("text", ""))[:80]  # 80 char fingerprint
        seen[key] = seen.get(key, 0) + 1

    for c in comments:
        key = normalize(c.get("text", ""))[:80]
        if seen[key] >= 3:  # Xuất hiện >=3 lần → spam
            c["spam"] = True
            c["spam_reason"] = f"lặp lại {seen[key]} lần"
    return comments


def analyze_comments_with_bot_detection(
    raw_comments: List[dict],  # [{"text", "author", "votes", ...}]
    predict_fn,
    sample_size: int = 500,
) -> dict:
    """
    Full pipeline:
    1. Lấy sample thông minh (không phải random)
    2. Detect bot/spam
    3. Predict sentiment
    4. Thống kê top commenters
    """
    total_fetched = len(raw_comments)

    # ── Bước 1: Detect spam ────────────────────────────────────────
    raw_comments = detect_duplicate_spam(raw_comments)
    for c in raw_comments:
        if not c.get("spam"):
            is_sp, reason = is_spam(c)
            c["spam"] = is_sp
            c["spam_reason"] = reason if is_sp else ""

    spam_comments  = [c for c in raw_comments if c.get("spam")]
    clean_comments = [c for c in raw_comments if not c.get("spam")]

    # ── Bước 2: Smart sampling ─────────────────────────────────────
    # Ưu tiên: votes cao + diverse authors
    clean_comments.sort(key=lambda c: c.get("votes", 0), reverse=True)

    # Lấy top voted + random sample để đa dạng
    top_voted = clean_comments[:min(sample_size // 2, len(clean_comments))]
    remaining = clean_comments[len(top_voted):]

    import random
    random.seed(42)
    random_sample = random.sample(remaining, min(sample_size // 2, len(remaining)))

    sample = top_voted + random_sample
    sample = sample[:sample_size]

    # ── Bước 3: Predict sentiment ──────────────────────────────────
    author_stats: Dict[str, dict] = {}

    for c in sample:
        result = predict_fn(c["text"])
        c["sentiment"]  = result["sentiment"]
        c["confidence"] = result.get("confidence", 0)

        # Track per-author
        author = c.get("author", "Unknown")
        if author not in author_stats:
            author_stats[author] = {"positive": 0, "negative": 0, "comments": []}
        author_stats[author][result["sentiment"]] += 1
        author_stats[author]["comments"].append({
            "text": c["text"][:100],
            "sentiment": result["sentiment"],
            "confidence": c["confidence"],
        })

    # ── Bước 4: Aggregation ────────────────────────────────────────
    pos = [c for c in sample if c["sentiment"] == "positive"]
    neg = [c for c in sample if c["sentiment"] == "negative"]
    pos_rate = len(pos) / len(sample) if sample else 0

    # Top commenters
    top_positive_users = sorted(
        [{"author": a, **s} for a, s in author_stats.items() if s["positive"] > 0],
        key=lambda x: x["positive"], reverse=True
    )[:5]

    top_negative_users = sorted(
        [{"author": a, **s} for a, s in author_stats.items() if s["negative"] > 0],
        key=lambda x: x["negative"], reverse=True
    )[:5]

    # Top comments
    top_pos = sorted(pos, key=lambda c: c.get("confidence", 0), reverse=True)[:5]
    top_neg = sorted(neg, key=lambda c: c.get("confidence", 0), reverse=True)[:5]

    # Spam breakdown
    spam_reasons = Counter(c["spam_reason"] for c in spam_comments if c["spam_reason"])

    # Chi tiết spam: ai spam, nội dung gì, lý do gì
    spam_details = [
        {
            "author":  c.get("author", "Unknown"),
            "text":    c.get("text", "")[:200],
            "reason":  c.get("spam_reason", ""),
            "votes":   c.get("votes", 0),
        }
        for c in spam_comments
    ]
    # Sort: duplicate spam trước, rồi theo lý do
    spam_details.sort(key=lambda x: (x["reason"] != "lặp lại", x["reason"]))

    return {
        # Overview
        "total_fetched":     total_fetched,
        "total_analyzed":    len(sample),
        "spam_filtered":     len(spam_comments),
        "spam_rate":         round(len(spam_comments) / total_fetched, 4) if total_fetched else 0,
        "spam_reasons":      dict(spam_reasons.most_common()),
        "spam_details":      spam_details,
        "overall_sentiment": "positive" if pos_rate >= 0.5 else "negative",
        "positive_count":    len(pos),
        "negative_count":    len(neg),
        "positive_rate":     round(pos_rate, 4),
        "negative_rate":     round(1 - pos_rate, 4),
        "avg_confidence":    round(sum(c["confidence"] for c in sample) / len(sample), 4) if sample else 0,
        # Top comments
        "top_positive":      [{"text": c["text"], "confidence": c["confidence"], "author": c.get("author","")} for c in top_pos],
        "top_negative":      [{"text": c["text"], "confidence": c["confidence"], "author": c.get("author","")} for c in top_neg],
        # Top commenters
        "top_positive_users": top_positive_users,
        "top_negative_users": top_negative_users,
        # Sample
        "sample_comments":   [{"text": c["text"], "sentiment": c["sentiment"],
                                "confidence": c["confidence"], "author": c.get("author","")}
                               for c in sample[:10]],
    }
