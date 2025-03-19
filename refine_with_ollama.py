import json
import requests

# Chemin vers le JSON brut
input_json_path = "annonces_leboncoin.json"
output_json_path = "annonces_refined.json"

# URL de l'API Ollama
ollama_url = "http://localhost:11434/api/generate"

# Charger le JSON brut
with open(input_json_path, "r", encoding="utf-8") as f:
    ads_data = json.load(f)

# Fonction pour interroger Ollama et obtenir le modèle
def get_item_model(subject, body):
    prompt = f"""Analyse cette annonce Leboncoin :
Titre : '{subject}'
Description : '{body}'
Quel est le modèle exact de l'article vendu ? Suis ce format strict :
1. Réflexion : [Analyse complète. Recherche activement un modèle dans le titre et la description (ex. marque + nom comme "Creality Ender 3"). Si incertain, explique pourquoi.]
2. Résultat : [Modèle exact (ex. "Creality Ender 3 Pro") ou "Unknown" si aucun modèle clair n'est trouvé, sur une ligne séparée, sans autre texte.]
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
        
        # Extraire le modèle après "2. Résultat :"
        lines = [line.strip() for line in raw_response.splitlines() if line.strip()]
        result_found = False
        for i, line in enumerate(lines):
            if line.startswith("2. Résultat :"):
                # Prendre la ligne suivante non vide comme résultat
                for next_line in lines[i+1:]:
                    if next_line:  # Si la ligne n'est pas vide
                        return next_line
                return "Unknown"  # Si rien après "2. Résultat :"
        return "Unknown"  # Fallback si "2. Résultat :" n'est pas trouvé
    except Exception as e:
        print(f"Erreur avec Ollama : {e}")
        return "Unknown"

# Raffiner les annonces
refined_ads = []
for ad in ads_data:
    subject = ad.get("subject", "")
    body = ad.get("body", "")
    item_model = get_item_model(subject, body)
    refined_ad = ad.copy()
    refined_ad["item_model"] = item_model
    print(f"Annonce {ad['list_id']} : item_model = {item_model}")
    refined_ads.append(refined_ad)

# Exporter le JSON raffiné
with open(output_json_path, "w", encoding="utf-8") as f:
    json.dump(refined_ads, f, ensure_ascii=False, indent=2)

print(f"Données raffinées exportées vers {output_json_path}")