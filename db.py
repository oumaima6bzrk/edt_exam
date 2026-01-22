# db.py - Version améliorée
import psycopg2
import os
from dotenv import load_dotenv
import sys

# Charger les variables d'environnement
load_dotenv()

def get_connection():
    """Établir la connexion à Neon PostgreSQL"""
    try:
        # Récupérer l'URL depuis les variables d'environnement
        database_url = os.getenv("DATABASE_URL")
        
        if not database_url:
            print("❌ ERREUR: DATABASE_URL non configuré dans .env")
            return None
        
        # Nettoyer l'URL (enlever les espaces)
        database_url = database_url.strip()
        
        print(f"🔗 Connexion à Neon...")
        print(f"URL: {database_url[:50]}...")
        
        # Pour Neon, on utilise directement l'URL
        # Le paramètre sslmode est déjà dans l'URL (?sslmode=require)
        conn = psycopg2.connect(database_url)
        
        # Tester la connexion
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        
        print("✅ Connexion à Neon PostgreSQL établie avec succès!")
        return conn
        
    except Exception as e:
        print(f"❌ Erreur de connexion PostgreSQL: {e}")
        
        # Afficher des informations détaillées
        if hasattr(e, 'pgerror'):
            print(f"   Détails: {e.pgerror}")
        
        # Suggestions de dépannage
        print("\n🔧 Suggestions de dépannage:")
        print("1. Vérifiez votre connexion Internet")
        print("2. Vérifiez que l'URL Neon est correcte")
        print("3. Vérifiez que votre projet Neon est actif")
        print("4. Essayez sans &channel_binding=require")
        
        return None

# Fonction utilitaire pour tester la connexion
def test_connection():
    """Tester la connexion et afficher les informations"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Informations sur la base de données
            cursor.execute("SELECT current_database(), current_user, version()")
            db_info = cursor.fetchone()
            
            print("\n📊 Informations de la base de données:")
            print(f"   Base: {db_info[0]}")
            print(f"   Utilisateur: {db_info[1]}")
            print(f"   Version: {db_info[2].split(',')[0]}")
            
            # Liste des tables
            cursor.execute("""
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            print(f"\n📋 Tables disponibles ({len(tables)}):")
            for table in tables:
                print(f"   • {table[0]} ({table[1]})")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors des requêtes: {e}")
            return False
    else:
        return False

if __name__ == "__main__":
    print("🔧 Test de connexion à Neon PostgreSQL")
    print("=" * 50)
    
    if test_connection():
        print("\n✅ La connexion fonctionne correctement!")
    else:
        print("\n❌ La connexion a échoué")