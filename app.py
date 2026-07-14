import atexit
import csv
import sqlite3
from datetime import date
from io import StringIO
from pathlib import Path
from xml.sax.saxutils import escape

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, Response, jsonify, render_template, request
from jsonschema import ValidationError, validate

# Import de fonctions utilitaires pour la détection et l'envoi de nouvelles
# contraventions
from b1_utils import detecter_et_envoyer_nouvelles_contraventions
from import_violations import CSV_PATH, CSV_URL, insert_violations

app = Flask(__name__)
app.json.ensure_ascii = False  # Affichage correct des caractères avec accents
DB_PATH = 'db/violations.sqlite'  # Fichier de BD des contraventions
RAML_PATH = Path("api.raml")  # Fichier RAML pour documentation RAML


# A2: Page d'accueil avec formulaire de recherche
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


# A2: Affichage de la page de résultats de recherche
@app.route('/resultats', methods=['GET', 'POST'])
def resultats():
    # Chaîne entrée par l'utilisateur
    chaine = request.values.get('chaine', '')
    # Critère de recherche choisi par l'utilisateur
    critere = request.values.get('critere', '')
    # Liste de resultats de recherche (rien au départ)
    resultats = []

    if critere and chaine:
        # Recherche dans la base de données
        resultats = rechercher_contraventions(critere, chaine)

    return render_template('resultats.html', resultats=resultats,
                           chaine=chaine, critere=critere)


# A2: Logique de la recherche de contraventions dans la base de données selon
# le critère et chaîne fournis par l'utilisateur
def rechercher_contraventions(critere, chaine):
    # Connexion à la base de données SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Recherche selon critère choisi (nom d'établissement, propriétaire ou
    # adresse)
    if critere == 'nom_etablissement':
        cur.execute("SELECT * FROM violations WHERE etablissement LIKE ?",
                    ('%' + chaine + '%',))
    elif critere == 'proprietaire':
        cur.execute("SELECT * FROM violations WHERE proprietaire LIKE ?",
                    ('%' + chaine + '%',))
    elif critere == 'adresse':
        cur.execute("SELECT * FROM violations WHERE adresse LIKE ?",
                    ('%' + chaine + '%',))
    else:
        return []
    lignes = cur.fetchall()
    conn.close()
    return lignes


# A3, B1: Synchronisation quotidienne et détection des nouvelles contraventions
def synchroniser_donnees_quotidiennes():
    # Téléchargement à partir du URL (timeout de 60 sec)
    response = requests.get(CSV_URL, timeout=60)
    # Vérification du succès (code 200, sinon exception levée)
    response.raise_for_status()
    # Décodage du contenu en UTF-8
    csv_content = response.content.decode("utf-8-sig")

    # Sauvegarde du contenu local
    with open(CSV_PATH, "w", encoding="utf-8-sig") as fichier_csv:
        fichier_csv.write(csv_content)

    # Détection et envoi des nouvelles contraventions avant le remplacement
    # (fonctionnalité intégrée pour B1)
    # SMTP simulé, mais exception couverte pour éviter crash
    detecter_et_envoyer_nouvelles_contraventions(csv_content, DB_PATH)

    # Suppression des données courantes avant insertion des nouvelles données
    connexion = sqlite3.connect(DB_PATH)
    curseur = connexion.cursor()
    curseur.execute("DELETE FROM violations")
    connexion.commit()
    connexion.close()

    # Insertion des données du CSV dans la base de données
    insert_violations(csv_content, DB_PATH)


# A3: Configuration du scheduler (pour synchronisation quotidienne)
def configurer_scheduler():
    # Scheduler en arrière-plan avec fuseau horaire de Montréal
    scheduler = BackgroundScheduler(timezone="America/Montreal")
    # Exécution tous les jours à minuit (00:00)
    scheduler.add_job(
        synchroniser_donnees_quotidiennes,
        trigger="cron",
        hour=0,
        minute=0,
        # Fonction synchronisation à exécuter
        id="synchronisation-quotidienne-violations",
        replace_existing=True,
    )
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=False))
    return scheduler


