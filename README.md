# logistique-bobo

Documentation technique
Automatisation de traitement de PDF de rapports d’arrivage
n8n – API FastAPI (Render) – Google Drive – Google Sheets
1. Objectif du système

Le système a pour objectif d’automatiser entièrement le traitement de rapports PDF reçus par email afin de :

centraliser les PDF sur Google Drive

extraire automatiquement les données métiers contenues dans ces documents

identifier et structurer les anomalies logistiques

alimenter automatiquement plusieurs Google Sheets selon des règles de filtrage

fonctionner sans intervention humaine, malgré les contraintes du plan gratuit Render

2. Architecture générale

Le système repose sur quatre briques principales :

n8n
Orchestre l’ensemble du processus (email, fichiers, API, filtrage, export)

API FastAPI
Effectue l’extraction et la structuration des données contenues dans les PDF

Render (plan gratuit)
Hébergement de l’API avec déploiement automatique depuis GitHub

Google Drive et Google Sheets
Stockage des fichiers et restitution des données structurées

3. API d’extraction PDF (FastAPI)
3.1 Rôle de l’API

L’API est responsable de :

la lecture complète du fichier PDF

l’extraction du texte brut

la normalisation du contenu textuel

l’identification des informations métier

la restitution d’un JSON structuré

Elle ne contient aucune logique métier liée à n8n ou au routage des données.

3.2 Code et fonctionnement

L’API est développée avec FastAPI et PyPDF2.

Endpoints exposés :

GET /
Endpoint de test et de wake-up
Utilisé uniquement pour maintenir l’API active

POST /extract-json
Endpoint métier
Reçoit un fichier PDF et retourne les données extraites

Principales étapes du traitement

Lecture du fichier PDF via UploadFile

Extraction du texte pour chaque page

Normalisation des espaces

Extraction de la date du document

Détection de tous les codes d’anomalies

Pour chaque anomalie :

récupération du numéro de commande (DO)

type d’anomalie

code anomalie

expéditeur

bordereau

V.I.R

EAN

3.3 Structure de la réponse API
{
  "resultats": [
    {
      "date": "...",
      "commande_do": "...",
      "code": "...",
      "anomalie": "...",
      "expediteur": "...",
      "bordereau": "...",
      "vir": "...",
      "ean": "..."
    }
  ]
}


Chaque PDF peut produire plusieurs entrées selon le nombre d’anomalies détectées.

4. Hébergement et déploiement API (Render + GitHub)

Le code est versionné sur GitHub

Render est connecté au dépôt GitHub

Chaque mise à jour du code déclenche un redéploiement automatique

Contrainte clé du plan gratuit Render

Mise en veille automatique après environ 15 minutes d’inactivité

Premier appel HTTP après veille lent ou en échec

Nécessite une gestion active du réveil

5. Gestion du sommeil automatique de l’API (Wake-up)

Deux solutions complémentaires ont été mises en place.

5.1 Wake-up intégré au scénario métier

Au démarrage du scénario principal :

Appel HTTP GET vers /

Node Wait (quelques secondes)

Appel HTTP POST réel vers /extract-json

Ces paramètres sont utilisés :

timeout élevé (60000 ms)

Always Output Data activé

Stop workflow désactivé

Cette solution garantit que le scénario métier peut fonctionner même si l’API était endormie.

5.2 Scénario n8n dédié au wake-up (solution principale)

Un scénario indépendant est configuré avec :

déclencheur Cron toutes les 5 minutes

appel HTTP GET vers / de l’API

timeout à 60000 ms

Always Output Data activé

aucun retry

Ce scénario empêche Render de placer l’API en veille et découple complètement l’infrastructure de la logique métier.

6. Scénario n8n principal – Traitement métier
6.1 Déclencheur

Gmail Trigger

Déclenché à la réception d’un email contenant un ou plusieurs PDF

6.2 Gestion des fichiers PDF

Les pièces jointes arrivent sous forme de binaires :

attachment_0

attachment_1

attachment_2

Chaque branche du scénario correspond à un PDF potentiel maximum attendu.

6.3 Stockage des fichiers

Pour chaque PDF :

Upload du fichier sur Google Drive

Download immédiat depuis Google Drive (standardisation du binaire)

Envoi du fichier à l’API via HTTP POST

Cette étape assure la traçabilité et l’archivage des documents originaux.

6.4 Appel API d’extraction

Méthode POST vers /extract-json

Envoi du PDF en multipart/form-data

Timeout métier réduit (10 à 15 secondes)

Réception du JSON structuré

6.5 Split Out des résultats

Le champ resultats est un tableau.

Le node Split Out permet de :

créer un item n8n par anomalie détectée

traiter chaque anomalie indépendamment

Cela permet un routage fin vers différents exports.

6.6 Filtrage et routage

Plusieurs nodes Filter sont utilisés pour :

séparer les anomalies selon leur type

router les données vers différentes feuilles Google Sheets

conserver une logique claire et lisible

Chaque filtre correspond à une règle métier explicite.

6.7 Export vers Google Sheets

Append Row dans des fichiers Google Sheets dédiés

Une ligne par anomalie

Les colonnes correspondent directement aux champs du JSON API

7. Choix techniques et justification

Séparation stricte entre extraction et orchestration

Compensation logicielle des limites du plan gratuit Render

Gestion explicite des PDF multiples

Scénarios lisibles même s’ils sont volontairement verbeux

Robustesse priorisée sur l’élégance théorique

8. Évolutions possibles

Passage à un plan Render payant

Réduction du nombre de branches via une logique multi-items

Centralisation des exports Sheet

Ajout de monitoring (logs, alertes)

Dockerisation complète hors Render

9. Conclusion

Le système mis en place permet de transformer un flux non structuré (emails + PDF) en données exploitables, de manière fiable, automatisée et maintenable, tout en tenant compte des contraintes réelles de l’infrastructure utilisée.
