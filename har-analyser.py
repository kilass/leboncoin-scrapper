import json
from haralyzer import HarParser
import csv
import base64
import gzip
import zlib
import brotli

# Charger le fichier HAR depuis le disque
har_file_path = "www.leboncoin.fr_Archive [25-03-20 18-27-00].har"  # Remplace par le chemin réel de ton fichier HAR
with open(har_file_path, "r", encoding="utf-8") as f:
    har_data = json.load(f)

# Initialiser HarParser avec le dictionnaire
har_parser = HarParser(har_data)

# Utiliser un dictionnaire pour stocker les annonces par list_id (évite les doublons)
ads_dict = {}
total_found = 0  # Compteur pour le nombre total d'annonces trouvées

# Fonction pour tenter de décompresser une réponse
def decompress_response(text, encoding):
    if not text:
        return None
    if text.strip().startswith(("{", "[")):
        return text
    try:
        # Si c’est du base64, décoder d’abord
        if is_base64_like(text):
            text = base64.b64decode(text)
        else:
            text = text.encode("utf-8")  # Sinon, encoder en bytes
        if encoding == "gzip":
            return gzip.decompress(text).decode("utf-8")
        elif encoding == "deflate":
            return zlib.decompress(text).decode("utf-8")
        elif encoding == "br":
            return brotli.decompress(text).decode("utf-8")
        else:
            return text.decode("utf-8") if isinstance(text, bytes) else text
    except Exception as e:
        print(f"Erreur de décompression ({encoding}) : {e}")
        return None

# Fonction pour vérifier si une chaîne ressemble à du base64
def is_base64_like(text):
    try:
        decoded = base64.b64decode(text)
        return len(decoded) > 0 and len(text) % 4 == 0
    except Exception:
        return False

# Parcourir les pages et entrées
for page in har_parser.pages:
    for entry in page.entries:
        if "finder/search" in entry.request.url:
            print(f"Analyse de {entry.request.url}")
            
            # Récupérer directement le contenu brut
            content = entry.response.raw_entry.get("content", {})
            if "text" not in content or not content["text"]:
                print(f"Réponse vide ou sans texte pour {entry.request.url}")
                with open("erreurs.log", "a", encoding="utf-8") as log_file:
                    log_file.write(f"Réponse vide ou sans texte : {entry.request.url}\n")
                continue

            response_text = content["text"]

            # Vérifier l'encodage dans les headers
            content_encoding = None
            for header in entry.response.headers:
                if header["name"].lower() == "content-encoding":
                    content_encoding = header["value"].lower()
                    break

            # Décompresser si nécessaire
            if content_encoding or is_base64_like(response_text):
                response_text = decompress_response(response_text, content_encoding)
                if response_text is None:
                    print(f"Échec de décompression pour {entry.request.url}")
                    with open("erreurs.log", "a", encoding="utf-8") as log_file:
                        log_file.write(f"Échec de décompression ({content_encoding}) : {entry.request.url}\n")
                    continue
                if is_base64_like(response_text):  # Double vérification après première tentative
                    try:
                        print(f"Décodage base64 supplémentaire pour {entry.request.url}")
                        response_text = base64.b64decode(response_text).decode("utf-8")
                    except Exception as e:
                        print(f"Erreur de décodage base64 pour {entry.request.url} : {e}")
                        with open("erreurs.log", "a", encoding="utf-8") as log_file:
                            log_file.write(f"URL: {entry.request.url}\nRéponse brute: {response_text}\nErreur: {e}\n\n")
                        continue

            try:
                response_json = json.loads(response_text)
                if "ads" in response_json:
                    total_found += len(response_json["ads"])  # Ajouter au total brut
                    for ad in response_json["ads"]:
                        list_id = ad.get("list_id")
                        if list_id and list_id not in ads_dict:
                            # Ajouter l'annonce au dictionnaire si elle n'existe pas encore
                            ads_dict[list_id] = ad
                    print(f"Requêtes trouvée avec 'ads' : {entry.request.url}, {len(response_json['ads'])} annonces (total unique : {len(ads_dict)})")
                else:
                    print(f"Requêtes ignorée (pas de 'ads') : {entry.request.url}")
            except json.JSONDecodeError as e:
                print(f"Erreur de décodage JSON pour {entry.request.url} : {e}")
                with open("erreurs.log", "a", encoding="utf-8") as log_file:
                    log_file.write(f"URL: {entry.request.url}\nRéponse brute: {response_text}\nErreur: {e}\n\n")
                continue

# Convertir le dictionnaire en liste pour l'export
ads_data = list(ads_dict.values())

# Récapitulatif final
print(f"{total_found} annonces trouvées, total uniques : {len(ads_data)}")

# Exporter en JSON
if ads_data:
    with open("annonces_leboncoin.json", "w", encoding="utf-8") as f:
        json.dump(ads_data, f, ensure_ascii=False, indent=2)
    print("Données exportées en JSON : annonces_leboncoin.json")

    # Collecter tous les champs pour le CSV
    all_fields = set()
    for ad in ads_data:
        all_fields.update(ad.keys())
    headers = list(all_fields)

    # Exporter en CSV
    with open("annonces_leboncoin.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(ads_data)
    print("Données exportées en CSV : annonces_leboncoin.csv")

    # Extraire les catégories pour category_mapping.json
    categories = {}
    for ad in ads_data:
        cat_id = ad.get("category_id")
        cat_name = ad.get("category_name")
        if cat_id and cat_name and cat_id not in categories:
            categories[cat_id] = {
                "id": cat_id,
                "name": cat_name,
                "typical_items": [],
                "description": ""
            }

    category_mapping = {"categories": list(categories.values())}
    with open("category_mapping.json", "w", encoding="utf-8") as f:
        json.dump(category_mapping, f, ensure_ascii=False, indent=4)
    print("Mapping des catégories exporté dans category_mapping.json")
else:
    print("Aucune annonce trouvée avec 'ads' dans le HAR.")