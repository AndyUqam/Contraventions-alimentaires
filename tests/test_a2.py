import os
import sqlite3
import tempfile
import unittest

import app as module_application


# Test de recherche de contraventions
class TestRechercheContraventions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Création base de données SQLite temporaire pour les tests
        descripteur_fichier, cls.chemin_bd_test = (
            tempfile.mkstemp(suffix=".sqlite")
        )
        os.close(descripteur_fichier)

        # Création table et insertion contravention de test
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
                "2024-01-10",
                "Infraction test",
                "Boulevard Rosemont",
                "2024-02-10",
                "Restaurant Rosemont",
                250.0,
                "Proprio Test",
                "Montreal",
                "Ouvert",
                "19931012",
                "Boucherie"
            ),
        )
        connexion.commit()
        connexion.close()

        # Utilisation du BD de test pour l'application Flask
        module_application.DB_PATH = cls.chemin_bd_test
        # Activation du mode test pour Flask (désactive certaines
        # fonctionnalités de sécurité)
        module_application.app.config["TESTING"] = True

    @classmethod
    # Nettoyage du fichier de base de données temporaire après les tests
    def tearDownClass(cls):
        if os.path.exists(cls.chemin_bd_test):
            os.remove(cls.chemin_bd_test)

    # Configuration avant chaque test
    def setUp(self):
        self.client_test = module_application.app.test_client()

    # Test chargement page d'accueil
    def test_page_accueil_se_charge(self):
        reponse = self.client_test.get("/")
        self.assertEqual(reponse.status_code, 200)
        self.assertIn("Recherche de contraventions".encode("utf-8"),
                      reponse.data)

    # Test de recherche par nom (contravention existante)
    def test_recherche_par_nom(self):
        reponse = self.client_test.post(
            "/resultats",
            data={"critere": "nom_etablissement", "chaine": "Rosemont"},
        )
        # Succès si page chargé (200) et nom établissement trouvé dans le
        # résultat
        self.assertEqual(reponse.status_code, 200)
        self.assertIn("Restaurant Rosemont".encode("utf-8"), reponse.data)

    # Test de recherche par propriétaire (contravention existante)
    def test_recherche_par_proprietaire(self):
        reponse = self.client_test.post(
            "/resultats",
            data={"critere": "proprietaire", "chaine": "Proprio Test"},
        )
        self.assertEqual(reponse.status_code, 200)
        self.assertIn("Restaurant Rosemont".encode("utf-8"), reponse.data)

    # Test de recherche par rue (contravention existante)
    def test_recherche_par_rue(self):
        reponse = self.client_test.post(
            "/resultats",
            data={"critere": "adresse", "chaine": "Rosemont"},
        )
        self.assertEqual(reponse.status_code, 200)
        self.assertIn("Restaurant Rosemont".encode("utf-8"), reponse.data)

    # Test de recherche sans résultat (contravention inexistante)
    def test_recherche_sans_resultat(self):
        reponse = self.client_test.post(
            "/resultats",
            data={"critere": "adresse", "chaine": "Inexistante"},
        )
        # Succès si page chargé (200) avec message "Aucun résultat trouvé"
        self.assertEqual(reponse.status_code, 200)
        self.assertIn("Aucun résultat trouvé".encode("utf-8"), reponse.data)


if __name__ == "__main__":
    unittest.main()
