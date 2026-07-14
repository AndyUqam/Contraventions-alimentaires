
"""
Script Python : insertion des données du fichier violations.csv dans la base
SQLite.
- Si violations.csv existe localement, il est utilisé.
- Sinon, le script télécharge le fichier depuis l’URL officielle.
"""


# Modules nécessaires :
# csv : traitement des fichiers CSV
# sqlite3 : manipulations de base de données SQLite
# os : vérification de l'existence du fichier local
# requests : téléchargement du fichier CSV depuis l'URL si non présent
# localement
# StringIO : traitement du contenu CSV en mémoire pour insertion dans la base
# de données
import csv
import sqlite3
import os
import requests
from io import StringIO

from b1_utils import detecter_et_envoyer_nouvelles_contraventions


# Chemin du fichier CSV local
CSV_PATH = "violations.csv"
# URL officielle du CSV si non présent localement
CSV_URL = (
    "https://data.montreal.ca/dataset/05a9e718-6810-4e73-8bb9-5955efeb91a0/"
    "resource/7f939a08-be8a-45e1-b208-d8744dca8fc6/download/violations.csv"
)
# Chemin de la base SQLite
DB_PATH = "db/violations.sqlite"


# Champs du CSV attendus dans le format actuel de la Ville de Montreal
CSV_FIELDS = [
    "id_poursuite",
    "business_id",
    "date",
    "description",
    "adresse",
    "date_jugement",
    "etablissement",
    "montant",
    "proprietaire",
    "ville",
    "statut",
    "date_statut",
    "categorie"
]


# Lecture du fichier CSV : localement ou par téléchargement
def get_csv_content():
    # Si fichier existant localement, alors le lire
    if os.path.exists(CSV_PATH):
        print(f"Fichier {CSV_PATH} trouvé localement.")
        with open(CSV_PATH, encoding='utf-8-sig') as f:
            return f.read()
    # sinon, télécharger le fichier depuis l'URL et le sauvegarder localement
    else:
        print(f"Fichier {CSV_PATH} non trouvé -> "
              + f"Téléchargement depuis {CSV_URL}...")
        try:
            # Télécharge avec timeout et configuration SSL robuste
            response = requests.get(CSV_URL, timeout=30, verify=True)
            response.raise_for_status()
            content = response.content.decode("utf-8-sig")
            # Sauvegarde le fichier téléchargé pour usage futur
            with open(CSV_PATH, "w", encoding="utf-8-sig") as f:
                f.write(content)
            print(f"Fichier téléchargé et sauvegardé sous {CSV_PATH}.")
            return content
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors du téléchargement: {e}")
            print(f"Vérifiez votre connexion réseau ou essayez plus tard.")
            raise


# Insertion des données du CSV dans la base SQLite
def insert_violations(csv_content, db_path):
    # Connexion à la base SQLite
    connection = sqlite3.connect(db_path)
    curseur = connection.cursor()
    # Lecture du CSV en mémoire
    lecteur = csv.DictReader(StringIO(csv_content))
    # Préparation des données à insérer (CSV -> liste locale)
    rangees = [
        (
            rangee.get("id_poursuite") or rangee.get("numero_jugement", ""),
            rangee.get("business_id") or
            rangee.get("numero_etablissement", ""),
            rangee.get("date") or rangee.get("date_infraction", ""),
            rangee.get("description") or
            rangee.get("description_infraction", ""),
            rangee.get("adresse", ""),
            rangee.get("date_jugement", ""),
            rangee.get("etablissement") or rangee.get("nom_etablissement", ""),
            rangee.get("montant") or rangee.get("montant_amende", ""),
            rangee.get("proprietaire", ""),
            rangee.get("ville", ""),
            rangee.get("statut", ""),
            rangee.get("date_statut", ""),
            rangee.get("categorie", "")
        )
        for rangee in lecteur
    ]
    # Insertion dans la table violations (liste locale -> base de données)
    curseur.executemany(
        """
        INSERT INTO violations (
            id_poursuite, business_id, date, description, adresse,
            date_jugement, etablissement, montant, proprietaire,
            ville, statut, date_statut, categorie
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rangees
    )
    connection.commit()
    connection.close()


# Fonction principale du script
def main():
    print("Obtention du contenu CSV")
    csv_content = get_csv_content()
    # Détection et envoi des nouvelles contraventions au destinataire
    # (fonctionnalité intégrée pour B1)
    # Comparaison non nécessaire pour processus d'initialisation
    # detecter_et_envoyer_nouvelles_contraventions(csv_content, DB_PATH)
    print("Insertion dans la base de données")
    insert_violations(csv_content, DB_PATH)
    print("Importation terminée.")


# Point d'entrée du script
if __name__ == "__main__":
    main()
