# frontend/dashboard_professor.py
import streamlit as st
import sys
import os
from datetime import datetime

# Import backend
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.append(backend_path)

try:
    from backend.database import (
        get_connection,
        hash_password,
        verify_password_strength,
        update_user_password
    )
    DB_AVAILABLE = True
except ImportError as e:
    st.error(f"Erreur d'import backend : {e}")
    DB_AVAILABLE = False


def show_professor_dashboard():
    """Dashboard professeur – Mes Surveillance et Mon Profil"""

    user = st.session_state.user

    # ================== SIDEBAR ==================
    with st.sidebar:
        # Infos professeur
        if DB_AVAILABLE:
            try:
                conn = get_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT p.specialite,
                           d.nom AS departement,
                           p.nb_max_surveillances_jour,
                           p.heures_semaine_max
                    FROM professeurs p
                    JOIN departements d ON p.departement_id = d.id
                    WHERE p.user_id = %s
                """, (user['id'],))
                info = cursor.fetchone()
                cursor.close()
                conn.close()

                if info:
                    st.write(f"🎓 **Spécialité :** {info['specialite']}")
                    st.write(f"🏢 **Département :** {info['departement']}")
                    st.write(f"📊 **Limite/jour :** {info['nb_max_surveillances_jour']}")
            except Exception as e:
                st.error(f"Erreur: {e}")

        st.write("---")

        st.markdown("### 📋 Menu")
        
        menu_option = st.radio(
            "Navigation",
            ["📋 Mes Surveillance", "👤 Mon Profil"]
        )

        st.write("---")
        if st.button("🚪 Déconnexion", use_container_width=True):
            del st.session_state.user
            st.rerun()

    # ================== CONTENU ==================
    st.title("👨‍🏫 Espace Professeur")
    st.markdown("---")
    
    if menu_option == "📋 Mes Surveillance":
        show_surveillance(user)
    elif menu_option == "👤 Mon Profil":
        show_professor_profile(user)


def show_surveillance(user):
    """Afficher les surveillances CONFIRMÉES du professeur"""
    st.header("📋 Mes Surveillance")
    
    if not DB_AVAILABLE:
        st.error("❌ Base de données non disponible")
        return
    
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Récupérer l'ID du professeur
        cursor.execute("SELECT id FROM professeurs WHERE user_id = %s", (user['id'],))
        prof_info = cursor.fetchone()
        
        if not prof_info:
            st.error("❌ Profil professeur non trouvé")
            return
        
        prof_id = prof_info['id']
        
        # Récupérer uniquement les surveillances pour les examens CONFIRMÉS
        cursor.execute("""
            SELECT 
                s.id,
                s.date_surveillance,
                s.heure_debut,
                e.duree_minutes,
                e.statut as examen_statut,
                m.nom as module_nom,
                f.nom as formation_nom,
                sa.nom as salle_nom,
                g.nom as groupe_nom,
                g.effectif,
                se.nom as session_nom
            FROM surveillances s
            JOIN examens e ON s.examen_id = e.id
            JOIN modules m ON e.module_id = m.id
            JOIN formations f ON e.formation_id = f.id
            LEFT JOIN salles sa ON e.salle_id = sa.id
            LEFT JOIN groupes g ON e.groupe_id = g.id
            LEFT JOIN sessions_examens se ON e.session_id = se.id
            WHERE s.prof_id = %s
            AND e.statut = 'CONFIRME'  -- UNIQUEMENT LES EXAMENS CONFIRMÉS
            ORDER BY 
                CASE 
                    WHEN s.date_surveillance IS NULL THEN 1
                    ELSE 0
                END,
                s.date_surveillance,
                s.heure_debut
        """, (prof_id,))
        
        surveillances = cursor.fetchall()
        
        if not surveillances:
            st.info("📭 Aucune surveillance confirmée pour le moment.")
            
            # Afficher les surveillances en attente (optionnel)
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM surveillances s
                JOIN examens e ON s.examen_id = e.id
                WHERE s.prof_id = %s
                AND e.statut = 'EN_ATTENTE'
            """, (prof_id,))
            
            en_attente = cursor.fetchone()['count']
            if en_attente > 0:
                st.info(f"ℹ️ Vous avez {en_attente} surveillance(s) en attente de confirmation")
            
            return
        
        # Statistiques
        total_surv = len(surveillances)
        surveillances_planifiees = len([s for s in surveillances if s['date_surveillance'] is not None])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total surveillances confirmées", total_surv)
        with col2:
            st.metric("Planifiées (avec date)", surveillances_planifiees)
        
        st.markdown("---")
        
        # Séparer les surveillances planifiées et non planifiées
        scheduled_surv = [s for s in surveillances if s['date_surveillance'] is not None]
        unscheduled_surv = [s for s in surveillances if s['date_surveillance'] is None]
        
        # Afficher d'abord les surveillances planifiées (avec date)
        if scheduled_surv:
            # Trier par date et heure
            scheduled_surv.sort(key=lambda x: (x['date_surveillance'], x['heure_debut'] or datetime.min.time()))
            
            st.subheader("📅 Surveillances planifiées")
            
            # Préparer les données pour le tableau
            surv_data = []
            for surv in scheduled_surv:
                # Calculer l'heure de fin
                heure_debut = surv['heure_debut']
                duree = surv['duree_minutes']
                
                if heure_debut:
                    heure_debut_obj = datetime.strptime(str(heure_debut), '%H:%M:%S')
                    heure_fin_obj = heure_debut_obj.replace(
                        hour=heure_debut_obj.hour + duree // 60,
                        minute=heure_debut_obj.minute + duree % 60
                    )
                    heure_fin = heure_fin_obj.strftime('%H:%M')
                    heure_str = f"{heure_debut_obj.strftime('%H:%M')} - {heure_fin}"
                else:
                    heure_str = "-"
                
                surv_info = {
                    "📚 Module": surv['module_nom'],
                    "📅 Date": surv['date_surveillance'].strftime("%d/%m/%Y"),
                    "🕐 Horaire": heure_str,
                    "🏫 Salle": surv['salle_nom'] or "Non assignée",
                    "👥 Groupe": surv['groupe_nom'] or "-",
                    "📋 Session": surv['session_nom'] or "-"
                }
                surv_data.append(surv_info)
            
            # Afficher le tableau
            st.dataframe(
                surv_data,
                use_container_width=True,
                hide_index=True
            )
            
            # Vue détaillée
            with st.expander("📋 Voir le détail des surveillances"):
                for idx, surv in enumerate(scheduled_surv, 1):
                    with st.container():
                        col_left, col_right = st.columns([3, 1])
                        
                        with col_left:
                            # Informations de la surveillance
                            st.markdown(f"**{idx}. {surv['module_nom']}**")
                            st.write(f"📅 **Date :** {surv['date_surveillance'].strftime('%A %d/%m/%Y')}")
                            
                            if surv['heure_debut']:
                                heure_debut_obj = datetime.strptime(str(surv['heure_debut']), '%H:%M:%S')
                                heure_fin_obj = heure_debut_obj.replace(
                                    hour=heure_debut_obj.hour + surv['duree_minutes'] // 60,
                                    minute=heure_debut_obj.minute + surv['duree_minutes'] % 60
                                )
                                st.write(f"🕐 **Horaire :** {heure_debut_obj.strftime('%H:%M')} - {heure_fin_obj.strftime('%H:%M')}")
                                st.write(f"⏱️ **Durée :** {surv['duree_minutes']} minutes")
                            else:
                                st.write("🕐 **Horaire :** À définir")
                            
                            if surv['salle_nom']:
                                st.write(f"🏫 **Salle :** {surv['salle_nom']}")
                            
                            if surv['groupe_nom']:
                                st.write(f"👥 **Groupe :** {surv['groupe_nom']} ({surv['effectif']} étudiants)")
                            
                            if surv['session_nom']:
                                st.write(f"📋 **Session :** {surv['session_nom']}")
                        
                        with col_right:
                            # Indicateur visuel
                            st.markdown("### ✅")
                            st.caption("Confirmé")
                        
                        st.divider()
        
        # Afficher les surveillances confirmées mais non planifiées (sans date)
        if unscheduled_surv:
            st.markdown("---")
            st.subheader("⏳ Surveillances confirmées (en attente de planification)")
            
            # Préparer les données pour le tableau
            unscheduled_data = []
            for surv in unscheduled_surv:
                surv_info = {
                    "📚 Module": surv['module_nom'],
                    "📅 Date": "À définir",
                    "🕐 Horaire": "À définir",
                    "🏫 Salle": "À définir",
                    "👥 Groupe": surv['groupe_nom'] or "-",
                    "📋 Session": surv['session_nom'] or "-"
                }
                unscheduled_data.append(surv_info)
            
            # Afficher le tableau
            st.dataframe(
                unscheduled_data,
                use_container_width=True,
                hide_index=True
            )
            
            st.info("ℹ️ Ces surveillances sont confirmées mais pas encore planifiées. Les dates et salles seront communiquées ultérieurement.")
        
        # Résumé : prochaine surveillance
        st.markdown("---")
        today = datetime.now().date()
        
        # Compter les surveillances à venir (dans le futur)
        upcoming_surv = [s for s in scheduled_surv if s['date_surveillance'] >= today]
        
        if upcoming_surv:
            # Trier par date la plus proche
            upcoming_surv.sort(key=lambda x: x['date_surveillance'])
            
            st.subheader("🎯 Prochaine surveillance")
            next_surv = upcoming_surv[0]
            
            days_until = (next_surv['date_surveillance'] - today).days
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**{next_surv['module_nom']}**")
                st.write(f"📅 {next_surv['date_surveillance'].strftime('%A %d/%m/%Y')}")
                
                if next_surv['heure_debut']:
                    heure_debut_obj = datetime.strptime(str(next_surv['heure_debut']), '%H:%M:%S')
                    heure_fin_obj = heure_debut_obj.replace(
                        hour=heure_debut_obj.hour + next_surv['duree_minutes'] // 60,
                        minute=heure_debut_obj.minute + next_surv['duree_minutes'] % 60
                    )
                    st.write(f"🕐 {heure_debut_obj.strftime('%H:%M')} - {heure_fin_obj.strftime('%H:%M')}")
                
                if next_surv['salle_nom']:
                    st.write(f"🏫 {next_surv['salle_nom']}")
                
                if next_surv['groupe_nom']:
                    st.write(f"👥 {next_surv['groupe_nom']}")
            
            with col2:
                if days_until == 0:
                    st.success("**Aujourd'hui!**")
                elif days_until == 1:
                    st.warning(f"**Demain**")
                else:
                    st.info(f"**Dans {days_until} jours**")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        st.error(f"Erreur lors du chargement des surveillances : {str(e)}")


