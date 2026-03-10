"""
🌐 Sprint 7 — Source Analyzers
Crawl & analyze từ URL, YouTube, File
"""
import re, requests, logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def _aggregate(results: List[dict]) -> dict:
    """Tổng hợp kết quả từ list predictions"""
    if not results:
        return {}
    pos = sum(1 for r in results if r.get("sentiment") == "positive")
    neg = len(results) - pos
    avg_conf = sum(r.get("confidence", 0) for r in results) / len(results)
    overall = "positive" if pos >= neg else "negative"
    return {
        "overall_sentiment": overall,
        "total_analyzed": len(results),
        "positive_count": pos,
        "negative_count": neg,
        "positive_rate": round(pos / len(results), 4),
        "negative_rate": round(neg / len(results), 4),
        "avg_confidence": round(avg_conf, 4),
    }

# ── URL Analyzer ──────────────────────────────────────────────────
def extract_text_from_url(url: str) -> Dict[str, Any]:
    """Crawl URL, extract title + paragraphs"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        raise ValueError(f"Không thể tải URL: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove script/style
    for tag in soup(["script","style","nav","footer","header","aside"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title else "N/A"

    # Extract paragraphs (>50 chars)
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")
                  if len(p.get_text(strip=True)) > 50]

    # Also try article / main content
    if not paragraphs:
        paragraphs = [soup.get_text(separator=" ", strip=True)]

    return {"title": title, "paragraphs": paragraphs[:50], "url": url}


def analyze_url(url: str, predict_fn) -> dict:
    data = extract_text_from_url(url)
    paragraphs = data["paragraphs"]
    if not paragraphs:
        raise ValueError("Không extract được text từ URL này")

    results = [predict_fn(p) for p in paragraphs]
    agg = _aggregate(results)

    return {
        "source": "url",
        "url": url,
        "title": data["title"],
        **agg,
        "sample_texts": [
            {"text": p[:120] + "..." if len(p) > 120 else p,
             "sentiment": r["sentiment"],
             "confidence": r["confidence"]}
            for p, r in zip(paragraphs[:5], results[:5])
        ]
    }


# ── YouTube Analyzer ──────────────────────────────────────────────
def extract_video_id(url: str) -> str:
    """Extract YouTube video ID từ nhiều dạng URL"""
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/)([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    raise ValueError("Không nhận ra YouTube URL. Dùng dạng: https://youtube.com/watch?v=VIDEO_ID")


def get_youtube_comments(video_id: str, max_comments: int = 500) -> List[str]:
    """Lấy comments từ YouTube (không cần API key)"""
    try:
        from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR
        downloader = YoutubeCommentDownloader()
        gen = downloader.get_comments_from_url(
            f"https://youtube.com/watch?v={video_id}",
            sort_by=SORT_BY_POPULAR
        )
        comments = []
        for c in gen:
            text = c.get("text", "").strip()
            if text and len(text) > 5:
                comments.append(text)
            if len(comments) >= max_comments:
                break
        return comments
    except Exception as e:
        raise ValueError(f"Lỗi lấy comments YouTube: {e}")


def analyze_youtube(url: str, predict_fn, max_comments: int = 500) -> dict:
    video_id = extract_video_id(url)

    # Get video title via oEmbed (no API key needed)
    title = "YouTube Video"
    try:
        oembed = requests.get(
            f"https://www.youtube.com/oembed?url=https://youtube.com/watch?v={video_id}&format=json",
            timeout=5
        ).json()
        title = oembed.get("title", title)
    except Exception:
        pass

    comments = get_youtube_comments(video_id, max_comments)
    if not comments:
        raise ValueError("Không lấy được comments (video private hoặc tắt comments)")

    results = [predict_fn(c) for c in comments]
    agg = _aggregate(results)

    # Top positive & negative
    scored = list(zip(comments, results))
    top_pos = sorted([(t,r) for t,r in scored if r["sentiment"]=="positive"],
                     key=lambda x: x[1]["confidence"], reverse=True)[:3]
    top_neg = sorted([(t,r) for t,r in scored if r["sentiment"]=="negative"],
                     key=lambda x: x[1]["confidence"], reverse=True)[:3]

    return {
        "source": "youtube",
        "url": url,
        "video_id": video_id,
        "title": title,
        **agg,
        "top_positive": [{"text": t[:150], "confidence": r["confidence"]} for t,r in top_pos],
        "top_negative": [{"text": t[:150], "confidence": r["confidence"]} for t,r in top_neg],
        "sample_comments": [
            {"text": c[:150], "sentiment": r["sentiment"], "confidence": r["confidence"]}
            for c, r in zip(comments[:5], results[:5])
        ]
    }


# ── File Analyzer ─────────────────────────────────────────────────
def analyze_file_content(content: str, filename: str, predict_fn) -> dict:
    """Analyze text file — mỗi dòng là 1 text"""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"

    if ext == "csv":
        import csv, io
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        # Tìm cột text
        text_cols = [c for c in (rows[0].keys() if rows else [])
                     if any(k in c.lower() for k in ["text","review","comment","content","body"])]
        col = text_cols[0] if text_cols else list(rows[0].keys())[0]
        texts = [r[col].strip() for r in rows if r.get(col, "").strip()]
    else:
        # TXT: mỗi dòng
        texts = [l.strip() for l in content.splitlines() if len(l.strip()) > 5]

    if not texts:
        raise ValueError("File không có nội dung hợp lệ")

    texts = texts[:500]  # limit 500 dòng
    results = [predict_fn(t) for t in texts]
    agg = _aggregate(results)

    return {
        "source": "file",
        "filename": filename,
        "file_type": ext,
        **agg,
        "sample_texts": [
            {"text": t[:120]+"..." if len(t)>120 else t,
             "sentiment": r["sentiment"],
             "confidence": r["confidence"]}
            for t, r in zip(texts[:5], results[:5])
        ]
    }
