"""Re-exports evaluation metric computation. Source of truth: backend/app/services/evaluation_service.py."""

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.services.evaluation_service import compute_metrics  # noqa: E402,F401
