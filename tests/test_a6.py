import os
import sqlite3
import tempfile
import unittest

import app as module_application


class TestA6RechercheRestaurant(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fd, cls.chemin_bd_test = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)

        # Création d'une table temporaire et insertion de données de test
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
                'J-201', '2001', '20240210', 'Infraction 1', '1 Rue A',
                '20240310', 'Resto A6', 120.0, 'Proprio A', 'Montreal',
                'Ouvert', '20240211', 'Bistro'
            ),
            (
                'J-202', '2001', '20240212', 'Infraction 2', '1 Rue A',
                '20240312', 'Resto A6', 90.0, 'Proprio A', 'Montreal',
                'Fermé', '20240213', 'Bistro'
            ),
            (
                'J-203', '2002', '20240215', 'Infraction 3', '2 Rue B',
                '20240315', 'Resto B6', 75.0, 'Proprio B', 'Montreal',
                'Ouvert', '20240216', 'Café'
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

    # Test de la route pour obtenir les noms corrects des restaurants
    def test_restaurants_retourne_liste_distincte(self):
        reponse = self.client.get('/restaurants')
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.content_type, 'application/json')
        restaurants = reponse.get_json()
        self.assertEqual(restaurants, ['Resto A6', 'Resto B6'])

    # Test sans paramètre pour recevoir une erreur 400
    def test_infractions_restaurant_sans_parametre_retourne_400(self):
        reponse = self.client.get('/infractions-restaurant')
        self.assertEqual(reponse.status_code, 400)

    # Test du bon nombre d'infractions retournées pour un restaurant donné et
    # de la présence des champs attendus
    def test_infractions_restaurant_retourne_details(self):
        reponse = self.client.get(
            '/infractions-restaurant?restaurant=Resto%20A6'
        )
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.content_type, 'application/json')
        infractions = reponse.get_json()
        self.assertEqual(len(infractions), 2)
        self.assertEqual(infractions[0]['etablissement'], 'Resto A6')
        self.assertIn('description', infractions[0])
        self.assertIn('montant', infractions[0])


if __name__ == '__main__':
    unittest.main()
