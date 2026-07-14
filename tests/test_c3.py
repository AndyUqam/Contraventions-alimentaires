import os
import sqlite3
import tempfile
import unittest
import csv
from io import StringIO

import app as module_application


class TestC3EtablissementsInfractionsCSV(unittest.TestCase):
    @classmethod
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
                'J-501', '5001', '20240310', 'Infraction 1', '1 Rue A',
                '20240410', 'Resto C3A', 120.0, 'Proprio A', 'Montreal',
                'Ouvert', '20240311', 'Bistro'
            ),
            (
                'J-502', '5001', '20240312', 'Infraction 2', '1 Rue A',
                '20240412', 'Resto C3A', 90.0, 'Proprio A', 'Montreal',
                'Fermé', '20240313', 'Bistro'
            ),
            (
                'J-503', '5002', '20240315', 'Infraction 3', '2 Rue B',
                '20240415', 'Resto C3B', 75.0, 'Proprio B', 'Montreal',
                'Ouvert', '20240316', 'Café'
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

    def test_etablissements_infractions_csv_utf8_et_trie(self):
        reponse = self.client.get('/etablissements-infractions/csv')
        self.assertEqual(reponse.status_code, 200)
        self.assertIn('text/csv', reponse.content_type)
        self.assertIn('charset=utf-8', reponse.content_type.lower())

        texte_csv = reponse.data.decode('utf-8')
        lecteur = csv.reader(StringIO(texte_csv))
        lignes = list(lecteur)

        self.assertGreaterEqual(len(lignes), 3)
        self.assertEqual(lignes[0], ['etablissement', 'nombre_infractions'])
        self.assertEqual(lignes[1][0], 'Resto C3A')
        self.assertEqual(lignes[1][1], '2')
        self.assertEqual(lignes[2][0], 'Resto C3B')
        self.assertEqual(lignes[2][1], '1')


if __name__ == '__main__':
    unittest.main()
