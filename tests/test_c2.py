import os
import sqlite3
import tempfile
import unittest
import xml.etree.ElementTree as ET

import app as module_application


class TestC2EtablissementsInfractionsXml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Base de données temporaire pour les tests
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
                'J-401', '4001', '20240310', 'Infraction 1', '1 Rue A',
                '20240410', 'Resto C2A', 120.0, 'Proprio A', 'Montreal',
                'Ouvert', '20240311', 'Bistro'
            ),
            (
                'J-402', '4001', '20240312', 'Infraction 2', '1 Rue A',
                '20240412', 'Resto C2A', 90.0, 'Proprio A', 'Montreal',
                'Fermé', '20240313', 'Bistro'
            ),
            (
                'J-403', '4002', '20240315', 'Infraction 3', '2 Rue B',
                '20240415', 'Resto C2B', 75.0, 'Proprio B', 'Montreal',
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

    def test_etablissements_infractions_xml_utf8_et_trie(self):
        reponse = self.client.get('/etablissements-infractions/xml')

        # Vérif. du code de statut et du type de contenu
        self.assertEqual(reponse.status_code, 200)
        self.assertIn('application/xml', reponse.content_type)
        self.assertIn('charset=utf-8', reponse.content_type.lower())

        # Vérif. du bon formatage XML
        texte_xml = reponse.data.decode('utf-8')
        racine = ET.fromstring(texte_xml)
        self.assertEqual(racine.tag, 'etablissements')

        # Bon ordre des établissements selon le nombre d'infractions
        items = racine.findall('item')
        self.assertEqual(len(items), 2)

        # Vérif. de la présence des champs et de leur contenu
        premier_nom = items[0].findtext('etablissement')
        premier_nb = items[0].findtext('nombre_infractions')
        second_nom = items[1].findtext('etablissement')
        second_nb = items[1].findtext('nombre_infractions')

        # Vérif. des bonnes valeurs
        self.assertEqual(premier_nom, 'Resto C2A')
        self.assertEqual(premier_nb, '2')
        self.assertEqual(second_nom, 'Resto C2B')
        self.assertEqual(second_nb, '1')


if __name__ == '__main__':
    unittest.main()
