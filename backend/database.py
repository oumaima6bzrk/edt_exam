# backend/database.py - VERSION CORRIGÉE
import psycopg2
from psycopg2 import Error
import hashlib
import os
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def get_connection():
    """Établir la connexion à Neon PostgreSQL"""
    try:
        print("🔗 Tentative de connexion à Neon PostgreSQL...")
        
        # Récupérer l'URL depuis .env
        database_url = os.getenv("DATABASE_URL")
        
        if not database_url:
            print("❌ DATABASE_URL non trouvé dans .env")
            print("Créez un fichier .env avec: DATABASE_URL=votre_url_neon")
            return None
        
        # Nettoyer l'URL
        database_url = database_url.strip()
        print(f"URL utilisée: {database_url[:50]}...")
        
        # Établir la connexion
        conn = psycopg2.connect(database_url, sslmode="require")
        print("✅ Connexion à Neon PostgreSQL réussie!")
        return conn
        
    except Error as e:
        print(f"❌ ERREUR de connexion PostgreSQL: {e}")
        print("\n🔧 Dépannage:")
        print("1. Vérifiez votre fichier .env")
        print("2. Vérifiez votre mot de passe Neon")
        print("3. Vérifiez votre connexion Internet")
        return None
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return None

def hash_password(password):
    """Hacher un mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(email, password):
    """Vérifier les identifiants de l'utilisateur avec mot de passe haché"""
    print(f"🔐 Vérification de l'utilisateur: {email}")
    
    conn = get_connection()
    if conn is None:
        print("❌ Impossible de se connecter à la base de données")
        return None
    
    try:
        cursor = conn.cursor()
        
        # Récupérer l'utilisateur par email
        query = "SELECT id, email, password, role, is_active, created_at FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        user_data = cursor.fetchone()
        
        if not user_data:
            print(f"❌ Utilisateur {email} non trouvé")
            cursor.close()
            conn.close()
            return None
        
        # Créer le dictionnaire utilisateur
        user_dict = {
            'id': user_data[0],
            'email': user_data[1],
            'password': user_data[2],
            'role': user_data[3],
            'is_active': user_data[4],
            'created_at': user_data[5]
        }
        
        print(f"✅ Utilisateur trouvé: {user_dict['email']} (Rôle: {user_dict['role']})")
        
        # Vérifier le mot de passe
        stored_password = user_dict['password']
        hashed_password = hash_password(password)
        
        print(f"🔐 Comparaison mot de passe:")
        print(f"  - Stocké: {stored_password[:20]}...")
        print(f"  - Fourni: {hashed_password[:20]}...")
        
        if stored_password != hashed_password:
            print("❌ Mot de passe incorrect")
            cursor.close()
            conn.close()
            return None
        
        print("✅ Mot de passe correct")
        
        # Récupérer les infos complètes selon le rôle
        if user_dict['role'] == 'ETUDIANT':
            cursor.execute("""
                SELECT e.id, e.groupe_id
                FROM etudiants e
                WHERE e.user_id = %s
            """, (user_dict['id'],))
            result = cursor.fetchone()
            if result:
                user_dict['profile_id'] = result[0]
                user_dict['groupe_id'] = result[1]
                print(f"👨‍🎓 Étudiant: groupe_id={result[1]}")
        
        elif user_dict['role'] == 'PROF':
            cursor.execute("""
                SELECT p.id, p.departement_id
                FROM professeurs p
                WHERE p.user_id = %s
            """, (user_dict['id'],))
            result = cursor.fetchone()
            if result:
                user_dict['profile_id'] = result[0]
                user_dict['departement_id'] = result[1]
                print(f"👨‍🏫 Professeur: département_id={result[1]}")
        
        elif user_dict['role'] == 'CHEF_DEPT':
            # Pour chef de département, on peut avoir un département associé
            cursor.execute("""
                SELECT u.departement_id 
                FROM users u 
                WHERE u.id = %s
            """, (user_dict['id'],))
            result = cursor.fetchone()
            if result and result[0]:
                user_dict['departement_id'] = result[0]
        
        cursor.close()
        conn.close()
        
        print(f"🎉 Authentification réussie pour {email}")
        return user_dict
        
    except Error as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return None
    finally:
        if conn:
            conn.close()

def authenticate_user(email, password):
    """Alias pour verify_user pour compatibilité"""
    return verify_user(email, password)

# ... (gardez le reste de vos fonctions existantes) ...

# Test de connexion au démarrage
if __name__ == "__main__":
    print("🧪 Test de connexion à la base de données...")
    print("=" * 50)
    
    # Tester la connexion
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Tester quelques requêtes
            cursor.execute("SELECT version();")
            print(f"📊 PostgreSQL: {cursor.fetchone()[0]}")
            
            # Compter les utilisateurs
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"👥 Nombre d'utilisateurs: {user_count}")
            
            # Lister les utilisateurs
            if user_count > 0:
                cursor.execute("SELECT email, role FROM users LIMIT 5")
                users = cursor.fetchall()
                print("📋 5 premiers utilisateurs:")
                for email, role in users:
                    print(f"  - {email} ({role})")
            
            cursor.close()
            conn.close()
            print("\n✅ Test de connexion réussi!")
            
        except Exception as e:
            print(f"❌ Erreur lors des requêtes: {e}")
    else:
        print("\n❌ Échec de la connexion")