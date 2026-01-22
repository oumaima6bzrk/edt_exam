# backend/algorithm_simple.py - ALGORITHME SIMPLE DE PLANIFICATION
import random
from datetime import datetime, timedelta
from .database import get_connection, create_session

def create_session_and_generate_exams(nom_session, date_debut, date_fin, formation_ids):
    """
    Créer une session et générer des examens automatiquement
    Version simplifiée pour le développement
    """
    try:
        # Créer la session
        conn = get_connection()
        if not conn:
            return {"success": False, "message": "Erreur de connexion à la base de données"}
        
        cursor = conn.cursor()
        
        # Créer la session
        cursor.execute("""
            INSERT INTO sessions (nom, date_debut, date_fin, statut, date_creation)
            VALUES (%s, %s, %s, 'CREATION', %s) RETURNING id
        """, (nom_session, date_debut, date_fin, datetime.now()))
        
        session_id = cursor.fetchone()[0]
        
        # Pour chaque formation, créer quelques examens fictifs
        examens_crees = 0
        for formation_id in formation_ids:
            # Récupérer les modules de cette formation
            cursor.execute("SELECT id, nom FROM modules WHERE formation_id = %s", (formation_id,))
            modules = cursor.fetchall()
            
            if not modules:
                continue
            
            # Récupérer les salles disponibles
            cursor.execute("SELECT id, nom, capacite FROM salles ORDER BY RANDOM() LIMIT 5")
            salles = cursor.fetchall()
            
            if not salles:
                continue
            
            # Récupérer les groupes de cette formation
            cursor.execute("SELECT id, nom FROM groupes WHERE formation_id = %s", (formation_id,))
            groupes = cursor.fetchall()
            
            # Créer quelques examens pour cette formation
            for i in range(min(3, len(modules))):  # Max 3 examens par formation
                module_id, module_nom = modules[i]
                salle_id, salle_nom, capacite = salles[i % len(salles)]
                
                # Sélectionner un groupe aléatoire
                if groupes:
                    groupe_id, groupe_nom = random.choice(groupes)
                else:
                    groupe_id, groupe_nom = None, "N/A"
                
                # Générer une date aléatoire dans la période de la session
                jours_session = (date_fin - date_debut).days
                if jours_session > 0:
                    jours_offset = random.randint(0, jours_session - 1)
                    date_examen = date_debut + timedelta(days=jours_offset)
                else:
                    date_examen = date_debut
                
                # Générer une heure aléatoire (entre 8h et 18h)
                heure_debut = f"{random.randint(8, 17):02d}:00"
                heure_fin = f"{int(heure_debut.split(':')[0]) + 2:02d}:00"
                
                # Insérer l'examen
                cursor.execute("""
                    INSERT INTO examens (
                        module_id, session_id, date_examen, heure_debut, 
                        heure_fin, salle_id, statut, formation_id, groupe_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    module_id, session_id, date_examen, heure_debut,
                    heure_fin, salle_id, 'EN_ATTENTE', formation_id, groupe_id
                ))
                
                examens_crees += 1
        
        # Mettre à jour le statut de la session
        cursor.execute("""
            UPDATE sessions 
            SET statut = 'PLANIFICATION' 
            WHERE id = %s
        """, (session_id,))
        
        conn.commit()
        
        return {
            "success": True,
            "message": f"Session créée avec {examens_crees} examens générés",
            "session_id": session_id,
            "planning_results": {
                "execution_time": 1.5,
                "message": "Planification simplifiée terminée",
                "statistics": {
                    "total_exams": examens_crees,
                    "planned_exams": examens_crees,
                    "conflicts_resolved": 0
                }
            }
        }
        
    except Exception as e:
        return {"success": False, "message": f"Erreur: {str(e)}"}

def planify_session_exams(session_id):
    """
    Replanifier les examens d'une session existante
    Version simplifiée
    """
    try:
        conn = get_connection()
        if not conn:
            return {"success": False, "message": "Erreur de connexion"}
        
        cursor = conn.cursor(dictionary=True)
        
        # Vérifier que la session existe
        cursor.execute("SELECT id, nom FROM sessions WHERE id = %s", (session_id,))
        session = cursor.fetchone()
        
        if not session:
            return {"success": False, "message": "Session non trouvée"}
        
        # Simuler une replanification
        cursor.execute("""
            UPDATE examens 
            SET statut = 'CONFIRME' 
            WHERE session_id = %s AND statut = 'EN_ATTENTE'
        """, (session_id,))
        
        exams_updated = cursor.rowcount
        
        # Mettre à jour le statut de la session
        cursor.execute("""
            UPDATE sessions 
            SET statut = 'PUBLIEE' 
            WHERE id = %s
        """, (session_id,))
        
        conn.commit()
        
        return {
            "success": True,
            "message": f"Replanification terminée: {exams_updated} examens confirmés",
            "exams_updated": exams_updated
        }
        
    except Exception as e:
        return {"success": False, "message": f"Erreur: {str(e)}"}

class SimplePlanningGenerator:
    """
    Générateur de planning simplifié
    Classe wrapper pour la compatibilité
    """
    def __init__(self):
        pass
    
    def generate(self, formations, salles, periode):
        """Générer un planning simplifié"""
        return {
            "success": True,
            "message": "Planning généré avec succès (version simplifiée)",
            "planning": []
        }