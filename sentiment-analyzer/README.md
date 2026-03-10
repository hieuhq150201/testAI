# 🎭 Sentiment Analyzer

Hệ thống phân tích cảm xúc review sản phẩm/phim sử dụng NLP pipeline — từ training đến production-ready API.

---

## 📊 Kết quả

| Chỉ số | Giá trị |
|--------|---------|
| Model | Logistic Regression + TF-IDF |
| Accuracy | **89.37%** (IMDB 25k test) |
| Latency (fresh) | ~0.16ms / request |
| Latency (cached) | ~0.01ms / request |
| Throughput | 10,703 predictions/sec |
| Model size | 2.3 MB |
| Test coverage | **43/43 tests pass** ✅ |

---

## 🏗️ Kiến trúc

```
sentiment-analyzer/
├── .github/workflows/
│   └── ci.yml              # CI/CD — auto test khi push
├── data/
│   ├── train.csv            # IMDB 25k train (gitignored)
│   ├── test.csv             # IMDB 25k test (gitignored)
│   ├── eda_report.txt       # Báo cáo EDA
│   └── predictions.db       # SQLite — lịch sử prediction
├── models/
│   └── best_model_v2.pkl    # Model tốt nhất (LR, C=5.0)
├── src/
│   ├── train.py             # Training pipeline (robust)
│   ├── cache.py             # LRU cache layer
│   └── observability.py     # SQLite logger + stats
├── api/
│   └── main.py              # FastAPI REST API v2
├── dashboard/
│   └── app.py               # Streamlit UI
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   ├── test_unit.py         # Unit tests (20 tests)
│   └── test_integration.py  # Integration tests (23 tests)
└── reports/
    ├── trainer_report.json
    ├── qa1_report.json
    └── qa2_report.json
```

---

## 🚀 Cài đặt & Chạy

### Yêu cầu

```bash
pip install scikit-learn nltk pandas fastapi uvicorn streamlit httpx pytest python-multipart
```

### Train model

```bash
# Cần download data trước (lần đầu)
pip install datasets
python src/train.py
```

### Chạy API

```bash
cd api
uvicorn main:app --reload --port 8000
```

### Chạy Dashboard

```bash
cd dashboard
streamlit run app.py
```

---

## 📡 API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/` | Thông tin service |
| GET | `/health` | Health check + cache stats |
| POST | `/predict` | Phân tích 1 đoạn text |
| POST | `/predict/batch` | Phân tích nhiều text (tối đa 100) |
| GET | `/stats` | Thống kê prediction history |

### Ví dụ

```bash
# Single prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This movie was absolutely amazing!"}'

# Response
{
  "sentiment": "positive",
  "confidence": 0.9823,
  "positive_prob": 0.9823,
  "negative_prob": 0.0177,
  "cached": false,
  "latency_ms": 0.18
}
```

```bash
# Batch prediction
curl -X POST http://localhost:8000/predict/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Great film!", "Terrible movie.", "It was okay."]}'
```

---

## 🔄 CI/CD

GitHub Actions tự động chạy mỗi khi push lên `main` hoặc tạo Pull Request:

```
push → test job (43 tests + coverage) → lint job
                ↓
         ✅ Pass → merge allowed
         ❌ Fail → block merge
```

Xem kết quả tại: **Actions tab** trên GitHub

---

## 📦 Tech Stack

| Layer | Công nghệ |
|-------|-----------|
| ML Model | scikit-learn — Logistic Regression |
| Feature Extraction | TF-IDF (50k features, bigrams, sublinear_tf) |
| Preprocessing | NLTK — stopword removal, HTML strip |
| API | FastAPI + Pydantic |
| Dashboard | Streamlit |
| Cache | LRU in-memory (thread-safe, 1000 entries) |
| Observability | SQLite — prediction logging + stats |
| Testing | pytest + pytest-cov |
| CI/CD | GitHub Actions |

---

## 🗺️ Lịch sử Sprint

### Sprint 1 — Foundation
- ✅ Download & EDA dataset IMDB (25k train, 25k test)
- ✅ Preprocessing pipeline (HTML strip, lowercase, stopwords)
- ✅ Train Logistic Regression + SVM, chọn LR (acc=88.71%)
- ✅ FastAPI REST API cơ bản
- ✅ Streamlit dashboard v1

### Sprint 2 — Quality & Reliability
- ✅ Robust training pipeline với validation, logging, accuracy gate
- ✅ Hyperparameter tuning (C=5.0, sublinear_tf) → acc tăng lên **89.37%**
- ✅ 20 unit tests — edge cases, confidence sanity, preprocessing
- ✅ 18 integration tests — API endpoints, error handling, performance
- ✅ **Bug fix:** `/health` thiếu field `model_loaded`
- ✅ **Bug fix:** `/predict/batch` crash khi nhận empty list (thay vì trả 400)

### Sprint 3 — Production Ready
- ✅ GitHub Actions CI/CD — tự động chạy 43 tests khi push
- ✅ LRU Cache layer — cache hit ~0.01ms (vs fresh ~0.16ms)
- ✅ Observability: SQLite logger, `/stats` endpoint, track uncertain predictions
- ✅ +5 cache tests, +3 stats tests
- ✅ **Bug fix:** SQLite `DEFAULT datetime()` syntax lỗi trên Python 3.13

---

## 🐛 Issues đã xử lý

| # | Sprint | Issue | Fix |
|---|--------|-------|-----|
| 1 | S1 | `pip` không có sẵn trong Docker | Bootstrap qua `get-pip.py` |
| 2 | S1 | `data/` directory chưa tồn tại khi save CSV | `os.makedirs(..., exist_ok=True)` |
| 3 | S1 | Git repo chưa có remote + user config | Setup `git config` + PAT authentication |
| 4 | S2 | `/health` thiếu field `model_loaded` | Thêm field vào response |
| 5 | S2 | `/predict/batch` với `[]` → crash thay vì 400 | Validate trước khi gọi model |
| 6 | S3 | SQLite `DEFAULT (datetime("now"))` lỗi Python 3.13 | Bỏ DEFAULT, thêm vào INSERT |
| 7 | S3 | Git push lần đầu thiếu `--set-upstream` | `git push --set-upstream origin main` |

---

## 🔮 Roadmap

- [ ] **Sprint 4:** Docker + docker-compose (API + Dashboard)
- [ ] **Sprint 4:** Dashboard charts từ `/stats` (volume, sentiment trend)
- [ ] **Sprint 5:** Vietnamese support — PhoBERT / multilingual model
- [ ] **Sprint 5:** Language detection tự động → route đúng model
- [ ] **Sprint 6:** Persistent Redis cache (thay LRU in-memory)
- [ ] **Sprint 6:** Model versioning + A/B testing

---

## 👥 Team

| Role | Nhiệm vụ |
|------|----------|
| 🎓 Agent-T1 (Trainer) | Training pipeline, hyperparameter tuning |
| 💻 Agent-D1 (Backend Dev) | FastAPI, CI/CD, bug fixes |
| 💻 Agent-D2 (Frontend Dev) | Streamlit dashboard, cache layer |
| 🧪 Agent-QA1 (Tester) | Unit tests |
| 🔍 Agent-QA2 (QA Engineer) | Integration tests, observability, performance |
