from shopify_client import ShopifyClient
import json

# Charger les settings
with open('../settings.json', 'r') as f:
    settings = json.load(f)

# Créer le client
client = ShopifyClient(
    settings['shopify_store_url'], 
    access_token=settings['shopify_access_token']
)

# ID du produit testé
product_id = 15086627750274

# Récupérer les images
print(f"Vérification des images pour le produit {product_id}...")
images = client.get_product_images(product_id)

print(f"\n📸 Nombre d'images trouvées: {len(images)}")

if images:
    print("\n🖼️ Liste des images:")
    for i, img in enumerate(images):
        print(f"  {i+1}. ID: {img.get('id')}")
        print(f"     Position: {img.get('position')}")
        print(f"     URL: {img.get('src', 'N/A')[:100]}...")
        print()
else:
    print("❌ Aucune image trouvée pour ce produit")
