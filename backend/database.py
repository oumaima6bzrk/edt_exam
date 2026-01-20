import mysql.connector
from mysql.connector import Error
import hashlib  # Ajout de l'import pour le hachage
import os 
def get_connection():
    """Établir la connexion à la base de données"""
    try:
        # Pour la production (Render)
        if os.environ.get('RENDER'):
            connection = mysql.connector.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                user=os.environ.get('DB_USER', 'root'),
                password=os.environ.get('DB_PASSWORD', ''),
                database=os.environ.get('DB_NAME', 'edt_exam'),
                charset='utf8mb4'
            )
        # Pour le développement local
        else:
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="edt_exam",
                charset='utf8mb4'
            )
        return connection
    except Error as e:
        print(f"Erreur de connexion à MySQL: {e}")
        return None

def hash_password(password):
    """Hacher un mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(email, password):
    """Vérifier les identifiants de l'utilisateur avec mot de passe haché"""
    conn = get_connection()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # D'abord, récupérer l'utilisateur par email
        query_find_user = "SELECT * FROM users WHERE email = %s"
        cursor.execute(query_find_user, (email,))
        user_data = cursor.fetchone()
        
        if not user_data:
            cursor.close()
            conn.close()
            return None
        
        # Vérifier si le mot de passe est stocké en clair ou haché
        # (On suppose que les mots de passe hachés ont une longueur de 64 caractères pour SHA-256)
        stored_password = user_data['password']
        
        # Si le mot de passe stocké a 64 caractères, c'est probablement un hash SHA-256
        if len(stored_password) == 64:
            # Hacher le mot de passe fourni pour comparaison
            hashed_password = hash_password(password)
            password_matches = (stored_password == hashed_password)
        else:
            # Sinon, comparer en clair (pour la transition)
            password_matches = (stored_password == password)
        
        if not password_matches:
            cursor.close()
            conn.close()
            return None
        
        # Si l'authentification réussit, récupérer les informations complètes
        query = """
        SELECT u.id, u.email, u.role, u.is_active,
               CASE 
                   WHEN u.role = 'ETUDIANT' THEN e.id
                   WHEN u.role = 'PROF' THEN p.id
                   ELSE NULL
               END as profile_id,
               CASE 
                   WHEN u.role = 'ETUDIANT' THEN e.groupe_id
                   ELSE NULL
               END as groupe_id
        FROM users u
        LEFT JOIN etudiants e ON u.id = e.user_id AND u.role = 'ETUDIANT'
        LEFT JOIN professeurs p ON u.id = p.user_id AND u.role = 'PROF'
        WHERE u.email = %s
        """
        
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return user
        
    except Error as e:
        print(f"Erreur lors de la vérification: {e}")
        return None

def create_user(email, password, role):
    """Créer un nouvel utilisateur avec mot de passe haché"""
    conn = get_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Hacher le mot de passe avant de le stocker
        hashed_password = hash_password(password)
        
        query = """
        INSERT INTO users (email, password, role, is_active, created_at)
        VALUES (%s, %s, %s, %s, NOW())
        """
        
        cursor.execute(query, (email, hashed_password, role, 1))
        conn.commit()
        
        user_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        return user_id
        
    except Error as e:
        print(f"Erreur lors de la création d'utilisateur: {e}")
        conn.rollback()
        return False

def update_user_password(user_id, new_password):
    """Mettre à jour le mot de passe d'un utilisateur avec hachage"""
    conn = get_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Hacher le nouveau mot de passe
        hashed_password = hash_password(new_password)
        
        query = "UPDATE users SET password = %s WHERE id = %s"
        
        cursor.execute(query, (hashed_password, user_id))
        conn.commit()
        
        affected_rows = cursor.rowcount
        
        cursor.close()
        conn.close()
        
        return affected_rows > 0
        
    except Error as e:
        print(f"Erreur lors de la mise à jour du mot de passe: {e}")
        conn.rollback()
        return False

def verify_password_strength(password):
    """Vérifier la force du mot de passe"""
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"
    
    if not any(char.isdigit() for char in password):
        return False, "Le mot de passe doit contenir au moins un chiffre"
    
    if not any(char.isupper() for char in password):
        return False, "Le mot de passe doit contenir au moins une majuscule"
    
    if not any(char.islower() for char in password):
        return False, "Le mot de passe doit contenir au moins une minuscule"
    
    return True, "Mot de passe valide"

# Fonctions existantes inchangées
def fetch_all_users():
    """Récupérer tous les utilisateurs (pour admin)"""
    conn = get_connection()
    if conn is None:
        return []
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

def fetch_etudiants():
    """Récupérer la liste des étudiants"""
    conn = get_connection()
    if conn is None:
        return []
    
    cursor = conn.cursor(dictionary=True)
    query = """
    SELECT u.id, u.email, e.groupe_id
    FROM etudiants e
    JOIN users u ON e.user_id = u.id
    WHERE u.role = 'ETUDIANT'
    """
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

