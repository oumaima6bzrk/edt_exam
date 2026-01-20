
import streamlit as st
from backend.database import get_connection
import pandas as pd

def show_vicedoyen_dashboard():
    """Dashboard spécifique au Vice-Doyen"""
    user = st.session_state.user
    
    st.title("👨‍🎓 Tableau de Bord - Vice-Doyen")
    
    # Barre latérale
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
        st.write(f"**👤 {user.get('email', 'Utilisateur')}**")
        st.write(f"**🎯 Rôle: Vice-Doyen**")
        st.divider()
        
        menu_option = st.radio(
            "Menu",
            ["📋 Validation Finale des Examens", "📊 Statistiques Globales"]
        )
        
        st.divider()
        if st.button("🚪 Déconnexion"):
            del st.session_state.user
            st.rerun()
    
    # Contenu principal
    if menu_option == "📋 Validation Finale des Examens":
        show_final_validation_section(user)
    elif menu_option == "📊 Statistiques Globales":
        show_global_statistics_section(user)

def show_final_validation_section(user):
    """Section de validation finale des examens par le vice-doyen"""
    st.header("📋 Validation Finale des Examens")
    
    conn = get_connection()
    if not conn:
        st.error("Impossible de se connecter à la base de données")
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Récupérer toutes les sessions
        cursor.execute("""
            SELECT s.id, s.nom, s.date_debut, s.date_fin, s.statut as session_statut
            FROM sessions_examens s
            ORDER BY s.date_debut DESC
        """)
        
        sessions = cursor.fetchall()
        
        if not sessions:
            st.info("📭 Aucune session d'examens disponible")
            return
        
        # Sélectionner une session
        session_options = {}
        for s in sessions:
            session_status = ""
            if s['session_statut'] == 'VALIDATION_FINALE':
                session_status = "✅ "
            elif s['session_statut'] == 'PUBLIE':
                session_status = "📢 "
            
            session_options[f"{session_status}{s['nom']} ({s['date_debut']} au {s['date_fin']})"] = s['id']
        
        selected_session_label = st.selectbox(
            "Sélectionnez une session:",
            list(session_options.keys())
        )
        
        if not selected_session_label:
            return
        
        session_id = session_options[selected_session_label]
        
        # Récupérer les détails de la session sélectionnée
        cursor.execute("""
            SELECT s.nom, s.date_debut, s.date_fin, s.statut as session_statut
            FROM sessions_examens s
            WHERE s.id = %s
        """, (session_id,))
        
        session_info = cursor.fetchone()
        
        if not session_info:
            st.error("Session introuvable")
            return
        
        # Vérifier si la session est déjà validée
        if session_info['session_statut'] == 'VALIDATION_FINALE' or session_info['session_statut'] == 'PUBLIE':
            st.success(f"✅ Session **{session_info['nom']}** déjà validée finalement")
            
            if session_info['session_statut'] == 'PUBLIE':
                st.warning("📢 Cette session est déjà publiée aux étudiants")
            
            # Afficher quand même les examens pour information
            show_exams = st.checkbox("Afficher les examens validés", value=True)
        else:
            show_exams = True
        
        if show_exams:
            # Récupérer tous les examens de la session groupés par formation
            cursor.execute("""
                SELECT 
                    f.nom as formation_nom,
                    d.nom as departement_nom,
                    g.nom as groupe_nom,
                    g.effectif as groupe_effectif,
                    m.nom as module_nom,
                    e.date_examen,
                    e.heure_debut,
                    e.duree_minutes,
                    s.nom as salle_nom,
                    u.email as professeur_email,
                    e.statut as examen_statut,
                    COUNT(e.id) OVER(PARTITION BY f.id, g.id) as nb_examens_groupe,
                    COUNT(e.id) OVER(PARTITION BY f.id) as nb_examens_formation
                FROM examens e
                JOIN modules m ON e.module_id = m.id
                JOIN formations f ON e.formation_id = f.id
                JOIN departements d ON f.departement_id = d.id
                JOIN groupes g ON e.groupe_id = g.id
                LEFT JOIN salles s ON e.salle_id = s.id
                LEFT JOIN surveillances sv ON e.id = sv.examen_id
                LEFT JOIN professeurs p ON sv.prof_id = p.id
                LEFT JOIN users u ON p.user_id = u.id
                WHERE e.session_id = %s
                ORDER BY 
                    d.nom,
                    f.nom,
                    g.nom,
                    e.date_examen,
                    e.heure_debut
            """, (session_id,))
            
            examens = cursor.fetchall()
            
            if not examens:
                st.info("📭 Aucun examen pour cette session")
                cursor.close()
                conn.close()
                return
            
            # Statistiques globales
            total_examens = len(examens)
            examens_confirme = len([e for e in examens if e['examen_statut'] == 'CONFIRME'])
            examens_attente = len([e for e in examens if e['examen_statut'] == 'EN_ATTENTE'])
            examens_refuse = len([e for e in examens if e['examen_statut'] == 'REFUSE'])
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total examens", total_examens)
            with col2:
                st.metric("Confirmés", examens_confirme, 
                         delta=f"{examens_confirme}/{total_examens}")
            with col3:
                st.metric("En attente", examens_attente)
            with col4:
                st.metric("Refusés", examens_refuse)
            
            # Afficher par département
            departements = {}
            for examen in examens:
                dept = examen['departement_nom']
                if dept not in departements:
                    departements[dept] = []
                departements[dept].append(examen)
            
            # Parcourir chaque département
            for dept_nom, dept_examens in departements.items():
                st.markdown("---")
                st.subheader(f"🏛️ Département: {dept_nom}")
                
                # Regrouper par formation dans ce département
                formations_dict = {}
                for examen in dept_examens:
                    formation = examen['formation_nom']
                    if formation not in formations_dict:
                        formations_dict[formation] = []
                    formations_dict[formation].append(examen)
                
                # Parcourir chaque formation
                for formation_nom, formation_examens in formations_dict.items():
                    with st.expander(f"🎓 {formation_nom} ({len(formation_examens)} examens)", expanded=True):
                        # Regrouper par groupe dans cette formation
                        groupes_dict = {}
                        for examen in formation_examens:
                            groupe = examen['groupe_nom']
                            if groupe not in groupes_dict:
                                groupes_dict[groupe] = []
                            groupes_dict[groupe].append(examen)
                        
                        # Afficher chaque groupe
                        for groupe_nom, groupe_examens in groupes_dict.items():
                            st.markdown(f"**Groupe: {groupe_nom}** ({groupe_examens[0]['groupe_effectif']} étudiants)")
                            
                            # Préparer les données pour le tableau
                            table_data = []
                            for examen in groupe_examens:
                                # Formater la date
                                date_formatted = ""
                                if examen['date_examen']:
                                    from datetime import datetime
                                    if isinstance(examen['date_examen'], str):
                                        try:
                                            date_obj = datetime.strptime(examen['date_examen'], '%Y-%m-%d').date()
                                        except:
                                            date_obj = examen['date_examen']
                                    else:
                                        date_obj = examen['date_examen']
                                    date_formatted = date_obj.strftime('%d/%m/%Y') if hasattr(date_obj, 'strftime') else str(date_obj)
                                
                                # Statut avec icône
                                statut_icon = ""
                                if examen['examen_statut'] == 'EN_ATTENTE':
                                    statut_icon = "⏳"
                                elif examen['examen_statut'] == 'CONFIRME':
                                    statut_icon = "✅"
                                elif examen['examen_statut'] == 'REFUSE':
                                    statut_icon = "❌"
                                elif examen['examen_statut'] == 'VALIDE':
                                    statut_icon = "🏆"
                                
                                table_data.append({
                                    "Module": examen['module_nom'],
                                    "Date": date_formatted,
                                    "Heure": examen['heure_debut'] if examen['heure_debut'] else "",
                                    "Durée": f"{examen['duree_minutes']} min" if examen['duree_minutes'] else "N/A",
                                    "Salle": examen['salle_nom'] or "Non assignée",
                                    "Surveillant": examen['professeur_email'] or "Non assigné",
                                    "Statut": f"{statut_icon} {examen['examen_statut']}"
                                })
                            
                            # Afficher le tableau
                            df_groupe = pd.DataFrame(table_data)
                            st.dataframe(
                                df_groupe,
                                column_config={
                                    "Module": st.column_config.TextColumn("Module", width="large"),
                                    "Date": st.column_config.TextColumn("Date", width="small"),
                                    "Heure": st.column_config.TextColumn("Heure", width="small"),
                                    "Durée": st.column_config.TextColumn("Durée", width="small"),
                                    "Salle": st.column_config.TextColumn("Salle", width="small"),
                                    "Surveillant": st.column_config.TextColumn("Surveillant", width="medium"),
                                    "Statut": st.column_config.TextColumn("Statut", width="small")
                                },
                                hide_index=True,
                                use_container_width=True
                            )
            
            # Bouton de validation finale
            st.markdown("---")
            st.subheader("🏆 Validation Finale")
            
            if session_info['session_statut'] not in ['VALIDATION_FINALE', 'PUBLIE']:
                # Vérifier si tous les examens sont confirmés
                if examens_attente > 0 or examens_refuse > 0:
                    st.warning(f"""
                    ⚠️ **Attention:** Vous ne pouvez pas valider finalement cette session car:
                    - **{examens_attente}** examen(s) sont encore en attente de validation par les chefs de département
                    - **{examens_refuse}** examen(s) ont été refusés par les chefs de département
                    
                    Tous les examens doivent être en statut **CONFIRME** pour pouvoir procéder à la validation finale.
                    """)
                    
                    # Afficher les détails des problèmes
                    if examens_attente > 0:
                        with st.expander("📋 Voir les examens en attente"):
                            attente_data = []
                            for examen in examens:
                                if examen['examen_statut'] == 'EN_ATTENTE':
                                    attente_data.append({
                                        "Département": examen['departement_nom'],
                                        "Formation": examen['formation_nom'],
                                        "Groupe": examen['groupe_nom'],
                                        "Module": examen['module_nom']
                                    })
                            
                            if attente_data:
                                df_attente = pd.DataFrame(attente_data)
                                st.dataframe(df_attente, hide_index=True)
                    
                    if examens_refuse > 0:
                        with st.expander("📋 Voir les examens refusés"):
                            refuse_data = []
                            for examen in examens:
                                if examen['examen_statut'] == 'REFUSE':
                                    refuse_data.append({
                                        "Département": examen['departement_nom'],
                                        "Formation": examen['formation_nom'],
                                        "Groupe": examen['groupe_nom'],
                                        "Module": examen['module_nom']
                                    })
                            
                            if refuse_data:
                                df_refuse = pd.DataFrame(refuse_data)
                                st.dataframe(df_refuse, hide_index=True)
                else:
                    # Tous les examens sont confirmés, permettre la validation finale
                    st.success(f"""
                    ✅ **Tous les {total_examens} examens sont confirmés!**
                    
                    Vous pouvez maintenant procéder à la validation finale de la session **{session_info['nom']}**.
                    Cette action changera le statut de tous les examens à **VALIDE** et le statut de la session à **VALIDATION_FINALE**.
                    """)
                    
                    # Options de validation
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        commentaire = st.text_area(
                            "Commentaire pour la validation finale (optionnel):",
                            placeholder="Ajouter un commentaire sur cette validation..."
                        )
                    
                    with col2:
                        st.info("""
                        **Effets de la validation finale:**
                        - Tous les examens passent au statut **VALIDE**
                        - La session passe au statut **VALIDATION_FINALE**
                        - Les examens ne peuvent plus être modifiés
                        """)
                    
                    # Bouton de validation finale
                    if st.button(
                        "🏆 Valider Finalement la Session",
                        type="primary",
                        use_container_width=True,
                        key="final_validation"
                    ):
                        # Mettre à jour le statut de la session
                        cursor.execute("""
                            UPDATE sessions_examens 
                            SET statut = 'VALIDATION_FINALE',
                                last_modified = NOW()
                            WHERE id = %s
                        """, (session_id,))
                        
                        # Mettre à jour le statut de tous les examens
                        cursor.execute("""
                            UPDATE examens 
                            SET statut = 'VALIDE',
                                last_modified = NOW(),
                                modified_by = %s
                            WHERE session_id = %s
                            AND statut = 'CONFIRME'
                        """, (user['id'], session_id))
                        
                        # Enregistrer l'historique
                        cursor.execute("""
                            INSERT INTO planning_generations 
                            (generated_by, generation_date, exams_scheduled, parameters)
                            VALUES (%s, NOW(), %s, %s)
                        """, (user['id'], total_examens, 
                              f"Validation finale session {session_id}. Commentaire: {commentaire or 'Aucun'}"))
                        
                        conn.commit()
                        
                        st.success(f"🏆 Session **{session_info['nom']}** validée finalement avec succès!")
                        st.balloons()
                        st.rerun()
            else:
                # Session déjà validée
                if session_info['session_statut'] == 'VALIDATION_FINALE':
                    st.info("""
                    📝 **Session en attente de publication:**
                    - Statut: **VALIDATION_FINALE**
                    - Tous les examens: **VALIDE**
                    - Prêt à être publié aux étudiants
                    """)
                    
                    # Bouton pour publier aux étudiants
                    if st.button(
                        "📢 Publier aux Étudiants",
                        type="secondary",
                        use_container_width=True,
                        key="publish_session"
                    ):
                        cursor.execute("""
                            UPDATE sessions_examens 
                            SET statut = 'PUBLIE',
                                last_modified = NOW()
                            WHERE id = %s
                        """, (session_id,))
                        
                        conn.commit()
                        
                        st.success(f"📢 Session **{session_info['nom']}** publiée aux étudiants!")
                        st.rerun()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        st.error(f"Erreur: {str(e)}")

