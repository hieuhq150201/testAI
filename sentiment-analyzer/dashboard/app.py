"""💻 Streamlit Dashboard v4 — với Source Analyzer (URL, YouTube, File)"""
import streamlit as st
import requests, re, pickle, os, time, nltk
import pandas as pd

nltk.download('stopwords', quiet=True)
from nltk.corpus import stopwords

st.set_page_config(page_title="Sentiment Analyzer", page_icon="🎭", layout="wide")
st.title("🎭 Sentiment Analyzer")
st.markdown("**Model:** LR + TF-IDF | **Accuracy:** 89.37% | **v4.0** | 🇻🇳🇬🇧 Đa ngôn ngữ")

stop_words = set(stopwords.words('english'))

@st.cache_resource
def load_model():
    path = os.path.join(os.path.dirname(__file__), '../models/best_model_v2.pkl')
    with open(path, 'rb') as f: return pickle.load(f)

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

def show_result_metrics(r, label="Kết quả"):
    col1, col2, col3 = st.columns(3)
    sentiment = "POSITIVE ✅" if r.get("overall_sentiment","") == "positive" or r.get("sentiment","") == "positive" else "NEGATIVE ❌"
    col1.metric(label, sentiment)
    if "positive_rate" in r:
        col2.metric("Positive", f"{r['positive_rate']*100:.1f}%")
        col3.metric("Analyzed", r["total_analyzed"])
    else:
        col2.metric("Confidence", f"{r.get('confidence',0)*100:.1f}%")
        col3.metric("Method", r.get("method","lr"))

# ── TABS ──────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Text", "📦 Batch", "🔗 URL", "🎬 YouTube", "📊 Stats"
])

with tab1:
    text_input = st.text_area("Nhập review:", height=150)
    col_a, col_b = st.columns([1,4])
    mode = col_a.radio("Ngôn ngữ", ["Auto", "English only"], horizontal=True)
    if st.button("Phân tích", type="primary"):
        if text_input.strip():
            r = predict(text_input)
            show_result_metrics(r)
            st.progress(r["positive_prob"], text="Positive score")
        else:
            st.warning("Nhập text trước!")

with tab2:
    batch_input = st.text_area("Mỗi review 1 dòng:", height=200)
    if st.button("Phân tích Batch", type="primary"):
        lines = [l.strip() for l in batch_input.split('\n') if l.strip()]
        if lines:
            rows = []
            for i, t in enumerate(lines):
                r = predict(t)
                rows.append({"#": i+1, "Text": t[:80]+"..." if len(t)>80 else t,
                             "Kết quả": "Positive ✅" if r["sentiment"]=="positive" else "Negative ❌",
                             "Confidence": f"{r['confidence']*100:.1f}%"})
            pos = sum(1 for r in rows if "Positive" in r["Kết quả"])
            c1,c2,c3 = st.columns(3)
            c1.metric("Tổng", len(rows)); c2.metric("Positive", pos); c3.metric("Negative", len(rows)-pos)
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
            st.bar_chart(pd.DataFrame({"Sentiment":["Positive","Negative"],"Count":[pos,len(rows)-pos]}).set_index("Sentiment"))

with tab3:
    st.markdown("**Nhập URL** (trang báo, blog, Wikipedia, review site...)")
    url_input = st.text_input("URL:", placeholder="https://example.com/article")
    max_p = st.slider("Số đoạn văn tối đa", 10, 100, 50)
    if st.button("🔗 Crawl & Phân tích", type="primary"):
        if url_input.strip():
            with st.spinner("Đang crawl..."):
                try:
                    import sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__),'..'))
                    from src.analyzers import analyze_url
                    r = analyze_url(url_input, predict)
                    st.success(f"**{r['title']}**")
                    show_result_metrics(r)
                    c1,c2 = st.columns(2)
                    c1.metric("Positive", f"{r['positive_rate']*100:.1f}%")
                    c2.metric("Negative", f"{r['negative_rate']*100:.1f}%")
                    st.progress(r["positive_rate"], text="Overall positive")
                    st.markdown("**Sample paragraphs:**")
                    for s in r["sample_texts"]:
                        icon = "✅" if s["sentiment"]=="positive" else "❌"
                        st.markdown(f"{icon} *{s['text']}* — **{s['confidence']:.0%}**")
                except Exception as e:
                    st.error(f"Lỗi: {e}")
        else:
            st.warning("Nhập URL!")

