import unittest

import app as module_application


class TestA5RechercheRapideAccueil(unittest.TestCase):
    def setUp(self):
        # Flack en mode test
        module_application.app.config["TESTING"] = True
        # Client HTTP de test
        self.client = module_application.app.test_client()

    # Vérifie la présence du formulaire rapide (A5) sur la page d'accueil
    def test_page_accueil_contient_formulaire_recherche_rapide(self):
        # Requête GET à la page d'accueil
        reponse = self.client.get("/")
        # Vérifie du code 200 (page correctement chargée)
        self.assertEqual(reponse.status_code, 200)
        # Présence du formulaire rapide
        self.assertIn(b'id="formulaire-rapide"', reponse.data)
        # Présence des champs de date
        self.assertIn(b'id="date-du"', reponse.data)
        self.assertIn(b'id="date-au"', reponse.data)
        # Présence du bouton de soumission
        self.assertIn(b'/contrevenants?du=', reponse.data)
        # Précense d'un message d'information sur la recherche rapide
        self.assertIn(b'Nombre de contraventions', reponse.data)


if __name__ == "__main__":
    unittest.main()
