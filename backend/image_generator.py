"""
Générateur d'images AI avec Gemini 2.5 Flash Image
Génère des variations réalistes de produits à partir d'une image source
"""
import google.generativeai as genai
import requests
import base64
import time
import os
from io import BytesIO
from PIL import Image

class ImageGenerator:
    def __init__(self, api_key):
        """
        Initialise le générateur d'images avec Gemini 2.5 Flash Image
        
        Args:
            api_key: Clé API Google Gemini
        """
        self.api_key = api_key
        
        # Utiliser la nouvelle API genai pour la génération d'images
        # Modèle officiel: gemini-2.5-flash-image (Nano Banana)
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash-image"
        
        print("✅ Gemini 2.5 Flash Image (Nano Banana) initialisé")
    
    def download_image_from_url(self, url):
        """
        Télécharge une image depuis une URL CDN
        
        Args:
            url: URL de l'image (CDN Shopify)
            
        Returns:
            bytes: Données de l'image ou None
        """
        try:
            # Nettoyer l'URL et optimiser la taille
            clean_url = url.split('?')[0]
            if 'cdn.shopify.com' in clean_url:
                clean_url += '?width=1024'
            
            response = requests.get(clean_url, timeout=15)
            response.raise_for_status()
            
            # Convertir en PIL Image pour validation
            img = Image.open(BytesIO(response.content))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Redimensionner si trop grande
            max_size = 1024
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convertir en bytes
            buffered = BytesIO()
            img.save(buffered, format="PNG", quality=95)
            return buffered.getvalue()
            
        except Exception as e:
            print(f"❌ Erreur téléchargement image {url}: {e}")
            return None
    
    def generate_product_variation(self, image_bytes, variation_prompt, variation_number=1):
        """
        Génère une variation d'image produit avec Gemini
        
        Args:
            image_bytes: Bytes de l'image source
            variation_prompt: Prompt pour la variation
            variation_number: Numéro de la variation (pour le nom)
            
        Returns:
            bytes: Image générée ou None
        """
        try:
            # Créer l'image PIL depuis les bytes
            source_image = Image.open(BytesIO(image_bytes))
            
            # Appel à Gemini 2.5 Flash Image (Nano Banana) pour générer une variation
            # On passe l'image PIL directement + le prompt texte
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[variation_prompt, source_image],
            )
            
            # Extraire l'image générée depuis la réponse
            for part in response.parts:
                if part.inline_data is not None:
                    # L'image est déjà en bytes, utiliser as_image() ou récupérer les données
                    try:
                        # Méthode 1: Utiliser as_image() si disponible
                        generated_img = part.as_image()
                        buffered = BytesIO()
                        generated_img.save(buffered, format="PNG")
                        return buffered.getvalue()
                    except:
                        # Méthode 2: Décoder manuellement le base64
                        if hasattr(part.inline_data, 'data'):
                            image_data = part.inline_data.data
                            if isinstance(image_data, str):
                                image_data = base64.b64decode(image_data)
                            return image_data
            
            print(f"⚠️ Pas d'image générée pour variation {variation_number}")
            return None
            
        except Exception as e:
            print(f"❌ Erreur génération variation {variation_number}: {e}")
            return None
    
    def analyze_and_generate_prompts(self, image_bytes, num_prompts=10):
        """
        ÉTAPE 1: Gemini 2.0 Flash (pas cher) analyse l'image et génère des prompts personnalisés
        
        Args:
            image_bytes: Bytes de l'image source
            num_prompts: Nombre de prompts à générer
            
        Returns:
            list: Liste de prompts générés par Gemini
        """
        try:
            source_image = Image.open(BytesIO(image_bytes))
            
            analysis_prompt = f"""You are an expert e-commerce and Pinterest photographer.

Look at this product image carefully. Identify:
- What type of product this is
- Its style, colors, materials
- Who would buy this (target audience)

Then create exactly {num_prompts} UNIQUE prompts to photograph this EXACT product in {num_prompts} DIFFERENT beautiful settings.

Be creative and choose settings that are COHERENT and RELEVANT for this specific product type. 
Each setting should have a different background, lighting, and atmosphere.
Around prompt 5, include a close-up/detail shot showing the product's texture and quality.

STRICT RULES:
- ULTRA REALISTIC photography only - like a real photo taken with a camera
- NO special effects, NO fantasy elements, NO magical lighting
- NO dramatic or artificial lighting effects - use natural, realistic lighting
- The product must remain IDENTICAL - never modify it
- NO logos, NO text, NO brand names
- Simple, clean, professional e-commerce photography
- Pinterest-worthy but REALISTIC and BELIEVABLE
- Each of the {num_prompts} settings must be COMPLETELY DIFFERENT

Return ONLY {num_prompts} prompts, numbered 1 to {num_prompts}. Each prompt = 2-3 detailed sentences.
Format:
1. [prompt]
2. [prompt]
...
"""
            
            # Utiliser gemini-2.5-flash pour l'analyse (meilleur pour lire les images)
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[analysis_prompt, source_image],
            )
            
            # Parser la réponse pour extraire les prompts
            response_text = response.text
            prompts = []
            
            for line in response_text.strip().split('\n'):
                line = line.strip()
                if line and len(line) > 10:
                    # Nettoyer le numéro du début si présent
                    if line[0].isdigit():
                        clean_prompt = line.lstrip('0123456789.-) ').strip()
                    elif line.startswith('-'):
                        clean_prompt = line.lstrip('- ').strip()
                    else:
                        clean_prompt = line
                    
                    if clean_prompt and len(clean_prompt) > 20:
                        # Ajouter les règles de base à chaque prompt
                        full_prompt = f"{clean_prompt} Keep the product IDENTICAL and unchanged. No logos, no text. Photorealistic Pinterest-style photography."
                        prompts.append(full_prompt)
            
            print(f"✅ {len(prompts)} prompts générés par Gemini")
            for i, p in enumerate(prompts[:num_prompts], 1):
                print(f"   📝 Prompt {i}: {p[:100]}...")
            
            return prompts[:num_prompts]
            
        except Exception as e:
            print(f"❌ Erreur analyse image: {e}")
            return []
    
    def generate_product_variations(self, source_image_url, num_variations=10):
        """
        Génère plusieurs variations d'un produit en 2 étapes:
        1. Gemini 2.0 Flash analyse l'image et génère des prompts personnalisés
        2. Gemini 2.5 Flash Image utilise ces prompts pour générer les images
        
        Args:
            source_image_url: URL de l'image source (CDN Shopify)
            num_variations: Nombre de variations à générer (max 10 pour Etsy)
            
        Yields:
            dict: {'status': str, 'progress': int, 'image_data': bytes, 'variation': int}
        """
        # Télécharger l'image source
        yield {
            'status': 'downloading',
            'message': '📥 Téléchargement de l\'image source...',
            'progress': 0
        }
        
        source_bytes = self.download_image_from_url(source_image_url)
        if not source_bytes:
            yield {
                'status': 'error',
                'message': '❌ Impossible de télécharger l\'image source',
                'progress': 0
            }
            return
        
        # ÉTAPE 1: Gemini 2.0 Flash analyse l'image et génère les prompts
        yield {
            'status': 'analyzing',
            'message': '🔍 Étape 1/2: Gemini analyse le produit et crée les prompts...',
            'progress': 5
        }
        
        custom_prompts = self.analyze_and_generate_prompts(source_bytes, num_variations)
        
        if not custom_prompts:
            yield {
                'status': 'error',
                'message': '❌ Échec de la génération des prompts',
                'progress': 0
            }
            return
        
        yield {
            'status': 'prompts_ready',
            'message': f'✅ {len(custom_prompts)} prompts personnalisés créés par l\'IA',
            'progress': 10
        }
        
        # Afficher les prompts dans les logs
        for i, prompt in enumerate(custom_prompts, 1):
            short_prompt = prompt[:80] + '...' if len(prompt) > 80 else prompt
            yield {
                'status': 'prompt_info',
                'message': f'📝 Prompt {i}: {short_prompt}',
                'progress': 10
            }
        
        # ÉTAPE 2: Générer les images avec les prompts personnalisés
        yield {
            'status': 'generating_start',
            'message': '🎨 Étape 2/2: Génération des images avec Gemini...',
            'progress': 15
        }
        
        generated_images = []
        
        for idx, prompt in enumerate(custom_prompts):
            variation_num = idx + 1
            progress = 15 + int((idx / len(custom_prompts)) * 85)
            
            yield {
                'status': 'generating',
                'message': f'🎨 Génération image {variation_num}/{len(custom_prompts)}...',
                'progress': progress,
                'variation': variation_num
            }
            
            # Générer avec le prompt personnalisé
            image_data = self.generate_product_variation(source_bytes, prompt, variation_num)
            
            if image_data:
                generated_images.append(image_data)
                yield {
                    'status': 'generated',
                    'message': f'✅ Image {variation_num} générée',
                    'progress': 15 + int(((idx + 1) / len(custom_prompts)) * 85),
                    'variation': variation_num,
                    'image_data': image_data
                }
            else:
                yield {
                    'status': 'warning',
                    'message': f'⚠️ Image {variation_num} échouée, passage à la suivante',
                    'progress': 15 + int(((idx + 1) / len(custom_prompts)) * 85),
                    'variation': variation_num
                }
            
            # Pause entre les requêtes
            if idx < len(custom_prompts) - 1:
                time.sleep(2)
        
        yield {
            'status': 'complete',
            'message': f'✅ {len(generated_images)} images générées avec succès',
            'progress': 100,
            'total_generated': len(generated_images),
            'images': generated_images
        }
    
    def process_product_for_csv(self, source_image_url, shopify_client, product_id, num_images=10):
        """
        Processus complet: génère les images et les upload sur Shopify
        
        Args:
            source_image_url: URL de l'image source
            shopify_client: Instance de ShopifyClient
            product_id: ID du produit Shopify
            num_images: Nombre d'images à générer
            
        Yields:
            dict: Progression et résultats
        """
        generated_images = []
        
        # Générer les variations
        for progress in self.generate_product_variations(source_image_url, num_images):
            if progress['status'] == 'generated' and 'image_data' in progress:
                generated_images.append(progress['image_data'])
            yield progress
            
            if progress['status'] == 'error':
                return
        
        if not generated_images:
            yield {
                'status': 'error',
                'message': '❌ Aucune image générée',
                'progress': 0
            }
            return
        
        # Upload vers Shopify et remplacer les anciennes images
        yield {
            'status': 'uploading',
            'message': f'📤 Upload de {len(generated_images)} images vers Shopify...',
            'progress': 0
        }
        
        result = shopify_client.replace_product_images(product_id, generated_images)
        
        if result['success']:
            yield {
                'status': 'complete',
                'message': f'✅ {result["uploaded_count"]} images uploadées sur Shopify',
                'progress': 100,
                'new_urls': result['new_urls']
            }
        else:
            yield {
                'status': 'error',
                'message': f'❌ Erreur upload: {result["error"]}',
                'progress': 0
            }


def load_gemini_api_key():
    """
    Charge la clé API Gemini depuis settings.json
    """
    settings_file = os.path.abspath('settings.json')
    try:
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                return settings.get('gemini_api_key', '')
    except Exception as e:
        print(f"⚠️ Erreur lecture clé API Gemini: {e}")
    return ''