# A4: Validation de date au format ISO (YYYY-MM-DD)
def valider_date_iso(texte_date):
    date.fromisoformat(texte_date)


# A4/A5: Service de contraventions entre deux dates (utilisé par l'Ajax A5)
@app.route('/contrevenants', methods=['GET'])
def contrevenants_par_dates():
    # Lecture des paramètres URL 'du' et 'au' (dates de début et de fin)
    date_du = request.args.get('du', '')
    date_au = request.args.get('au', '')

    # Erreur si paramètres manquants
    if not date_du or not date_au:
        return jsonify({
            'erreur': "Les paramètres 'du' et 'au' sont obligatoires."
        }), 400

    # Erreur si format de date invalide
    try:
        valider_date_iso(date_du)
        valider_date_iso(date_au)
    except ValueError:
        return jsonify({
            'erreur': 'Les dates doivent être au format ISO 8601 (YYYY-MM-DD).'
        }), 400

    # Erreur si date de début est après date de fin (du > au)
    if date_du > date_au:
        return jsonify({
            'erreur': "Le paramètre 'du' doit être inférieur ou égal à 'au'."
        }), 400

    # Effacement des tirets pour comparaison numérique dans la requête SQL
    # (ex: 2024-01-01 -> 20240101)
    date_du_compact = date_du.replace('-', '')
    date_au_compact = date_au.replace('-', '')

    # Requête SQL: contraventions entre les deux dates
    connexion = sqlite3.connect(DB_PATH)
    connexion.row_factory = sqlite3.Row
    curseur = connexion.cursor()
    curseur.execute(
        """
        SELECT *
        FROM violations
        WHERE REPLACE(date, '-', '') BETWEEN ? AND ?
        ORDER BY REPLACE(date, '-', '') ASC
        """,
        (date_du_compact, date_au_compact),
    )
    resultats = [dict(rangee) for rangee in curseur.fetchall()]
    connexion.close()

    # Retour des résultats au format JSON
    return jsonify(resultats)


# A4: Représentation HTML du document RAML
@app.route('/doc', methods=['GET'])
def doc_raml():
    # Erreur 404 si fichier RAML introuvable
    if not RAML_PATH.exists():
        return render_template('doc.html', contenu_raml=None), 404

    # Lecture en UTF-8
    contenu_raml = RAML_PATH.read_text(encoding='utf-8')
    return render_template('doc.html', contenu_raml=contenu_raml)


# D1: schema JSON pour la demande d'inspection
SCHEMA_DEMANDE_INSPECTION = {
    "type": "object",
    "required": [
        "nom_etablissement",
        "adresse",
        "ville",
        "date_visite_client",
        "nom_client",
        "prenom_client",
        "description_probleme",
    ],
    "properties": {
        "nom_etablissement": {"type": "string", "minLength": 1},
        "adresse": {"type": "string", "minLength": 1},
        "ville": {"type": "string", "minLength": 1},
        "date_visite_client": {"type": "string", "minLength": 1},
        "nom_client": {"type": "string", "minLength": 1},
        "prenom_client": {"type": "string", "minLength": 1},
        "description_probleme": {"type": "string", "minLength": 1},
    },
    "additionalProperties": False,
}