def show_professor_profile(user):
    """Affichage et gestion du profil professeur"""

    st.header("👤 Mon Profil")

    if not DB_AVAILABLE:
        st.error("❌ Base de données non disponible")
        return

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Récupérer les informations du professeur
        cursor.execute("""
            SELECT 
                u.email,
                u.role,
                u.is_active,
                p.specialite,
                d.nom AS departement,
                p.nb_max_surveillances_jour,
                p.heures_semaine_max
            FROM users u
            JOIN professeurs p ON u.id = p.user_id
            JOIN departements d ON p.departement_id = d.id
            WHERE u.id = %s
        """, (user['id'],))

        data = cursor.fetchone()

        if not data:
            st.warning("Aucune information trouvée")
            return

        # Affichage en deux colonnes
        col1, col2 = st.columns(2)

        with col1:
            st.info(f"**Email :** {data['email']}")
            st.info(f"**Rôle :** {data['role']}")
            st.info(f"**Spécialité :** {data['specialite']}")

        with col2:
            st.info(f"**Département :** {data['departement']}")
            st.info(f"**Statut :** {'Actif' if data['is_active'] == 1 else 'Inactif'}")
            st.info(f"**Limite surveillances/jour :** {data['nb_max_surveillances_jour']}")

        st.markdown("---")
        
        # Statistiques du professeur
        st.subheader("📊 Mes statistiques")
        
        # Compter les surveillances confirmées
        cursor.execute("""
            SELECT COUNT(*) as total_surv
            FROM surveillances s
            JOIN examens e ON s.examen_id = e.id
            JOIN professeurs p ON s.prof_id = p.id
            WHERE p.user_id = %s
            AND e.statut = 'CONFIRME'
        """, (user['id'],))
        
        stats = cursor.fetchone()
        total_surv = stats['total_surv'] if stats else 0
        
        # Compter les surveillances cette semaine
        cursor.execute("""
            SELECT COUNT(*) as surv_semaine
            FROM surveillances s
            JOIN examens e ON s.examen_id = e.id
            JOIN professeurs p ON s.prof_id = p.id
            WHERE p.user_id = %s
            AND e.statut = 'CONFIRME'
            AND YEARWEEK(s.date_surveillance, 1) = YEARWEEK(CURDATE(), 1)
        """, (user['id'],))
        
        stats_semaine = cursor.fetchone()
        surv_semaine = stats_semaine['surv_semaine'] if stats_semaine else 0
        
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("Surveillances confirmées (total)", total_surv)
        with col_stat2:
            st.metric("Surveillances cette semaine", surv_semaine)

        st.markdown("---")
        
        # Changer le mot de passe
        st.subheader("🔐 Changer mon mot de passe")

        with st.form("prof_pwd_form"):
            old = st.text_input("Ancien mot de passe", type="password")
            new = st.text_input("Nouveau mot de passe", type="password")
            confirm = st.text_input("Confirmer le mot de passe", type="password")

            submit = st.form_submit_button("Changer le mot de passe", use_container_width=True)

            if submit:
                if not old or not new or not confirm:
                    st.error("Tous les champs sont obligatoires")
                elif new != confirm:
                    st.error("Les mots de passe ne correspondent pas")
                else:
                    valid, msg = verify_password_strength(new)
                    if not valid:
                        st.error(msg)
                    else:
                        success = update_user_password(user['id'], new)
                        if success:
                            st.success("✅ Mot de passe modifié avec succès")
                        else:
                            st.error("❌ Erreur lors de la mise à jour")

        cursor.close()
        conn.close()

    except Exception as e:
        st.error(f"Erreur: {str(e)}")


if __name__ == "__main__":
    # Simulation d'un utilisateur professeur pour le test
   
    
    show_professor_dashboard()