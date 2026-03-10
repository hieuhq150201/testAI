#!/usr/bin/env python3
"""
Smoke test chạy lúc Docker build.
Nếu fail -> image không được tạo ra.
"""
import sys, os

errors = []

def check(name, fn):
    try:
        fn()
        print(f"  OK  {name}")
    except Exception as e:
        print(f"  FAIL {name}: {e}")
        errors.append(name)

# 1. Imports
check("fastapi", lambda: __import__("fastapi"))
check("uvicorn", lambda: __import__("uvicorn"))
check("sklearn", lambda: __import__("sklearn"))
check("beautifulsoup4", lambda: __import__("bs4"))
check("requests", lambda: __import__("requests"))
check("youtube_comment_downloader", lambda: __import__("youtube_comment_downloader"))
check("nltk stopwords", lambda: __import__("nltk.corpus", fromlist=["stopwords"]).stopwords.words("english"))
check("langdetect", lambda: __import__("langdetect"))

# 2. sklearn version
def check_sklearn_version():
    import sklearn
    major, minor = map(int, sklearn.__version__.split(".")[:2])
    assert (major, minor) >= (1, 8), f"sklearn {sklearn.__version__} < 1.8.0"
check("sklearn >= 1.8.0", check_sklearn_version)

# 3. Models
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

# 4. API import
def check_api():
    sys.path.insert(0, ".")
    import importlib.util
    spec = importlib.util.spec_from_file_location("main", "api/main.py")
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "app")
check("api/main.py imports OK", check_api)

# Result
if errors:
    print(f"\nFAILED: {errors}")
    sys.exit(1)
else:
    print(f"\nAll smoke tests passed!")
    sys.exit(0)
