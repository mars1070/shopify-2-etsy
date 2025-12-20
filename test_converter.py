"""
Script de test rapide pour la conversion Shopify → Etsy
Utilise directement le converter sans passer par l'interface web
"""

import sys
import os

# Ajouter le dossier backend au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from converter import ShopifyToEtsyConverter

def test_conversion():
    print("=" * 60)
    print("TEST DE CONVERSION SHOPIFY → ETSY")
    print("=" * 60)
    print()
    
    # Fichiers
    input_file = "Shopify CSV Model.csv"
    output_file = "test_output_etsy.csv"
    
    # Vérifier que le fichier existe
    if not os.path.exists(input_file):
        print(f"❌ Erreur: Le fichier '{input_file}' n'existe pas")
        print(f"   Assurez-vous qu'il est dans le dossier: {os.getcwd()}")
        return
    
    print(f"📁 Fichier d'entrée: {input_file}")
    print(f"📁 Fichier de sortie: {output_file}")
    print()
    
    # Configuration
    price_multiplier = 2.5
    print(f"💰 Multiplicateur de prix: {price_multiplier}")
    print(f"   Exemple: 10€ × {price_multiplier} = {10 * price_multiplier}€ → {(10 * price_multiplier) - 0.10}€")
    print()
    
    # Conversion
    print("🔄 Conversion en cours...")
    try:
        converter = ShopifyToEtsyConverter(price_multiplier)
        products_count = converter.convert(input_file, output_file)
        
        print()
        print("=" * 60)
        print("✅ CONVERSION RÉUSSIE !")
        print("=" * 60)
        print(f"📊 Nombre de produits convertis: {products_count}")
        print(f"📄 Fichier généré: {output_file}")
        print()
        print("⚠️  Note: Ce fichier n'a PAS été optimisé avec Gemini AI")
        print("   Pour l'optimisation AI, utilisez l'interface web")
        print()
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERREUR LORS DE LA CONVERSION")
        print("=" * 60)
        print(f"Erreur: {str(e)}")
        print()
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_conversion()
