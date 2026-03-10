FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data lúc build — không phụ thuộc network lúc runtime
RUN python -c "import nltk; nltk.download('stopwords', quiet=True); nltk.download('punkt', quiet=True)"

COPY . .

# Smoke test: verify tất cả imports OK trước khi ship image
RUN python -c "
from fastapi import FastAPI
from bs4 import BeautifulSoup
import youtube_comment_downloader
import sklearn; assert sklearn.__version__ == '1.8.0', f'sklearn version mismatch: {sklearn.__version__}'
import pickle
with open('models/best_model_v2.pkl','rb') as f: m = pickle.load(f)
assert hasattr(m, 'predict')
with open('models/vi_model.pkl','rb') as f: m = pickle.load(f)
print('✅ Docker smoke test passed')
"

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
