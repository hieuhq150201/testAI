import pytest, pickle, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture(scope="session")
def model():
    path = os.path.join(os.path.dirname(__file__), '../models/best_model_v2.pkl')
    with open(path, 'rb') as f:
        return pickle.load(f)

@pytest.fixture(scope="session")
def predict_fn(model):
    import re, nltk
    nltk.download('stopwords', quiet=True)
    from nltk.corpus import stopwords
    stop_words = set(stopwords.words('english'))
    def _predict(text):
        t = text.lower()
        t = re.sub(r'<[^>]+>', ' ', t)
        t = re.sub(r'[^a-z\s]', ' ', t)
        t = ' '.join(w for w in t.split() if w not in stop_words) or "empty"
        pred  = model.predict([t])[0]
        proba = model.predict_proba([t])[0]
        return {"sentiment": "positive" if pred==1 else "negative",
                "confidence": float(proba[pred]),
                "pos_prob": float(proba[1]),
                "neg_prob": float(proba[0])}
    return _predict
