#!/usr/bin/env python3
"""Smoke test cho dashboard container."""
import sys, os

errors = []

def check(name, fn):
    try:
        fn()
        print(f"  OK  {name}")
    except Exception as e:
        print(f"  FAIL {name}: {e}")
        errors.append(name)

check("streamlit",   lambda: __import__("streamlit"))
check("pandas",      lambda: __import__("pandas"))
check("requests",    lambda: __import__("requests"))
check("httpx",       lambda: __import__("httpx"))
check("nltk stopwords", lambda: __import__("nltk.corpus", fromlist=["stopwords"]).stopwords.words("english"))

def check_sklearn_version():
    import sklearn
    major, minor = map(int, sklearn.__version__.split(".")[:2])
    assert (major, minor) >= (1, 8), f"sklearn {sklearn.__version__} < 1.8.0"
check("sklearn >= 1.8.0", check_sklearn_version)

def load_model(path):
    import pickle, warnings
    assert os.path.exists(path), f"Model not found: {path}"
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with open(path, "rb") as f:
            m = pickle.load(f)
    assert hasattr(m, "predict") or isinstance(m, dict)
check("model EN (best_model_v2.pkl)", lambda: load_model("models/best_model_v2.pkl"))
check("model VI (vi_model.pkl)",      lambda: load_model("models/vi_model.pkl"))

if errors:
    print(f"\nFAILED: {errors}")
    sys.exit(1)
else:
    print(f"\nAll dashboard smoke tests passed!")
    sys.exit(0)