def fetch_professeurs():
    """Récupérer la liste des professeurs"""
    conn = get_connection()
    if conn is None:
        return []
    
    cursor = conn.cursor(dictionary=True)
    query = """
    SELECT p.id, p.specialite, p.departement_id, u.email, u.is_active, d.nom as departement
    FROM professeurs p
    JOIN users u ON p.user_id = u.id
    JOIN departements d ON p.departement_id = d.id
    WHERE u.role = 'PROF'
    """
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

def fetch_salles():
    """Récupérer la liste des salles"""
    conn = get_connection()
    if conn is None:
        return []
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM salles ORDER BY type, nom")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

def fetch_examens():
    """Récupérer la liste des examens"""
    conn = get_connection()
    if conn is None:
        return []
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.*, m.nom as module_nom, f.nom as formation_nom
        FROM examens e
        JOIN modules m ON e.module_id = m.id
        JOIN formations f ON e.formation_id = f.id
        ORDER BY e.date_examen, e.heure_debut
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

def fetch_formations():
    """Récupérer la liste des formations"""
    conn = get_connection()
    if conn is None:
        return []
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
      SELECT f.id, f.nom, d.nom as departement
FROM formations f
JOIN departements d ON f.departement_id = d.id
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

# Test rapide avec vérification de mot de passe
if __name__ == "__main__":
    # Test de connexion
    try:
        conn = get_connection()
        if conn:
            print("✅ Connexion MySQL réussie")
            
            # Test de hachage de mot de passe
            test_password = "MonMotDePasse123"
            hashed = hash_password(test_password)
            print(f"✅ Test de hachage: '{test_password}' -> '{hashed}'")
            print(f"   Longueur du hash: {len(hashed)} caractères")
            
            # Test de vérification de mot de passe
            print(f"\n✅ Test de vérification:")
            print(f"   Mot de passe correct: {hash_password(test_password) == hashed}")
            print(f"   Mot de passe incorrect: {hash_password('wrong') == hashed}")
            
            # Test de force de mot de passe
            print(f"\n✅ Test de force de mot de passe:")
            test_passwords = [
                "short",
                "nouppercase123",
                "NOLOWERCASE123",
                "NoNumbers",
                "ValidPass123"
            ]
            
            for pwd in test_passwords:
                is_valid, message = verify_password_strength(pwd)
                status = "✅" if is_valid else "❌"
                print(f"   {status} '{pwd}': {message}")
            
            conn.close()
        else:
            print("❌ Échec de connexion MySQL")
    except Exception as e:
        print(f"❌ Erreur: {e}")
def fetch_examens_by_session_grouped(session_id):
    """Récupérer les examens d'une session groupés par formation et groupe"""
    conn = get_connection()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT e.*, 
                   m.nom as module_nom, 
                   f.nom as formation_nom,
                   s.nom as salle_nom,
                   g.nom as groupe_nom,
                   g.effectif as groupe_effectif
            FROM examens e
            JOIN modules m ON e.module_id = m.id
            JOIN formations f ON e.formation_id = f.id
            JOIN groupes g ON e.groupe_id = g.id
            LEFT JOIN salles s ON e.salle_id = s.id
            WHERE e.session_id = %s
            ORDER BY f.nom, g.nom, e.date_examen, e.heure_debut
        """, (session_id,))
        
        examens = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return examens
    except Error as e:
        print(f"Erreur: {e}")
        return []
        # Ajouter à votre fichier database.py existant

def create_session(nom, date_debut, date_fin):
    """Créer une nouvelle session d'examens avec vérification de doublon"""
    conn = get_connection()
    if conn is None:
        return {"success": False, "message": "Erreur de connexion", "session_id": None}
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Vérifier si une session similaire existe déjà
        cursor.execute("""
            SELECT id, nom, date_debut, date_fin 
            FROM sessions_examens 
            WHERE nom = %s 
            AND (
                (date_debut BETWEEN %s AND %s) 
                OR (date_fin BETWEEN %s AND %s)
                OR (%s BETWEEN date_debut AND date_fin)
                OR (%s BETWEEN date_debut AND date_fin)
            )
        """, (nom, date_debut, date_fin, date_debut, date_fin, date_debut, date_fin))
        
        existing_session = cursor.fetchone()
        
        if existing_session:
            cursor.close()
            conn.close()
            return {
                "success": False, 
                "message": f"Une session '{nom}' existe déjà sur cette période ({existing_session['date_debut']} au {existing_session['date_fin']})",
                "session_id": None,
                "existing_session": existing_session
            }
        
        # Si pas de doublon, créer la session
        cursor.execute("""
            INSERT INTO sessions_examens (nom, date_debut, date_fin, statut)
            VALUES (%s, %s, %s, 'CREATION')
        """, (nom, date_debut, date_fin))
        
        session_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"Session '{nom}' créée avec succès",
            "session_id": session_id,
            "existing_session": None
        }
        
    except Error as e:
        print(f"Erreur création session: {e}")
        if conn:
            conn.rollback()
        return {"success": False, "message": str(e), "session_id": None}

