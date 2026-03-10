"""
💻 Agent-D2 (Frontend Dev) — Streamlit Dashboard v2
"""
import streamlit as st
import requests
import pandas as pd
import re, pickle, os, nltk

nltk.download('stopwords', quiet=True)
from nltk.corpus import stopwords

st.set_page_config(page_title="Sentiment Analyzer", page_icon="🎭", layout="wide")

st.title("🎭 Sentiment Analyzer Dashboard")
st.markdown("**Model:** Logistic Regression + TF-IDF (bigrams, sublinear_tf) | **Accuracy:** 89.37%")

stop_words = set(stopwords.words('english'))

@st.cache_resource
def load_model():
    path = os.path.join(os.path.dirname(__file__), '../models/best_model_v2.pkl')
    with open(path, 'rb') as f:
        return pickle.load(f)

model = load_model()

def preprocess(text):
    text = text.lower()
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[^a-z\s]', '', text)
    return ' '.join(w for w in text.split() if w not in stop_words)

tab1, tab2 = st.tabs(["🔍 Single Analyze", "📦 Batch Analyze"])

with tab1:
    text_input = st.text_area("Enter review text:", height=150, placeholder="Type your review here...")
    if st.button("Analyze", type="primary"):
        if text_input.strip():
            pred = model.predict([preprocess(text_input)])[0]
            proba = model.predict_proba([preprocess(text_input)])[0]
            col1, col2, col3 = st.columns(3)
            sentiment = "POSITIVE ✅" if pred == 1 else "NEGATIVE ❌"
            color = "green" if pred == 1 else "red"
            col1.metric("Sentiment", sentiment)
            col2.metric("Confidence", f"{proba[pred]*100:.1f}%")
            col3.metric("Positive / Negative", f"{proba[1]*100:.1f}% / {proba[0]*100:.1f}%")
            st.progress(float(proba[1]), text=f"Positive score")

with tab2:
    st.markdown("Enter one review per line:")
    batch_input = st.text_area("Batch input:", height=200, placeholder="Review 1\nReview 2\n...")
    if st.button("Analyze Batch", type="primary"):
        lines = [l.strip() for l in batch_input.split('\n') if l.strip()]
        if lines:
            cleaned = [preprocess(t) for t in lines]
            preds = model.predict(cleaned)
            probas = model.predict_proba(cleaned)
            rows = []
            for i, (t, p, pb) in enumerate(zip(lines, preds, probas)):
                rows.append({"#": i+1, "Text": t[:80]+"..." if len(t)>80 else t,
                             "Sentiment": "Positive ✅" if p==1 else "Negative ❌",
                             "Confidence": f"{pb[p]*100:.1f}%"})
            df = pd.DataFrame(rows)
            pos = sum(1 for p in preds if p==1)
            c1, c2, c3 = st.columns(3)
            c1.metric("Total", len(lines))
            c2.metric("Positive", pos)
            c3.metric("Negative", len(lines)-pos)
            st.dataframe(df, use_container_width=True)

st.divider()
st.caption("Trained on IMDB 25k reviews | TF-IDF 50k features + bigrams + sublinear_tf | C=5.0")
