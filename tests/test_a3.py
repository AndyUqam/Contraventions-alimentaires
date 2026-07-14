import os
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch

import app as module_application


# Faux scheduler pour tester la configuration sans lancer APScheduler réel.
class FauxScheduler:
    def __init__(self, timezone):
        self.timezone = timezone
        self.jobs = []
        self.demarre = False
        self.arrete = False

    def add_job(self, func, **kwargs):
        self.jobs.append((func, kwargs))

    def start(self):
        self.demarre = True

    def shutdown(self, wait=False):
        self.arrete = True


class TestA3Synchronisation(unittest.TestCase):
    def setUp(self):
        # Sauvegarde des chemins globaux (évite effets de bord)
        self.original_db_path = module_application.DB_PATH
        self.original_csv_path = module_application.CSV_PATH

    def tearDown(self):
        # Restauration des chemins originaux après chaque test
        module_application.DB_PATH = self.original_db_path
        module_application.CSV_PATH = self.original_csv_path

    @patch("app.requests.get")
    def test_synchronisation_quotidienne_remplace_les_donnees(self, mock_get):
        # BD et un CSV temporaires pour test isolé
        with tempfile.TemporaryDirectory() as dossier_temp:
            chemin_bd = os.path.join(dossier_temp, "test.sqlite")
            chemin_csv = os.path.join(dossier_temp, "violations_sync.csv")

            # Création de la table attendue et d'une ancienne ligne à remplacer
            connexion = sqlite3.connect(chemin_bd)
            curseur = connexion.cursor()
            curseur.execute(
                """
                CREATE TABLE violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_poursuite TEXT,
                    business_id TEXT,
                    date TEXT,
                    description TEXT,
                    adresse TEXT,
                    date_jugement TEXT,
                    etablissement TEXT,
                    montant REAL,
                    proprietaire TEXT,
                    ville TEXT,
                    statut TEXT,
                    date_statut TEXT,
                    categorie TEXT
                )
                """
            )
            curseur.execute(
                """
                INSERT INTO violations (
                    id_poursuite, business_id, date, description, adresse,
                    date_jugement, etablissement, montant, proprietaire,
                    ville, statut, date_statut, categorie
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "ANCIEN",
                    "0",
                    "20200101",
                    "Ancienne ligne",
                    "Ancienne adresse",
                    "20200102",
                    "Ancien resto",
                    1,
                    "Ancien proprio",
                    "Montreal",
                    "Ouvert",
                    "20200103",
                    "Categorie"
                ),
            )
            connexion.commit()
            connexion.close()

            # CSV simulé représentant la nouvelle ligne
            # qui remplacera l'ancienne ligne.
            contenu_csv = (
                "id_poursuite,business_id,date,description,adresse,"
                "date_jugement,"
                "etablissement,montant,proprietaire,ville,statut,"
                "date_statut,categorie\n"
                "J-900,900,20240310,Description test,10 Rue Test,"
                "20240410,"
                "Resto Sync,100.5,Proprio Sync,Montreal,Ouvert,"
                "20240311,Bistro\n"
            )

            reponse = Mock()
            reponse.content = contenu_csv.encode("utf-8-sig")
            reponse.raise_for_status = Mock()
            mock_get.return_value = reponse

            # Obligation pour l'application d'utiliser les fichiers temporaires
            module_application.DB_PATH = chemin_bd
            module_application.CSV_PATH = chemin_csv

            # Exécute la synchronisation quotidienne à tester.
            module_application.synchroniser_donnees_quotidiennes()

            # Vérif. que l'ancienne donnée a été remplacée par la nouvelle
            connexion = sqlite3.connect(chemin_bd)
            curseur = connexion.cursor()
            curseur.execute("SELECT COUNT(*) FROM violations")
            total = curseur.fetchone()[0]
            curseur.execute(
                "SELECT id_poursuite, "
                "etablissement FROM violations"
            )
            ligne = curseur.fetchone()
            connexion.close()

            # Vérif: 1 ligne présente avec nouvelles données
            self.assertEqual(total, 1)
            self.assertEqual(ligne[0], "J-900")
            self.assertEqual(ligne[1], "Resto Sync")
            self.assertTrue(os.path.exists(chemin_csv))

    @patch("app.atexit.register")
    @patch("app.BackgroundScheduler")
    def test_configurer_scheduler_planifie_minuit(
        self, mock_scheduler_class, mock_atexit_register
    ):
        # Remplacement du scheduler réel par un faux objet contrôlable
        scheduler = FauxScheduler(timezone="America/Montreal")
        mock_scheduler_class.return_value = scheduler

        # Config. du scheduler via la fonction de l'app
        resultat = module_application.configurer_scheduler()

        # Vérif. de la configuration globale
        self.assertIs(resultat, scheduler)
        self.assertTrue(scheduler.demarre)
        self.assertEqual(scheduler.timezone, "America/Montreal")
        self.assertEqual(len(scheduler.jobs), 1)

        # Vérif. que la tâche est planifiée en cron à minuit.
        fonction_job, kwargs_job = scheduler.jobs[0]
        self.assertIs(
            fonction_job,
            module_application.synchroniser_donnees_quotidiennes,
        )
        self.assertEqual(kwargs_job["trigger"], "cron")
        self.assertEqual(kwargs_job["hour"], 0)
        self.assertEqual(kwargs_job["minute"], 0)
        self.assertEqual(
            kwargs_job["id"], "synchronisation-quotidienne-violations"
        )
        self.assertTrue(kwargs_job["replace_existing"])

        # Vérif. d'un arrêt propre à la fermeture du process.
        mock_atexit_register.assert_called_once()


if __name__ == "__main__":
    unittest.main()
