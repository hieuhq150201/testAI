"""
Agent-T1: Robust Training Pipeline
- Input validation
- Reproducible (random_state fixed)
- Auto-save with versioning
- Detailed logging
"""
import pandas as pd, pickle, re, nltk, json, logging, sys, os, hashlib
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from nltk.corpus import stopwords

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

nltk.download('stopwords', quiet=True)
STOP_WORDS = set(stopwords.words('english'))
RANDOM_STATE = 42

def validate_dataframe(df: pd.DataFrame, name: str):
    assert 'text' in df.columns and 'label' in df.columns, f"{name}: missing columns"
    assert df['text'].notna().all(), f"{name}: null texts found"
    assert df['label'].isin([0,1]).all(), f"{name}: invalid labels"
    assert len(df) > 0, f"{name}: empty dataframe"
    log.info(f"✅ {name} validated: {len(df)} rows, {df['label'].value_counts().to_dict()}")

def preprocess(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return "empty"
    text = text.lower()
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[^a-z\s]', ' ', text)
    tokens = [w for w in text.split() if w not in STOP_WORDS and len(w) > 1]
    return ' '.join(tokens) if tokens else "empty"

def build_pipeline(C=5.0) -> Pipeline:
    return Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=50000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=2,
            max_df=0.95
        )),
        ('clf', LogisticRegression(
            C=C, max_iter=1000,
            random_state=RANDOM_STATE,
            solver='lbfgs', n_jobs=-1
        ))
    ])

def train(data_dir: str, models_dir: str, reports_dir: str):
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    log.info("📥 Loading data...")
    train_df = pd.read_csv(os.path.join(data_dir, 'train.csv'))
    test_df  = pd.read_csv(os.path.join(data_dir, 'test.csv'))

    validate_dataframe(train_df, 'train')
    validate_dataframe(test_df,  'test')

    log.info("🔧 Preprocessing...")
    X_train = train_df['text'].apply(preprocess)
    X_test  = test_df['text'].apply(preprocess)
    y_train, y_test = train_df['label'], test_df['label']

    empty_train = (X_train == 'empty').sum()
    empty_test  = (X_test  == 'empty').sum()
    if empty_train > 0: log.warning(f"⚠️  {empty_train} empty texts in train")
    if empty_test  > 0: log.warning(f"⚠️  {empty_test}  empty texts in test")

    log.info("🤖 Training model (C=5.0)...")
    model = build_pipeline(C=5.0)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    acc   = accuracy_score(y_test, preds)
    report = classification_report(y_test, preds, target_names=['Negative','Positive'], output_dict=True)
    cm     = confusion_matrix(y_test, preds).tolist()

    log.info(f"✅ Accuracy: {acc:.4f}")
    if acc < 0.85:
        log.error(f"❌ Accuracy {acc:.4f} below threshold 0.85 — aborting save")
        sys.exit(1)

    # versioned save
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    model_path = os.path.join(models_dir, f'model_{ts}.pkl')
    latest_path = os.path.join(models_dir, 'best_model_v2.pkl')
    with open(model_path,  'wb') as f: pickle.dump(model, f)
    with open(latest_path, 'wb') as f: pickle.dump(model, f)

    report_data = {
        "timestamp": ts,
        "accuracy": round(acc, 4),
        "classification_report": report,
        "confusion_matrix": cm,
        "model_path": model_path,
        "train_size": len(train_df),
        "test_size": len(test_df),
        "empty_texts": {"train": int(empty_train), "test": int(empty_test)},
        "status": "PASS"
    }
    with open(os.path.join(reports_dir, 'trainer_report.json'), 'w') as f:
        json.dump(report_data, f, indent=2)

    log.info(f"💾 Model saved: {model_path}")
    log.info(f"📄 Report saved: reports/trainer_report.json")
    return model, acc

if __name__ == '__main__':
    base = os.path.join(os.path.dirname(__file__), '..')
    model, acc = train(
        data_dir=os.path.join(base, 'data'),
        models_dir=os.path.join(base, 'models'),
        reports_dir=os.path.join(base, 'reports')
    )
    print(f"\n✅ Training complete. Accuracy: {acc:.4f}")
