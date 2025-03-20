import json
import argparse
import logging
import re
import ollama

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

client = ollama.Client(host='http://localhost:11434')

def clean_value(value):
    """Nettoie les caractères indésirables et les réflexions du LLM."""
    value = re.sub(r'[\*`]', '', value).strip()
    value = re.sub(r'\s*\(.*?\)|\s*Raison\s*:.*$', '', value).strip()
    return value

def write_incremental_json(output_file, refined_ads):
    """Écrit les données raffinées dans le fichier JSON de manière incrémentale."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(refined_ads, f, ensure_ascii=False, indent=4)

def refine_json(input_file, output_file, limit=None):
    # Charger les données brutes
    with open(input_file, 'r', encoding='utf-8') as f:
        ads = json.load(f)
    
    # Charger le mapping des catégories
    with open('category_mapping.json', 'r', encoding='utf-8') as f:
        category_mapping = json.load(f)['categories']
    
    # Charger les données existantes dans le fichier de sortie, s'il existe
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            refined_ads = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        refined_ads = {}

    for i, ad in enumerate(ads):
        if limit is not None and i >= limit:
            break
        
        ad_id = str(ad['list_id'])
        logging.info(f"Processing ad {ad_id} ({i+1}/{len(ads)})")

        # Mapping des champs pour le prompt avec gestion des cas manquants
        title = ad.get('subject', 'Titre inconnu')
        description = ad.get('body', 'Description inconnue')
        images = ad.get('images', {})
        image_url = images.get('urls', [None])[0] if images.get('urls') else "No image available"
        category_id = ad.get('category_id', 'N/A')
        category_name = ad.get('category_name', 'N/A')

        # Prompt mis à jour avec le mapping des catégories
        prompt = f"""
        Analyse cette annonce Leboncoin :
        Titre : {title}
        Description : {description}
        URL de l'image : {image_url}
        Catégorie de l'annonce : ID={category_id}, Nom={category_name}

        Voici les catégories disponibles avec leurs objets typiques :
        {json.dumps(category_mapping, ensure_ascii=False, indent=2)}

        Fournis les informations suivantes :
        - item_model : le modèle exact de l'objet (ex. "Creality Ender 3") ou "Unknown" si non identifiable
        - item_category : la catégorie la plus appropriée basée sur la catégorie de l’annonce (ID={category_id}) et les objets typiques dans le mapping ; si elle diffère de la catégorie de l’annonce, choisis la plus pertinente
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
            if not line or ':' not in line:
                continue
            key, value = line.split(':', 1)
            value = clean_value(value)
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
        
        # Écriture incrémentale dans le fichier JSON
        write_incremental_json(output_file, refined_ads)
        logging.info(f"Ad {ad_id} - Données enregistrées dans {output_file}")
    
    logging.info(f"Traitement terminé - Données finales enregistrées dans {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Raffine les annonces Leboncoin avec Ollama")
    parser.add_argument('--limit', type=int, help="Limite le nombre d'annonces à traiter")
    args = parser.parse_args()
    
    refine_json('annonces_leboncoin.json', 'annonces_refined.json', args.limit)