import json

with open('/Users/mukhtarsyafii/.gemini/antigravity/scratch/data_prepared.json') as f:
    data = json.load(f)

for p in data["products"]:
    p.pop("weekly", None)

products_json = json.dumps(data["products"])
print(f"Compact products length: {len(products_json)}")
