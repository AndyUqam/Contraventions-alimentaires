from pathlib import Path
import sqlite3

# Suppression du fichier CSV local et vidage de la base de données
# SQLite
racine_projet = Path(__file__).resolve().parent
chemin_bd = racine_projet / "db" / "violations.sqlite"
fichiers_a_supprimer = [racine_projet / "violations.csv"]


def vider_base_sqlite(chemin_sqlite: Path):
    # Fichier doit exister (base vide fournie dans le projet)
    chemin_sqlite.parent.mkdir(parents=True, exist_ok=True)
    chemin_sqlite.touch(exist_ok=True)

    connexion = sqlite3.connect(chemin_sqlite)
    curseur = connexion.cursor()

    # Suppression de tous les objets (tables, vues, triggers, index)
    curseur.execute(
        """
        SELECT type, name
        FROM sqlite_master
        WHERE name NOT LIKE 'sqlite_%'
          AND type IN ('table', 'view', 'index', 'trigger')
        ORDER BY CASE type
            WHEN 'view' THEN 1
            WHEN 'table' THEN 2
            WHEN 'trigger' THEN 3
            WHEN 'index' THEN 4
            ELSE 5
        END
        """
    )
    objets = curseur.fetchall()

    for type_objet, nom_objet in objets:
        if type_objet == "table":
            curseur.execute(f'DROP TABLE IF EXISTS "{nom_objet}"')
        elif type_objet == "view":
            curseur.execute(f'DROP VIEW IF EXISTS "{nom_objet}"')
        elif type_objet == "trigger":
            curseur.execute(f'DROP TRIGGER IF EXISTS "{nom_objet}"')
        elif type_objet == "index":
            curseur.execute(f'DROP INDEX IF EXISTS "{nom_objet}"')

    connexion.commit()
    connexion.execute("VACUUM")
    connexion.close()


for chemin in fichiers_a_supprimer:
    if chemin.exists():
        chemin.unlink()
        print(f"Supprime : {chemin}")
    else:
        print(f"Deja absent : {chemin}")

vider_base_sqlite(chemin_bd)
print(f"Base vidée (fichier conservé) : {chemin_bd}")
print("Projet reinitialisé. Relancez la creation des tables :\n"
      + "sqlite3 db/violations.sqlite < db/db.sql")
