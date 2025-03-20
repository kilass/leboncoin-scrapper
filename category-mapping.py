import json

with open('annonces_leboncoin.json', 'r', encoding='utf-8') as f:
    ads = json.load(f)

categories = {}
for ad in ads:
    cat_id = ad['category_id']
    cat_name = ad['category_name']
    if cat_id not in categories:
        categories[cat_id] = cat_name

with open('category_mapping.json', 'w', encoding='utf-8') as f:
    json.dump({"categories": [{"id": k, "name": v, "typical_items": [], "description": ""} for k, v in categories.items()]}, f, ensure_ascii=False, indent=4)