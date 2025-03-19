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
else:
    print("Aucune annonce trouvée avec 'ads' dans le HAR.")