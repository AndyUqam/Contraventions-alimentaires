# Correction – Projet INF5190

## A1 – Importation des données dans la base SQLite

### Description A1

Le script "import_violations.py" importe les données des contraventions dans la
 base de données SQLite (db/violations.sqlite).

- Si le fichier "violations.csv" est déjà présent dans le projet, il est
 utilisé directement.
- Sinon, le script télécharge automatiquement le fichier CSV depuis le site
 officiel et le sauvegarde localement.
- Les données sont insérées dans la table "violations"
(définie dans "db/db.sql").
- Pour exécuter le script d'importation, entrez la commande suivante dans le
terminal :

  ```bash
  python3 import_violations.py
  ```

### Test automatisé A1

```bash
python3 -m unittest tests/test_a1.py
```

- `test_get_csv_content_depuis_fichier_local` :  
vérifie que le script lit
 correctement un fichier CSV local existant.
- `test_get_csv_content_telechargement_si_absent` :  
vérifie que lors d'un fichier CSV local abscent, le script télécharge le
 contenu (simulé par un mock), crée le fichier local et retourne le bon contenu.
- `test_insert_violations_inserer_lignes_dans_sqlite` :  
vérifie que les lignes CSV sont bien insérées dans SQLite
 (2 lignes attendues, 2 lignes insérées).

### Test manuel A1

A1 est testable en exécutant script Python. Si l'importation du fichier CSV
 dans la base de données fonctionne, alors A1 est bien fonctionnel.

### Fichiers concernés A1

- `import_violations.py` : script d’importation de CSV à sqlite3
- `db/db.sql` : script de création des tables
- `db/violations.sqlite` : base de données (vide au départ)
- `violations.csv` : fichier csv de données
 (téléchargé automatiquement si non-présent)

---

## A2 – Application Flask : Recherche de contraventions

### Description A2

L’application permet de rechercher des contraventions dans la base de données
 selon trois critères :

- nom d’établissement
- propriétaire
- rue  

La page d’accueil contient uniquement le formulaire de recherche.  
L’utilisateur choisit un critère, saisit une chaîne dans le champ libre, puis
 lance la recherche.  
Les résultats s’affichent sur une nouvelle page dédiée (/resultats) dans un tableau
 qui présente toutes les informations disponibles sur chaque contravention.  
Il est possible qu’un même établissement apparaisse plusieurs fois s’il a reçu
 plusieurs sanctions.

### Test automatisé A2

```bash
python3 -m unittest tests/test_a2.py
```

- `test_page_accueil_se_charge` :  
vérifie que la page d’accueil répond correctement (code HTTP 200) et affiche le
 titre de recherche.
- `test_recherche_par_nom` :  
vérifie que la recherche par nom d’établissement retourne retourne le bon résultat.
- `test_recherche_par_proprietaire` :  
vérifie que la recherche par propriétaire retourne le bon résultat.
- `test_recherche_par_rue` :  
vérifie que la recherche par rue (adresse) retourne le bon résultat.
- `test_recherche_sans_resultat` :  
vérifie que la recherche sans correspondance affiche le message 
 « Aucun résultat trouvé ».

### Test manuel A2

Il suffit d'effectuer des recherches sur l'application web et de voir les résultats.
 Si les résultats dans le site web sont les mêmes que eux de la base de données
  SQLite en effectuant l'exacte même requête, alors A2 est bien fonctionnelle.

### Fichiers concernés A2

- `app.py` : application Flask
- `templates/index.html` : page d’accueil (formulaire de recherche)
- `templates/resultats.html` : page de résultats de recherche
- `static/style.css` : style du site

---

## A3 – Synchronisation quotidienne des données

### Description A3

L’application intègre un BackgroundScheduler qui exécute une synchronisation
 automatique des données chaque jour à minuit (fuseau horaire de Montreal).

- Une tâche planifiée appelle la fonction "synchroniser_donnees_quotidiennes".
- Cette fonction télécharge le fichier CSV officiel de la Ville de Montréal.
- La table "violations" est vidée, puis remplie à nouveau avec les données les plus récentes.

### Test automatisé A3

```bash
python3 -m unittest tests/test_a3.py
```