with tab4:
    st.markdown("**Phân tích YouTube comments** — paste link video")
    yt_url = st.text_input("YouTube URL:", placeholder="https://youtube.com/watch?v=...")
    max_c = st.slider("Số comments tối đa", 20, 200, 100)
    if st.button("🎬 Lấy Comments & Phân tích", type="primary"):
        if yt_url.strip():
            with st.spinner("Đang lấy comments từ YouTube..."):
                try:
                    import sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__),'..'))
                    from src.analyzers import analyze_youtube
                    r = analyze_youtube(yt_url, predict, max_comments=max_c)
                    st.success(f"🎬 **{r['title']}**")
                    c1,c2,c3,c4 = st.columns(4)
                    c1.metric("Tổng comments", r["total_analyzed"])
                    c2.metric("Overall", r["overall_sentiment"].upper())
                    c3.metric("Positive", f"{r['positive_rate']*100:.1f}%")
                    c4.metric("Negative", f"{r['negative_rate']*100:.1f}%")
                    st.progress(r["positive_rate"], text="Positive sentiment")

                    col_pos, col_neg = st.columns(2)
                    with col_pos:
                        st.markdown("**🏆 Top Positive Comments:**")
                        for c in r.get("top_positive",[]):
                            st.markdown(f"✅ *{c['text']}*")
                    with col_neg:
                        st.markdown("**👎 Top Negative Comments:**")
                        for c in r.get("top_negative",[]):
                            st.markdown(f"❌ *{c['text']}*")
                except Exception as e:
                    st.error(f"Lỗi: {e}")
        else:
            st.warning("Nhập YouTube URL!")

with tab5:
    st.subheader("📊 Stats & Observability")
    try:
        res = requests.get("http://localhost:8000/stats", timeout=2)
        data = res.json()
        cache = data.get("cache", {}); preds = data.get("predictions", {})
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Cache Size", cache.get("size",0))
        c2.metric("Hit Rate", f"{cache.get('hit_rate',0)*100:.1f}%")
        c3.metric("Total Predictions", preds.get("total",0))
        c4.metric("Uncertain", preds.get("uncertain_count",0))
        if preds.get("hourly_volume"):
            hourly_df = pd.DataFrame(preds["hourly_volume"]).set_index("hour")
            st.bar_chart(hourly_df)
    except Exception:
        st.info("API offline — chạy: `uvicorn api.main:app --port 8000`")

    st.markdown("---")
    st.markdown("**📄 Analyze từ File (CSV/TXT)**")
    uploaded = st.file_uploader("Upload file", type=["csv","txt"])
    if uploaded:
        content = uploaded.read().decode("utf-8", errors="ignore")
        import sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__),'..'))
        from src.analyzers import analyze_file_content
        r = analyze_file_content(content, uploaded.name, predict)
        c1,c2,c3 = st.columns(3)
        c1.metric("Tổng dòng", r["total_analyzed"])
        c2.metric("Positive", f"{r['positive_rate']*100:.1f}%")
        c3.metric("Overall", r["overall_sentiment"].upper())
        st.dataframe(pd.DataFrame(r["sample_texts"]), use_container_width=True)

st.divider()
st.caption("Sentiment Analyzer v4.0 | IMDB 25k | TF-IDF+LR | vi/en | 🔗 URL | 🎬 YouTube | 📄 File")
