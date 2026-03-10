"""
Sprint 9 — Video Facial Emotion Analyzer
Stack: OpenCV face detection + DeepFace emotion analysis
Emotions: angry, disgust, fear, happy, sad, surprise, neutral
Sentiment: positive=[happy,surprise], negative=[angry,disgust,fear,sad], neutral=[neutral]
"""
import os
import tempfile
from typing import List, Dict

EMOTIONS = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
POSITIVE_EMOTIONS = {'happy', 'surprise'}
NEGATIVE_EMOTIONS = {'angry', 'disgust', 'fear', 'sad'}
EMOTION_VI = {
    'angry': 'tức giận', 'disgust': 'ghê tởm', 'fear': 'sợ hãi',
    'happy': 'vui vẻ',   'sad': 'buồn',         'surprise': 'ngạc nhiên',
    'neutral': 'trung tính',
}

_deepface_loaded = False

def _ensure_deepface():
    global _deepface_loaded
    if not _deepface_loaded:
        from deepface import DeepFace  # noqa
        _deepface_loaded = True

def analyze_frame_emotions(frame) -> List[Dict]:
    """Analyze emotions in a single frame using DeepFace"""
    _ensure_deepface()
    from deepface import DeepFace
    try:
        results = DeepFace.analyze(
            frame,
            actions=['emotion'],
            enforce_detection=False,
            silent=True
        )
        if not isinstance(results, list):
            results = [results]
        out = []
        for r in results:
            em = r.get('emotion', {})
            dom = r.get('dominant_emotion', 'neutral').lower()
            dom = dom if dom in EMOTIONS else 'neutral'
            probs = {e: round(em.get(e, 0.0) / 100.0, 4) for e in EMOTIONS}
            out.append({
                'dominant_emotion': dom,
                'dominant_emotion_vi': EMOTION_VI[dom],
                'confidence': round(probs[dom], 4),
                'probabilities': probs,
            })
        return out
    except Exception:
        return []

def analyze_video_file(video_path: str, sample_fps: float = 1.0) -> Dict:
    """Sample video at sample_fps, detect faces+emotions, return sentiment summary"""
    import cv2
    import numpy as np
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Không mở được video: {video_path}")

    video_fps  = cap.get(cv2.CAP_PROP_FPS) or 25
    total_f    = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration   = total_f / video_fps
    frame_step = max(1, int(video_fps / sample_fps))

    emotion_counts: Dict[str, float] = {e: 0.0 for e in EMOTIONS}
    total_detections = 0
    frames_processed = 0
    idx = 0

    while cap.isOpened() and frames_processed < 300:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % frame_step == 0:
            detections = analyze_frame_emotions(frame)
            for d in detections:
                for e in EMOTIONS:
                    emotion_counts[e] += d['probabilities'].get(e, 0.0)
                total_detections += 1
            frames_processed += 1
        idx += 1
    cap.release()

    if total_detections == 0:
        return {
            'sentiment': 'neutral', 'confidence': 0.5,
            'positive_prob': 0.5,   'negative_prob': 0.5,
            'emotion_distribution': {e: 0.0 for e in EMOTIONS},
            'emotion_distribution_vi': {},
            'dominant_emotion': 'neutral', 'dominant_emotion_vi': 'trung tính',
            'total_faces_detected': 0, 'frames_analyzed': frames_processed,
            'duration_sec': round(duration, 1),
            'note': 'Không phát hiện khuôn mặt trong video', 'method': 'facial_emotion_deepface'
        }

    dist = {e: round(emotion_counts[e] / total_detections, 4) for e in EMOTIONS}
    pos  = sum(dist[e] for e in POSITIVE_EMOTIONS)
    neg  = sum(dist[e] for e in NEGATIVE_EMOTIONS)
    neu  = dist['neutral']
    denom = pos + neg + neu * 0.5 or 1.0
    adj_pos = pos / denom
    adj_neg = neg / denom

    dominant = max(dist, key=dist.get)
    sentiment = 'positive' if adj_pos > adj_neg else ('negative' if adj_neg > adj_pos else 'neutral')

    return {
        'sentiment': sentiment,
        'confidence': round(max(adj_pos, adj_neg), 4),
        'positive_prob': round(adj_pos, 4),
        'negative_prob': round(adj_neg, 4),
        'emotion_distribution': dist,
        'emotion_distribution_vi': {EMOTION_VI[e]: round(dist[e]*100, 1) for e in EMOTIONS},
        'dominant_emotion': dominant,
        'dominant_emotion_vi': EMOTION_VI[dominant],
        'total_faces_detected': total_detections,
        'frames_analyzed': frames_processed,
        'duration_sec': round(duration, 1),
        'method': 'facial_emotion_deepface'
    }

def analyze_video_bytes(video_bytes: bytes, filename: str = 'upload.mp4') -> Dict:
    """API entry point — nhận bytes, lưu temp, analyze, cleanup"""
    suffix = os.path.splitext(filename)[1] or '.mp4'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name
    try:
        return analyze_video_file(tmp_path)
    finally:
        os.unlink(tmp_path)
