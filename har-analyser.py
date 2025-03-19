import json
import csv
from haralyzer import HarParser

# Chemins des fichiers
har_file_path = "www.leboncoin.fr.har"
output_csv = "annonces_leboncoin.csv"
output_json = "annonces_leboncoin.json"

# Charger le fichier HAR
with open(har_file_path, 'r', encoding='utf-8') as f:
    har_parser = HarParser(json.load(f))

# Liste pour stocker les données des annonces
annonces = []
request_count = 0  # Compteur pour suivre les requêtes

# Parcourir toutes les entrées du fichier HAR
for page in har_parser.pages:
    for entry in page.entries:
        request_count += 1
        try:
            # Extraire response.content.text
            response_content = entry.response['content'].get('text', '')
            if response_content:
                # Parser le JSON
                data = json.loads(response_content)
                if isinstance(data, dict) and 'ads' in data:
                    print(f"Requête {request_count} ({entry.request['url']}) contient 'ads'.")
                    # Extraire les annonces de la clé "ads"
                    for ad in data['ads']:
                        attributes = {attr['key']: attr['value_label'] for attr in ad.get('attributes', [])}
                        annonce = {
                            'page_id': page.page_id,  # Corrigé ici
                            'page_url': page.title,   # Corrigé ici
                            'request_url': entry.request['url'],
                            'request_number': request_count,
                            'list_id': ad.get('list_id', ''),
                            'first_publication_date': ad.get('first_publication_date', ''),
                            'index_date': ad.get('index_date', ''),
                            'status': ad.get('status', ''),
                            'category_id': ad.get('category_id', ''),
                            'category_name': ad.get('category_name', ''),
                            'subject': ad.get('subject', ''),
                            'body': ad.get('body', ''),
                            'price': ad.get('price', [0])[0] if ad.get('price') else 0,
                            'price_cents': ad.get('price_cents', 0),
                            'url': ad.get('url', ''),
                            'image_url': ad.get('images', {}).get('urls', [''])[0],
                            'city': ad.get('location', {}).get('city', ''),
                            'zipcode': ad.get('location', {}).get('zipcode', ''),
                            'department_name': ad.get('location', {}).get('department_name', ''),
                            'latitude': ad.get('location', {}).get('lat', ''),
                            'longitude': ad.get('location', {}).get('lng', ''),
                            'owner_name': ad.get('owner', {}).get('name', ''),
                            'owner_type': ad.get('owner', {}).get('type', ''),
                            'condition': attributes.get('condition', ''),
                            'product': attributes.get('computer_accessories_product', ''),
                            'shippable': attributes.get('shippable', ''),
                            'has_option': ad.get('options', {}).get('has_option', False),
                            'booster': ad.get('options', {}).get('booster', False)
                        }
                        annonces.append(annonce)
                else:
                    print(f"Requête {request_count} ({entry.request['url']}) ne contient pas 'ads'.")
            else:
                print(f"Aucune réponse trouvée pour la requête {request_count} ({entry.request['url']}).")
        except json.JSONDecodeError as e:
            print(f"Erreur de décodage JSON pour la requête {request_count} ({entry.request['url']}) : {e}")

# Exporter en JSON
with open(output_json, 'w', encoding='utf-8') as json_file:
    json.dump(annonces, json_file, ensure_ascii=False, indent=4)
print(f"Données exportées en JSON : {output_json}")

# Exporter en CSV
if annonces:
    keys = annonces[0].keys()
    with open(output_csv, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(annonces)
    print(f"Données exportées en CSV : {output_csv}")
else:
    print("Aucune annonce trouvée dans le fichier HAR.")