def show_global_statistics_section(user):
    """Section de statistiques globales pour le vice-doyen"""
    st.header("📊 Statistiques Globales")
    
    conn = get_connection()
    if not conn:
        st.error("Impossible de se connecter à la base de données")
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Statistiques globales
        st.subheader("📈 Vue d'ensemble de l'établissement")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cursor.execute("SELECT COUNT(*) as total FROM departements")
            total_departements = cursor.fetchone()['total']
            st.metric("Départements", total_departements)
        
        with col2:
            cursor.execute("SELECT COUNT(*) as total FROM formations")
            total_formations = cursor.fetchone()['total']
            st.metric("Formations", total_formations)
        
        with col3:
            cursor.execute("SELECT COUNT(*) as total FROM groupes")
            total_groupes = cursor.fetchone()['total']
            st.metric("Groupes", total_groupes)
        
        with col4:
            cursor.execute("SELECT COUNT(*) as total FROM examens")
            total_examens = cursor.fetchone()['total']
            st.metric("Examens totaux", total_examens)
        
        # Statistiques par département
        st.subheader("🏛️ Examens par département")
        
        cursor.execute("""
            SELECT 
                d.nom as departement,
                COUNT(e.id) as total_examens,
                SUM(CASE WHEN e.statut = 'VALIDE' THEN 1 ELSE 0 END) as valides,
                SUM(CASE WHEN e.statut = 'CONFIRME' THEN 1 ELSE 0 END) as confirmes,
                SUM(CASE WHEN e.statut = 'EN_ATTENTE' THEN 1 ELSE 0 END) as en_attente,
                SUM(CASE WHEN e.statut = 'REFUSE' THEN 1 ELSE 0 END) as refuses
            FROM departements d
            LEFT JOIN formations f ON d.id = f.departement_id
            LEFT JOIN examens e ON f.id = e.formation_id
            GROUP BY d.id, d.nom
            ORDER BY d.nom
        """)
        
        stats_departements = cursor.fetchall()
        
        if stats_departements:
            df_departements = pd.DataFrame(stats_departements)
            
            # Calculer les pourcentages
            for idx, row in df_departements.iterrows():
                total = row['total_examens']
                if total > 0:
                    df_departements.loc[idx, 'valide_pct'] = (row['valides'] / total * 100)
                    df_departements.loc[idx, 'confirme_pct'] = (row['confirmes'] / total * 100)
                    df_departements.loc[idx, 'attente_pct'] = (row['en_attente'] / total * 100)
                    df_departements.loc[idx, 'refuse_pct'] = (row['refuses'] / total * 100)
            
            # Afficher le tableau
            st.dataframe(
                df_departements,
                column_config={
                    "departement": "Département",
                    "total_examens": "Total",
                    "valides": "🏆 Validés",
                    "confirmes": "✅ Confirmés",
                    "en_attente": "⏳ En attente",
                    "refuses": "❌ Refusés"
                },
                hide_index=True
            )
        
        # Sessions en cours
        st.subheader("📅 Sessions d'examens")
        
        cursor.execute("""
            SELECT 
                s.nom,
                s.date_debut,
                s.date_fin,
                s.statut,
                COUNT(e.id) as nb_examens,
                SUM(CASE WHEN e.statut = 'VALIDE' THEN 1 ELSE 0 END) as valides,
                SUM(CASE WHEN e.statut = 'CONFIRME' THEN 1 ELSE 0 END) as confirmes
            FROM sessions_examens s
            LEFT JOIN examens e ON s.id = e.session_id
            GROUP BY s.id, s.nom, s.date_debut, s.date_fin, s.statut
            ORDER BY s.date_debut DESC
            LIMIT 10
        """)
        
        sessions = cursor.fetchall()
        
        if sessions:
            sessions_data = []
            for session in sessions:
                status_icon = ""
                if session['statut'] == 'CREATION':
                    status_icon = "📝"
                elif session['statut'] == 'VALIDATION_FINALE':
                    status_icon = "🏆"
                elif session['statut'] == 'PUBLIE':
                    status_icon = "📢"
                
                sessions_data.append({
                    "Session": session['nom'],
                    "Période": f"{session['date_debut']} au {session['date_fin']}",
                    "Statut": f"{status_icon} {session['statut']}",
                    "Examens": session['nb_examens'],
                    "Validés": session['valides'],
                    "Confirmés": session['confirmes']
                })
            
            df_sessions = pd.DataFrame(sessions_data)
            st.dataframe(
                df_sessions,
                column_config={
                    "Session": st.column_config.TextColumn("Session", width="medium"),
                    "Période": st.column_config.TextColumn("Période", width="medium"),
                    "Statut": st.column_config.TextColumn("Statut", width="small"),
                    "Examens": st.column_config.NumberColumn("Examens"),
                    "Validés": st.column_config.NumberColumn("Validés"),
                    "Confirmés": st.column_config.NumberColumn("Confirmés")
                },
                hide_index=True
            )
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        st.error(f"Erreur lors du chargement des statistiques: {str(e)}")
