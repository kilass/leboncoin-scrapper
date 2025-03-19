import json

# Chemin vers ton fichier JSON
json_file_path = "annonces_leboncoin.json"

# Ouvre et charge le fichier JSON
with open(json_file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Vérifie si c'est une liste
if isinstance(data, list):
    num_annonces = len(data)
    print(f"Nombre total d'annonces dans le JSON : {num_annonces}")

    # Compte les list_id uniques
    list_ids = [ad.get("list_id") for ad in data if "list_id" in ad]
    unique_list_ids = len(set(list_ids))
    print(f"Nombre de list_id uniques : {unique_list_ids}")

    # Vérifie les doublons
    if num_annonces == unique_list_ids:
        print("Aucun doublon détecté.")
    else:
        print(f"Attention : {num_annonces - unique_list_ids} doublons détectés.")
else:
    print("Le fichier JSON ne contient pas une liste d'annonces au niveau racine.")  