# test_neon.py
from backend.database import get_connection, fetch_formations, fetch_salles

print("🧪 Test de connexion Neon PostgreSQL...")

# Test 1: Connexion simple
conn = get_connection()
if conn:
    print("✅ 1. Connexion réussie")
    conn.close()
else:
    print("❌ 1. Échec connexion")

# Test 2: Récupérer des données
print("\n📊 Test de récupération des données...")

formations = fetch_formations()
print(f"✅ 2. Formations: {len(formations)} trouvée(s)")
for f in formations[:3]:  # Afficher les 3 premières
    print(f"   - {f['nom']} ({f['departement']})")

salles = fetch_salles()
print(f"✅ 3. Salles: {len(salles)} trouvée(s)")

print("\n🎉 Tests terminés !")