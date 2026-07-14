import csv
import smtplib
import sqlite3
from email.message import EmailMessage
from io import StringIO

try:
    import yaml
except ImportError:
    yaml = None

CONFIG_B1_PATH = "b1.yaml"
SMTP_HOST = "localhost"
SMTP_PORT = 25
EXPEDITEUR_DEFAUT = "noreply@inf5190.local"
SUJET_DEFAUT = "Nouvelles contraventions détectées"


def nettoyer_texte(valeur, valeur_defaut=""):
    if valeur is None:
        return valeur_defaut
    return str(valeur).strip()


# Lecture du fichier contenant le courriel du destinataire
def charger_configuration_b1(chemin_config=CONFIG_B1_PATH):
    if yaml is None:
        return {}
    try:
        with open(chemin_config, encoding="utf-8") as fichier_yaml:
            configuration = yaml.safe_load(fichier_yaml) or {}
    except (FileNotFoundError, OSError, yaml.YAMLError):
        configuration = {}
    if not isinstance(configuration, dict):
        return {}
    return configuration


# Récupération de tous les id_poursuite existants dans le BD SQLite
def charger_ids_existants(db_path):
    try:
        connexion = sqlite3.connect(db_path)
        curseur = connexion.cursor()
        curseur.execute(
            """
            SELECT id_poursuite
            FROM violations
            WHERE id_poursuite IS NOT NULL
              AND TRIM(id_poursuite) <> ''
            """
        )
        ids_existants = {rangee[0] for rangee in curseur.fetchall()}
        connexion.close()
        return ids_existants
    except sqlite3.Error:
        return set()


# Extraction des nouvelles contraventions à partir du contenu CSV
def extraire_nouvelles_contraventions(csv_content, db_path):
    ids_existants = charger_ids_existants(db_path)
    if not ids_existants:
        return []

    lecteur = csv.DictReader(StringIO(csv_content))
    contraventionsNouv = []
    ids_vus = set()

    for rangee in lecteur:
        id_poursuite = (rangee.get("id_poursuite") or "").strip()
        # id_poursuite vide ou null (ignorer ligne)
        if not id_poursuite:
            continue
        # id_poursuite déjà dans la base de données
        if id_poursuite in ids_existants:
            continue
        # id_poursuite déjà vu (éviter doublon)
        if id_poursuite in ids_vus:
            continue
        ids_vus.add(id_poursuite)
        contraventionsNouv.append(rangee)

    return contraventionsNouv


# Rédaction du message de courriel à partir des nouvelles contraventions
def composer_texte_courriel(nouvelles_contraventions):
    lignes = ["Nouvelles contraventions détectées :", ""]
    # Structure simple: 1 ligne par contravention
    for rangee in nouvelles_contraventions:
        lignes.append(
            f"- {rangee.get('id_poursuite', '')} | "
            f"{rangee.get('date', '')} | "
            f"{rangee.get('etablissement', '')} | "
            f"{rangee.get('adresse', '')}"
        )
    return "\n".join(lignes)


# Envoi du courriel
def envoyer_courriel_nouvelles_contraventions(
    nouvelles_contraventions,
    chemin_config=CONFIG_B1_PATH,
):
    # Pas d'envoi si aucune nouvelle contravention
    if not nouvelles_contraventions:
        return False

    # Extraction du destinataire dans b1.yaml
    configuration = charger_configuration_b1(chemin_config)
    destinataire = nettoyer_texte(configuration.get("destinataire", ""))
    # Pas d'envoi si destinataire absent ou vide
    # (prévient un crash en cas de config. manquante)
    if not destinataire:
        return False

    # Expéditeur par défaut (personnalisable)
    expediteur = nettoyer_texte(configuration.get(
        "expediteur",
        EXPEDITEUR_DEFAUT,
    ))
    # Nom du sujet par défaut (personnalisable)
    sujet = nettoyer_texte(configuration.get(
        "sujet",
        SUJET_DEFAUT,
    ))

    # Rédaction du corps
    corps = composer_texte_courriel(nouvelles_contraventions)

    message = EmailMessage()
    message["Subject"] = sujet
    message["From"] = expediteur
    message["To"] = destinataire
    message.set_content(corps)

    # Envoi du courriel via SMTP local
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException, ValueError):
        return False

    return True


# Fonction principale (appel de toutes les fonctions précédentes)
def detecter_et_envoyer_nouvelles_contraventions(
    csv_content,
    db_path,
    chemin_config=CONFIG_B1_PATH,
):
    try:
        nouvelles = extraire_nouvelles_contraventions(csv_content, db_path)
        envoyer_courriel_nouvelles_contraventions(nouvelles, chemin_config)
        return nouvelles
    # Exception attrapée pour éviter crash de l'application
    except Exception:
        return []
