# frontend/dashboard_chef.py
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from backend.database import get_connection, fetch_formations, fetch_examens_by_session_grouped
    DB_AVAILABLE = True
except ImportError as e:
    DB_AVAILABLE = False
    st.warning(f"Backend non disponible: {e}")

def show_chef_dashboard():
    """Dashboard Chef de Département"""
    
    st.title("🏢 Tableau de Bord - Chef de Département")
    
    # Barre latérale
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
        
        if 'user' in st.session_state:
            user = st.session_state.user
            st.write(f"**👤 {user.get('email', 'Utilisateur')}**")
            st.write(f"**🎯 Rôle: Chef de Département**")
        
        st.divider()
        
        menu_option = st.radio(
            "📋 Menu",
            ["✅ Validation Examens", "📊 Statistiques Département", "⚠️ Gestion Conflits", "👤 Mon Profil"]
        )
        
        st.divider()
        if st.button("🚪 Déconnexion", use_container_width=True):
            del st.session_state.user
            st.rerun()
    
    # Contenu principal
    if menu_option == "✅ Validation Examens":
        show_validation_section()
    elif menu_option == "📊 Statistiques Département":
        show_statistics_section()
    elif menu_option == "⚠️ Gestion Conflits":
        show_conflicts_section()
    elif menu_option == "👤 Mon Profil":
        show_profile()

def show_validation_section():
    """Validation des examens par département"""
    st.header("✅ Validation des Examens - Département")
    
    if not DB_AVAILABLE:
        st.error("❌ Base de données non disponible")
        return
    
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Récupérer le département du chef (simulation)
        # Dans une vraie application, récupérer depuis la table users
        user_email = st.session_state.user.get('email', '')
        
        # Déterminer le département basé sur l'email
        if 'info' in user_email or 'admin' in user_email:
            departement_id = 1  # Informatique
        elif 'math' in user_email:
            departement_id = 2  # Mathématiques
        elif 'phy' in user_email:
            departement_id = 3  # Physique
        else:
            departement_id = 1
        
        # Récupérer les formations du département
        cursor.execute("""
            SELECT id, nom FROM formations 
            WHERE departement_id = %s
            ORDER BY nom
        """, (departement_id,))
        
        formations = cursor.fetchall()
        
        if not formations:
            st.info("Aucune formation dans votre département")
            return
        
        # Sélectionner une formation
        formation_options = {f['nom']: f['id'] for f in formations}
        selected_formation = st.selectbox(
            "Sélectionnez une formation:",
            list(formation_options.keys())
        )
        
        if not selected_formation:
            return
        
        formation_id = formation_options[selected_formation]
        
        # Récupérer les examens de la formation
        cursor.execute("""
            SELECT e.*, m.nom as module_nom, g.nom as groupe_nom,
                   s.nom as salle_nom, se.nom as session_nom,
                   se.date_debut, se.date_fin
            FROM examens e
            JOIN modules m ON e.module_id = m.id
            JOIN groupes g ON e.groupe_id = g.id
            JOIN sessions se ON e.session_id = se.id
            LEFT JOIN salles s ON e.salle_id = s.id
            WHERE e.formation_id = %s
            AND e.statut IN ('EN_ATTENTE', 'CONFIRME', 'REFUSE')
            ORDER BY e.date_examen, e.heure_debut
        """, (formation_id,))
        
        examens = cursor.fetchall()
        
        if not examens:
            st.info("Aucun examen à valider pour cette formation")
            return
        
        # Filtrer par statut
        col1, col2, col3 = st.columns(3)
        with col1:
            show_pending = st.checkbox("En attente ⏳", value=True)
        with col2:
            show_confirmed = st.checkbox("Confirmés ✅", value=True)
        with col3:
            show_refused = st.checkbox("Refusés ❌", value=False)
        
        # Appliquer les filtres
        filtered_exams = []
        for exam in examens:
            if show_pending and exam['statut'] == 'EN_ATTENTE':
                filtered_exams.append(exam)
            elif show_confirmed and exam['statut'] == 'CONFIRME':
                filtered_exams.append(exam)
            elif show_refused and exam['statut'] == 'REFUSE':
                filtered_exams.append(exam)
        
        # Afficher les statistiques
        total = len(filtered_exams)
        pending = len([e for e in filtered_exams if e['statut'] == 'EN_ATTENTE'])
        confirmed = len([e for e in filtered_exams if e['statut'] == 'CONFIRME'])
        refused = len([e for e in filtered_exams if e['statut'] == 'REFUSE'])
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        with col_stat1:
            st.metric("Total", total)
        with col_stat2:
            st.metric("⏳ En attente", pending)
        with col_stat3:
            st.metric("✅ Confirmés", confirmed)
        with col_stat4:
            st.metric("❌ Refusés", refused)
        
        # Tableau des examens
        st.subheader("📋 Liste des Examens")
        
        exam_data = []
        for exam in filtered_exams:
            # Icône de statut
            statut_icon = ""
            if exam['statut'] == 'EN_ATTENTE':
                statut_icon = "⏳"
            elif exam['statut'] == 'CONFIRME':
                statut_icon = "✅"
            elif exam['statut'] == 'REFUSE':
                statut_icon = "❌"
            
            exam_data.append({
                "Module": exam['module_nom'],
                "Groupe": exam['groupe_nom'],
                "Date": exam['date_examen'].strftime("%d/%m/%Y") if exam['date_examen'] else "N/A",
                "Heure": str(exam['heure_debut'])[:5] if exam['heure_debut'] else "N/A",
                "Salle": exam['salle_nom'] or "N/A",
                "Session": exam['session_nom'],
                "Statut": f"{statut_icon} {exam['statut']}",
                "ID": exam['id']
            })
        
        if exam_data:
            df_exams = pd.DataFrame(exam_data)
            st.dataframe(
                df_exams,
                column_config={
                    "ID": None  # Cacher l'ID
                },
                hide_index=True
            )
            
            # Actions de validation
            st.subheader("🔧 Actions de Validation")
            
            col_action1, col_action2 = st.columns(2)
            
            with col_action1:
                if pending > 0:
                    if st.button("✅ Valider tous les examens en attente", type="primary"):
                        update_exams_status(formation_id, 'CONFIRME')
                        st.success(f"{pending} examens validés!")
                        st.rerun()
            
            with col_action2:
                if confirmed > 0:
                    if st.button("↩️ Remettre en attente", type="secondary"):
                        update_exams_status(formation_id, 'EN_ATTENTE')
                        st.info(f"{confirmed} examens remis en attente!")
                        st.rerun()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        st.error(f"Erreur: {str(e)}")