# D1: creation automatique de la table des demandes d'inspection
# (si non-existant)
def assurer_table_demandes_inspection():
    connexion = sqlite3.connect(DB_PATH)
    curseur = connexion.cursor()
    curseur.execute(
        """
        CREATE TABLE IF NOT EXISTS demandes_inspection (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_etablissement TEXT NOT NULL,
            adresse TEXT NOT NULL,
            ville TEXT NOT NULL,
            date_visite_client TEXT NOT NULL,
            nom_client TEXT NOT NULL,
            prenom_client TEXT NOT NULL,
            description_probleme TEXT NOT NULL,
            date_creation TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connexion.commit()
    connexion.close()


# D1: validation d'une demande d'inspection selon le schema JSON et le format
# de date ISO (YYYY-MM-DD)
def valider_demande_inspection(demande):
    validate(instance=demande, schema=SCHEMA_DEMANDE_INSPECTION)
    date_visite = date.fromisoformat(demande["date_visite_client"])
    # Erreur si date de visite plus loin que date actuelle (futur)
    if date_visite > date.today():
        raise ValueError(
            "La date de visite du client ne peut pas être dans le futur."
        )


# A6: Liste déroulante de tous les restaurants
# (ordre alphabétique, sans doublons)
@app.route('/restaurants', methods=['GET'])
def liste_restaurants():
    connexion = sqlite3.connect(DB_PATH)
    connexion.row_factory = sqlite3.Row
    curseur = connexion.cursor()
    curseur.execute(
        """
        SELECT DISTINCT etablissement
        FROM violations
        WHERE etablissement IS NOT NULL
          AND TRIM(etablissement) <> ''
        ORDER BY etablissement COLLATE NOCASE ASC
        """
    )
    restaurants = [rangee['etablissement'] for rangee in curseur.fetchall()]
    connexion.close()
    return jsonify(restaurants)


# A6: Informations détaillés selon recherche de nom de restaurant
# venant de la liste déroulante
@app.route('/infractions-restaurant', methods=['GET'])
def infractions_par_restaurant():
    # Lecture param. URL 'restaurant' (nom d'établissement)
    restaurant = request.args.get('restaurant', '').strip()
    # Erreur si paramètre manquant
    if not restaurant:
        return jsonify({
            'erreur': "Le paramètre 'restaurant' est obligatoire."
        }), 400

    # Requête SQL: contraventions pour le restaurant en ordre décroissant
    # de date
    connexion = sqlite3.connect(DB_PATH)
    connexion.row_factory = sqlite3.Row
    curseur = connexion.cursor()
    curseur.execute(
        """
        SELECT id_poursuite, etablissement, date, description, adresse,
               montant, statut, date_jugement, date_statut, categorie,
               proprietaire, ville
        FROM violations
        WHERE etablissement = ?
        ORDER BY REPLACE(date, '-', '') DESC
        """,
        (restaurant,),
    )
    resultats = [dict(rangee) for rangee in curseur.fetchall()]
    connexion.close()
    return jsonify(resultats)


# Liste des établissements avec leur nb d'infractions (ordre décroissant du
# nombre d'infractions, puis ordre alphabétique du nom d'établissement)
# C1/C2/C3: requête commune des établissements avec leur nombre d'infractions
def obtenir_etablissements_avec_infractions():
    connexion = sqlite3.connect(DB_PATH)
    connexion.row_factory = sqlite3.Row
    curseur = connexion.cursor()
    curseur.execute(
        """
        SELECT etablissement, COUNT(*) AS nombre_infractions
        FROM violations
        WHERE etablissement IS NOT NULL
          AND TRIM(etablissement) <> ''
        GROUP BY etablissement
        ORDER BY nombre_infractions DESC, etablissement COLLATE NOCASE ASC
        """
    )
    resultats = [dict(rangee) for rangee in curseur.fetchall()]
    connexion.close()
    return resultats


# C1: service REST JSON des établissements avec nombre d'infractions
@app.route('/etablissements-infractions', methods=['GET'])
def etablissements_avec_nombre_infractions():
    resultats = obtenir_etablissements_avec_infractions()
    # Format JSON retourné
    return jsonify(resultats)


# C2: Même fonction que /etablissements-infractions, mais en XML UTF-8
@app.route('/etablissements-infractions/xml', methods=['GET'])
def etablissements_avec_nombre_infractions_xml():
    resultats = obtenir_etablissements_avec_infractions()

    # Encodage en XML
    lignes_xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<etablissements>',
    ]
    for rangee in resultats:
        nom = escape(str(rangee['etablissement']))
        nombre = int(rangee['nombre_infractions'])
        lignes_xml.extend([
            '  <item>',
            f'    <etablissement>{nom}</etablissement>',
            f'    <nombre_infractions>{nombre}</nombre_infractions>',
            '  </item>',
        ])
    lignes_xml.append('</etablissements>')
    contenu_xml = '\n'.join(lignes_xml)

    return Response(
        contenu_xml,
        content_type='application/xml; charset=utf-8',
    )


# C3: Même fonction que C1/C2, mais en CSV
@app.route('/etablissements-infractions/csv', methods=['GET'])
def etablissements_avec_nombre_infractions_csv():
    resultats = obtenir_etablissements_avec_infractions()

    sortie = StringIO()
    writer = csv.writer(sortie)
    writer.writerow(['etablissement', 'nombre_infractions'])
    for rangee in resultats:
        writer.writerow([
            rangee['etablissement'],
            int(rangee['nombre_infractions']),
        ])
    contenu_csv = sortie.getvalue()

    return Response(
        contenu_csv,
        content_type='text/csv; charset=utf-8',
    )


# D1: Page de formulaire de demande d'inspection
@app.route('/plainte', methods=['GET'])
def page_plainte():
    return render_template('plainte.html')


# D1: Service REST de création de demande d'inspection
@app.route('/demandes-inspection', methods=['POST'])
def creer_demande_inspection():
    # Vérif. de la structure JSON
    demande = request.get_json(silent=True)
    if not isinstance(demande, dict):
        return jsonify({
            'erreur': 'La requête doit suivre une structure JSON valide.'
        }), 400

    # Validation des champs de la demande
    try:
        valider_demande_inspection(demande)
    except ValidationError as erreur:
        return jsonify({
            'erreur': f"Erreur: {erreur.message}"
        }), 400
    except ValueError as erreur:
        return jsonify({
            'erreur': f"Erreur: {erreur}"
        }), 400

    # Création de la table demandes_inspection si pas encore créée
    # (évite erreur si table absente)
    assurer_table_demandes_inspection()

    # Insertion demande d'inspection dans BD SQLite
    connexion = sqlite3.connect(DB_PATH)
    curseur = connexion.cursor()
    curseur.execute(
        """
        INSERT INTO demandes_inspection (
            nom_etablissement,
            adresse,
            ville,
            date_visite_client,
            nom_client,
            prenom_client,
            description_probleme
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            demande['nom_etablissement'].strip(),
            demande['adresse'].strip(),
            demande['ville'].strip(),
            demande['date_visite_client'].strip(),
            demande['nom_client'].strip(),
            demande['prenom_client'].strip(),
            demande['description_probleme'].strip(),
        ),
    )
    id_demande = curseur.lastrowid
    connexion.commit()
    connexion.close()

    # Code 201 (succès de création) avec ID demande en JSON
    return jsonify({
        'message': 'Demande d\'inspection créée avec succès.',
        'id': id_demande,
    }), 201


