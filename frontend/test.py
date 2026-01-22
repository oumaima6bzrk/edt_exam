import sys
import os

# إضافة جذر المشروع للـ PYTHONPATH
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.database import verify_user

print("✅ backend.database importé avec succès")

# Test simple
user = verify_user("admin@univ.dz", "admin123")
print("Résultat:", user)