def update_exams_status(formation_id, new_status):
    """Mettre à jour le statut des examens"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE examens 
            SET statut = %s
            WHERE formation_id = %s
            AND statut != %s
        """, (new_status, formation_id, new_status))
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        st.error(f"Erreur de mise à jour: {str(e)}")

def show_statistics_section():
    """Statistiques du département"""
    st.header("📊 Statistiques du Département")
    
    if not DB_AVAILABLE:
        st.error("❌ Base de données non disponible")
        return
    
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Statistiques générales
        st.subheader("📈 Vue d'ensemble")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cursor.execute("SELECT COUNT(*) as total FROM formations")
            total_formations = cursor.fetchone()['total']
            st.metric("Formations", total_formations)
        
        with col2:
            cursor.execute("SELECT COUNT(*) as total FROM groupes")
            total_groupes = cursor.fetchone()['total']
            st.metric("Groupes", total_groupes)
        
        with col3:
            cursor.execute("SELECT COUNT(*) as total FROM examens")
            total_examens = cursor.fetchone()['total']
            st.metric("Examens", total_examens)
        
        with col4:
            cursor.execute("SELECT COUNT(*) as total FROM professeurs")
            total_profs = cursor.fetchone()['total']
            st.metric("Professeurs", total_profs)
        
        # Distribution des examens par statut
        st.subheader("📊 Distribution par Statut")
        
        cursor.execute("""
            SELECT 
                statut,
                COUNT(*) as nombre,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM examens), 1) as pourcentage
            FROM examens
            GROUP BY statut
            ORDER BY nombre DESC
        """)
        
        stats = cursor.fetchall()
        
        if stats:
            df_stats = pd.DataFrame(stats)
            st.bar_chart(df_stats.set_index('statut')['nombre'])
            
            # Tableau détaillé
            for stat in stats:
                statut_text = ""
                if stat['statut'] == 'EN_ATTENTE':
                    statut_text = "⏳ En attente"
                elif stat['statut'] == 'CONFIRME':
                    statut_text = "✅ Confirmé"
                elif stat['statut'] == 'REFUSE':
                    statut_text = "❌ Refusé"
                elif stat['statut'] == 'VALIDE':
                    statut_text = "🏆 Validé"
                else:
                    statut_text = stat['statut']
                
                st.write(f"{statut_text}: {stat['nombre']} ({stat['pourcentage']}%)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        st.error(f"Erreur: {str(e)}")

def show_conflicts_section():
    """Gestion des conflits"""
    st.header("⚠️ Gestion des Conflits")
    
    st.info("""
    **Types de conflits détectés:**
    1. **Conflit d'étudiant:** Même étudiant dans deux examens simultanés
    2. **Conflit de professeur:** Même professeur surveillant deux examens simultanés
    3. **Conflit de salle:** Même salle utilisée pour deux examens simultanés
    4. **Salle trop petite:** Capacité insuffisante pour le groupe
    """)
    
    if not DB_AVAILABLE:
        st.error("❌ Base de données non disponible")
        return
    
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Détecter les conflits de salle
        st.subheader("🏫 Conflits de Salle")
        
        cursor.execute("""
            SELECT 
                e1.id as examen1_id,
                e1.date_examen,
                e1.heure_debut,
                e1.salle_id,
                s.nom as salle_nom,
                m1.nom as module1,
                m2.nom as module2,
                e2.id as examen2_id
            FROM examens e1
            JOIN examens e2 ON e1.salle_id = e2.salle_id 
                AND e1.id < e2.id
                AND e1.date_examen = e2.date_examen
                AND e1.heure_debut = e2.heure_debut
            JOIN modules m1 ON e1.module_id = m1.id
            JOIN modules m2 ON e2.module_id = m2.id
            JOIN salles s ON e1.salle_id = s.id
            WHERE e1.statut IN ('EN_ATTENTE', 'CONFIRME')
            ORDER BY e1.date_examen, e1.heure_debut
        """)
        
        conflits_salle = cursor.fetchall()
        
        if conflits_salle:
            conflit_data = []
            for conflit in conflits_salle:
                conflit_data.append({
                    "Salle": conflit['salle_nom'],
                    "Date": conflit['date_examen'].strftime("%d/%m/%Y"),
                    "Heure": str(conflit['heure_debut'])[:5],
                    "Module 1": conflit['module1'],
                    "Module 2": conflit['module2'],
                    "Type": "Salle double utilisation"
                })
            
            df_conflits = pd.DataFrame(conflit_data)
            st.dataframe(df_conflits, hide_index=True)
        else:
            st.success("✅ Aucun conflit de salle détecté")
        
        # Conflits de capacité
        st.subheader("👥 Conflits de Capacité")
        
        cursor.execute("""
            SELECT 
                e.id,
                m.nom as module_nom,
                g.nom as groupe_nom,
                g.effectif,
                s.nom as salle_nom,
                s.capacite,
                CASE 
                    WHEN g.effectif > s.capacite THEN 'Dépassement'
                    WHEN g.effectif > s.capacite * 0.9 THEN 'Proche limite'
                    ELSE 'OK'
                END as etat
            FROM examens e
            JOIN modules m ON e.module_id = m.id
            JOIN groupes g ON e.groupe_id = g.id
            LEFT JOIN salles s ON e.salle_id = s.id
            WHERE e.statut IN ('EN_ATTENTE', 'CONFIRME')
            AND s.id IS NOT NULL
            ORDER BY (g.effectif - s.capacite) DESC
        """)
        
        capacites = cursor.fetchall()
        
        if capacites:
            cap_data = []
            for cap in capacites:
                if cap['effectif'] > cap['capacite']:
                    cap_data.append({
                        "Module": cap['module_nom'],
                        "Groupe": cap['groupe_nom'],
                        "Salle": cap['salle_nom'],
                        "Effectif": cap['effectif'],
                        "Capacité": cap['capacite'],
                        "Déficit": cap['effectif'] - cap['capacite'],
                        "État": "❌ Dépassement"
                    })
            
            if cap_data:
                df_cap = pd.DataFrame(cap_data)
                st.dataframe(df_cap, hide_index=True)
            else:
                st.success("✅ Aucun problème de capacité détecté")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        st.error(f"Erreur: {str(e)}")

def show_profile():
    """Profil Chef de Département"""
    st.header("👤 Mon Profil")
    
    if 'user' not in st.session_state:
        st.error("Non connecté")
        return
    
    user = st.session_state.user
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Email:** {user.get('email', 'N/A')}")
        st.info(f"**Rôle:** {user.get('role', 'N/A')}")
        st.info(f"**ID:** {user.get('id', 'N/A')}")
    
    with col2:
        st.info("**Permissions:**")
        st.write("- ✅ Validation des examens du département")
        st.write("- 📊 Statistiques départementales")
        st.write("- ⚠️ Détection et gestion des conflits")
        st.write("- 📋 Consultation des formations")

if __name__ == "__main__":
    show_chef_dashboard()