# D2: Service REST de suppression d'une demande d'inspection
@app.route('/demandes-inspection/<int:demande_id>', methods=['DELETE'])
def supprimer_demande_inspection(demande_id):
    # Connection à la base de données SQLite
    connexion = sqlite3.connect(DB_PATH)
    curseur = connexion.cursor()

    # Création de la table demandes_inspection si pas encore créée
    assurer_table_demandes_inspection()

    # Recherche de la demande d'inspection par ID
    curseur.execute(
        "SELECT id FROM demandes_inspection WHERE id = ?",
        (demande_id,),
    )
    demande = curseur.fetchone()

    # Erreur 404 si ID inexistant
    if demande is None:
        connexion.close()
        return jsonify({
            'erreur': 'Demande d\'inspection introuvable.'
        }), 404

    # Suppression de la demande d'inspection par id
    curseur.execute(
        "DELETE FROM demandes_inspection WHERE id = ?",
        (demande_id,),
    )
    connexion.commit()
    connexion.close()

    # Code 200 (succès) avec ID de la demande supprimée en JSON
    return jsonify({
        'message': 'Demande d\'inspection supprimée avec succès.',
        'id': demande_id,
    })


if __name__ == '__main__':
    configurer_scheduler()
    # Scheduler désactivé en mode debug pour éviter exécutions multiples
    app.run(debug=True, use_reloader=False)
