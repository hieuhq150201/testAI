# 🎭 Sentiment Analyzer

Phân tích cảm xúc review sản phẩm/phim sử dụng NLP pipeline.

## 📊 Results
- **Model:** Logistic Regression + TF-IDF (bigrams, sublinear_tf)
- **Accuracy:** 89.37% (IMDB 25k test set)
- **Latency:** 0.16ms/prediction
- **Throughput:** 10,703 predictions/sec

## 🏗️ Structure
```
sentiment-analyzer/
├── data/           # Dataset (gitignored - large files)
├── models/         # Trained model (.pkl)
├── src/            # Core preprocessing
├── api/            # FastAPI REST API
│   └── main.py
├── dashboard/      # Streamlit UI
│   └── app.py
├── tests/          # Unit tests (QA1)
└── reports/        # QA & training reports
```

## 🚀 Quick Start
```bash
# Install dependencies
pip install fastapi uvicorn streamlit scikit-learn nltk datasets pandas

# Run API
cd api && uvicorn main:app --reload --port 8000

# Run Dashboard
cd dashboard && streamlit run app.py
```

## 📋 API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/predict` | Single prediction |
| POST | `/predict/batch` | Batch prediction (max 100) |

## 🗺️ Roadmap
- [ ] Sprint 2: BERT/PhoBERT for Vietnamese
- [ ] Sprint 2: Docker containerization
- [ ] Sprint 2: CI/CD pipeline
