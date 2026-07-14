import os
import sqlite3
import tempfile
import unittest

import app as module_application


class TestC1EtablissementsInfractions(unittest.TestCase):
    @classmethod
    # Init. du DB de test et insertion de données de test
    def setUpClass(cls):
        fd, cls.chemin_bd_test = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)

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
        donnees = [
            (
                'J-301', '3001', '20240310', 'Infraction 1', '1 Rue A',
                '20240410', 'Resto C1', 120.0, 'Proprio A', 'Montreal',
                'Ouvert', '20240311', 'Bistro'
            ),
            (
                'J-302', '3001', '20240312', 'Infraction 2', '1 Rue A',
                '20240412', 'Resto C1', 90.0, 'Proprio A', 'Montreal',
                'Fermé', '20240313', 'Bistro'
            ),
            (
                'J-303', '3002', '20240315', 'Infraction 3', '2 Rue B',
                '20240415', 'Resto C2', 75.0, 'Proprio B', 'Montreal',
                'Ouvert', '20240316', 'Café'
            ),
            (
                'J-304', '3003', '20240318', 'Infraction 4', '3 Rue C',
                '20240418', 'Resto C1', 55.0, 'Proprio A', 'Montreal',
                'Ouvert', '20240319', 'Bistro'
            ),
        ]
        curseur.executemany(
            """
            INSERT INTO violations (
                id_poursuite, business_id, date, description, adresse,
                date_jugement, etablissement, montant, proprietaire,
                ville, statut, date_statut, categorie
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            donnees,
        )
        connexion.commit()
        connexion.close()

        module_application.DB_PATH = cls.chemin_bd_test
        module_application.app.config['TESTING'] = True

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.chemin_bd_test):
            os.remove(cls.chemin_bd_test)

    def setUp(self):
        self.client = module_application.app.test_client()

    # Test de la bonne ordre des établissements selon le nombre d'infractions
    def test_etablissements_infractions_retourne_compte_trie(self):
        reponse = self.client.get('/etablissements-infractions')
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.content_type, 'application/json')

        donnees = reponse.get_json()
        self.assertEqual(len(donnees), 2)
        self.assertEqual(donnees[0]['etablissement'], 'Resto C1')
        self.assertEqual(donnees[0]['nombre_infractions'], 3)
        self.assertEqual(donnees[1]['etablissement'], 'Resto C2')
        self.assertEqual(donnees[1]['nombre_infractions'], 1)


if __name__ == '__main__':
    unittest.main()
