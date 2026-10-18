"""Sistem Pendeteksi Pesan Penipuan Online - FastAPI backend."""

import sys
from pathlib import Path

# The canonical preprocessing and model artifacts live in the top-level `ml/`
# package. Make the repository root importable when the API runs from backend/.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

__version__ = "0.1.0"
