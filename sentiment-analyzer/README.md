# 🎭 Sentiment Analyzer

Hệ thống phân tích cảm xúc văn bản đa ngôn ngữ (Tiếng Việt + Tiếng Anh), được xây dựng theo mô hình sprint agile với đầy đủ pipeline từ training đến production.

---

## 🚀 Tính năng

| Tính năng | Mô tả |
|-----------|-------|
| 🔍 **Phân tích text** | Nhập text thủ công, hỗ trợ VI + EN |
| 🔗 **Phân tích URL** | Paste link bất kỳ → tự crawl → phân tích |
| 🎬 **Phân tích YouTube** | Lấy comments → sentiment + top pos/neg |
| 📄 **Phân tích File** | Upload CSV/TXT → phân tích từng dòng |
| 📦 **Batch predict** | Gửi nhiều text cùng lúc |
| 📊 **Dashboard** | Streamlit UI 5 tabs với charts |
| ⚡ **Cache** | LRU in-memory, tự động fallback Redis |
| 🗄️ **Observability** | SQLite log mọi prediction, `/stats` endpoint |
| 🔄 **Model Registry** | Hot-swap model không cần restart |
| 🐳 **Docker** | docker-compose ready |
| 🤖 **CI/CD** | GitHub Actions tự chạy test khi push |

---

## 🏗️ Kiến trúc

```
sentiment-analyzer/
├── api/
│   └── main.py              # FastAPI app v3.0 — 10+ endpoints
├── src/
│   ├── train.py             # Training pipeline (accuracy gate ≥85%)
│   ├── multilingual.py      # Router VI/EN — auto detect ngôn ngữ
│   ├── analyzers.py         # URL, YouTube, File analyzers
│   ├── cache.py             # LRU cache (Redis fallback)
│   ├── observability.py     # SQLite prediction logger
│   └── model_registry.py   # Model versioning + hot-swap
├── dashboard/
│   └── app.py               # Streamlit Dashboard v4
├── models/
│   ├── best_model_v2.pkl    # EN model (TF-IDF + LR, 89.37%)
│   └── vi_model.pkl         # VI model (TF-IDF + LR, 92.9%)
├── data/
│   ├── train.csv / test.csv # IMDB 25k/25k
│   ├── vi_train.csv         # VI dataset 864 samples
│   └── vi_test.csv          # VI test 216 samples
├── tests/
│   ├── test_unit.py         # 20 unit tests
│   ├── test_integration.py  # 40 integration tests
│   └── load_test.py         # Load test 600 users
├── .github/workflows/
│   └── ci.yml               # GitHub Actions CI
├── Dockerfile
├── Dockerfile.dashboard
└── docker-compose.yml
```

---

## 📦 Cài đặt

### Chạy thủ công

```bash
# Clone
git clone https://github.com/hieuhq150201/testAI.git
cd testAI/sentiment-analyzer

# Cài dependencies
pip install fastapi uvicorn streamlit scikit-learn nltk datasets \
            pandas numpy pytest httpx beautifulsoup4 requests \
            youtube-comment-downloader python-multipart aiofiles langdetect

# Train model
python3 src/train.py

# Chạy API
uvicorn api.main:app --port 8000 --workers 4

# Chạy Dashboard
streamlit run dashboard/app.py --server.port 8501
```

### Chạy Docker

```bash
docker-compose up --build
# API:       http://localhost:8000
# Dashboard: http://localhost:8501
```

---

## 🔌 API Endpoints

### Cơ bản

```bash
# Health check
GET /health

# Phân tích 1 text
POST /predict
{"text": "Phim này hay quá!"}

# Phân tích nhiều text
POST /predict/batch
{"texts": ["Hay lắm!", "Dở quá!"]}

# Đa ngôn ngữ (auto-detect VI/EN)
POST /predict/multilingual
{"text": "Phim này hay quá, tôi rất thích!"}
```

### Phân tích từ nguồn

```bash
# Crawl URL bất kỳ
POST /analyze/url
{"url": "https://example.com/review"}

# YouTube comments
POST /analyze/youtube
{"url": "https://youtube.com/watch?v=...", "max_items": 100}

# Upload file CSV/TXT
POST /analyze/file
[multipart form: file=reviews.csv]
```

### Quản lý

```bash
# Stats & observability
GET /stats

# Danh sách models
GET /models

# Đổi active model (hot-swap)
POST /models/{version}/activate
```

### Response mẫu

