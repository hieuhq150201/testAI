"""
Sprint 9 Tests:
1. Confidence-based language blending
2. Context-aware analysis
3. Video analyzer (mock — no real video file needed)
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ── 1. Multilingual blending ───────────────────────────────────────
class TestMultilingual:
    def test_detect_language_returns_tuple(self):
        from src.multilingual import detect_language
        lang, conf = detect_language("I love this product so much")
        assert lang in ('en', 'vi', 'unknown')
        assert 0.0 <= conf <= 1.0

    def test_detect_vi_with_confidence(self):
        from src.multilingual import detect_language
        lang, conf = detect_language("Sản phẩm này thật tuyệt vời và đáng mua")
        assert lang == 'vi'
        assert conf > 0.0

    def test_detect_en_with_confidence(self):
        from src.multilingual import detect_language
        lang, conf = detect_language("This is an excellent product I highly recommend")
        assert lang == 'en'
        assert conf > 0.0

    def test_blend_results_math(self):
        from src.multilingual import _blend_results
        en = {"sentiment": "positive", "confidence": 0.8, "positive_prob": 0.8, "negative_prob": 0.2}
        vi = {"sentiment": "negative", "confidence": 0.9, "positive_prob": 0.1, "negative_prob": 0.9}
        # lang_conf=0.4 (uncertain) → ưu tiên VI hơn
        result = _blend_results(en, vi, lang_conf=0.4)
        assert result['sentiment'] in ('positive', 'negative')
        assert 0.0 <= result['positive_prob'] <= 1.0
        assert abs(result['positive_prob'] + result['negative_prob'] - 1.0) < 0.01
        assert 'blend_weights' in result
        assert abs(result['blend_weights']['en'] + result['blend_weights']['vi'] - 1.0) < 0.01

    def test_blend_high_en_confidence_prefers_en(self):
        from src.multilingual import _blend_results
        en = {"sentiment": "positive", "confidence": 0.95, "positive_prob": 0.95, "negative_prob": 0.05}
        vi = {"sentiment": "negative", "confidence": 0.55, "positive_prob": 0.45, "negative_prob": 0.55}
        result = _blend_results(en, vi, lang_conf=0.85)  # EN confident
        assert result['sentiment'] == 'positive'

    def test_predict_multilingual_vi_high_conf(self):
        import pickle
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'best_model_v2.pkl')
        with open(model_path, 'rb') as f:
            en_model = pickle.load(f)
        from src.multilingual import predict_multilingual
        r = predict_multilingual("Sản phẩm này cực kỳ tuyệt vời, tôi rất hài lòng", en_model)
        assert r['language'] == 'vi'
        assert r['sentiment'] in ('positive', 'negative')

    def test_predict_multilingual_en_high_conf(self):
        import pickle
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'best_model_v2.pkl')
        with open(model_path, 'rb') as f:
            en_model = pickle.load(f)
        from src.multilingual import predict_multilingual
        r = predict_multilingual("This movie is absolutely fantastic and I loved every minute", en_model)
        assert r['language'] == 'en'
        assert r['sentiment'] == 'positive'

    def test_predict_multilingual_mixed_text(self):
        """Code-switching: Vừa VI vừa EN → blend"""
        import pickle
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'best_model_v2.pkl')
        with open(model_path, 'rb') as f:
            en_model = pickle.load(f)
        from src.multilingual import predict_multilingual
        r = predict_multilingual("sản phẩm này really good, tôi thích lắm", en_model)
        assert r['sentiment'] in ('positive', 'negative')
        assert 'confidence' in r


# ── 2. Context-aware analysis ──────────────────────────────────────
class TestContextAnalyzer:
    def _mock_predict(self, text: str):
        """Mock predict: 'good' → positive, else negative"""
        pos = 0.8 if 'good' in text.lower() or 'great' in text.lower() else 0.2
        return {
            'sentiment': 'positive' if pos >= 0.5 else 'negative',
            'confidence': pos if pos >= 0.5 else 1 - pos,
            'positive_prob': pos,
            'negative_prob': 1 - pos,
        }

    def test_build_reply_threads(self):
        from src.context_analyzer import build_reply_threads
        comments = [
            {'text': '@Alice nice video!', 'author': 'Bob'},
            {'text': '@Alice agree with you', 'author': 'Charlie'},
            {'text': 'just a comment', 'author': 'Dave'},
        ]
        threads = build_reply_threads(comments)
        assert 'Alice' in threads
        assert len(threads['Alice']) == 2

    def test_get_context_window_returns_float(self):
        from src.context_analyzer import get_context_window
        comments = [
            {'text': 'good product', 'author': 'A'},
            {'text': 'great item', 'author': 'B'},
            {'text': 'bad quality', 'author': 'C'},
            {'text': 'good value', 'author': 'D'},
            {'text': 'mediocre', 'author': 'E'},
        ]
        avg = get_context_window(2, comments, self._mock_predict, window=2)
        assert avg is not None
        assert 0.0 <= avg <= 1.0

    def test_adjust_with_context_positive_boost(self):
        from src.context_analyzer import adjust_with_context
        result = {'sentiment': 'positive', 'confidence': 0.6, 'positive_prob': 0.6, 'negative_prob': 0.4}
        adjusted = adjust_with_context(result, context_pos_avg=0.8)
        assert adjusted['positive_prob'] > result['positive_prob']
        assert adjusted['context_adjusted'] is True

    def test_adjust_with_context_none_no_change(self):
        from src.context_analyzer import adjust_with_context
        result = {'sentiment': 'positive', 'confidence': 0.7, 'positive_prob': 0.7, 'negative_prob': 0.3}
        adjusted = adjust_with_context(result, context_pos_avg=None)
        assert adjusted['context_adjusted'] is False
        assert adjusted['positive_prob'] == result['positive_prob']

    def test_analyze_with_context_full_pipeline(self):
        from src.context_analyzer import analyze_with_context
        comments = [
            {'text': 'good product', 'author': 'A', 'votes': 5},
            {'text': 'great item',   'author': 'B', 'votes': 2},
            {'text': 'bad quality',  'author': 'C', 'votes': 0},
            {'text': 'good value',   'author': 'D', 'votes': 1},
        ]
        results = analyze_with_context(comments, self._mock_predict, use_context=True)
        assert len(results) == 4
        for r in results:
            assert 'sentiment' in r
            assert 'context_adjusted' in r
            assert 'author' in r

    def test_analyze_without_context(self):
        from src.context_analyzer import analyze_with_context
        comments = [{'text': 'good', 'author': 'A', 'votes': 0}]
        results = analyze_with_context(comments, self._mock_predict, use_context=False)
        assert results[0]['context_adjusted'] is False


# ── 3. Video analyzer (mock / unit) ───────────────────────────────
class TestVideoAnalyzer:
    def test_import(self):
        from src.video_analyzer import analyze_video_bytes, analyze_video_file
        assert callable(analyze_video_bytes)
        assert callable(analyze_video_file)

    def test_analyze_video_bytes_invalid(self):
        from src.video_analyzer import analyze_video_bytes
        with pytest.raises(Exception):
            analyze_video_bytes(b"not a video", "test.mp4")

    def test_emotions_constants(self):
        from src.video_analyzer import EMOTIONS, EMOTION_VI, POSITIVE_EMOTIONS, NEGATIVE_EMOTIONS
        assert len(EMOTIONS) == 7
        assert 'happy' in POSITIVE_EMOTIONS
        assert 'angry' in NEGATIVE_EMOTIONS
        assert set(EMOTION_VI.keys()) == set(EMOTIONS)

    def test_sentiment_coverage(self):
        """Tất cả emotions phải được map sang sentiment category"""
        from src.video_analyzer import EMOTIONS, POSITIVE_EMOTIONS, NEGATIVE_EMOTIONS
        for e in EMOTIONS:
            assert e in POSITIVE_EMOTIONS or e in NEGATIVE_EMOTIONS or e == 'neutral', \
                f"{e} không được map"


# ── Sprint 10 QA fixes ─────────────────────────────────────────────

class TestEmojiSentiment:
    def test_emoji_score_positive(self):
        from src.multilingual import emoji_score
        assert emoji_score("tuyệt vời 😍❤️🔥") > 0

    def test_emoji_score_negative(self):
        from src.multilingual import emoji_score
        assert emoji_score("thất vọng 💀😭😤") < 0

    def test_emoji_score_mixed(self):
        from src.multilingual import emoji_score
        # 2 positive, 2 negative → 0
        score = emoji_score("😍😊💀😭")  # 2 pos, 2 neg
        assert score == 0.0

    def test_emoji_score_no_emoji(self):
        from src.multilingual import emoji_score
        assert emoji_score("great movie no emoji") == 0.0

    def test_apply_emoji_blend_missing_keys(self):
        from src.multilingual import _apply_emoji_blend
        result = {"sentiment": "positive", "confidence": 0.8}  # no positive_prob
        out = _apply_emoji_blend(result, "😍😍")
        assert out == result  # guard: return unchanged

    def test_apply_emoji_blend_weight(self):
        from src.multilingual import _apply_emoji_blend
        base = {"positive_prob": 0.8, "negative_prob": 0.2,
                "sentiment": "positive", "confidence": 0.8}
        out = _apply_emoji_blend(base, "💀💀💀")  # all negative emoji
        assert out["positive_prob"] < 0.8  # emoji pulled it down
        assert "emoji_score" in out
        assert out["emoji_score"] < 0


class TestFeedbackAPI:
    def test_feedback_post(self, client):
        resp = client.post("/feedback", json={
            "text": "phim hay", "predicted": "positive",
            "correct": True, "user_label": None
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_feedback_stats_empty(self, client):
        resp = client.get("/feedback/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "accuracy" in data

    def test_feedback_stats_accuracy(self, client):
        # Post 2 correct, 1 wrong
        for correct in [True, True, False]:
            client.post("/feedback", json={
                "text": "test", "predicted": "positive", "correct": correct
            })
        resp = client.get("/feedback/stats")
        data = resp.json()
        assert data["total"] >= 3
        assert data["correct"] >= 2

    def test_feedback_invalid_body(self, client):
        resp = client.post("/feedback", json={"text": "missing fields"})
        assert resp.status_code == 422
