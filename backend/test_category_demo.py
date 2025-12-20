"""
DÉMO du système de catégorisation
Montre comment le système filtre et sélectionne les catégories
"""
import json
import os

def demo_category_filtering():
    """Démontre le filtrage des catégories feuilles"""
    
    # Charger les catégories
    json_path = os.path.join(os.path.dirname(__file__), '..', 'Etsy Categories.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        all_categories = json.load(f)
    
    print("="*70)
    print("🎯 DÉMO: FILTRAGE DES CATÉGORIES FEUILLES")
    print("="*70)
    
    print(f"\n📊 Total de catégories dans le JSON: {len(all_categories)}")
    
    # Filtrer les catégories feuilles
    leaf_categories = []
    parent_categories = []
    
    for category in all_categories:
        is_parent = False
        search_pattern = category + " >"
        
        for other_category in all_categories:
            if other_category != category and other_category.startswith(search_pattern):
                is_parent = True
                break
        
        if is_parent:
            parent_categories.append(category)
        else:
            leaf_categories.append(category)
    
    print(f"✅ Catégories FEUILLES (spécifiques): {len(leaf_categories)}")
    print(f"❌ Catégories MÈRES (générales): {len(parent_categories)}")
    
    # Exemples de catégories mères (à éviter)
    print("\n" + "="*70)
    print("❌ EXEMPLES DE CATÉGORIES MÈRES (ÉVITÉES par le système)")
    print("="*70)
    for cat in parent_categories[:10]:
        print(f"  - {cat}")
    
    # Exemples de catégories feuilles (utilisées)
    print("\n" + "="*70)
    print("✅ EXEMPLES DE CATÉGORIES FEUILLES (UTILISÉES par le système)")
    print("="*70)
    for cat in leaf_categories[:15]:
        print(f"  - {cat}")
    
    # Exemple concret: Jewelry > Rings
    print("\n" + "="*70)
    print("📋 EXEMPLE CONCRET: Hiérarchie 'Rings'")
    print("="*70)
    
    rings_categories = [cat for cat in all_categories if 'Rings' in cat and cat.startswith('Jewelry')]
    
    for cat in sorted(rings_categories)[:20]:
        depth = cat.count('>')
        is_leaf = cat in leaf_categories
        status = "✅ UTILISABLE" if is_leaf else "❌ ÉVITÉE"
        indent = "  " * depth
        print(f"{indent}{status} {cat}")
    
    # Statistiques par profondeur
    print("\n" + "="*70)
    print("📊 DISTRIBUTION PAR PROFONDEUR")
    print("="*70)
    
    depth_stats = {}
    for cat in leaf_categories:
        depth = cat.count('>')
        depth_stats[depth] = depth_stats.get(depth, 0) + 1
    
    for depth in sorted(depth_stats.keys()):
        count = depth_stats[depth]
        bar = "█" * (count // 50)
        print(f"Niveau {depth+1} ({depth} '>'): {count:4d} catégories {bar}")
    
    print("\n" + "="*70)
    print("💡 CONCLUSION")
    print("="*70)
    print(f"""
Le système utilise UNIQUEMENT les {len(leaf_categories)} catégories feuilles.
Cela garantit que chaque produit est placé dans la catégorie LA PLUS SPÉCIFIQUE.

Exemple:
  ❌ "Jewelry > Rings" → TROP GÉNÉRAL
  ✅ "Jewelry > Rings > Wedding & Engagement > Wedding Bands" → PARFAIT
    """)


def demo_keyword_matching():
    """Démontre le pré-filtrage par mots-clés"""
    
    print("\n" + "="*70)
    print("🔍 DÉMO: PRÉ-FILTRAGE PAR MOTS-CLÉS")
    print("="*70)
    
    # Charger les catégories
    json_path = os.path.join(os.path.dirname(__file__), '..', 'Etsy Categories.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        all_categories = json.load(f)
    
    # Filtrer les feuilles
    leaf_categories = []
    for category in all_categories:
        is_parent = False
        search_pattern = category + " >"
        for other_category in all_categories:
            if other_category != category and other_category.startswith(search_pattern):
                is_parent = True
                break
        if not is_parent:
            leaf_categories.append(category)
    
    # Test avec différents titres
    test_titles = [
        "Handmade Silver Wedding Ring for Men",
        "Vintage Leather Crossbody Bag",
        "Watercolor Mountain Landscape Painting",
        "Cotton Baby Girl Dress with Flowers"
    ]
    
    for title in test_titles:
        print(f"\n📦 Titre: \"{title}\"")
        print("-" * 70)
        
        # Extraire mots-clés
        keywords = [w.lower() for w in title.split() if len(w) > 2]
        print(f"🔑 Mots-clés: {', '.join(keywords)}")
        
        # Scorer les catégories
        scored = []
        for category in leaf_categories:
            score = 0
            category_lower = category.lower()
            
            for keyword in keywords:
                if keyword in category_lower:
                    score += 1
            
            if score > 0:
                scored.append((category, score))
        
        # Top 5
        scored.sort(key=lambda x: x[1], reverse=True)
        print(f"\n🎯 Top 5 catégories pré-filtrées (envoyées à Gemini):")
        for i, (cat, score) in enumerate(scored[:5], 1):
            print(f"  {i}. [{score} matches] {cat}")
        
        print(f"\n💡 Gemini choisira parmi ces {min(len(scored), 30)} catégories")


if __name__ == "__main__":
    demo_category_filtering()
    demo_keyword_matching()
