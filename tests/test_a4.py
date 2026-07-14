import os
import sqlite3
import tempfile
import unittest

import app as module_application


class TestA4ServiceRestDates(unittest.TestCase):
    @classmethod
    # Initialisation de la BD de test avec une contravention
    def setUpClass(cls):
        fd, cls.chemin_bd_test = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)

        # Création de la table et insertion d'une contravention de test
        connexion = sqlite3.connect(cls.chemin_bd_test)
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
                "J-123",
                "1001",
                "20240310",
                "Infraction test",
                "10 Rue Test",
                "20240410",
                "Resto A4",
                100.0,
                "Proprio A4",
                "Montreal",
                "Ouvert",
                "20240311",
                "Bistro",
            ),
        )
        connexion.commit()
        connexion.close()

        module_application.DB_PATH = cls.chemin_bd_test
        module_application.app.config["TESTING"] = True

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.chemin_bd_test):
            os.remove(cls.chemin_bd_test)

    def setUp(self):
        self.client = module_application.app.test_client()

    # Test /contrevenants avec des dates valides
    def test_contrevenants_entre_deux_dates_retourne_json(self):
        reponse = self.client.get("/contrevenants?du=2024-03-01&au=2024-03-31")
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.content_type, "application/json")
        donnees = reponse.get_json()
        self.assertEqual(len(donnees), 1)
        self.assertEqual(donnees[0]["id_poursuite"], "J-123")

    # Test /contrevenants avec des dates invalides
    def test_contrevenants_dates_invalides_retourne_400(self):
        reponse = self.client.get("/contrevenants?du=2024-99-99&au=2024-03-31")
        self.assertEqual(reponse.status_code, 400)

    # Test /contrevenants avec des dates dans le mauvais ordre (du > au)
    def test_contrevenants_dates_mauvais_ordre_retourne_400(self):
        reponse = self.client.get("/contrevenants?du=2024-03-31&au=2024-03-01")
        self.assertEqual(reponse.status_code, 400)

    # Test /doc avec un fichier RAML existant
    def test_doc_affiche_raml_en_html(self):
        reponse = self.client.get("/doc")
        self.assertEqual(reponse.status_code, 200)
        self.assertIn(b"Documentation RAML", reponse.data)
        self.assertIn(b"/contrevenants", reponse.data)


if __name__ == "__main__":
    unittest.main()
