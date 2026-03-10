"""
Smoke tests — verify tất cả production imports hoạt động.
Test này sẽ fail ngay trong CI/Docker nếu thiếu package.
"""

def test_fastapi_import():
    import fastapi, uvicorn
    assert fastapi.__version__

def test_ml_imports():
    import sklearn, numpy, pandas
    assert sklearn.__version__
    # Verify sklearn >= 1.8 (cần để load model)
    major, minor = map(int, sklearn.__version__.split(".")[:2])
    assert (major, minor) >= (1, 8), f"sklearn {sklearn.__version__} quá cũ, cần >= 1.8.0"

def test_nlp_imports():
    import nltk, langdetect
    from nltk.corpus import stopwords
    words = stopwords.words("english")
    assert len(words) > 100

def test_scraping_imports():
    """Sprint 7 deps — cái này đã từng thiếu trong requirements.txt"""
    from bs4 import BeautifulSoup
    import requests, aiofiles
    import youtube_comment_downloader

def test_api_module_loads():
    """Verify api/main.py import được — catch lỗi như 'No module named bs4'"""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "main",
        os.path.join(os.path.dirname(__file__), "../api/main.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # Nếu thiếu package → fail ngay tại đây
    assert hasattr(mod, "app")

def test_src_modules_load():
    """Verify tất cả src modules import được"""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from src.cache import LRUCache
    from src.observability import log_prediction
    from src.multilingual import predict_multilingual
    from src.analyzers import analyze_url, analyze_youtube, analyze_file_content
    from src.model_registry import ModelRegistry

def test_model_loads():
    """Verify model file tồn tại và load được — catch sklearn version mismatch"""
    import pickle, os, warnings
    model_path = os.path.join(os.path.dirname(__file__), "../models/best_model_v2.pkl")
    assert os.path.exists(model_path), "Model file missing!"
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # InconsistentVersionWarning → Error
        with open(model_path, "rb") as f:
            model = pickle.load(f)
    assert hasattr(model, "predict")

def test_vi_model_loads():
    """Verify Vietnamese model load được"""
    import pickle, os, warnings
    model_path = os.path.join(os.path.dirname(__file__), "../models/vi_model.pkl")
    assert os.path.exists(model_path), "VI model file missing!"
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    assert model is not None
