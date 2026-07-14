import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import b1_utils


# Simulation d'un serveur SMTP (test sans envoi réel)
class FauxSMTP:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.message_envoyee = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def send_message(self, message):
        self.message_envoyee = message


class TestB1NouvellesContraventions(unittest.TestCase):
    @classmethod
    # Base de données temporaire
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
        curseur.execute(
            """
            INSERT INTO violations (
                id_poursuite, business_id, date, description, adresse,
                date_jugement, etablissement, montant, proprietaire,
                ville, statut, date_statut, categorie
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                'J-100', '100', '20240301', 'Ancienne infraction',
                '1 Rue Ancienne', '20240302', 'Resto Ancien', 50.0,
                'Proprio Ancien', 'Montreal', 'Ouvert', '20240303',
                'Bistro'
            ),
        )
        connexion.commit()
        connexion.close()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.chemin_bd_test):
            os.remove(cls.chemin_bd_test)

    def test_detecter_nouvelles_contraventions_dedoublonne(self):
        # CSV de test en mémoire (2 nouvelles contraventions, 1 doublon)
        csv_content = (
            'id_poursuite,business_id,date,description,adresse,'
            'date_jugement,etablissement,montant,proprietaire,ville,'
            'statut,date_statut,categorie\n'
            'J-100,100,20240301,Ancienne infraction,1 Rue Ancienne,'
            '20240302,Resto Ancien,50.0,Proprio Ancien,Montreal,Ouvert,'
            '20240303,Bistro\n'
            'J-200,200,20240401,Nouvelle infraction,2 Rue Nouvelle,'
            '20240402,Resto Nouveau,75.0,Proprio Nouveau,Montreal,Ouvert,'
            '20240403,Café\n'
            'J-200,200,20240401,Nouvelle infraction,2 Rue Nouvelle,'
            '20240402,Resto Nouveau,75.0,Proprio Nouveau,Montreal,Ouvert,'
            '20240403,Café\n'
            'J-300,300,20240405,Autre nouvelle infraction,3 Rue Autre,'
            '20240406,Resto Autre,80.0,Proprio Autre,Montreal,Ouvert,'
            '20240407,Bistro\n'
        )

        nouvelles = b1_utils.extraire_nouvelles_contraventions(
            csv_content,
            self.chemin_bd_test,
        )

        # 2 nouvelles contraventions détectées (J-200 et J-300)
        self.assertEqual(len(nouvelles), 2)
        self.assertEqual(nouvelles[0]['id_poursuite'], 'J-200')
        self.assertEqual(nouvelles[1]['id_poursuite'], 'J-300')

    @patch('b1_utils.smtplib.SMTP', new=FauxSMTP)
    # Test d'envoi avec YAML
    def test_envoyer_courriel_utilise_yaml(self):
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8',
        ) as fichier_yaml:
            # YAML temporaire
            chemin_yaml = fichier_yaml.name
            fichier_yaml.write('destinataire: courrieltest@exemple.com\n')

        try:
            nouvelles = [
                {
                    'id_poursuite': 'J-200',
                    'date': '20240401',
                    'etablissement': 'Resto Nouveau',
                    'adresse': '2 Rue Nouvelle',
                }
            ]
            # Appel de la fct. d'envoi (doit retourner True et envoyer à YAML)
            resultat = b1_utils.envoyer_courriel_nouvelles_contraventions(
                nouvelles,
                chemin_yaml,
            )
            self.assertTrue(resultat)
        finally:
            if os.path.exists(chemin_yaml):
                os.remove(chemin_yaml)


if __name__ == '__main__':
    unittest.main()
