import json
import argparse
import logging
import re
import ollama  # Importation explicite du module ollama

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

client = ollama.Client(host='http://localhost:11434')  # Utilisation correcte de ollama.Client

def clean_value(value):
    """Nettoie les caractères indésirables et les réflexions du LLM."""
    # Supprime les caractères de mise en forme
    value = re.sub(r'[\*`]', '', value).strip()
    # Supprime les réflexions entre parenthèses ou après "Raison :"
    value = re.sub(r'\s*\(.*?\)|\s*Raison\s*:.*$', '', value).strip()
    return value

def refine_json(input_file, output_file, limit=None):
    with open(input_file, 'r', encoding='utf-8') as f:
        ads = json.load(f)
    
    refined_ads = {}
    for i, ad in enumerate(ads):
        if limit is not None and i >= limit:
            break
        
        ad_id = ad['list_id']
        logging.info(f"Processing ad {ad_id} ({i+1}/{len(ads)})")
        
        # Mapping des champs pour le prompt
        title = ad['subject']
        description = ad['body']
        image_url = ad['images']['urls'][0] if ad['images']['urls'] else "No image available"
        
        prompt = f"""
        Analyse cette annonce Leboncoin :
        Titre : {title}
        Description : {description}
        URL de l'image : {image_url}

        Fournis les informations suivantes :
        - item_model : le modèle exact de l'objet (ex. "Creality Ender 3") ou "Unknown" si non identifiable
        - item_category : la catégorie de l'objet (ex. "Imprimante 3D", "Filament", "Accessoire") ou "Unknown" si non identifiable
        - image_coherence : "Oui" si l'image correspond au titre/description, "Non" sinon
        
        Formate ta réponse exactement comme suit :
        item_model: <valeur>
        item_category: <valeur>
        image_coherence: <valeur>
        """
        
        response = client.generate(model='llama3.2-vision:latest', prompt=prompt)
        logging.info(f"Ad {ad_id} - Réponse LLM : {response['response']}")
        
        # Extraction des champs avec robustesse
        lines = response['response'].split('\n')
        refined_data = {'item_model': 'Unknown', 'item_category': 'Unknown', 'image_coherence': 'No'}
        for line in lines:
            line = line.strip()
            if not line or ':' not in line:  # Ignore les lignes vides ou sans format clé:valeur
                continue
            key, value = line.split(':', 1)
            value = clean_value(value)  # Nettoyage des valeurs
            if 'item_model' in key.lower():
                refined_data['item_model'] = value if value else 'Unknown'
            elif 'item_category' in key.lower():
                refined_data['item_category'] = value if value else 'Unknown'
            elif 'image_coherence' in key.lower():
                refined_data['image_coherence'] = 'Yes' if value.lower() in ['oui', 'yes'] else 'No'
        
        logging.info(f"Ad {ad_id} - Données raffinées : {refined_data}")
        
        # Copie complète de l'annonce originale + ajout des champs raffinés
        refined_ad = ad.copy()
        refined_ad.update(refined_data)
        refined_ads[ad_id] = refined_ad
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(refined_ads, f, ensure_ascii=False, indent=4)
    logging.info(f"Données raffinées enregistrées dans {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Raffine les annonces Leboncoin avec Ollama")
    parser.add_argument('--limit', type=int, help="Limite le nombre d'annonces à traiter")
    args = parser.parse_args()
    
    refine_json('annonces_leboncoin.json', 'annonces_refined.json', args.limit)