```json
{
  "text": "Phim này hay quá!",
  "sentiment": "positive",
  "confidence": 0.94,
  "language": "vi",
  "method": "tfidf_vi_trained_v2",
  "cached": false,
  "latency_ms": 3.2
}
```

---

## 🤖 Models

### English Model
- **Algorithm:** Logistic Regression + TF-IDF (bigrams, sublinear_tf)
- **Dataset:** IMDB 25,000 reviews
- **Accuracy:** 89.37% (C=5.0)
- **Latency:** ~4ms

### Vietnamese Model
- **Algorithm:** Logistic Regression + TF-IDF (word 1-3gram)
- **Dataset:** 1,080 samples tự xây dựng — 10 domains
- **Domains:** Music, Shopping, Food, Film, Tech, Travel, Health, Education, Sport, Social
- **Accuracy:** 92.9% (real-world validation)
- **Đặc điểm:** Nhận diện được "cảm ơn", khen ngợi kiểu Việt

---

## 🧪 Tests

```bash
# Chạy toàn bộ tests
pytest tests/ -v

# Kết quả: 60/60 pass ✅

# Load test 600 users
python3 tests/load_test.py
```

### Kết quả Load Test (600 concurrent users)

| Users | RPS | Avg Latency | p95 | Lỗi |
|-------|-----|-------------|-----|-----|
| 10 | 96 | 4ms | 8ms | 0% |
| 100 | 935 | 7ms | 11ms | 0% |
| 400 | 1,483 | 132ms | 163ms | 0% |
| **600** | **1,529** | **227ms** | **284ms** | **0%** |

---

## 📅 Sprint History

### Sprint 1 — Foundation
- IMDB dataset pipeline, Logistic Regression model
- FastAPI: `/predict`, `/predict/batch`, `/health`
- Streamlit Dashboard v1

### Sprint 2 — Robustness
- Training pipeline với accuracy gate (≥85%)
- Versioned model saves (`model_YYYYMMDD_HHMMSS.pkl`)
- 38 tests (20 unit + 18 integration) — fix 2 bugs

### Sprint 3 — Production Ready
- CI/CD với GitHub Actions
- LRU Cache (1,000 entries, thread-safe)
- SQLite observability, `/stats` endpoint
- API v2.0: thêm `cached`, `latency_ms`, `cache_hits`

### Sprint 4 — Docker & Dashboard
- Dockerfile + docker-compose
- Dashboard v3 với charts từ `/stats`

### Sprint 5 — Multilingual
- Vietnamese support (lexicon-based)
- `/predict/multilingual` — auto-detect VI/EN
- `langdetect` integration

### Sprint 6 — Scale & Registry
- Redis cache (tự fallback về LRU nếu không có Redis)
- Model Registry: versioning + hot-swap không restart
- API v3.0

### Sprint 7 — Source Analyzers
- Crawl URL bất kỳ (báo, blog, review site)
- YouTube comments analyzer (không cần API key)
- File upload: CSV/TXT (max 5MB, 500 rows)
- Dashboard v4: 5 tabs

### Sprint 8 — Vietnamese Model v2
- Tự build dataset 1,080 samples — 10 domains
- Real-world accuracy: **92.9%** (vượt target 90%)
- Fix vấn đề "cảm ơn" bị classify nhầm là negative
- Load test: 600 users, 1,529 RPS, 0% error

---

## 🐛 Bugs đã fix

| # | Vấn đề | Sprint | Bài học |
|---|--------|--------|---------|
| 1 | `pip` không có trong Docker | 1 | Bootstrap pip trước |
| 2 | Directory chưa tồn tại khi save file | 1 | `exist_ok=True` everywhere |
| 3 | Git auth qua HTTPS | 1 | Dùng PAT thay password |
| 4 | `/health` thiếu field `model_loaded` | 2 | Test-driven catch được ngay |
| 5 | `/predict/batch` crash trên list rỗng | 2 | Validate input trước khi touch model |
| 6 | SQLite syntax lỗi trên Python 3.13 | 3 | Test trên cùng Python version |
| 7 | Git upstream chưa set | 3 | `--set-upstream` khi push lần đầu |
| 8 | "Cảm ơn" bị classify là negative | 8 | Train trên data đúng domain |

---

## 👥 Team

Dự án được xây dựng theo mô hình agile với team ảo:

- **T1** — Trainer: phụ trách data pipeline và model training
- **D1, D2** — Developer: phụ trách API và business logic
- **QA1, QA2** — QA Engineer: phụ trách test và quality gate
- **PM** — Project Manager: điều phối sprint và review

---

## 📄 License

MIT
