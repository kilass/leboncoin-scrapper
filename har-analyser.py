import json
from haralyzer import HarParser
import csv
import base64
import gzip
import zlib
import brotli

# Charger le fichier HAR depuis le disque
har_file_path = "www.leboncoin.fr.har"  # Remplace par le chemin réel de ton fichier HAR
with open(har_file_path, "r", encoding="utf-8") as f:
    har_data = json.load(f)

# Initialiser HarParser avec le dictionnaire
har_parser = HarParser(har_data)
ads_data = []

# Champs principaux à garder
wanted_fields = [
    "list_id", "first_publication_date", "index_date", "status", "category_id",
    "category_name", "subject", "body", "url", "price", "price_cents", "old_price",
    "images", "location", "owner", "has_phone", "options"
]

# Champs à extraire de "attributes"
attribute_fields = {
    "condition": "condition",
    "shipping_type": "shipping_type",
    "shippable": "shippable",
    "estimated_parcel_weight": "estimated_parcel_weight",
    "rating_score": "rating_score",
    "rating_count": "rating_count"
}

# Fonction pour tenter de décompresser une réponse
def decompress_response(text, encoding):
    if not text:
        return None
    if text.strip().startswith(("{", "[")):
        return text
    try:
        if encoding == "gzip":
            return gzip.decompress(text.encode()).decode("utf-8")
        elif encoding == "deflate":
            return zlib.decompress(text.encode()).decode("utf-8")
        elif encoding == "br":
            return brotli.decompress(text.encode()).decode("utf-8")
        else:
            return text
    except Exception as e:
        print(f"Erreur de décompression ({encoding}) : {e}")
        return text

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
            response_text = entry.response.text

            if not response_text:
                print(f"Réponse vide pour {entry.request.url}")
                with open("erreurs.log", "a", encoding="utf-8") as log_file:
                    log_file.write(f"Réponse vide : {entry.request.url}\n")
                continue

            content_encoding = None
            for header in entry.response.headers:
                if header["name"].lower() == "content-encoding":
                    content_encoding = header["value"].lower()
                    break

            if content_encoding:
                response_text = decompress_response(response_text, content_encoding)

            is_base64 = is_base64_like(response_text)
            if is_base64:
                try:
                    print(f"Décodage base64 pour {entry.request.url}")
                    decoded_bytes = base64.b64decode(response_text)
                    response_text = decoded_bytes.decode("utf-8")
                except Exception as e:
                    print(f"Erreur de décodage base64 pour {entry.request.url} : {e}")
                    with open("erreurs.log", "a", encoding="utf-8") as log_file:
                        log_file.write(f"URL: {entry.request.url}\nRéponse brute: {response_text}\nErreur: {e}\n\n")
                    continue

            try:
                response_json = json.loads(response_text)
                if "ads" in response_json:
                    filtered_ads = []
                    for ad in response_json["ads"]:
                        # Filtrer les champs principaux
                        filtered_ad = {key: ad[key] for key in wanted_fields if key in ad}

                        # Extraire les champs spécifiques de "attributes"
                        if "attributes" in ad:
                            for attr in ad["attributes"]:
                                key = attr.get("key")
                                if key in attribute_fields:
                                    filtered_ad[attribute_fields[key]] = attr.get("value")

                        filtered_ads.append(filtered_ad)
                    print(f"Requêtes trouvée avec 'ads' : {entry.request.url}, {len(filtered_ads)} annonces")
                    ads_data.extend(filtered_ads)
                else:
                    print(f"Requêtes ignorée (pas de 'ads') : {entry.request.url}")
            except json.JSONDecodeError as e:
                print(f"Erreur de décodage JSON pour {entry.request.url} : {e}")
                with open("erreurs.log", "a", encoding="utf-8") as log_file:
                    log_file.write(f"URL: {entry.request.url}\nRéponse brute: {response_text}\nErreur: {e}\n\n")
                continue

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
else:
    print("Aucune annonce trouvée avec 'ads' dans le HAR.")