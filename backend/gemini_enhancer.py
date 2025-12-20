import pandas as pd
import google.generativeai as genai
import requests
import time
import re
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
from category_matcher import CategoryMatcher

class GeminiEnhancer:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        # Utilisation de Gemini 2.5 Flash (meilleur pour images + long output)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        print("✅ Gemini 2.5 Flash activé (1M tokens input, 65K output)")
        
        # Initialiser le système de catégorisation
        try:
            self.category_matcher = CategoryMatcher(api_key)
            print("✅ Système de catégorisation automatique activé")
        except Exception as e:
            print(f"⚠️ Catégorisation automatique désactivée: {e}")
            self.category_matcher = None
    
    def download_image_as_base64(self, url):
        """
        Télécharge une image depuis une URL CDN et la convertit en bytes
        """
        try:
            # Nettoyer l'URL (parfois des paramètres bizarres)
            clean_url = url.split('?')[0] + '?width=800' # Optimisation Shopify
            response = requests.get(clean_url, timeout=5)
            response.raise_for_status()
            
            img = Image.open(BytesIO(response.content))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Redimensionner pour optimiser l'envoi (max 600px pour vitesse)
            img.thumbnail((600, 600))
            
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=75)
            return buffered.getvalue()
        except Exception as e:
            print(f"Erreur image {url}: {e}")
            return None
    
    def generate_product_content(self, image_bytes):
        """
        Utilise Gemini pour générer titre, description et tags
        """
        try:
            # Récupérer la niche si elle a été définie
            niche_context = ""
            if hasattr(self, 'product_niche') and self.product_niche:
                niche_context = f"""
CRITICAL CONTEXT - PRODUCT NICHE/TYPE:
🎯 The seller has specified that this product is: "{self.product_niche}"
You MUST identify and describe the product according to this context.
Focus ONLY on the main product matching this description, NOT on accessories, lighting, stands, displays, or background elements.
The product niche/type provided by the seller is your PRIMARY guide for identification.

"""
            
            prompt = f"""{niche_context}CRITICAL INSTRUCTIONS: You MUST follow these formatting rules EXACTLY. No exceptions.

Analyze this product image VISUALLY to create optimized Etsy listing content.

Generate:

1. SEO TITLE (max 140 characters):
   Create a title with 2 or 3 keyword-rich phrases separated by " | "
   Each phrase should be descriptive and natural, using connector words (for, with, in) where it makes sense.
   
   CRITICAL: Start with the product's MOST DISTINCTIVE feature (design, symbol, pattern) in 2-4 words, THEN add material/color if needed.
   You can use up to 4 words if it makes the description more precise and complete.
   Priority order: Distinctive Design Element > Material/Finish > Generic Type
   
   Examples of GOOD titles:
   - "Viking Arrowhead Necklace | Norse Vegvisir Compass Pendant | Stainless Steel Men's Jewelry"
   - "Tall Gold Vintage Faucet | Waterfall Spout Bathroom Fixture | Single Handle Basin Tap"
   - "Snake Head Bracelet | Braided Metal & Leather Wristband for Men | Gothic Biker Jewelry"
   - "Brushed Bronze Bathroom Faucet | Modern Single Handle Mixer | Tall Vessel Sink Tap"
   
   Examples of BAD titles (too generic at start):
   - "Silver Stainless Steel Necklace | Norse Viking Arrowhead..." ❌ (material first)
   - "Metal Bracelet | Snake Head Design..." ❌ (generic type first)

2. DESCRIPTION:
   CRITICAL FORMATTING RULES:
   - NEVER use asterisks (*) for bold text. NO **text** anywhere in description.
   - NEVER use bullet points with * or - 
   - ALL formatting must use emojis and plain text only.
   
   REQUIRED STRUCTURE:
   1. Hook Paragraph: Powerful opening sentence + ONE BLANK LINE + emoji + creative title (e.g. "✨ Transform Your Space") + ONE BLANK LINE + 2-3 emotional sentences + ONE BLANK LINE.
   2. Detailed Paragraphs: Two paragraphs, each starting with emoji + creative title (e.g. "🌿 All-Natural Ingredients"). Integrate SEO keywords naturally.
   3. "✨ Features": List of 5-6 key strengths. Each starting with "✅ ".
   4. "❓ FAQ": 5-6 relevant Q&A. Questions start with "➡️ ", Answers with "🔹 ". Separate Q&A blocks with blank lines.
   
   CRITICAL LINE BREAK RULES:
   - After first sentence of hook, add ONE BLANK LINE before emotional sentences
   - Add ONE blank line between each major section (after hook, after paragraphs, before Features, before FAQ)
   - Add ONE blank line between each Q&A pair in FAQ section
   - NO blank lines after section titles like "✨ Features" or "❓ FAQ"
   
   DESCRIPTION EXAMPLE:
   Transform your daily routine with this stunning chrome faucet that combines elegance and functionality.
   
   👍 Elevate Your Bathroom Style
   Every detail has been carefully crafted to bring luxury to your space. The waterfall spout creates a soothing flow while the tall design adds a modern touch. Perfect for vessel sinks and contemporary bathrooms.
   
   🚰 Premium Quality Construction
   Built with solid brass and finished in durable chrome, this faucet resists tarnishing and corrosion. The ceramic disc valve ensures smooth operation and drip-free performance for years to come.
   
   💎 Modern Design Features
   The sleek single-handle design allows effortless temperature and flow control. Its tall profile accommodates large vessels while the curved spout adds an elegant arc to your vanity.
   
   ✨ Features
   ✅ Solid brass construction with chrome finish
   ✅ Ceramic disc valve for leak-free operation
   ✅ Single handle temperature control
   ✅ Tall design for vessel sinks
   ✅ Easy installation with standard fittings
   ✅ Waterfall spout for smooth water flow
   
   ❓ FAQ
   ➡️ What sink types work with this faucet?
   🔹 Perfect for vessel sinks and above-counter basins. The tall height accommodates most vessel sink styles.
   
   ➡️ Is installation difficult?
   🔹 Standard installation with included mounting hardware. Most DIYers complete it in 30-45 minutes.
   
   Tone: Simple, sales-oriented, easy to read.

3. TAGS (13 keywords, comma-separated WITHOUT spaces after commas):
   CRITICAL FORMATTING RULES:
   - Commas with NO space after: tag1,tag2,tag3
   - BUT keywords MUST have spaces between words: "kitchen faucet" NOT "kitchenfaucet"
   - WRONG: bathroomfaucet,chromefaucet,tallfaucet
   - CORRECT: bathroom faucet,chrome faucet,tall faucet
   
   - TAG GENERATION ALGORITHM (Strict keyword matching, NOT creative writing):
     
     Phase 1: DIRECT SEARCH TERMS & SYNONYMS (~8 tags):
     - Answer "What is this object?" in every possible way.
     - CRITICAL: First tag MUST be the most obvious direct name (max 2 words WITH space).
     - Use synonyms, plural/singular, common names.
     - ALWAYS separate words with spaces: "bathroom faucet" not "bathroomfaucet"
     - Example: `silver tap,chrome faucet,bathroom faucet,mixer tap,basin tap`

     Phase 2: SPECIFIC ATTRIBUTES (~3 tags):
     - Combine material/color/style with object name (WITH spaces).
     - Example: `wooden lamp,rustic lighting,boho light`

     Phase 3: ALTERNATIVE DESCRIPTIONS (~2 tags):
     - Different ways to describe the SAME product (WITH spaces).
     - Focus on function, use case, or alternative names.
     - Example for a lamp: `reading light,desk lighting`
     - Example for a faucet: `basin mixer,sink fixture`
     - NEVER use generic category terms like "home decor" or "gift".

   - STRICTLY FORBIDDEN:
     - NO generic terms ('shop', 'trend').
     - NO isolated adjectives ('beautiful', 'unique'). Must be combined ('unique ring' OK).
     - NO tags > 3 words.
     - NO specific quantities ('set of 6'). Use 'chair set'.

   - UNIVERSAL RULES:
     1. ENGLISH ONLY.
     2. ALL LOWERCASE.
     3. Max 3 words per tag.
     4. NO spaces after commas.
     5. ALWAYS put spaces between words in tags: "bathroom faucet" NOT "bathroomfaucet".
     6. Multi-word tags are REQUIRED for better search visibility.

Format your response EXACTLY like this:
TITLE: [phrase 1] | [phrase 2]

DESCRIPTION:
[your structured description with emojis, NO bold text]

TAGS: tag1,tag2,tag3,tag4,tag5,tag6,tag7,tag8,tag9,tag10,tag11,tag12,tag13
"""
            image_part = {'mime_type': 'image/jpeg', 'data': image_bytes}
            response = self.model.generate_content([prompt, image_part])
            
            content = response.text
            
            # Parsing robuste qui préserve les sauts de ligne
            title = ""
            description = ""
            tags = ""
            
            lines = content.split('\n')
            current_section = None
            
            for line in lines:
                original_line = line  # Garder la ligne originale pour préserver les sauts de ligne
                clean_line = line.strip()
                
                if clean_line.startswith('TITLE:'):
                    title = clean_line.replace('TITLE:', '').strip()
                    current_section = None
                elif clean_line.startswith('DESCRIPTION:'):
                    current_section = 'description'
                    description = ""
                elif clean_line.startswith('TAGS:'):
                    tags = clean_line.replace('TAGS:', '').strip()
                    current_section = None
                elif current_section == 'description':
                    # Ajouter la ligne exacte comme elle vient (avec sauts de ligne)
                    if clean_line:  # Ligne non vide
                        description += original_line.strip() + "\n"
                    else:  # Ligne vide = saut de ligne voulu
                        description += "\n"
            
            # POST-TRAITEMENT FORCÉ pour garantir le formatage correct
            # Supprimer tout le texte en gras de la description
            description = description.replace('**', '').replace('* ', ' ').replace(' *', ' ')
            
            # Nettoyer les sauts de ligne multiples mais en garder un entre les sections
            description = description.replace('\n\n\n', '\n\n').strip()
            
            # Nettoyer les tags: supprimer les espaces après les virgules et forcer minuscules
            if tags:
                # Supprimer tous les espaces après les virgules
                tags = tags.replace(', ', ',').replace(' ,', ',')
                # Forcer minuscules
                tags = tags.lower()
                # Supprimer les espaces en trop au début/fin
                tags = tags.strip()
                
                # 🔧 CORRECTION: Ajouter des espaces dans les mots composés collés
                # Détecter les mots collés (ex: bathroomfaucet) et les séparer
                tag_list = tags.split(',')
                fixed_tags = []
                for tag in tag_list:
                    tag = tag.strip()
                    # Si le tag a plus de 12 caractères sans espace, c'est probablement collé
                    if len(tag) > 12 and ' ' not in tag:
                        # Insérer un espace avant chaque majuscule (camelCase) ou avant des mots communs
                        # Patterns courants: bathroom, kitchen, chrome, modern, etc.
                        tag = re.sub(r'(bathroom|kitchen|chrome|modern|vintage|rustic|wooden|metal|glass|ceramic|plastic|waterfall|single|double|pull|down|handle|lever|mixer|basin|sink|lavatory|vanity|counter|wall|mounted|floor|standing|tall|short|wide|narrow|round|square|oval|rectangular)', r'\1 ', tag)
                        tag = tag.strip()
                    fixed_tags.append(tag)
                tags = ','.join(fixed_tags)
            
            return {
                'title': title[:139] if title else "Titre à vérifier",
                'description': description if description else "Description à générer",
                'tags': tags
            }
        
        except Exception as e:
            print(f"Erreur Gemini: {e}")
            return None

    def process_single_product(self, row, max_retries=3):
        """
        Traite un seul produit avec retry automatique en cas d'échec
        max_retries: nombre de tentatives (défaut 3)
        """
        first_image = row.get('Photo 1')
        sku = row.get('SKU', '')
        
        if not first_image or pd.isna(first_image):
            return None
        
        image_bytes = self.download_image_as_base64(first_image)
        if not image_bytes:
            return None
        
        # 🔄 RETRY LOGIC avec backoff exponentiel
        for attempt in range(max_retries):
            try:
                content = self.generate_product_content(image_bytes)
                if content:
                    result = {
                        'sku': sku,
                        'title': content['title'],
                        'description': content['description'],
                        'tags': content['tags'],
                        'category': ''  # Par défaut vide
                    }
                    
                    # 🎯 CATÉGORISATION AUTOMATIQUE
                    if self.category_matcher:
                        try:
                            cat_result = self.category_matcher.find_best_category(
                                product_title=content['title'],
                                product_description=content['description']
                            )
                            result['category'] = cat_result['category']
                            result['category_confidence'] = cat_result.get('confidence', 'unknown')
                        except Exception as e:
                            print(f"⚠️ Erreur catégorisation pour {sku}: {e}")
                    
                    return result
                else:
                    # Pas de contenu généré, réessayer
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
                        print(f"⚠️ Retry {attempt + 1}/{max_retries} pour {sku} dans {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    return None
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"❌ Erreur {sku} (tentative {attempt + 1}/{max_retries}): {e}")
                    print(f"   Retry dans {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Échec définitif pour {sku} après {max_retries} tentatives: {e}")
                    return None
        
        return None

    def enhance_generator(self, input_path, output_path, product_niche=''):
        """
        Générateur qui yield la progression pour le streaming
        Utilise le parallélisme (Batch Processing)
        
        Args:
            input_path: Chemin du fichier CSV d'entrée
            output_path: Chemin du fichier CSV de sortie
            product_niche: Niche/type de produit (ex: "Figurines Manga") pour aider Gemini
        
        IMPORTANT: Avec les variantes Etsy, seules les lignes avec Photo 1 sont des 
        produits principaux. Les lignes sans Photo 1 sont des variantes et ne doivent
        pas avoir de Title/Description/Tags.
        """
        # Stocker la niche pour l'utiliser dans process_single_product
        self.product_niche = product_niche
        print(f"🎯 Niche configurée: {product_niche if product_niche else 'Non spécifiée'}")
        
        df = pd.read_csv(input_path)
        
        print(f"📊 CSV chargé: {len(df)} lignes totales")
        
        # Identifier les lignes principales (celles avec Photo 1 = produits uniques)
        # Les lignes de variantes n'ont pas de Photo 1
        main_products_mask = df['Photo 1'].notna() & (df['Photo 1'] != '')
        main_products = df[main_products_mask].copy()
        
        print(f"📸 Produits avec Photo 1: {len(main_products)}")
        print(f"📦 Lignes variantes (sans Photo 1): {len(df) - len(main_products)}")
        
        # Liste des indices des lignes principales
        main_indices = main_products.index.tolist()
        unique_rows = [df.loc[idx] for idx in main_indices]
        
        # Dictionnaire pour stocker les résultats par index de ligne
        results_map = {}
        
        if not unique_rows:
            yield {
                'status': 'complete',
                'message': "Aucun produit avec image trouvé.",
                'output_file': 'etsy_final.csv',
                'products_count': 0
            }
            return
        
        # Utiliser un ThreadPoolExecutor pour paralléliser (10 workers pour vitesse optimale)
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Lancer les tâches avec l'index comme clé
            future_to_idx = {
                executor.submit(self.process_single_product, row): idx 
                for idx, row in zip(main_indices, unique_rows)
            }
            
            processed = 0
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                # sku = df.loc[idx, 'SKU'] if pd.notna(df.loc[idx, 'SKU']) else f"Produit-{idx}"
                processed += 1
                product_label = f"Produit #{processed}"
                
                try:
                    result = future.result()
                    if result:
                        results_map[idx] = result
                        # Afficher la catégorie si disponible
                        category_info = ""
                        if 'category' in result and result['category']:
                            # Afficher seulement la dernière partie de la catégorie pour ne pas surcharger
                            cat_parts = result['category'].split(' > ')
                            category_info = f" → {cat_parts[-1]}"
                        
                        yield {
                            'status': 'processing',
                            'message': f"✅ Optimisé: {product_label}{category_info}",
                            'progress': int((processed / len(unique_rows)) * 100)
                        }
                    else:
                        yield {
                            'status': 'processing',
                            'message': f"⚠️ Ignoré: {product_label}",
                            'progress': int((processed / len(unique_rows)) * 100)
                        }
                except Exception as e:
                    print(f"Erreur thread {product_label}: {e}")
                    yield {
                        'status': 'processing',
                        'message': f"❌ Erreur: {product_label}",
                        'progress': int((processed / len(unique_rows)) * 100)
                    }
        
        # Appliquer les résultats UNIQUEMENT aux lignes principales (pas aux variantes)
        print("Application des résultats aux produits principaux...")
        
        # 📊 RAPPORT D'ERREURS DÉTAILLÉ
        errors_report = {
            'missing_title': [],
            'missing_description': [],
            'missing_tags': [],
            'missing_category': [],
            'total_processed': len(results_map),
            'total_products': len(unique_rows)
        }
        
        for idx, data in results_map.items():
            product_num = list(results_map.keys()).index(idx) + 1
            
            # Appliquer et vérifier le titre
            if data.get('title'):
                df.loc[idx, 'Title'] = data['title']
            else:
                errors_report['missing_title'].append(f"Produit #{product_num} (ligne {idx})")
            
            # Appliquer et vérifier la description
            if data.get('description'):
                df.loc[idx, 'Description'] = data['description']
            else:
                errors_report['missing_description'].append(f"Produit #{product_num} (ligne {idx})")
            
            # Appliquer et vérifier les tags
            if data.get('tags'):
                df.loc[idx, 'Tags'] = data['tags']
            else:
                errors_report['missing_tags'].append(f"Produit #{product_num} (ligne {idx})")
            
            # 🎯 Appliquer et vérifier la catégorie automatique
            if 'category' in data and data['category']:
                df.loc[idx, 'Category'] = data['category']
            else:
                errors_report['missing_category'].append(f"Produit #{product_num} (ligne {idx})")
        
        # Les lignes de variantes (sans Photo 1) gardent Title/Description/Tags vides
        # C'est le comportement attendu par Etsy
        
        print(f"💾 Sauvegarde du CSV final: {len(df)} lignes totales")
        print(f"   - Produits optimisés: {len(results_map)}")
        print(f"   - Lignes variantes conservées: {len(df) - len(results_map)}")
            
        # Sauvegarder TOUTES les lignes (produits + variantes)
        df.to_csv(output_path, index=False)
        
        print(f"✅ Fichier sauvegardé: {output_path}")
        
        # 📊 Générer le message de rapport
        success_count = errors_report['total_processed']
        total_errors = len(errors_report['missing_title']) + len(errors_report['missing_description']) + len(errors_report['missing_tags']) + len(errors_report['missing_category'])
        
        if total_errors == 0:
            status_message = f"✅ PARFAIT ! {success_count} produits traités sans erreur"
        else:
            status_message = f"⚠️ {success_count} produits traités avec {total_errors} erreurs"
        
        yield {
            'status': 'complete',
            'message': status_message,
            'errors_report': errors_report,
            'output_file': 'etsy_final.csv',
            'products_count': len(results_map)
        }