- `test_synchronisation_quotidienne_remplace_les_donnees` :  
vérifie que la synchronisation télécharge le CSV, remplace les données existantes
 dans la table "violations", puis insère les nouvelles données.
- `test_configurer_scheduler_planifie_minuit` :  
vérifie que le scheduler est configuré avec un déclencheur "cron" à minuit,
 donc 00:00 AM (heure de Montréal) et que la tâche de synchronisation est bien
 enregistrée.

### Test manuel A3

A3 n'est manuellement testable qu'en modifiant directement la base de données
 SQLite, puisque l'application web n'a pas de fonction web dédiée pour cette
 fin. Ajoutez une nouvelle contravention directement dans la base de données.
 Si cette contravention disparaît après l'appel de A3, alors la synchronisation
 a bien fonctionné.

### Fichiers concernés A3

- `app.py` : configuration du scheduler et fonction de synchronisation quotidienne
- `import_violations.py` : fonction d’insertion réutilisée pendant la synchronisation
- `tests/test_a3.py` : tests unitaires de la synchronisation et de la planification
- `requirements.txt` : dépendance "apscheduler"

---

## A4 – Service REST des contrevenants entre deux dates

### Description A4

Le système effectur un service REST qui retourne en JSON la liste des contraventions
 émises entre deux dates passées en paramètres.

- Route REST : /contrevenants?du=YYYY-MM-DD&au=YYYY-MM-DD
- Paramètres "du" et "au" sont obligatoires et validés au format ISO 8601 (YYYY-MM-DD).
- La page retournée affiche une liste de contraventions sous la structure JSON
 sans style html.
- Cas d'erreur 400 retourné: paramètres absents ou invalides, ou si du > au
 (date illogique).
- Données retournées en application/json.
- La route /doc affiche la représentation HTML du document RAML du service.

### Test automatisé A4

```bash
python3 -m unittest tests/test_a4.py
```

- `test_contrevenants_entre_deux_dates_retourne_json` :  
vérifie que la route /contrevenants retourne bien du JSON avec les données
 attendues pour une plage valide.
- `test_contrevenants_dates_invalides_retourne_400` :  
vérifie que des dates invalides retournent le code HTTP 400.
- `test_contrevenants_dates_mauvais_ordre_retourne_400` :  
vérifie que le code HTTP 400 est retourné lorsque la date de début (du) est
 après la date de fin (au).
- `test_doc_affiche_raml_en_html` :  
vérifie que la route /doc retourne la page HTML contenant le fichier RAML.

### Test manuel A4

Si-dessous sont des exemples de tests manuels. Comparez les résultats avec la
 même requête dans la base de données SQLite:
- Dates valides: [http://localhost:5000/contrevenants?du=2024-03-01&au=2024-03-31](http://localhost:5000/contrevenants?du=2024-03-01&au=2024-03-31)
- Dates invalides: [http://localhost:5000/contrevenants?du=2024-99-99&au=2024-03-31](http://localhost:5000/contrevenants?du=2024-99-99&au=2024-03-31)
- Ordre invalide (du > au): [http://localhost:5000/contrevenants?du=2024-03-31&au=2024-03-01](http://localhost:5000/contrevenants?du=2024-03-31&au=2024-03-01)
- Paramètre manquant: [http://localhost:5000/contrevenants?du=2024-03-01](http://localhost:5000/contrevenants?du=2024-03-01)
- Consultation du document RAML: [http://localhost:5000/doc](http://localhost:5000/doc)

### Fichiers concernés A4

- `app.py` : implémentation des routes "/contrevenants" et /doc
- `api.raml` : document RAML du service REST
- `tests/test_a4.py` : tests unitaires de la route REST et de la documentation

---

## A5 – Recherche rapide Ajax sur la page d’accueil

### Description A5

La page d’accueil contient un formulaire de recherche rapide avec deux dates
 (du, au).  
À la soumission du formulaire, une requête Ajax est envoyée à la route utilisée pour A4:  
/contrevenants?du=YYYY-MM-DD&au=YYYY-MM-DD.

Après la réponse JSON, l’application regroupe les résultats par établissement et
affiche un tableau avec deux colonnes :

- nom de l’établissement
- nombre de contraventions obtenues pendant la période

Lors d'erreurs (dates invalides ou manquantes), un message d'erreur apparaîtra.  
Pour faire disparaître le tableau des résultats ou le message d'erreur, il
 suffit de rafraichir la page.  
Cette fonctionnalité utilise le code la route pour A4. La logique du
 formulaire, de l'ajax et du tableau est faite en html.

### Test automatisé A5

```bash
python3 -m unittest tests/test_a5.py
```

- `test_page_accueil_contient_formulaire_recherche_rapide` :  
vérifie que la page d’accueil contient les éléments A5 (formulaire rapide,
 champs de date, appel Ajax vers "/contrevenants", et en-tête "Nombre de
 contraventions").

### Test manuel A5

Sur l'application web, essayez la recherche rapide avec des dates rapprochés
 pour un résultat rapide.  
 Ensuite, comparez les résultats avec ceux de la base de données SQLite en
 effectuant une requête identique. Les résultats doivent être la même.

### Fichiers concernés A5

- `templates/index.html` :  
formulaire rapide, script Ajax, affichage du tableau des résultats
- `static/style.css` :  
CSS des formulaires et de la zone des résultats
- `tests/test_a5.py` :  
test unitaire de présence des éléments A5 sur la page d’accueil

---

## A6 – Recherche Ajax par nom de restaurant

### Description A6

La page d'accueil contient un mode de recherche par nom de restaurant avec
 liste déroulante.  
La liste est chargée en Ajax depuis un service REST, et son codage est séparé de A5.
Puis l'utilisateur choisit un restaurant pour voir la liste de toutes les
 infractions venant du restaurant choisi.  
La liste contient les colonnes date, description, adresse, montant et statut.

### Routes REST ajoutées

- `/restaurants` : retourne la liste distincte des établissements disponibles
- `/infractions-restaurant?restaurant=Nom` : retourne les infractions du restaurant choisi

### Test automatisé A6

```bash
python3 -m unittest tests/test_a6.py
```

- `test_restaurants_retourne_liste_distincte` :  
vérifie que "/restaurants" retourne la liste JSON des restaurants sans doublons.
- `test_infractions_restaurant_sans_parametre_retourne_400` :  
vérifie que l’absence du paramètre "restaurant" retourne HTTP 400.
- `test_infractions_restaurant_retourne_details` :  
vérifie que "/infractions-restaurant" retourne les infractions du restaurant
 demandé avec les bonnes colonnes.

### Test manuel A6

Vérifiez si tous les établissements apparaîssent bien dans la liste déroulante
 en effectuant la même requête dans la base de données SQLite et en comparant
 les résultats.

### Fichiers concernés A6

- `app.py` : routes REST A6 ("/restaurants", "/infractions-restaurant")
- `templates/index.html` : formulaire A6, chargement Ajax de la liste et
 affichage des infractions
- `tests/test_a6.py` : tests unitaires des routes REST A6

---

## C1 – Service REST des établissements avec nombre d'infractions

### Description C1

Le système présente un service REST qui retourne la liste en JSON des
 établissements ayant commis une ou plusieurs infractions.

- Route REST pour consulter la liste : "/etablissements-infractions".
- Nombre d'infraction connus donné pour chaque établissement, liste trié en
 ordre décroissant de nb d'infraction.
 puis en ordre alphabétique de nom d'établissement, format JSON
- Documentation RAML consultable via "/doc".

### Test automatisé C1

```bash
python3 -m unittest tests/test_c1.py
```

- `test_etablissements_infractions_retourne_compte_trie` :  
vérifie que le service retourne les établissements avec leur nombre
 d'infractions, dans l'ordre décroissant.

### Test manuel C1

Lien vers C1: [http://localhost:5000/etablissements-infractions](http://localhost:5000/etablissements-infractions)  
Comparez les données de la réponse JSON avec les résultats de la base de
 données après avoir exécuté la même requête SQL.

### Fichiers concernés C1

- `app.py` : route REST "/etablissements-infractions"
- `api.raml` : documentation RAML pour la fonctionnalité C1
- `tests/test_c1.py` : test unitaire du service REST de C1

---

## C2 – Service REST C1 en format XML UTF-8

### Description C2

Ce service est le même que C1 (établissement + nombre d'infractions), mais en
 format XML.

- Route REST : "/etablissements-infractions/xml".
- Données identiques à C1, triées en ordre décroissant du nombre d'infractions.
- Réponse XML encodée en UTF-8.
- Documentation RAML consultable via "/doc".

### Test automatisé C2

```bash
python3 -m unittest tests/test_c2.py
```

- `test_etablissements_infractions_xml_utf8_et_trie` :  
vérifie que la route C2 retourne du XML, avec charset UTF-8 et un ordre
 décroissant correct.

### Test manuel C2

Lien vers C2: [http://localhost:5000/etablissements-infractions/xml](http://localhost:5000/etablissements-infractions/xml)  
Meme test manuel qu'avec C1

### Fichiers concernés C2

- `app.py` : route REST XML "/etablissements-infractions/xml"
- `api.raml` : documentation RAML de C2
- `tests/test_c2.py` : test unitaire du service REST XML C2

---

## C3 – Service REST C1 en format CSV UTF-8

### Description C3

Ceci est le même principe que C1 et C2, à l'exception que ce service télécharge
 la liste en format CSV (consultable par Excel).

- Route REST : "/etablissements-infractions/csv".
- Données identiques à C1/C2, triées en ordre décroissant du nombre d'infractions.
- Réponse CSV encodée en UTF-8, avec en-tête "etablissement,nombre_infractions".
- Documentation RAML consultable via "/doc".

### Test automatisé C3

```bash
python3 -m unittest tests/test_c3.py
```

- `test_etablissements_infractions_csv_utf8_et_trie` :  
vérifie que la route C3 retourne du CSV, avec charset UTF-8, et un ordre
 décroissant correct.

### Test manuel C3

Lien vers C3: [http://localhost:5000/etablissements-infractions/csv](http://localhost:5000/etablissements-infractions/csv)  
Même test manuel qu'avec C1 et C2

### Fichiers concernés C3

- `app.py` : route REST CSV "/etablissements-infractions/csv"
- `api.raml` : documentation RAML de C3
- `tests/test_c3.py` : test unitaire du service REST CSV C3

---

## B1 – Détection des nouvelles contraventions et envoi par courriel

### Description B1

Le système détecte les nouvelles contraventions entre deux importations et
 envoie un courriel avec la liste sans doublon.

- La détection compare les "id_poursuite" du nouveau CSV avec ceux
 actuellement dans la base SQLite.
- Les nouvelles contraventions, donc la différence, sont considérées
 pour l'envoi.
- Les doublons sont ignorés.
- L'adresse du destinataire, qui recevra la nouvelle liste, est lue dans le
 fichier YAML "b1.yaml".
- L'appel au code pour cette fonctionnalité est intégrée dans la fonction
 synchroniser_donnees_quotidiennes() utiisée pour A3.
 Donc, le courriel est envoyé automatiquement pendant l'importation des données.
- B1 a son propre fichier de code de fonction: b1_utils.py
- NOTE IMPORTANTE:  
 Cette application ne fournit pas de serveur SMTP, l'envoi ne peut pas être
 validé manuellement.  
 Cette fonctionnalité est seulement vérifiable par les tests unitaires qui
 simulent un serveur SMTP.

### Test automatisé B1

```bash
python3 -m unittest tests/test_b1.py
```

- `test_detecter_nouvelles_contraventions_dedoublonne` :  
vérifie que les nouvelles contraventions sont détectées et dédoublonnées.
- `test_envoyer_courriel_utilise_yaml` :  
vérifie que le courriel utilise l'adresse lue dans le fichier YAML.

### Test manuel B1

B1 ne peut pas être testé manuellement, car un serveur SMTP est nécessaire.  
Du codage additionnel a été fait pour éviter un crash ou un cas inattendu dans
 le cas où B1 doit être exécuté sans SMTP établi.  
Cette fonctionnalité est vérifiable que par ses tests unitaires qui simulent
 un serveur SMTP.

### Fichiers concernés B1

- `b1_utils.py` :  logique de détection et d'envoi des nouvelles contraventions
- `import_violations.py` : appel de B1 pendant l'importation
- `app.py` : appel de B1 pendant la synchronisation quotidienne de A3
- `b1.yaml` : fichier de configuration YAML qui contient l'adresse courriel du destinataire
- `tests/test_b1.py` : tests unitaires de B1

---

## D1 – Création d'une demande d'inspection (REST + page de plainte)

### Description D1

Il est possible de créer une demande d'inspection à la ville. Le document JSON
 est validé avec "json-schema" avant l'insertion dans la base de données.

- Route REST : "/demandes-inspection" (POST)
- Champs requis : nom de l'établissement, adresse, ville, date de visite, nom
 et prénom du client, description du problème.
- Validation: schéma JSON + validation du format de date ISO 8601.
- En cas de succès, la demande est enregistrée dans la table
 "demandes_inspection" et un code 201 est retourné.
- La table "demandes_inspection" est automatiquement créée par db.sql
- Code 400 retourné si date plus loin que la date d'aujourd'hui ou erreur
 quelconque de validation.

Une page dédiée pour la rédaction de demande d'inspection est disponible:

- Route page : "/plainte"
- Formulaire HTML + envoi JavaScript (Ajax/fetch) vers "/demandes-inspection".
- L'hyperlien pour acccéder à cette page est disponible à la page d'accueil.

### Documentation RAML

- Le service D1 est documenté dans "api.raml" et visible sur "/doc".

### Test automatisé D1

```bash
python3 -m unittest tests/test_d1.py
```

- `test_creer_demande_inspection_valide` :  
vérifie la création REST avec code 201 et insertion en base.
- `test_creer_demande_inspection_invalide_retourne_400` :  
vérifie qu'une demande invalide retourne 400.
- `test_creer_demande_inspection_date_future_retourne_400` :  
vérifie qu'une date de visite dans le futur retourne 400.
- `test_page_plainte_contient_formulaire_ajax` :  
vérifie la présence du formulaire et de l appel Ajax sur la page "/plainte".

### Test manuel D1

À la page de demande d'inspection, créez une demande d'inspection. Ensuite,
 vérifiez l'existence de cette demande dans la base de données SQLite.

### Fichiers concernés D1

- `app.py` : route page "/plainte" + route REST "/demandes-inspection"
- `templates/plainte.html` : page de plainte avec formulaire Ajax
- `templates/index.html` : lien vers la page de plainte
- `static/style.css` : styles de la page de plainte
- `db/db.sql` : ajout de la table "demandes_inspection" à la base de données
- `api.raml` : documentation RAML du service D1
- `tests/test_d1.py` : tests unitaires D1
- `requirements.txt` : ajout de la dépendance "jsonschema"

---

## D2 – Suppression d'une demande d'inspection (REST)

### Description D2

Il est possible de supprimer une demande d'inspection à la ville à partir de
 son identifiant.

- Route REST : "/demandes-inspection/{id}" (DELETE)
- En cas de succès, la demande est supprimée de la table "demandes_inspection"
 et un code 200 est retourné.
- En cas d'id introuvable, un code 404 est retourné.
- Le service est documenté dans "api.raml" qui est visible sur "/doc".

### Test automatisé D2

```bash
python3 -m unittest tests/test_d2.py
```

- `test_supprimer_demande_inspection_reussit` :  
vérifie la suppression d'une demande existante et la disparition de la ligne 
dans la base de données SQLite.
- `test_supprimer_demande_inspection_introuvable_retourne_404` :  
vérifie qu'une demande inexistante retourne 404.

### Test manuel D2

Assurez-vous d'avoir une demande d'inspection existante dans la base de données
 SQLite et que l'application est bien démarée.  
Ouvrez un autre terminal, car le 1er terminal doit garder l'application démarrée
 en tout temps.
Dans le nouveau terminal, entrez la commande suivante dont ID = l'id de la
 demande d'inspection à supprimer.

```bash
curl -X DELETE http://localhost:5000/demandes-inspection/ID
```

Pour tester un cas invalide (id inexistante), entrez un id inexistant (Ex: 99999).

```bash
curl -X DELETE http://localhost:5000/demandes-inspection/99999
```

### Fichiers concernés D2

- `app.py` : route REST DELETE "/demandes-inspection/{id}"
- `api.raml` : documentation RAML du service D2
- `tests/test_d2.py` : tests unitaires D2
