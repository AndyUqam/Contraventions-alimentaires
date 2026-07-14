import os
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta

import app as module_application


class TestD1DemandesInspection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # BD temporaire pour tests
        fd, cls.chemin_bd_test = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)

        # Création table violations
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

    # Test de validité de la demande d'inspection
    def test_creer_demande_inspection_valide(self):
        payload = {
            'nom_etablissement': 'Restaurant Quelconque',
            'adresse': '1234 Rue Exemple',
            'ville': 'Montreal',
            'date_visite_client': '2026-04-14',
            'nom_client': 'Nguyen',
            'prenom_client': 'Andy',
            'description_probleme': 'Cheveux dans la nourriture',
        }

        reponse = self.client.post('/demandes-inspection', json=payload)
        # Insertion réussie (code 201)
        self.assertEqual(reponse.status_code, 201)
        # Format JSON
        self.assertEqual(reponse.content_type, 'application/json')
        contenu = reponse.get_json()
        # Présence de l'ID dans la réponse
        self.assertIn('id', contenu)

        # Présence de la demande dans la BD initialement vide
        connexion = sqlite3.connect(self.chemin_bd_test)
        curseur = connexion.cursor()
        curseur.execute('SELECT COUNT(*) FROM demandes_inspection')
        total = curseur.fetchone()[0]
        connexion.close()
        # 1 demande = celle nouvellement créée pour ce test
        self.assertEqual(total, 1)

    # Test de demande invalide (champ "ville" manquant)
    def test_creer_demande_inspection_invalide_retourne_400(self):
        payload = {
            'nom_etablissement': 'Restaurant Autre-Test',
            'adresse': '5678 Rue Autre-Exemple',
            'date_visite_client': '2026-02-20',
            'nom_client': 'Tremblay',
            'prenom_client': 'John',
            'description_probleme': 'Poulet expiré servi',
        }

        reponse = self.client.post('/demandes-inspection', json=payload)
        # Requête refusée (code 400)
        self.assertEqual(reponse.status_code, 400)
        contenu = reponse.get_json()
        # Message d'erreur dans la réponse
        self.assertIn('erreur', contenu)

    # Test de demande invalide (date de visite dans le futur)
    def test_creer_demande_inspection_date_future_retourne_400(self):
        # Date futur: 1 jour après la date actuelle
        date_futur = (date.today() + timedelta(days=1)).isoformat()
        payload = {
            'nom_etablissement': 'Restaurant Futur-Test',
            'adresse': '9999 Rue Futur-Exemple',
            'ville': 'Montreal',
            'date_visite_client': date_futur,
            'nom_client': 'Client',
            'prenom_client': 'Futur',
            'description_probleme': 'Date illogique (dans le futur)',
        }

        reponse = self.client.post('/demandes-inspection', json=payload)
        self.assertEqual(reponse.status_code, 400)
        contenu = reponse.get_json()
        self.assertIn('erreur', contenu)

    # Test de la présence de la page de plainte et de son formulaire
    def test_page_plainte_contient_formulaire_ajax(self):
        reponse = self.client.get('/plainte')
        # Page chargée avec succès (200)
        self.assertEqual(reponse.status_code, 200)
        # Formulaire de plainte présent
        self.assertIn(b'id="formulaire-plainte"', reponse.data)
        # Script JavaScript pointé vers /demandes-inspection présent
        self.assertIn(b'/demandes-inspection', reponse.data)
        # Champ description présent
        self.assertIn(b'description-probleme', reponse.data)


if __name__ == '__main__':
    unittest.main()
