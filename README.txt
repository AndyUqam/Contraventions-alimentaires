Programme de contravention alimentaire
INF5090: Programmation Web Avancée
Andy Bao-Hung Nguyen: NGUA74080104

Cette application permet de consulter les contraventions alimentaires des
établissement de Montréal, ainsi que de créer une demande de plainte et
recevoir l'annonce de nouvelles contraventions par courriel électronique.


Pour démarrer le programme, veuillez suivre les étapes suivantes.

1- Installez Python3 sur votre système.
Installer python 3

2- Dans la racine du projet, créez un nouvel environnement virtuel (automatiquement appelé venv ici).
python3 -m venv venv

3- Activez cet environnement. Il doit rester actif durant l'utilisation de l'application.
source venv/bin/activate

4- Installez les outils requis pour l'application.
pip install -r requirements.txt

5- Importez les tables dans le fichier de base de données.
sqlite3 db/violations.sqlite < db/db.sql

6- Exécutez le programme python qui importe les données du fichier CSV dans la base de données SQLite.
python3 import_violations.py

7- Démarrez l'application.
python3 app.py

8- Accédez à l'application web en ouvrant le lien suivant.
http://127.0.0.1:5000


Pour vérifier pycodestyle tout en ignorant les fichier de l'environnement virtuel venv:
pycodestyle . --exclude=venv

Pour réinitialiser le projet à son état initial (vider violations.sqlite et supprimer violations.csv):
python3 reinit_projet.py



Fonctionnalités choisies pour atteindre 100XP:
A1 (10 XP)
A2 (10 XP)
A3 (5 XP)
A4 (10 XP)
A5 (10 XP)
A6 (10 XP)
C1 (10 XP)
C2 (5 XP)
C3 (5 XP)
B1 (5 XP)
D1 (15 XP)
D2 (5 XP)


La description approfondie des fonctionnalités ainsi que les procédures pour
effectuer les tests pour chaque fonctionnalité sont expliqués dans le fichier
"correction.md".

PROCÉDURE POUR TESTER LES FONCTIONNALITÉS.
Toutes les fonctionnalités sont accompagnés d'un fichier dédié qui exécute les
test unitaires.

A2, A4, A5, A6, C1, C2, C3, D1 et D2 sont manuellement testables en consultant
l'application web ou en regardant la base de données SQLite avant et après le
test.

A1 est testable en exécutant le programme Python dédié. Si l'importation du
fichier CSV dans la base de données fonctionne, alors A1 est bien fonctionnelle.

A3 n'est manuellement testable qu'en modifiant directement la base de données
SQL, puisque l'application web n'a pas de fonction web dédié pour cette fin. 

B1 ne peut pas être testé manuellement, car un serveur SMTP est nécessaire. Du 
codage additionnel a été fait pour éviter un crash ou un cas inattendu dans le
cas où B1 doit être exécuté sans SMTP établi. Cette fonctionnalité n'est
vérifiable que par ses tests unitaires qui simulent un serveur SMTP.