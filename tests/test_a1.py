import os
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch

import import_violations as a1


class TestA1ImportViolations(unittest.TestCase):

    # Initialisation de départ pour les tests
    def setUp(self):
        self.chemin_csv_original = a1.CSV_PATH
        self.url_csv_original = a1.CSV_URL

    # Nettoyage après chaque tests (restauration des valeurs originales)
    def tearDown(self):
        a1.CSV_PATH = self.chemin_csv_original
        a1.CSV_URL = self.url_csv_original

    # Test de lecture du CSV depuis un fichier local
    def test_get_csv_content_depuis_fichier_local(self):
        # Dossier temporaire pour test (supprimé automatiquement après le test)
        with tempfile.TemporaryDirectory() as dossier_temp:
            # Chemin du du fichier CSV
            chemin_csv = os.path.join(dossier_temp, "violations_test.csv")
            # Contenu attendu à lire du fichier CSV
            contenu_attendu = "col1,col2\nval1,val2\n"
            # Création du fichier CSV avec le contenu attendu
            with open(chemin_csv, "w", encoding="utf-8-sig") as fichier:
                fichier.write(contenu_attendu)
            # Modification chemin CSV dans le module pour pointer vers le
            # fichier de test
            a1.CSV_PATH = chemin_csv
            contenu = a1.get_csv_content()
            # Comparaison contenu lu vs. au contenu attendu
            self.assertEqual(contenu, contenu_attendu)

    # Test de téléchargement du CSV si fichier local absent
    # Remplacement de requests.get par un mock pour éviter appels réels
    @patch("import_violations.requests.get")
    def test_get_csv_content_telechargement_si_absent(self, mock_obtenir):
        # Dossier temporaire pour test (supprimé automatiquement après le test)
        with tempfile.TemporaryDirectory() as dossier_temp:
            chemin_csv = os.path.join(dossier_temp, "absent.csv")
            contenu_telecharge = "a,b\n1,2\n"
            # Mock pour simuler téléchargement du CSV
            reponse = Mock()
            reponse.content = contenu_telecharge.encode("utf-8-sig")
            reponse.raise_for_status = Mock()
            mock_obtenir.return_value = reponse
            # Obligation d'utiliser chemin CSV non-existant pour forcer
            # un téléchargement
            a1.CSV_PATH = chemin_csv
            a1.CSV_URL = "http://exemple.test/violations.csv"
            # Appel de la fonction à tester
            contenu = a1.get_csv_content()
            # Vérification que le contenu téléchargé est correct et que le
            # fichier a été créé avec le bon contenu
            self.assertEqual(contenu, contenu_telecharge)
            self.assertTrue(os.path.exists(chemin_csv))
            with open(chemin_csv, "r", encoding="utf-8-sig") as fichier:
                self.assertEqual(fichier.read(), contenu_telecharge)
            mock_obtenir.assert_called_once_with(a1.CSV_URL, timeout=30, verify=True)

    # Test d'insertion des données du CSV dans la base de données SQLite
    def test_insert_violations_inserer_lignes_dans_sqlite(self):
        # Dossier temporaire pour test (supprimé automatiquement après le test)
        with tempfile.TemporaryDirectory() as dossier_temp:
            chemin_bd = os.path.join(dossier_temp, "test.sqlite")
            connexion = sqlite3.connect(chemin_bd)
            curseur = connexion.cursor()
            # Création table pour les violations
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
            connexion.commit()
            connexion.close()
            # Création faux CSV en mémoire pour test d'insertion
            # (2 contraventions à insérer)
            contenu_csv = (
                "numero_etablissement,nom_etablissement,proprietaire,adresse,"
                "ville,code_postal,date_infraction,description_infraction,"
                "montant_amende,date_jugement,numero_jugement\n"
                "1001,Test Resto,Test Proprio,Rue Test,Montreal,H1A1A1,"
                "2024-01-01,Description A,250,2024-02-01,J-001\n"
                "1002,Test Resto 2,Test Proprio 2,Rue Test 2,Montreal,H1A1A2,"
                "2024-01-02,Description B,500,2024-02-02,J-002\n"
            )
            # Insertion des données du faux CSV
            a1.insert_violations(contenu_csv, chemin_bd)
            # Vérification de la bonne insertion des données
            # (doit être 2 lignes dans la table violations)
            connexion = sqlite3.connect(chemin_bd)
            curseur = connexion.cursor()
            curseur.execute("SELECT COUNT(*) FROM violations")
            total = curseur.fetchone()[0]
            connexion.close()

            self.assertEqual(total, 2)


if __name__ == "__main__":
    unittest.main()
