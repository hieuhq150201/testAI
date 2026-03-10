"""
💻 Agent-D2: Streamlit Dashboard v3 — với Charts từ /stats
"""
import streamlit as st
import requests, re, pickle, os, time, nltk
import pandas as pd

nltk.download('stopwords', quiet=True)
from nltk.corpus import stopwords

st.set_page_config(page_title="Sentiment Analyzer", page_icon="🎭", layout="wide")
st.title("🎭 Sentiment Analyzer Dashboard")
st.markdown("**Model:** Logistic Regression + TF-IDF | **Accuracy:** 89.37% | **v3.0**")

stop_words = set(stopwords.words('english'))

@st.cache_resource
def load_model():
    path = os.path.join(os.path.dirname(__file__), '../models/best_model_v2.pkl')
    with open(path, 'rb') as f:
        return pickle.load(f)

model = load_model()

def preprocess(text):
    text = text.lower()
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[^a-z\s]', ' ', text)
    tokens = [w for w in text.split() if w not in stop_words and len(w) > 1]
    return ' '.join(tokens) if tokens else "empty"

def predict(text):
    pred = model.predict([preprocess(text)])[0]
    proba = model.predict_proba([preprocess(text)])[0]
    return {"sentiment": "positive" if pred==1 else "negative",
            "confidence": float(proba[pred]),
            "positive_prob": float(proba[1]),
            "negative_prob": float(proba[0])}

# ── Tabs ──────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🔍 Phân tích", "📦 Batch", "📊 Thống kê"])

with tab1:
    text_input = st.text_area("Nhập review:", height=150, placeholder="Type your review here...")
    if st.button("Phân tích", type="primary"):
        if text_input.strip():
            r = predict(text_input)
            col1, col2, col3 = st.columns(3)
            label = "POSITIVE ✅" if r["sentiment"]=="positive" else "NEGATIVE ❌"
            color = "green" if r["sentiment"]=="positive" else "red"
            col1.metric("Kết quả", label)
            col2.metric("Confidence", f"{r['confidence']*100:.1f}%")
            col3.metric("Positive / Negative", f"{r['positive_prob']*100:.1f}% / {r['negative_prob']*100:.1f}%")
            st.progress(r["positive_prob"], text="Positive score")
        else:
            st.warning("Nhập text trước!")

with tab2:
    batch_input = st.text_area("Mỗi review 1 dòng:", height=200,
                                placeholder="Review 1\nReview 2\nReview 3...")
    if st.button("Phân tích Batch", type="primary"):
        lines = [l.strip() for l in batch_input.split('\n') if l.strip()]
        if lines:
            rows = []
            for i, t in enumerate(lines):
                r = predict(t)
                rows.append({"#": i+1,
                             "Text": t[:80]+"..." if len(t)>80 else t,
                             "Kết quả": "Positive ✅" if r["sentiment"]=="positive" else "Negative ❌",
                             "Confidence": f"{r['confidence']*100:.1f}%"})
            df = pd.DataFrame(rows)
            pos = sum(1 for r in rows if "Positive" in r["Kết quả"])
            c1, c2, c3 = st.columns(3)
            c1.metric("Tổng", len(rows))
            c2.metric("Positive", pos)
            c3.metric("Negative", len(rows)-pos)
            st.dataframe(df, use_container_width=True)

            # Pie chart
            pie_data = pd.DataFrame({
                "Sentiment": ["Positive", "Negative"],
                "Count": [pos, len(rows)-pos]
            })
            st.bar_chart(pie_data.set_index("Sentiment"))

with tab3:
    st.subheader("📊 Model & Prediction Stats")
    # Try to get from API, fallback to local DB
    try:
        res = requests.get("http://localhost:8000/stats", timeout=2)
        data = res.json()
        cache = data.get("cache", {})
        preds = data.get("predictions", {})

        st.markdown("#### ⚡ Cache Performance")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Cache Size", cache.get("size", 0))
        c2.metric("Hit Rate", f"{cache.get('hit_rate',0)*100:.1f}%")
        c3.metric("Hits", cache.get("hits", 0))
        c4.metric("Misses", cache.get("misses", 0))

        if preds.get("total", 0) > 0:
            st.markdown("#### 📈 Prediction History")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tổng predictions", preds["total"])
            c2.metric("Positive rate", f"{preds['positive_rate']*100:.1f}%")
            c3.metric("Avg confidence", f"{preds['avg_confidence']*100:.1f}%")
            c4.metric("Uncertain (<60%)", preds["uncertain_count"])

            # Hourly volume chart
            if preds.get("hourly_volume"):
                hourly_df = pd.DataFrame(preds["hourly_volume"])
                hourly_df = hourly_df.set_index("hour")
                st.markdown("#### 📅 Volume theo giờ")
                st.bar_chart(hourly_df)

            # Recent predictions
            if preds.get("recent_predictions"):
                st.markdown("#### 🕐 Gần đây")
                recent_df = pd.DataFrame(preds["recent_predictions"])
                st.dataframe(recent_df, use_container_width=True)
    except Exception:
        st.info("API không chạy — stats chỉ hiển thị khi API online (port 8000)")
        st.markdown("Chạy: `uvicorn api.main:app --port 8000`")

st.divider()
st.caption("Trained on IMDB 25k | TF-IDF 50k features + bigrams | C=5.0 | sublinear_tf=True")
