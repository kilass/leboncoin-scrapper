
# Leboncoin Scrapper

  

## But du projet

  

Le projet **Leboncoin Scrapper** vise à automatiser l’extraction et l’analyse des annonces publiées sur Leboncoin, avec un focus particulier sur les imprimantes 3D. L’objectif est de scraper les données brutes (titre, description, prix, images, etc.), de les enrichir avec des informations spécifiques (modèle exact, catégorie, cohérence des images) en utilisant un modèle de langage multimodal (Ollama), et de produire une base de données structurée pour une analyse ultérieure (ex. prix moyen par modèle, filtrage des annonces pertinentes). Ce projet est conçu pour être modulaire, robuste et extensible à d’autres catégories ou analyses.

  

---

  

## Étapes de téléchargement et d’installation

  

### Prérequis

-  **Système d’exploitation** : Windows, Linux ou macOS.

-  **Python** : Version 3.8 ou supérieure.

-  **Ollama** : Serveur local pour exécuter le modèle `llama3.2-vision:latest`.

-  **Dépendances Python** : Listées dans `requirements.txt` (à créer si besoin).

  

### Téléchargement

1.  **Cloner le dépôt** :

```bash
git clone https://github.com/kilass/leboncoin-scrapper.git
cd leboncoin-scrapper
```
2.  **Télécharger Ollama** :

```bash
git clone https://github.com/kilass/leboncoin-scrapper.git
cd leboncoin-scrapper
```
2.  **Télécharger Ollama** :
Rendez-vous sur [le site officiel d’Ollama](https://ollama.ai/) et suivez les instructions pour installer Ollama sur votre système.
-   Assurez-vous que le modèle llama3.2-vision:latest est téléchargé :
    
    ```bash
    ollama pull llama3.2-vision:latest
    ```
### Installation

1.  **Créer un environnement virtuel** :
```bash
python -m venv venv 
source venv/bin/activate # Linux/macOS
venv\Scripts\activate # Windows
```
    
2.  **Installer les dépendances** :
    -   Créez un fichier requirements.txt avec :
```text
ollama
```
Puis exécutez :
```bash
pip install -r requirements.txt
```        
3.  **Démarrer le serveur Ollama** :
Dans un terminal séparé, lancez le serveur Ollama :
``` bash
ollama run llama3.2-vision:latest
```
Vérifiez qu’il est accessible sur http://localhost:11434.

5.  **Vérifier les fichiers** :
Assurez-vous que annonces_leboncoin.json (données brutes) est présent dans le répertoire principal. Sinon, utilisez un script de scraping (non fourni ici) pour le générer.

### Utilisation
-   **Collecte des données initiales** :
Pour le moment la collecte des données se fait de manière manuelle, à cause du blocage anti-bot de leboncoin. 

La méthode employée pour générer un fichier .har d'entrée avec les annonces a analyser est telle que : 
1. **ouvrir le site leboncoin.fr** et lancer une recherche souhaitée (ex: imprimante 3D) :
2.   **Ouvrir les outils de développement** : F12
3. **Filtrer les requêtes** : ouvrir l'onglet network, cocher uniquement les fichiers de type fetch / XHR, appliquer le filtre "finder/search" , activer le record network (CTRL + E) recharger la page (F5) pour capturer toutes les requêtes réseau
4. **Exporter en fichier HAR** : Naviguer dans toutes les pages d'annonce (attention, la page 1 devra être revisitée). Une fois l'ensemble des pages a extraire visitées, stopper le record ( CTRL + E) et exporter le HAR
5. **Utilisation du fichier HAR** : Placer le fichier HAR dans le projet cloné a la racine et nommez le "www.leboncoin.fr.har", ou ajustez la  ligne 10 de har-analyzer.py
-   **Lancer le script de scraping** :
``` bash
python har-analyzer.py
```
Sortie : annonces_leboncoin.json avec les données brutes.

-   **Lancer le script de raffinement** :
``` bash
python refine_with_ollama.py --limit 5
```
  -   --limit : Optionnel, limite le nombre d’annonces à traiter (ex. 5 pour tester).
    -   Sortie : annonces_refined.json avec les données enrichies.
-   **Exemple de sortie** : Le fichier annonces_refined.json contient les annonces originales plus les champs item_model, item_category, et image_coherence.

## Roadmap

Le projet est organisé en 7 étapes. Voici l’état actuel au 19 mars 2025 :

1.  **Scraping initial des données Leboncoin**
    -   **Description** : Récupérer les annonces brutes depuis Leboncoin et les stocker dans annonces_leboncoin.json.
    -   **Statut** : **Terminé**
        -   Les données brutes sont déjà disponibles dans le fichier JSON fourni.
2.  **Extraction du modèle exact avec Ollama**
    -   **Description** : Utiliser un LLM pour identifier le modèle exact des objets (ex. imprimantes 3D) à partir du texte.
    -   **Statut** : **Terminé**
        -   Le script refine_with_ollama.py extrait correctement item_model (ex. "Creality Ender 3 V2 Neo").
3.  **Raffinement avec LLM (catégorie et cohérence image)**
    -   **Description** : Ajouter la catégorie (item_category) et vérifier la cohérence des images (image_coherence) avec un modèle multimodal.
    -   **Statut** : **Terminé**
        -   Le script extrait ces champs de manière robuste, avec écriture incrémentale dans annonces_refined.json. Les caractères indésirables sont nettoyés, et les champs originaux sont conservés.
4.  **Filtrage des annonces pertinentes**
    -   **Description** : Filtrer les annonces pour ne garder que celles liées aux imprimantes 3D (exclure filaments, accessoires seuls, etc.) ou marquer les incohérences.
    -   **Statut** : **Non commencé**
        -   Prochaine étape à implémenter.
5.  **Validation manuelle ou automatique des résultats**
    -   **Description** : Vérifier un échantillon des résultats pour s’assurer de leur exactitude, ou implémenter une validation automatique.
    -   **Statut** : **Non commencé**
        -   À planifier après le filtrage.
6.  **Analyse statistique ou enrichissement**
    -   **Description** : Ajouter des analyses (ex. prix moyen par modèle) ou enrichir les données (ex. recherches web pour confirmer les modèles).
    -   **Statut** : **Non commencé**
        -   Optionnel, selon les besoins futurs.
7.  **Export final et utilisation**
    -   **Description** : Produire un JSON final propre pour une utilisation ultérieure (ex. base de données, visualisation).
    -   **Statut** : **Non commencé**
        -   Dépend des étapes précédentes.

### État actuel

-   **Étape actuelle** : Étape 3 (terminée).
-   **Progrès** : 3/7 étapes validées.
-   **Prochaine étape** : Étape 4 (filtrage des annonces pertinentes).

## Contribution

-   Pour contribuer, fork le dépôt, créez une branche, et soumettez une pull request avec vos modifications.
-   Signalez les bugs ou suggestions dans la section [Issues](https://github.com/kilass/leboncoin-scrapper/issues).

## Licence

-   À définir (ex. MIT, GPL). Pour l’instant, usage personnel uniquement.