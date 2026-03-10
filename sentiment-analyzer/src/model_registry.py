"""
📦 Sprint 6 — Model Registry & Versioning
Quản lý nhiều model version, switch model không cần restart
"""
import os, pickle, json, glob, logging
from datetime import datetime

log = logging.getLogger(__name__)
MODELS_DIR = os.path.join(os.path.dirname(__file__), '../models')

class ModelRegistry:
    def __init__(self, models_dir: str = MODELS_DIR):
        self._dir = models_dir
        self._models = {}      # version → model object
        self._metadata = {}    # version → metadata dict
        self._active = None
        os.makedirs(models_dir, exist_ok=True)
        self._load_all()

    def _load_all(self):
        """Scan models/ và load tất cả .pkl có metadata"""
        pattern = os.path.join(self._dir, 'model_*.pkl')
        for path in sorted(glob.glob(pattern)):
            version = os.path.basename(path).replace('.pkl','').replace('model_','')
            meta_path = path.replace('.pkl', '_meta.json')
            try:
                with open(path, 'rb') as f:
                    self._models[version] = pickle.load(f)
                if os.path.exists(meta_path):
                    with open(meta_path) as f:
                        self._metadata[version] = json.load(f)
                else:
                    self._metadata[version] = {"version": version, "path": path}
                log.info(f"📦 Loaded model version: {version}")
            except Exception as e:
                log.warning(f"⚠️  Failed to load {path}: {e}")

        # Load best_model_v2 làm active mặc định
        best_path = os.path.join(self._dir, 'best_model_v2.pkl')
        if os.path.exists(best_path):
            with open(best_path, 'rb') as f:
                self._models['latest'] = pickle.load(f)
            self._metadata['latest'] = {"version": "latest", "path": best_path,
                                         "accuracy": 0.8937, "note": "Best tuned model"}
            self._active = 'latest'
            log.info("✅ Active model: latest (best_model_v2)")

    def register(self, model, accuracy: float, notes: str = "") -> str:
        """Đăng ký model mới, trả về version string"""
        version = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(self._dir, f'model_{version}.pkl')
        meta = {"version": version, "accuracy": accuracy,
                "registered_at": datetime.now().isoformat(), "notes": notes, "path": path}
        with open(path, 'wb') as f:
            pickle.dump(model, f)
        with open(path.replace('.pkl','_meta.json'), 'w') as f:
            json.dump(meta, f, indent=2)
        self._models[version] = model
        self._metadata[version] = meta
        log.info(f"✅ Registered model v{version} (acc={accuracy:.4f})")
        return version

    def activate(self, version: str):
        if version not in self._models:
            raise ValueError(f"Version '{version}' not found. Available: {self.list_versions()}")
        self._active = version
        log.info(f"🔄 Active model switched to: {version}")

    def get_active(self):
        return self._models[self._active]

    def list_versions(self):
        return [
            {**self._metadata.get(v, {}), "active": v == self._active}
            for v in self._models
        ]

    @property
    def active_version(self):
        return self._active

    @property
    def active_metadata(self):
        return self._metadata.get(self._active, {})


registry = ModelRegistry()
