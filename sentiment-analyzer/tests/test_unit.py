"""🧪 Agent-QA1: Unit Tests"""
import pytest

# ── Sentiment correctness ──────────────────────────────────────────
class TestPositive:
    def test_strong(self, predict_fn):
        assert predict_fn("Absolutely incredible! Best movie ever made.")["sentiment"] == "positive"
    def test_mild(self, predict_fn):
        assert predict_fn("Pretty decent film, enjoyed it.")["sentiment"] == "positive"
    def test_html_positive(self, predict_fn):
        assert predict_fn("<b>Amazing</b> film, I loved it!")["sentiment"] == "positive"

class TestNegative:
    def test_strong(self, predict_fn):
        assert predict_fn("Terrible, boring waste of time. I hated everything.")["sentiment"] == "negative"
    def test_mild(self, predict_fn):
        assert predict_fn("Disappointing. Story was weak and acting poor.")["sentiment"] == "negative"

# ── Confidence sanity ──────────────────────────────────────────────
class TestConfidence:
    def test_high_confidence_positive(self, predict_fn):
        r = predict_fn("Outstanding masterpiece! I loved every single moment.")
        assert r["confidence"] > 0.7, f"Expected >0.7, got {r['confidence']}"
    def test_high_confidence_negative(self, predict_fn):
        r = predict_fn("Disgusting garbage, worst film ever, hated it completely.")
        assert r["confidence"] > 0.7, f"Expected >0.7, got {r['confidence']}"
    def test_probs_sum_to_one(self, predict_fn):
        r = predict_fn("This movie was okay.")
        assert abs(r["pos_prob"] + r["neg_prob"] - 1.0) < 1e-5

# ── Edge cases ─────────────────────────────────────────────────────
class TestEdgeCases:
    def test_empty_string(self, predict_fn):
        r = predict_fn("")
        assert r["sentiment"] in ["positive", "negative"]
    def test_only_html(self, predict_fn):
        r = predict_fn("<br/><p></p><div></div>")
        assert r["sentiment"] in ["positive", "negative"]
    def test_very_long_text(self, predict_fn):
        r = predict_fn("great movie " * 1000)
        assert r["sentiment"] == "positive"
    def test_numbers_only(self, predict_fn):
        r = predict_fn("1234567890")
        assert r["sentiment"] in ["positive", "negative"]
    def test_special_chars(self, predict_fn):
        r = predict_fn("!!! ??? *** ...")
        assert r["sentiment"] in ["positive", "negative"]
    def test_mixed_case(self, predict_fn):
        r = predict_fn("AMAZING FILM loved IT!")
        assert r["sentiment"] == "positive"
    def test_unicode_stripped(self, predict_fn):
        r = predict_fn("great film 🎬🔥")
        assert r["sentiment"] == "positive"

# ── Preprocessing pipeline ─────────────────────────────────────────
class TestPreprocessing:
    def test_html_removed(self, predict_fn):
        r1 = predict_fn("Great movie!")
        r2 = predict_fn("<b>Great</b> <i>movie</i>!")
        assert r1["sentiment"] == r2["sentiment"]
    def test_case_insensitive(self, predict_fn):
        r1 = predict_fn("great movie")
        r2 = predict_fn("GREAT MOVIE")
        assert r1["sentiment"] == r2["sentiment"]

# ── Model output shape ─────────────────────────────────────────────
class TestOutputShape:
    def test_output_keys(self, predict_fn):
        r = predict_fn("test")
        assert set(r.keys()) == {"sentiment", "confidence", "pos_prob", "neg_prob"}
    def test_sentiment_values(self, predict_fn):
        r = predict_fn("test")
        assert r["sentiment"] in ["positive", "negative"]
    def test_confidence_range(self, predict_fn):
        r = predict_fn("test")
        assert 0.0 <= r["confidence"] <= 1.0
