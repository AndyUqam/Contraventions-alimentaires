import os
import sqlite3
import tempfile
import unittest

import app as module_application


class TestD2SuppressionDemandeInspection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fd, cls.chemin_bd_test = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)

        # Base de données temporaire pour les tests
        connexion = sqlite3.connect(cls.chemin_bd_test)
        curseur = connexion.cursor()
        curseur.execute(
            """
            CREATE TABLE demandes_inspection (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom_etablissement TEXT NOT NULL,
                adresse TEXT NOT NULL,
                ville TEXT NOT NULL,
                date_visite_client TEXT NOT NULL,
                nom_client TEXT NOT NULL,
                prenom_client TEXT NOT NULL,
                description_probleme TEXT NOT NULL,
                date_creation TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        curseur.execute(
            """
            INSERT INTO demandes_inspection (
                nom_etablissement, adresse, ville, date_visite_client,
                nom_client, prenom_client, description_probleme
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                'Restaurant TestD2',
                '1222 Rue ExempleD2',
                'Montreal',
                '2026-04-15',
                'Tremblay',
                'Jean',
                'Problème pour tester D2',
            ),
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

    # Test de suppression de demande d'inspection existante
    def test_supprimer_demande_inspection_reussit(self):
        # Id = 1 (premiière demande créée au setupClass)
        reponse = self.client.delete('/demandes-inspection/1')
        # Code 200 (succès)
        self.assertEqual(reponse.status_code, 200)
        # Réponse JSON
        self.assertEqual(reponse.content_type, 'application/json')
        contenu = reponse.get_json()
        # ID demande supprimée = 1
        self.assertEqual(contenu['id'], 1)

        connexion = sqlite3.connect(self.chemin_bd_test)
        curseur = connexion.cursor()
        curseur.execute('SELECT COUNT(*) FROM demandes_inspection')
        total = curseur.fetchone()[0]
        connexion.close()
        # Table vide après suppression de la seule demande d'inspection: 0
        self.assertEqual(total, 0)

    # Test de suppression d'une demande d'inspection inexistante
    def test_supprimer_demande_inspection_introuvable_retourne_404(self):
        # Id 99999 (inexistant)
        reponse = self.client.delete('/demandes-inspection/99999')
        # Code 404 (non trouvé)
        self.assertEqual(reponse.status_code, 404)
        contenu = reponse.get_json()
        # Erreur dans la réponse JSON
        self.assertIn('erreur', contenu)


if __name__ == '__main__':
    unittest.main()
