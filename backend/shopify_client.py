"""
Client Shopify pour OAuth et gestion des images produits
"""
import requests
import base64
import json
import os

class ShopifyClient:
    def __init__(self, store_url, access_token=None, api_key=None, api_secret=None):
        """
        Initialise le client Shopify
        
        Args:
            store_url: URL du store (ex: votre-boutique.myshopify.com)
            access_token: Token d'accès OAuth (optionnel si api_key/api_secret fournis)
            api_key: API Key (Client ID) pour Basic Auth
            api_secret: API Secret Key pour Basic Auth
        """
        # Nettoyer l'URL du store
        clean_url = store_url.replace('https://', '').replace('http://', '').rstrip('/')
        
        # S'assurer que l'URL contient .myshopify.com
        if '.myshopify.com' not in clean_url and '.' not in clean_url:
            # Si c'est juste le nom du store, ajouter .myshopify.com
            clean_url = f"{clean_url}.myshopify.com"
        
        self.store_url = clean_url
        self.access_token = access_token
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_version = '2025-01'
        self.base_url = f"https://{self.store_url}/admin/api/{self.api_version}"
        
        # Choisir le mode d'authentification
        if api_key and api_secret:
            # Basic Auth avec API Key + Secret
            self.auth = (api_key, api_secret)
            self.headers = {
                'Content-Type': 'application/json'
            }
        else:
            # Access Token (header)
            self.auth = None
            self.headers = {
                'X-Shopify-Access-Token': self.access_token,
                'Content-Type': 'application/json'
            }
    
    def test_connection(self):
        """
        Teste la connexion à Shopify
        
        Returns:
            dict: {'success': bool, 'shop_name': str, 'error': str}
        """
        try:
            response = requests.get(
                f"{self.base_url}/shop.json",
                headers=self.headers,
                auth=self.auth,
                timeout=10
            )
            
            if response.status_code == 200:
                shop_data = response.json().get('shop', {})
                return {
                    'success': True,
                    'shop_name': shop_data.get('name', 'Unknown'),
                    'shop_domain': shop_data.get('domain', ''),
                    'error': None
                }
            elif response.status_code == 401:
                # Déterminer le mode d'auth utilisé pour un message plus clair
                if self.api_key and self.api_secret:
                    error_msg = 'Authentification échouée. Note: Shopify ne supporte plus API Key + Secret pour l\'Admin API. Utilisez plutôt l\'Access Token (shpat_...).'
                else:
                    error_msg = 'Access Token invalide ou expiré. Vérifiez que le token commence par "shpat_" et que l\'app est installée sur votre boutique.'
                return {
                    'success': False,
                    'shop_name': None,
                    'error': error_msg
                }
            elif response.status_code == 404:
                return {
                    'success': False,
                    'shop_name': None,
                    'error': 'Store non trouvé. Vérifiez l\'URL du store.'
                }
            else:
                return {
                    'success': False,
                    'shop_name': None,
                    'error': f'Erreur Shopify: {response.status_code} - {response.text}'
                }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'shop_name': None,
                'error': 'Timeout: Shopify ne répond pas'
            }
        except Exception as e:
            return {
                'success': False,
                'shop_name': None,
                'error': f'Erreur de connexion: {str(e)}'
            }
    
    def get_products(self, limit=250):
        """
        Récupère la liste des produits
        
        Args:
            limit: Nombre max de produits (max 250)
            
        Returns:
            list: Liste des produits
        """
        try:
            products = []
            url = f"{self.base_url}/products.json?limit={limit}"
            
            while url:
                response = requests.get(url, headers=self.headers, auth=self.auth, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                products.extend(data.get('products', []))
                
                # Pagination via Link header
                link_header = response.headers.get('Link', '')
                url = None
                if 'rel="next"' in link_header:
                    for link in link_header.split(','):
                        if 'rel="next"' in link:
                            url = link.split(';')[0].strip('<> ')
                            break
            
            return products
        except Exception as e:
            print(f"❌ Erreur récupération produits: {e}")
            return []
    
    def get_product_by_handle(self, handle):
        """
        Récupère un produit par son handle
        
        Args:
            handle: Handle du produit (slug URL)
            
        Returns:
            dict: Données du produit ou None
        """
        try:
            response = requests.get(
                f"{self.base_url}/products.json?handle={handle}",
                headers=self.headers,
                auth=self.auth,
                timeout=10
            )
            response.raise_for_status()
            
            products = response.json().get('products', [])
            return products[0] if products else None
        except Exception as e:
            print(f"❌ Erreur récupération produit {handle}: {e}")
            return None
    
    def get_product_images(self, product_id):
        """
        Récupère les images d'un produit
        
        Args:
            product_id: ID du produit Shopify
            
        Returns:
            list: Liste des images avec leurs URLs CDN
        """
        try:
            response = requests.get(
                f"{self.base_url}/products/{product_id}/images.json",
                headers=self.headers,
                auth=self.auth,
                timeout=10
            )
            response.raise_for_status()
            
            return response.json().get('images', [])
        except Exception as e:
            print(f"❌ Erreur récupération images produit {product_id}: {e}")
            return []
    
    def upload_image_to_product(self, product_id, image_data, filename="generated_image.png", position=None):
        """
        Upload une image vers un produit Shopify
        
        Args:
            product_id: ID du produit Shopify
            image_data: Bytes de l'image
            filename: Nom du fichier
            position: Position de l'image (1 = première)
            
        Returns:
            dict: {'success': bool, 'image_url': str, 'error': str}
        """
        try:
            # Encoder en base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            payload = {
                'image': {
                    'attachment': image_base64,
                    'filename': filename
                }
            }
            
            if position is not None:
                payload['image']['position'] = position
            
            response = requests.post(
                f"{self.base_url}/products/{product_id}/images.json",
                headers=self.headers,
                auth=self.auth,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            image_info = response.json().get('image', {})
            return {
                'success': True,
                'image_id': image_info.get('id'),
                'image_url': image_info.get('src'),
                'position': image_info.get('position'),
                'error': None
            }
        except requests.exceptions.HTTPError as e:
            error_msg = f"Erreur HTTP {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg = str(error_detail.get('errors', error_msg))
            except:
                pass
            return {
                'success': False,
                'image_url': None,
                'error': error_msg
            }
        except Exception as e:
            return {
                'success': False,
                'image_url': None,
                'error': str(e)
            }
    
    def delete_product_image(self, product_id, image_id):
        """
        Supprime une image d'un produit
        
        Args:
            product_id: ID du produit
            image_id: ID de l'image à supprimer
            
        Returns:
            bool: True si succès
        """
        try:
            response = requests.delete(
                f"{self.base_url}/products/{product_id}/images/{image_id}.json",
                headers=self.headers,
                auth=self.auth,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erreur suppression image {image_id}: {e}")
            return False
    
    def replace_product_images(self, product_id, new_images_data):
        """
        Remplace toutes les images d'un produit par de nouvelles
        
        Args:
            product_id: ID du produit
            new_images_data: Liste de bytes d'images
            
        Returns:
            dict: {'success': bool, 'new_urls': list, 'error': str}
        """
        try:
            # 1. Récupérer les anciennes images
            old_images = self.get_product_images(product_id)
            
            # 2. Supprimer les anciennes images
            for img in old_images:
                self.delete_product_image(product_id, img['id'])
            
            # 3. Uploader les nouvelles images
            new_urls = []
            for idx, img_data in enumerate(new_images_data):
                result = self.upload_image_to_product(
                    product_id, 
                    img_data, 
                    filename=f"ai_generated_{idx+1}.png",
                    position=idx + 1
                )
                if result['success']:
                    new_urls.append(result['image_url'])
                else:
                    print(f"⚠️ Erreur upload image {idx+1}: {result['error']}")
            
            return {
                'success': len(new_urls) > 0,
                'new_urls': new_urls,
                'uploaded_count': len(new_urls),
                'error': None if new_urls else 'Aucune image uploadée'
            }
        except Exception as e:
            return {
                'success': False,
                'new_urls': [],
                'error': str(e)
            }
    
    def download_image(self, image_url):
        """
        Télécharge une image depuis une URL CDN Shopify
        
        Args:
            image_url: URL de l'image
            
        Returns:
            bytes: Données de l'image ou None
        """
        try:
            # Optimiser l'URL pour une taille raisonnable
            clean_url = image_url.split('?')[0]
            if 'cdn.shopify.com' in clean_url:
                clean_url += '?width=1024'
            
            response = requests.get(clean_url, timeout=15)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"❌ Erreur téléchargement image: {e}")
            return None


def load_shopify_settings():
    """
    Charge les paramètres Shopify depuis settings.json
    """
    settings_file = os.path.abspath('settings.json')
    try:
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                return {
                    'store_url': settings.get('shopify_store_url', ''),
                    'access_token': settings.get('shopify_access_token', ''),
                    'api_key': settings.get('shopify_api_key', ''),
                    'api_secret': settings.get('shopify_api_secret', ''),
                    'connected': bool(settings.get('shopify_store_url') and (settings.get('shopify_access_token') or (settings.get('shopify_api_key') and settings.get('shopify_api_secret'))))
                }
    except Exception as e:
        print(f"⚠️ Erreur lecture settings Shopify: {e}")
    
    return {'store_url': '', 'access_token': '', 'api_key': '', 'api_secret': '', 'connected': False}


def save_shopify_settings(store_url, access_token=None, api_key=None, api_secret=None):
    """
    Sauvegarde les paramètres Shopify dans settings.json
    """
    settings_file = os.path.abspath('settings.json')
    try:
        settings = {}
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                content = f.read()
                if content.strip():
                    settings = json.loads(content)
        
        settings['shopify_store_url'] = store_url
        if access_token:
            settings['shopify_access_token'] = access_token
        if api_key:
            settings['shopify_api_key'] = api_key
        if api_secret:
            settings['shopify_api_secret'] = api_secret
        
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=4)
        
        return True
    except Exception as e:
        print(f"❌ Erreur sauvegarde settings Shopify: {e}")
        return False
