"""
Système intelligent de catégorisation Etsy
Utilise Gemini pour sélectionner LA catégorie la plus spécifique et pertinente
"""
import json
import os
import google.generativeai as genai
from typing import List, Dict, Optional

class CategoryMatcher:
    def __init__(self, api_key: str):
        """Initialise le matcher avec l'API Gemini"""
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
        # Utiliser Gemini 2.5 Flash pour la catégorisation
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        self.categories = self._load_categories()
        self.leaf_categories = self._filter_leaf_categories()
        
    def _load_categories(self) -> List[str]:
        """Charge les catégories depuis le JSON"""
        json_path = os.path.join(os.path.dirname(__file__), '..', 'Etsy Categories.json')
        
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"Fichier de catégories introuvable: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            categories = json.load(f)
        
        print(f"✅ {len(categories)} catégories Etsy chargées")
        return categories
    
    def _filter_leaf_categories(self) -> List[str]:
        """
        Filtre pour garder UNIQUEMENT les catégories feuilles (les plus profondes)
        Une catégorie est une feuille si aucune autre catégorie ne commence par elle
        """
        leaf_categories = []
        
        for category in self.categories:
            # Vérifier si cette catégorie est un parent d'une autre
            is_parent = False
            search_pattern = category + " >"
            
            for other_category in self.categories:
                if other_category != category and other_category.startswith(search_pattern):
                    is_parent = True
                    break
            
            # Si ce n'est pas un parent, c'est une feuille
            if not is_parent:
                leaf_categories.append(category)
        
        print(f"✅ {len(leaf_categories)} catégories feuilles (les plus spécifiques)")
        return leaf_categories
    
    def _get_relevant_categories(self, title: str, limit: int = 20) -> List[str]:
        """
        Pré-filtre les catégories pertinentes basées sur des mots-clés
        pour réduire le nombre de catégories envoyées à Gemini
        """
        # Extraire les mots-clés du titre
        keywords = title.lower().split()
        
        # Scorer chaque catégorie feuille
        scored_categories = []
        for category in self.leaf_categories:
            score = 0
            category_lower = category.lower()
            
            # Compter les mots-clés qui matchent
            for keyword in keywords:
                if len(keyword) > 2 and keyword in category_lower:
                    score += 1
            
            if score > 0:
                scored_categories.append((category, score))
        
        # Trier par score et prendre les top N
        scored_categories.sort(key=lambda x: x[1], reverse=True)
        
        # Si on a des matches, retourner les meilleurs
        if scored_categories:
            return [cat for cat, score in scored_categories[:limit]]
        
        # 🎯 FALLBACK INTELLIGENT pour produits sans mots-clés matchants
        # Détecter le type de produit par patterns
        title_lower = title.lower()
        
        # Produits digitaux (PNG, SVG, PDF, Template, etc.)
        if any(ext in title_lower for ext in ['png', 'svg', 'pdf', 'jpeg', 'jpg', 'eps', 'ai', 'psd']):
            digital_categories = [cat for cat in self.leaf_categories if 'digital' in cat.lower() or 'template' in cat.lower() or 'clip art' in cat.lower() or 'graphic' in cat.lower()]
            if digital_categories:
                return digital_categories[:limit]
        
        # Templates spécifiques
        if 'template' in title_lower or 'printable' in title_lower:
            template_categories = [cat for cat in self.leaf_categories if 'template' in cat.lower() or 'design' in cat.lower()]
            if template_categories:
                return template_categories[:limit]
        
        # Logos & Graphics
        if 'logo' in title_lower or 'graphic' in title_lower or 'design' in title_lower:
            design_categories = [cat for cat in self.leaf_categories if 'logo' in cat.lower() or 'graphic' in cat.lower() or 'design' in cat.lower()]
            if design_categories:
                return design_categories[:limit]
        
        # Clip Art & Images
        if 'clipart' in title_lower or 'clip art' in title_lower or 'image' in title_lower:
            clipart_categories = [cat for cat in self.leaf_categories if 'clip art' in cat.lower() or 'image' in cat.lower()]
            if clipart_categories:
                return clipart_categories[:limit]
        
        # Dernier fallback: catégories digitales génériques
        print(f"⚠️ Aucun mot-clé trouvé pour '{title}', utilisation des catégories digitales par défaut")
        digital_fallback = [cat for cat in self.leaf_categories if any(keyword in cat.lower() for keyword in ['digital', 'template', 'clip art', 'graphic design', 'file'])]
        
        if digital_fallback:
            return digital_fallback[:limit]
        
        # Ultime fallback: catégories art & craft supplies
        import random
        return random.sample(self.leaf_categories, min(limit, len(self.leaf_categories)))
    
    def find_best_category(self, product_title: str, product_description: str = "") -> Dict:
        """
        Trouve LA meilleure catégorie Etsy pour un produit
        
        Args:
            product_title: Titre du produit
            product_description: Description du produit (optionnel, améliore la précision)
        
        Returns:
            {
                'category': 'Jewelry > Rings > Wedding & Engagement > Wedding Bands',
                'confidence': 'high',
                'reasoning': 'Explication de Gemini'
            }
        """
        try:
            # 1. Pré-filtrer les catégories pertinentes
            relevant_categories = self._get_relevant_categories(product_title, limit=30)
            
            # 2. Construire le prompt pour Gemini
            prompt = f"""Tu es un expert en catégorisation de produits Etsy.

RÈGLES CRITIQUES:
1. ANALYSE LE DÉBUT DU TITRE EN PRIORITÉ - il indique le produit principal
2. Le premier mot/groupe de mots du titre est souvent le TYPE de produit (ex: "Black Waterfall Bathroom Faucet" = FAUCET/robinet)
3. NE JAMAIS choisir une catégorie basée uniquement sur un détail secondaire (matériau, couleur, style)
4. Choisis LA catégorie la PLUS SPÉCIFIQUE qui correspond au PRODUIT PRINCIPAL
5. Si le titre mentionne "Faucet/Tap/Mixer" = c'est un robinet, PAS un objet décoratif
6. Si le titre mentionne "Bathroom/Kitchen" + "Faucet" = catégorie robinetterie, PAS décoration

PRODUIT À CATÉGORISER:
Titre: "{product_title}"
{f'Description: "{product_description}"' if product_description else ''}

CATÉGORIES DISPONIBLES (toutes sont des catégories finales/spécifiques):
{chr(10).join([f"{i+1}. {cat}" for i, cat in enumerate(relevant_categories)])}

INSTRUCTIONS:
1. Identifie le TYPE de produit principal (début du titre)
2. Élimine les catégories qui ne correspondent PAS au produit principal
3. Choisis le NUMÉRO (1-{len(relevant_categories)}) de la catégorie LA PLUS PERTINENTE
4. Réponds au format JSON exact:
{{
    "number": <numéro>,
    "confidence": "high|medium|low",
    "reasoning": "Courte explication"
}}

Réponds UNIQUEMENT avec le JSON, rien d'autre."""

            # 3. Appeler Gemini
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Nettoyer la réponse (enlever les markdown code blocks si présents)
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            # 4. Parser la réponse
            result = json.loads(response_text)
            
            # 5. Récupérer la catégorie choisie
            chosen_index = int(result['number']) - 1
            
            if 0 <= chosen_index < len(relevant_categories):
                chosen_category = relevant_categories[chosen_index]
                
                return {
                    'category': chosen_category,
                    'confidence': result.get('confidence', 'medium'),
                    'reasoning': result.get('reasoning', 'Catégorie sélectionnée par Gemini'),
                    'success': True
                }
            else:
                raise ValueError(f"Numéro invalide: {result['number']}")
                
        except Exception as e:
            print(f"❌ Erreur lors de la catégorisation: {e}")
            # Fallback: retourner la première catégorie pertinente
            fallback_categories = self._get_relevant_categories(product_title, limit=1)
            
            return {
                'category': fallback_categories[0] if fallback_categories else self.leaf_categories[0],
                'confidence': 'low',
                'reasoning': f'Fallback suite à erreur: {str(e)}',
                'success': False,
                'error': str(e)
            }
    
    def batch_categorize(self, products: List[Dict]) -> List[Dict]:
        """
        Catégorise plusieurs produits en batch
        
        Args:
            products: Liste de dicts avec 'title' et optionnellement 'description'
        
        Returns:
            Liste de résultats de catégorisation
        """
        results = []
        
        for i, product in enumerate(products):
            print(f"📋 Catégorisation {i+1}/{len(products)}: {product['title'][:50]}...")
            
            result = self.find_best_category(
                product['title'],
                product.get('description', '')
            )
            
            results.append({
                **product,
                **result
            })
        
        return results


# Fonction utilitaire pour tester
def test_categorizer():
    """Test du système de catégorisation"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ GEMINI_API_KEY non trouvée dans .env")
        return
    
    matcher = CategoryMatcher(api_key)
    
    # Tests
    test_products = [
        {
            'title': 'Handmade Silver Wedding Ring for Men',
            'description': 'Beautiful handcrafted sterling silver wedding band'
        },
        {
            'title': 'Vintage Leather Crossbody Bag',
            'description': 'Genuine leather crossbody purse for women'
        },
        {
            'title': 'Watercolor Painting of Mountain Landscape',
            'description': 'Original watercolor art on canvas'
        }
    ]
    
    print("\n" + "="*60)
    print("🧪 TEST DU SYSTÈME DE CATÉGORISATION")
    print("="*60 + "\n")
    
    for product in test_products:
        result = matcher.find_best_category(product['title'], product['description'])
        
        print(f"\n📦 Produit: {product['title']}")
        print(f"✅ Catégorie: {result['category']}")
        print(f"🎯 Confiance: {result['confidence']}")
        print(f"💡 Raison: {result['reasoning']}")
        print("-" * 60)


if __name__ == "__main__":
    test_categorizer()
