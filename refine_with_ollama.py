import json
import requests
import argparse
import os

# URL de l'API Ollama
ollama_url = "http://localhost:11434/api/generate"

# Fonction pour nettoyer les valeurs
def clean_value(value):
    value = value.replace("**", "").strip()
    if "(" in value:
        value = value.split("(")[0].strip()
    if value.lower() in ["oui", "yes"]:
        return "Yes"
    elif value.lower() in ["non", "no"]:
        return "No"
    elif value.lower() in ["incertain", "unsure"]:
        return "Unsure"
    return value

# Fonction pour interroger Ollama
def refine_ad(subject, body, image_urls):
    image_url = image_urls[0] if image_urls else ""
    prompt = f"""Analyse cette annonce Leboncoin :
Titre : '{subject}'
Description : '{body}'
Image : '{image_url}'
Suis ce format strict :
1. Réflexion : [Analyse complète du texte et de l'image. Identifie le modèle exact et la catégorie (ex. "imprimante 3D", "filament", "accessoire"). Vérifie si l'image correspond au modèle spécifique détecté dans le texte, pas juste à la catégorie.]
2. Résultat :
   - Modèle : [Modèle exact (ex. "Creality Ender 3 Pro") ou "Unknown"]
   - Catégorie : [ex. "imprimante 3D", "filament", "accessoire"]
   - Cohérence image : ["Yes" si l'image montre le modèle détecté, "No" si elle montre autre chose, "Unsure" si impossible à déterminer]
"""
    payload = {
        "model": "llama3.2-vision:latest",
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(ollama_url, json=payload)
        response.raise_for_status()
        result = response.json()
        raw_response = result.get("response", "Unknown").strip()
        print(f"Réflexion LLM pour {subject} :\n{raw_response}\n")
        
        # Extraction des résultats
        lines = [line.strip() for line in raw_response.splitlines() if line.strip()]
        model, category, coherence = "Unknown", "Unknown", "Unsure"
        
        # Parcourir toutes les lignes pour trouver les champs
        for line in lines:
            if "Modèle :" in line:
                model = clean_value(line.split("Modèle :")[-1])
            elif "Catégorie :" in line:
                category = clean_value(line.split("Catégorie :")[-1])
            elif "Cohérence image :" in line:
                coherence = clean_value(line.split("Cohérence image :")[-1])
        
        return model, category, coherence
    except Exception as e:
        print(f"Erreur avec Ollama : {e}")
        return "Unknown", "Unknown", "Unsure"

# Gestion des arguments en ligne de commande
parser = argparse.ArgumentParser(description="Raffiner les annonces Leboncoin avec Ollama.")
parser.add_argument("--limit", type=int, default=None, help="Nombre maximum d'annonces à analyser")
args = parser.parse_args()

# Chemins des fichiers
input_json_path = "annonces_leboncoin.json"
output_json_path = "annonces_refined.json"

# Charger le JSON brut
with open(input_json_path, "r", encoding="utf-8") as f:
    ads_data = json.load(f)

# Limiter le nombre d'annonces si spécifié
if args.limit is not None:
    ads_data = ads_data[:args.limit]

# Initialiser le fichier JSON
if os.path.exists(output_json_path):
    os.remove(output_json_path)
with open(output_json_path, "w", encoding="utf-8") as f:
    f.write("[\n")

# Raffiner les annonces et écrire progressivement
first_entry = True
for i, ad in enumerate(ads_data):
    subject = ad.get("subject", "")
    body = ad.get("body", "")
    image_urls = ad.get("images", {}).get("urls", [])
    item_model, item_category, image_coherence = refine_ad(subject, body, image_urls)
    
    refined_ad = ad.copy()
    refined_ad["item_model"] = item_model
    refined_ad["item_category"] = item_category
    refined_ad["image_coherence"] = image_coherence
    print(f"Annonce {ad['list_id']} : item_model = {item_model}, item_category = {item_category}, image_coherence = {image_coherence}")
    
    # Écriture progressive dans le JSON
    with open(output_json_path, "a", encoding="utf-8") as f:
        if not first_entry:
            f.write(",\n")
        json.dump(refined_ad, f, ensure_ascii=False, indent=2)
        first_entry = False

# Finaliser le JSON
with open(output_json_path, "a", encoding="utf-8") as f:
    f.write("\n]")
print(f"Données raffinées exportées vers {output_json_path}")