def fetch_examens_by_status(statut):
    """Récupérer les examens par statut"""
    conn = get_connection()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT e.*, m.nom as module_nom, f.nom as formation_nom,
                   s.nom as salle_nom, g.nom as groupe_nom
            FROM examens e
            JOIN modules m ON e.module_id = m.id
            JOIN formations f ON e.formation_id = f.id
            LEFT JOIN salles s ON e.salle_id = s.id
            LEFT JOIN groupes g ON e.groupe_id = g.id
            WHERE e.statut = %s
            ORDER BY e.date_examen, e.heure_debut
        """, (statut,))
        
        examens = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return examens
    except Error as e:
        print(f"Erreur: {e}")
        return []

def update_examen_statut(examen_id, nouveau_statut, user_id=None):
    """Mettre à jour le statut d'un examen"""
    conn = get_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        query = """
            UPDATE examens 
            SET statut = %s, 
                last_modified = NOW(),
                modified_by = %s
            WHERE id = %s
        """
        
        cursor.execute(query, (nouveau_statut, user_id, examen_id))
        conn.commit()
        
        affected_rows = cursor.rowcount
        
        cursor.close()
        conn.close()
        
        return affected_rows > 0
        
    except Error as e:
        print(f"Erreur mise à jour statut: {e}")
        return False
    
    
def fetch_sessions():
    """Récupérer toutes les sessions"""
    conn = get_connection()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.*, COUNT(e.id) as nb_examens
            FROM sessions_examens s
            LEFT JOIN examens e ON s.id = e.session_id
            GROUP BY s.id
            ORDER BY s.date_debut DESC
        """)
        sessions = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return sessions
    except Error as e:
        print(f"Erreur fetch sessions: {e}")
        return []

def check_session_exists(nom, date_debut, date_fin):
    """Vérifier si une session avec le même nom et dates existe déjà"""
    conn = get_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM sessions_examens 
            WHERE nom = %s 
            AND (
                (date_debut BETWEEN %s AND %s) 
                OR (date_fin BETWEEN %s AND %s)
                OR (%s BETWEEN date_debut AND date_fin)
                OR (%s BETWEEN date_debut AND date_fin)
            )
        """, (nom, date_debut, date_fin, date_debut, date_fin, date_debut, date_fin))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return result['count'] > 0 if result else False
        
    except Error as e:
        print(f"Erreur vérification session: {e}")
        return False


def fetch_examens_by_session(session_id):
    """Récupérer les examens d'une session"""
    conn = get_connection()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT e.*, m.nom as module_nom, f.nom as formation_nom,
                   s.nom as salle_nom
            FROM examens e
            JOIN modules m ON e.module_id = m.id
            JOIN formations f ON e.formation_id = f.id
            LEFT JOIN salles s ON e.salle_id = s.id
            WHERE e.session_id = %s
            ORDER BY e.date_examen, e.heure_debut
        """, (session_id,))
        
        examens = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return examens
    except Error as e:
        print(f"Erreur: {e}")
        return []

def generate_exams_for_session(session_id, formation_ids):
    """Générer les examens pour une session"""
    conn = get_connection()
    if conn is None:
        return {"success": False, "message": "Erreur connexion"}
    
    try:
        cursor = conn.cursor(dictionary=True)
        exams_created = 0
        
        for formation_id in formation_ids:
            cursor.execute("SELECT id FROM modules WHERE formation_id = %s", (formation_id,))
            modules = cursor.fetchall()
            
            for module in modules:
                cursor.execute("""
                    SELECT id FROM examens 
                    WHERE module_id = %s AND session_id = %s
                """, (module['id'], session_id))
                
                if cursor.fetchone():
                    continue
                
                # MODIFICATION ICI : Créer avec statut 'EN_ATTENTE' au lieu de 'A_CREER'
                cursor.execute("""
                    INSERT INTO examens (
                        module_id, formation_id, session_id,
                        duree_minutes, priorite, statut
                    ) VALUES (%s, %s, %s, 90, 2, 'EN_ATTENTE')
                """, (module['id'], formation_id, session_id))
                
                exams_created += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"{exams_created} examens générés (en attente de validation)",
            "exams_created": exams_created
        }
        
    except Error as e:
        print(f"Erreur génération examens: {e}")
        return {"success": False, "message": str(e)}
    
    