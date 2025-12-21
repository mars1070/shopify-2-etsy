from flask import Flask, request, jsonify, send_file, Response, stream_with_context, redirect
from flask_cors import CORS
import os
import secrets
import hmac
import hashlib
from urllib.parse import urlencode
from dotenv import load_dotenv
from converter import ShopifyToEtsyConverter
from gemini_enhancer import GeminiEnhancer
from shopify_client import ShopifyClient, load_shopify_settings, save_shopify_settings
from image_generator import ImageGenerator
import json
import pandas as pd

load_dotenv()

app = Flask(__name__)
CORS(app)

# Utiliser des chemins absolus basés sur le dossier parent (racine du projet)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')
OUTPUT_FOLDER = os.path.join(PROJECT_ROOT, 'outputs')
SETTINGS_FILE = os.path.join(PROJECT_ROOT, 'settings.json')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                content = f.read()
                if not content or content.strip() == '':
                    print("⚠️ Fichier settings.json vide, retour dict vide")
                    return {}
                return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"⚠️ Erreur JSON dans settings.json: {e}")
            print(f"   Contenu du fichier: {content[:100] if 'content' in locals() else 'N/A'}")
            return {}
        except Exception as e:
            print(f"⚠️ Erreur lecture settings.json: {e}")
            return {}
    print("ℹ️ Fichier settings.json n'existe pas encore")
    return {}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des paramètres: {e}")
        raise e

@app.route('/api/convert', methods=['POST'])
def convert():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        file = request.files['file']
        price_multiplier = float(request.form.get('price_multiplier', 2.5))
        category = request.form.get('category', '')
        product_type = request.form.get('product_type', 'physical')
        product_niche = request.form.get('product_niche', '')  # Niche obligatoire pour Gemini
        
        if file.filename == '':
            return jsonify({'error': 'Nom de fichier vide'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Le fichier doit être au format CSV'}), 400
        
        # Save uploaded file
        input_path = os.path.join(UPLOAD_FOLDER, 'shopify_input.csv')
        file.save(input_path)
        
        # Convert
        converter = ShopifyToEtsyConverter(price_multiplier)
        temp_output = os.path.join(OUTPUT_FOLDER, 'temp_etsy.csv')
        products_count = converter.convert(input_path, temp_output, category, product_type)
        
        return jsonify({
            'success': True,
            'temp_file': 'temp_etsy.csv',
            'products_count': products_count,
            'product_niche': product_niche
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/enhance', methods=['POST'])
def enhance():
    try:
        data = request.json
        temp_file = data.get('temp_file')
        product_niche = data.get('product_niche', '')  # Niche obligatoire pour Gemini
        
        if not temp_file:
            return jsonify({'error': 'Fichier temporaire manquant'}), 400
        
        settings = load_settings()
        api_key = settings.get('gemini_api_key') or os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            print("❌ ERREUR: Clé API Gemini manquante!")
            return jsonify({'error': '🔑 Clé API Gemini manquante! Allez dans Paramètres pour configurer votre clé API.'}), 400
        
        temp_path = os.path.join(OUTPUT_FOLDER, temp_file)
        output_path = os.path.join(OUTPUT_FOLDER, 'etsy_final.csv')
        
        # Tester l'initialisation de Gemini
        try:
            enhancer = GeminiEnhancer(api_key)
        except Exception as init_error:
            error_msg = str(init_error)
            print(f"❌ ERREUR initialisation Gemini: {error_msg}")
            
            # Détecter si c'est un problème de clé API
            if 'API' in error_msg or 'key' in error_msg.lower() or 'auth' in error_msg.lower():
                return jsonify({'error': '🔑 Clé API Gemini invalide ou manquante! Vérifiez votre clé dans Paramètres.'}), 400
            else:
                return jsonify({'error': f'Erreur initialisation Gemini: {error_msg}'}), 500
        
        def generate():
            try:
                for progress in enhancer.enhance_generator(temp_path, output_path, product_niche=product_niche):
                    yield f"data: {json.dumps(progress)}\n\n"
            except Exception as gen_error:
                error_msg = str(gen_error)
                print(f"❌ ERREUR génération: {error_msg}")
                
                # Détecter si c'est un problème de clé API pendant la génération
                if 'API' in error_msg or 'key' in error_msg.lower() or 'auth' in error_msg.lower() or 'quota' in error_msg.lower():
                    yield f"data: {json.dumps({'status': 'error', 'message': '🔑 Erreur API Gemini: Clé invalide ou quota dépassé'})}\n\n"
                else:
                    yield f"data: {json.dumps({'status': 'error', 'message': f'Erreur: {error_msg}'})}\n\n"
                
        return Response(stream_with_context(generate()), mimetype='text/event-stream')
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ ERREUR globale: {error_msg}")
        
        # Détecter si c'est un problème de clé API
        if 'API' in error_msg or 'key' in error_msg.lower() or 'auth' in error_msg.lower():
            return jsonify({'error': '🔑 Clé API Gemini invalide! Vérifiez votre clé dans Paramètres.'}), 400
        else:
            return jsonify({'error': f'Erreur serveur: {error_msg}'}), 500

@app.route('/api/preview/<filename>', methods=['GET'])
def preview_csv(filename):
    try:
        # Prevent directory traversal
        safe_name = os.path.basename(filename)
        file_path = os.path.join(OUTPUT_FOLDER, safe_name)

        if not os.path.exists(file_path):
            return jsonify({'error': 'Fichier non trouvé'}), 404

        # Lire quelques lignes pour l'aperçu (augmenté à 50)
        df = pd.read_csv(file_path)
        
        # Renvoyer toutes les colonnes disponibles
        available_columns = df.columns.tolist()

        if not available_columns:
            return jsonify({'columns': [], 'rows': [], 'filename': safe_name})

        preview_rows = df.head(50).fillna('').to_dict(orient='records')

        return jsonify({
            'columns': available_columns,
            'rows': preview_rows,
            'filename': safe_name
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<filename>', methods=['GET'])
def download(filename):
    try:
        print(f"📥 Demande de téléchargement pour: {filename}")
        
        # Prevent directory traversal
        safe_name = os.path.basename(filename)
        print(f"🔒 Nom sécurisé: {safe_name}")
        
        # Use same path as preview_csv for consistency
        file_path = os.path.join(OUTPUT_FOLDER, safe_name)
        print(f"📂 Chemin complet: {file_path}")
        print(f"📁 OUTPUT_FOLDER: {os.path.abspath(OUTPUT_FOLDER)}")
        
        if not os.path.exists(file_path):
            print(f"❌ Fichier non trouvé: {file_path}")
            return jsonify({'error': f'Fichier non trouvé: {file_path}'}), 404
        
        print(f"✅ Fichier trouvé, envoi en cours...")
        return send_file(file_path, as_attachment=True, download_name='etsy_products.csv')
    
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET'])
def get_settings():
    print(f"GET /api/settings called. Using file: {SETTINGS_FILE}")
    try:
        settings = load_settings()
        print(f"✅ Settings loaded successfully")
        print(f"   Has API key: {bool(settings.get('gemini_api_key'))}")
        
        # Vérifier connexion Shopify
        shopify_connected = bool(settings.get('shopify_store_url') and settings.get('shopify_access_token'))
        
        return jsonify({
            'has_api_key': bool(settings.get('gemini_api_key')),
            'shopify_connected': shopify_connected,
            'shopify_store_url': settings.get('shopify_store_url', ''),
            'shopify_shop_name': settings.get('shopify_shop_name', '')
        })
    except Exception as e:
        print(f"❌ Error in GET /api/settings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'has_api_key': False,
            'shopify_connected': False
        })

@app.route('/api/settings', methods=['POST'])
def save_settings_route():
    print(f"POST /api/settings called. Using file: {SETTINGS_FILE}")
    try:
        data = request.json
        print(f"Reçu données settings: {data}") # Debug log
        
        if not data:
            print("Erreur: Aucune donnée reçue")
            return jsonify({'error': 'Aucune donnée reçue'}), 400
        
        api_key = data.get('gemini_api_key')
        
        if not api_key:
            print("Erreur: Clé API manquante dans la requête")
            return jsonify({'error': 'Clé API manquante'}), 400
        
        # Vérifier la longueur minimale de la clé
        if len(api_key) < 30:
            print("Erreur: Clé API trop courte")
            return jsonify({'error': 'Clé API invalide (trop courte)'}), 400
        
        # 🔍 VALIDATION: Tester la clé avec Gemini
        print("🔍 Validation de la clé API avec Gemini...")
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Test avec Gemini 2.5 Flash
            print("   Tentative de connexion à Gemini 2.5 Flash...")
            model = genai.GenerativeModel('gemini-2.5-flash')
            test_response = model.generate_content("Hello", generation_config={'max_output_tokens': 10})
            
            # Si on arrive ici, la clé est valide
            print("✅ Clé API validée avec succès!")
            # Pas besoin de lire la réponse, juste vérifier qu'il n'y a pas d'erreur
            if test_response:
                print("   Test de connexion réussi!")
            
        except Exception as validation_error:
            error_msg = str(validation_error)
            print(f"❌ Validation échouée: {error_msg}")
            print(f"   Type d'erreur: {type(validation_error).__name__}")
            
            # Messages d'erreur personnalisés
            if 'API_KEY_INVALID' in error_msg or 'invalid' in error_msg.lower():
                return jsonify({'error': '🔑 Clé API invalide. Vérifiez votre clé sur Google AI Studio (https://aistudio.google.com/app/apikey)'}), 400
            elif 'quota' in error_msg.lower() or 'RESOURCE_EXHAUSTED' in error_msg:
                return jsonify({'error': '📊 Quota API dépassé. Attendez ou augmentez votre quota sur Google AI.'}), 400
            elif 'permission' in error_msg.lower() or 'PERMISSION_DENIED' in error_msg:
                return jsonify({'error': '🚫 Permission refusée. Activez l\'API Gemini sur votre compte Google Cloud.'}), 400
            elif 'not found' in error_msg.lower() or '404' in error_msg:
                return jsonify({'error': '❌ Modèle Gemini 2.5 Flash non trouvé. Vérifiez que votre clé a accès à ce modèle.'}), 400
            else:
                return jsonify({'error': f'⚠️ Erreur validation: {error_msg[:200]}'}), 400
        
        # Vérifier que le fichier settings.json existe, sinon le créer
        if not os.path.exists(SETTINGS_FILE):
            print(f"Création du fichier {SETTINGS_FILE}")
            with open(SETTINGS_FILE, 'w') as f:
                json.dump({}, f)
        
        settings = load_settings()
        settings['gemini_api_key'] = api_key
        save_settings(settings)
        print(f"✅ Paramètres sauvegardés avec succès dans {SETTINGS_FILE}")
        
        return jsonify({'success': True, 'message': 'Clé API validée et enregistrée avec succès!'})
    
    except Exception as e:
        print(f"❌ Erreur dans save_settings_route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500

# ==================== SHOPIFY OAUTH ENDPOINTS ====================

# Variable globale pour stocker le state OAuth temporairement
oauth_states = {}

@app.route('/api/shopify/oauth/start', methods=['POST'])
def shopify_oauth_start():
    """
    Démarre le flux OAuth Shopify.
    Retourne l'URL d'autorisation vers laquelle rediriger l'utilisateur.
    """
    try:
        data = request.json
        store_url = data.get('store_url', '').strip()
        client_id = data.get('client_id', '').strip()
        client_secret = data.get('client_secret', '').strip()
        
        if not store_url:
            return jsonify({'error': 'URL de la boutique manquante'}), 400
        if not client_id:
            return jsonify({'error': 'Client ID manquant'}), 400
        if not client_secret:
            return jsonify({'error': 'API Secret manquant'}), 400
        
        # Nettoyer l'URL du store
        clean_url = store_url.replace('https://', '').replace('http://', '').rstrip('/')
        if '.myshopify.com' not in clean_url and '.' not in clean_url:
            clean_url = f"{clean_url}.myshopify.com"
        
        # Générer un state unique pour la sécurité
        state = secrets.token_urlsafe(32)
        
        # Sauvegarder temporairement les credentials et le state
        oauth_states[state] = {
            'store_url': clean_url,
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        # Construire l'URL d'autorisation Shopify
        redirect_uri = 'http://localhost:3000/auth/callback'
        # TOUS les scopes utiles pour l'app
        scopes = ','.join([
            # Produits & Collections
            'read_products',
            'write_products',
            # Fichiers & Images
            'read_files',
            'write_files',
            # Inventaire
            'read_inventory',
            'write_inventory',
            # Commandes
            'read_orders',
            'write_orders',
            # Clients
            'read_customers',
            'write_customers',
            # Contenu (pages, blogs)
            'read_content',
            'write_content',
            # Thèmes
            'read_themes',
            'write_themes',
            # Localisations
            'read_locales',
            'write_locales',
            # Locations/Entrepôts
            'read_locations',
            # Prix & Réductions
            'read_price_rules',
            'write_price_rules',
            'read_discounts',
            'write_discounts',
            # Metafields
            'read_metaobjects',
            'write_metaobjects',
            # Shipping
            'read_shipping',
            'write_shipping',
            # Fulfillment
            'read_fulfillments',
            'write_fulfillments',
        ])
        
        auth_url = f"https://{clean_url}/admin/oauth/authorize?" + urlencode({
            'client_id': client_id,
            'scope': scopes,
            'redirect_uri': redirect_uri,
            'state': state
        })
        
        print(f"🔗 OAuth démarré pour: {clean_url}")
        print(f"   Auth URL: {auth_url}")
        
        return jsonify({
            'success': True,
            'auth_url': auth_url,
            'state': state
        })
        
    except Exception as e:
        print(f"❌ Erreur oauth_start: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/shopify/oauth/callback', methods=['POST'])
def shopify_oauth_callback():
    """
    Traite le callback OAuth après autorisation.
    Échange le code contre un access_token.
    """
    try:
        data = request.json
        code = data.get('code', '').strip()
        state = data.get('state', '').strip()
        shop = data.get('shop', '').strip()
        
        if not code:
            return jsonify({'error': 'Code d\'autorisation manquant'}), 400
        if not state:
            return jsonify({'error': 'State manquant'}), 400
        
        # Vérifier que le state existe et récupérer les credentials
        if state not in oauth_states:
            return jsonify({'error': 'State invalide ou expiré. Recommencez le processus.'}), 400
        
        oauth_data = oauth_states.pop(state)  # Récupérer et supprimer
        store_url = oauth_data['store_url']
        client_id = oauth_data['client_id']
        client_secret = oauth_data['client_secret']
        
        print(f"🔄 Échange du code OAuth pour: {store_url}")
        
        # Échanger le code contre un access_token
        import requests
        token_url = f"https://{store_url}/admin/oauth/access_token"
        
        response = requests.post(token_url, data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code
        }, headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }, timeout=30)
        
        if response.status_code != 200:
            error_msg = f"Erreur Shopify: {response.status_code}"
            try:
                error_data = response.json()
                error_msg = error_data.get('error_description', error_data.get('error', error_msg))
            except:
                error_msg = response.text[:200]
            print(f"❌ Erreur échange token: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        token_data = response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            return jsonify({'error': 'Access token non reçu de Shopify'}), 400
        
        print(f"✅ Access token obtenu pour: {store_url}")
        
        # Tester la connexion avec le nouveau token
        client = ShopifyClient(store_url, access_token=access_token)
        result = client.test_connection()
        
        if result['success']:
            # Sauvegarder les credentials
            settings = load_settings()
            settings['shopify_store_url'] = store_url
            settings['shopify_access_token'] = access_token
            settings['shopify_api_key'] = client_id
            settings['shopify_api_secret'] = client_secret
            settings['shopify_shop_name'] = result['shop_name']
            save_settings(settings)
            
            print(f"✅ Connecté à Shopify via OAuth: {result['shop_name']}")
            return jsonify({
                'success': True,
                'shop_name': result['shop_name'],
                'shop_domain': result.get('shop_domain', ''),
                'auth_mode': 'OAuth'
            })
        else:
            print(f"❌ Token obtenu mais connexion échouée: {result['error']}")
            return jsonify({'error': result['error']}), 400
        
    except Exception as e:
        print(f"❌ Erreur oauth_callback: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== SHOPIFY DIRECT ENDPOINTS ====================

@app.route('/api/shopify/connect', methods=['POST'])
def shopify_connect():
    """Connecte et valide les credentials Shopify (Access Token OU API Key + Secret)"""
    try:
        data = request.json
        store_url = data.get('store_url', '').strip()
        access_token = data.get('access_token', '').strip()
        api_key = data.get('api_key', '').strip()
        api_secret = data.get('api_secret', '').strip()
        
        if not store_url:
            return jsonify({'error': 'URL de la boutique manquante'}), 400
        
        # Vérifier qu'on a soit access_token, soit api_key+api_secret
        has_access_token = bool(access_token)
        has_api_credentials = bool(api_key and api_secret)
        
        if not has_access_token and not has_api_credentials:
            return jsonify({'error': 'Fournissez soit un Access Token, soit API Key + API Secret'}), 400
        
        # Valider le format de l'URL
        clean_url = store_url.replace('https://', '').replace('http://', '').rstrip('/')
        if '.myshopify.com' not in clean_url and '.' not in clean_url:
            clean_url = f"{clean_url}.myshopify.com"
        
        # Vérifier que l'URL ressemble à une URL Shopify valide
        if not clean_url.endswith('.myshopify.com') and 'shopify' not in clean_url.lower():
            return jsonify({'error': f'URL invalide. Utilisez le format: votre-boutique.myshopify.com (reçu: {store_url})'}), 400
        
        # Tester la connexion avec le mode approprié
        if has_api_credentials:
            print(f"🔗 Test connexion Shopify (API Key + Secret): {store_url}")
            client = ShopifyClient(store_url, api_key=api_key, api_secret=api_secret)
        else:
            print(f"🔗 Test connexion Shopify (Access Token): {store_url}")
            client = ShopifyClient(store_url, access_token=access_token)
        
        result = client.test_connection()
        
        if result['success']:
            # Sauvegarder les credentials
            settings = load_settings()
            settings['shopify_store_url'] = store_url
            if has_api_credentials:
                settings['shopify_api_key'] = api_key
                settings['shopify_api_secret'] = api_secret
                settings.pop('shopify_access_token', None)  # Supprimer l'ancien si présent
            else:
                settings['shopify_access_token'] = access_token
                settings.pop('shopify_api_key', None)
                settings.pop('shopify_api_secret', None)
            settings['shopify_shop_name'] = result['shop_name']
            save_settings(settings)
            
            auth_mode = 'API Key + Secret' if has_api_credentials else 'Access Token'
            print(f"✅ Connecté à Shopify ({auth_mode}): {result['shop_name']}")
            return jsonify({
                'success': True,
                'shop_name': result['shop_name'],
                'shop_domain': result.get('shop_domain', ''),
                'auth_mode': auth_mode
            })
        else:
            print(f"❌ Échec connexion Shopify: {result['error']}")
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        print(f"❌ Erreur shopify_connect: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/shopify/disconnect', methods=['POST'])
def shopify_disconnect():
    """Déconnecte Shopify"""
    try:
        settings = load_settings()
        settings.pop('shopify_store_url', None)
        settings.pop('shopify_access_token', None)
        settings.pop('shopify_api_key', None)
        settings.pop('shopify_api_secret', None)
        settings.pop('shopify_shop_name', None)
        save_settings(settings)
        
        print("🔌 Déconnecté de Shopify")
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/shopify/products', methods=['GET'])
def shopify_get_products():
    """Récupère la liste des produits Shopify"""
    try:
        settings = load_settings()
        store_url = settings.get('shopify_store_url')
        access_token = settings.get('shopify_access_token')
        
        print(f"📦 GET /api/shopify/products")
        print(f"   Store URL: {store_url}")
        print(f"   Access Token: {access_token[:20] if access_token else 'NONE'}...")
        
        if not store_url:
            return jsonify({'error': 'Shopify non connecté'}), 400
        
        if not access_token:
            return jsonify({'error': 'Access Token manquant - Reconnectez Shopify'}), 400
        
        # Créer le client avec l'Access Token
        client = ShopifyClient(store_url, access_token=access_token)
        
        # D'abord tester la connexion
        test_result = client.test_connection()
        print(f"   Test connexion: {test_result}")
        
        if not test_result['success']:
            return jsonify({
                'success': False,
                'error': test_result['error'],
                'products': [],
                'count': 0
            })
        
        # Récupérer les produits
        products = client.get_products(limit=250)
        print(f"   ✅ {len(products)} produits récupérés")
        
        return jsonify({
            'success': True,
            'products': products,
            'count': len(products)
        })
    except Exception as e:
        print(f"❌ Erreur shopify_get_products: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== IMAGE GENERATION ENDPOINTS ====================

@app.route('/api/generate-images', methods=['POST'])
def generate_images():
    """
    Génère des variations d'images pour les produits avec Gemini 2.5 Flash Image
    Streaming endpoint pour afficher la progression
    """
    try:
        data = request.json
        temp_file = data.get('temp_file')
        num_images = int(data.get('num_images', 10))
        
        if not temp_file:
            return jsonify({'error': 'Fichier temporaire manquant'}), 400
        
        # Charger les settings
        settings = load_settings()
        gemini_api_key = settings.get('gemini_api_key')
        store_url = settings.get('shopify_store_url')
        access_token = settings.get('shopify_access_token')
        
        if not gemini_api_key:
            return jsonify({'error': '🔑 Clé API Gemini manquante! Configurez-la dans Paramètres.'}), 400
        
        if not store_url or not access_token:
            return jsonify({'error': '🛒 Shopify non connecté! Connectez votre boutique dans Paramètres.'}), 400
        
        temp_path = os.path.join(OUTPUT_FOLDER, temp_file)
        if not os.path.exists(temp_path):
            return jsonify({'error': 'Fichier CSV temporaire non trouvé'}), 404
        
        # Initialiser les clients
        shopify_client = ShopifyClient(store_url, access_token)
        image_generator = ImageGenerator(gemini_api_key)
        
        def generate():
            try:
                df = pd.read_csv(temp_path)
                
                # Identifier les produits avec images (Photo 1)
                products_with_images = df[df['Photo 1'].notna() & (df['Photo 1'] != '')].copy()
                total_products = len(products_with_images)
                
                if total_products == 0:
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Aucun produit avec image trouvé'})}\n\n"
                    return
                
                yield f"data: {json.dumps({'status': 'starting', 'message': f'🚀 Démarrage génération pour {total_products} produits', 'total': total_products})}\n\n"
                
                processed = 0
                for idx, row in products_with_images.iterrows():
                    processed += 1
                    source_url = row['Photo 1']
                    sku = row.get('SKU', f'Produit-{processed}')
                    
                    yield f"data: {json.dumps({'status': 'processing', 'message': f'🖼️ Traitement {sku} ({processed}/{total_products})', 'progress': int((processed-1)/total_products*100)})}\n\n"
                    
                    # Générer les variations
                    generated_urls = []
                    for progress in image_generator.generate_product_variations(source_url, num_images):
                        if progress['status'] == 'generated' and 'image_data' in progress:
                            # Pour l'instant, on stocke les images localement
                            # TODO: Upload vers Shopify quand on aura le product_id
                            pass
                        
                        if progress['status'] in ['generating', 'generated', 'warning']:
                            yield f"data: {json.dumps({'status': 'generating', 'message': progress['message'], 'progress': int((processed-1)/total_products*100 + progress.get('progress', 0)/total_products)})}\n\n"
                        
                        if progress['status'] == 'complete':
                            generated_urls = progress.get('new_urls', [])
                            
                            # Mettre à jour le CSV avec les nouvelles URLs
                            if generated_urls:
                                for i, url in enumerate(generated_urls[:10]):
                                    col_name = f'Photo {i+1}'
                                    if col_name in df.columns:
                                        df.loc[idx, col_name] = url
                            
                            yield f"data: {json.dumps({'status': 'product_done', 'message': f'✅ {sku}: {len(generated_urls)} images générées', 'progress': int(processed/total_products*100)})}\n\n"
                        
                        if progress['status'] == 'error':
                            error_msg = progress.get('message', 'Erreur inconnue')
                            yield f"data: {json.dumps({'status': 'warning', 'message': f'⚠️ {sku}: {error_msg}'})}\\n\\n"
                            break
                
                # Sauvegarder le CSV mis à jour
                df.to_csv(temp_path, index=False)
                
                yield f"data: {json.dumps({'status': 'complete', 'message': f'✅ Génération terminée pour {total_products} produits', 'progress': 100})}\n\n"
                
            except Exception as e:
                print(f"❌ Erreur génération images: {e}")
                import traceback
                traceback.print_exc()
                yield f"data: {json.dumps({'status': 'error', 'message': f'Erreur: {str(e)}'})}\n\n"
        
        return Response(stream_with_context(generate()), mimetype='text/event-stream')
        
    except Exception as e:
        print(f"❌ Erreur generate_images: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-images-product', methods=['POST'])
def generate_images_for_product():
    """
    Génère des variations d'images pour UN produit Shopify spécifique.
    Utilisé par la page Images AI.
    """
    try:
        data = request.json
        product_id = data.get('product_id')
        source_image_url = data.get('source_image_url')
        num_variations = int(data.get('num_variations', 10))
        
        if not product_id:
            return jsonify({'error': 'ID produit manquant'}), 400
        if not source_image_url:
            return jsonify({'error': 'URL image source manquante'}), 400
        
        # Charger les settings
        settings = load_settings()
        gemini_api_key = settings.get('gemini_api_key')
        store_url = settings.get('shopify_store_url')
        access_token = settings.get('shopify_access_token')
        api_key = settings.get('shopify_api_key')
        api_secret = settings.get('shopify_api_secret')
        
        if not gemini_api_key:
            return jsonify({'error': '🔑 Clé API Gemini manquante! Configurez-la dans Paramètres.'}), 400
        
        if not store_url:
            return jsonify({'error': '🛒 Shopify non connecté!'}), 400
        
        # Initialiser le client Shopify avec le bon mode d'auth
        if api_key and api_secret and access_token:
            shopify_client = ShopifyClient(store_url, access_token=access_token)
        elif access_token:
            shopify_client = ShopifyClient(store_url, access_token=access_token)
        else:
            return jsonify({'error': '🛒 Credentials Shopify manquants!'}), 400
        
        # Initialiser le générateur d'images
        image_generator = ImageGenerator(gemini_api_key)
        
        print(f"🖼️ Génération de {num_variations} images pour produit {product_id}")
        print(f"   Source: {source_image_url[:80]}...")
        
        # Générer les images et les uploader sur Shopify
        generated_images = []
        generated_urls = []
        
        for progress in image_generator.generate_product_variations(source_image_url, num_variations):
            if progress['status'] == 'generated' and 'image_data' in progress:
                generated_images.append(progress['image_data'])
                print(f"   ✅ Variation {progress['variation']} générée")
            
            if progress['status'] == 'error':
                return jsonify({
                    'success': False,
                    'error': progress.get('message', 'Erreur génération')
                }), 400
            
            if progress['status'] == 'complete':
                print(f"   📊 {len(generated_images)} images générées au total")
        
        if not generated_images:
            return jsonify({
                'success': False,
                'error': 'Aucune image générée'
            }), 400
        
        # Uploader les images sur Shopify
        print(f"📤 Upload de {len(generated_images)} images vers Shopify...")
        
        upload_result = shopify_client.replace_product_images(product_id, generated_images)
        
        if upload_result['success']:
            print(f"✅ {upload_result['uploaded_count']} images uploadées sur Shopify")
            return jsonify({
                'success': True,
                'total_generated': len(generated_images),
                'uploaded_count': upload_result['uploaded_count'],
                'new_urls': upload_result['new_urls']
            })
        else:
            print(f"❌ Erreur upload: {upload_result['error']}")
            return jsonify({
                'success': False,
                'error': f"Erreur upload Shopify: {upload_result['error']}",
                'total_generated': len(generated_images)
            }), 400
        
    except Exception as e:
        print(f"❌ Erreur generate_images_for_product: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def sse_log(log_type, emoji, message, color='white', progress=None, **extra):
    """Helper pour créer un message SSE formaté"""
    data = {'type': log_type, 'emoji': emoji, 'message': message, 'color': color}
    if progress is not None:
        data['progress'] = progress
    data.update(extra)
    return 'data: ' + json.dumps(data) + '\n\n'


@app.route('/api/shopify/products/<product_id>/images/<image_id>', methods=['DELETE'])
def delete_product_image(product_id, image_id):
    """
    Supprime une image spécifique d'un produit Shopify
    Endpoint: DELETE /admin/api/2023-10/products/{product_id}/images/{image_id}.json
    """
    try:
        # Charger les settings Shopify
        settings = load_settings()
        store_url = settings.get('shopify_store_url')
        access_token = settings.get('shopify_access_token')
        api_key = settings.get('shopify_api_key')
        api_secret = settings.get('shopify_api_secret')
        
        if not store_url:
            return jsonify({'error': '🛒 Shopify non connecté!'}), 400
        
        # Initialiser le client Shopify avec le bon mode d'auth
        if access_token:
            shopify_client = ShopifyClient(store_url, access_token=access_token)
        elif api_key and api_secret:
            shopify_client = ShopifyClient(store_url, api_key=api_key, api_secret=api_secret)
        else:
            return jsonify({'error': '🛒 Credentials Shopify manquants!'}), 400
        
        print(f"🗑️ Suppression de l'image {image_id} du produit {product_id}")
        
        # Utiliser l'endpoint DELETE de l'API Shopify
        import requests
        
        # Construire l'URL de l'API
        api_version = "2023-10"
        delete_url = f"https://{store_url}/admin/api/{api_version}/products/{product_id}/images/{image_id}.json"
        
        # Préparer les headers
        headers = {
            'Content-Type': 'application/json',
            'X-Shopify-Access-Token': access_token if access_token else ''
        }
        
        # Faire la requête DELETE
        response = requests.delete(delete_url, headers=headers, timeout=30)
        
        if response.status_code == 200 or response.status_code == 204:
            print(f"✅ Image {image_id} supprimée avec succès")
            return jsonify({
                'success': True,
                'message': 'Image supprimée avec succès'
            })
        else:
            # Gérer les erreurs
            error_msg = f"Erreur Shopify: {response.status_code}"
            try:
                error_data = response.json()
                error_msg = error_data.get('error', error_data.get('errors', error_msg))
            except:
                if response.text:
                    error_msg = response.text[:200]
            
            print(f"❌ Erreur suppression image: {error_msg}")
            return jsonify({'error': error_msg}), 400
            
    except Exception as e:
        print(f"❌ Erreur delete_product_image: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500




@app.route('/api/generate-images-stream', methods=['POST'])
def generate_images_stream():
    """
    Génère des images avec streaming des logs en temps réel.
    Utilise Server-Sent Events (SSE) pour envoyer les logs au frontend.
    """
    data = request.json
    product_id = data.get('product_id')
    product_title = data.get('product_title', 'Produit')
    source_image_url = data.get('source_image_url')
    num_variations = int(data.get('num_variations', 10))
    
    if not product_id:
        return jsonify({'error': 'ID produit manquant'}), 400
    if not source_image_url:
        return jsonify({'error': 'URL image source manquante'}), 400
    
    # Charger les settings
    settings = load_settings()
    gemini_api_key = settings.get('gemini_api_key')
    store_url = settings.get('shopify_store_url')
    access_token = settings.get('shopify_access_token')
    
    if not gemini_api_key:
        return jsonify({'error': 'Clé API Gemini manquante'}), 400
    if not store_url or not access_token:
        return jsonify({'error': 'Shopify non connecté'}), 400
    
    def generate_with_logs():
        import time as time_module
        from PIL import Image as PILImage
        from io import BytesIO
        
        # 🚀 DÉMARRAGE
        yield sse_log('info', '🚀', 'Démarrage génération pour: ' + product_title, 'cyan')
        yield sse_log('info', '📦', 'Product ID: ' + str(product_id), 'gray')
        yield sse_log('info', '🎯', 'Variations demandées: ' + str(num_variations), 'gray')
        
        # 🔑 INITIALISATION GEMINI
        yield sse_log('step', '🔑', 'Initialisation Gemini 2.5 Flash Image (Nano Banana)...', 'yellow')
        
        try:
            image_generator = ImageGenerator(gemini_api_key)
            yield sse_log('success', '✅', 'Gemini initialisé avec succès', 'green')
        except Exception as e:
            yield sse_log('error', '❌', 'Erreur init Gemini: ' + str(e), 'red')
            yield sse_log('done', '🛑', 'Arrêt', success=False, error=str(e))
            return
        
        # 🛒 INITIALISATION SHOPIFY
        yield sse_log('step', '🛒', 'Connexion à Shopify: ' + store_url, 'yellow')
        
        try:
            shopify_client = ShopifyClient(store_url, access_token=access_token)
            yield sse_log('success', '✅', 'Shopify connecté', 'green')
        except Exception as e:
            yield sse_log('error', '❌', 'Erreur Shopify: ' + str(e), 'red')
            yield sse_log('done', '🛑', 'Arrêt', success=False, error=str(e))
            return
        
        # 📥 TÉLÉCHARGEMENT IMAGE SOURCE
        yield sse_log('step', '📥', 'Téléchargement image source depuis CDN Shopify...', 'yellow')
        yield sse_log('info', '🔗', 'URL: ' + source_image_url[:80] + '...', 'gray')
        
        source_bytes = image_generator.download_image_from_url(source_image_url)
        
        if not source_bytes:
            yield sse_log('error', '❌', "Impossible de télécharger l'image source", 'red')
            yield sse_log('done', '🛑', 'Arrêt', success=False, error='Download failed')
            return
        
        size_kb = len(source_bytes) / 1024
        yield sse_log('success', '✅', 'Image téléchargée: ' + str(round(size_kb, 1)) + ' KB', 'green')
        
        # 🖼️ CONVERSION EN PIL IMAGE
        yield sse_log('step', '🖼️', 'Conversion en PIL Image pour Gemini...', 'yellow')
        
        source_pil = PILImage.open(BytesIO(source_bytes))
        yield sse_log('success', '✅', 'Image convertie: ' + str(source_pil.size[0]) + 'x' + str(source_pil.size[1]) + ' pixels', 'green')
        
        # 🔍 ÉTAPE 1: ANALYSE IA ET GÉNÉRATION DES PROMPTS
        yield sse_log('step', '🔍', 'Étape 1/2: Gemini analyse le produit et crée les prompts personnalisés...', 'magenta')
        
        custom_prompts = image_generator.analyze_and_generate_prompts(source_bytes, num_variations)
        
        if not custom_prompts:
            yield sse_log('error', '❌', 'Échec de la génération des prompts par Gemini', 'red')
            yield sse_log('done', '🛑', 'Arrêt', success=False, error='Prompt generation failed')
            return
        
        yield sse_log('success', '✅', str(len(custom_prompts)) + ' prompts personnalisés créés par l\'IA', 'green')
        
        # Afficher les prompts générés
        for i, prompt in enumerate(custom_prompts, 1):
            short_prompt = prompt[:100] + '...' if len(prompt) > 100 else prompt
            yield sse_log('info', '📝', 'Prompt ' + str(i) + ': ' + short_prompt, 'gray')
        
        # 🎨 ÉTAPE 2: GÉNÉRATION DES IMAGES
        yield sse_log('step', '🎨', 'Étape 2/2: Génération de ' + str(len(custom_prompts)) + ' images avec les prompts IA...', 'magenta')
        
        generated_images = []
        
        for idx, prompt in enumerate(custom_prompts):
            variation_num = idx + 1
            progress_pct = int((idx / len(custom_prompts)) * 100)
            
            yield sse_log('generating', '🔄', '[' + str(variation_num) + '/' + str(len(custom_prompts)) + '] Génération image...', 'cyan', progress=progress_pct)
            yield sse_log('info', '🤖', 'Envoi à Gemini 2.5 Flash Image...', 'gray')
            
            # Générer l'image avec retry automatique
            image_data = None
            max_retries = 2
            for attempt in range(max_retries + 1):
                image_data = image_generator.generate_product_variation(source_bytes, prompt, variation_num)
                if image_data:
                    break
                if attempt < max_retries:
                    yield sse_log('warning', '🔄', 'Retry ' + str(attempt + 1) + '/' + str(max_retries) + '...', 'orange')
                    time_module.sleep(1)
            
            if image_data:
                generated_images.append(image_data)
                img_size_kb = len(image_data) / 1024
                progress_done = int(((idx + 1) / len(custom_prompts)) * 100)
                yield sse_log('success', '✅', '[' + str(variation_num) + '/' + str(len(custom_prompts)) + '] Image générée (' + str(round(img_size_kb, 1)) + ' KB)', 'green', progress=progress_done)
            else:
                yield sse_log('warning', '⚠️', '[' + str(variation_num) + '/' + str(len(custom_prompts)) + '] Image échouée après ' + str(max_retries) + ' retries', 'orange')
            
            # Pause entre les requêtes
            if idx < len(custom_prompts) - 1:
                yield sse_log('info', '⏳', 'Pause 1s...', 'gray')
                time_module.sleep(1)
        
        yield sse_log('step', '📊', 'Génération terminée: ' + str(len(generated_images)) + '/' + str(len(custom_prompts)) + ' images créées', 'cyan')
        
        if not generated_images:
            yield sse_log('error', '❌', 'Aucune image générée', 'red')
            yield sse_log('done', '🛑', 'Arrêt', success=False, error='No images generated')
            return
        
        # 📤 UPLOAD VERS SHOPIFY
        yield sse_log('step', '📤', 'Upload de ' + str(len(generated_images)) + ' images vers Shopify CDN...', 'yellow')
        
        for i in range(len(generated_images)):
            yield sse_log('info', '⬆️', 'Upload image ' + str(i+1) + '/' + str(len(generated_images)) + '...', 'gray')
        
        upload_result = shopify_client.replace_product_images(product_id, generated_images)
        
        if upload_result['success']:
            yield sse_log('success', '✅', str(upload_result['uploaded_count']) + ' images uploadées sur Shopify', 'green')
            yield sse_log('success', '🎉', 'GÉNÉRATION TERMINÉE AVEC SUCCÈS!', 'green')
            yield sse_log('done', '🏁', 'Terminé', success=True, total_generated=len(generated_images), uploaded_count=upload_result['uploaded_count'], new_urls=upload_result.get('new_urls', []))
        else:
            yield sse_log('error', '❌', 'Erreur upload: ' + str(upload_result.get('error', 'Unknown')), 'red')
            yield sse_log('done', '🛑', 'Arrêt', success=False, error=upload_result.get('error', 'Upload failed'), total_generated=len(generated_images))
    
    return Response(stream_with_context(generate_with_logs()), mimetype='text/event-stream')


@app.route('/api/generate-images-add', methods=['POST'])
def generate_images_add():
    """
    Génère des images supplémentaires SANS supprimer les existantes.
    Utilise Server-Sent Events (SSE) pour envoyer les logs au frontend.
    """
    data = request.json
    product_id = data.get('product_id')
    product_title = data.get('product_title', 'Produit')
    source_image_url = data.get('source_image_url')
    num_variations = int(data.get('num_variations', 5))

    if not product_id:
        return jsonify({'error': 'ID produit manquant'}), 400
    if not source_image_url:
        return jsonify({'error': 'URL image source manquante'}), 400

    settings = load_settings()
    gemini_api_key = settings.get('gemini_api_key')
    store_url = settings.get('shopify_store_url')
    access_token = settings.get('shopify_access_token')

    if not gemini_api_key:
        return jsonify({'error': 'Clé API Gemini manquante'}), 400
    if not store_url or not access_token:
        return jsonify({'error': 'Shopify non connecté'}), 400

    def generate_with_logs():
        import time as time_module
        from PIL import Image as PILImage
        from io import BytesIO

        yield sse_log('info', '➕', 'Ajout de ' + str(num_variations) + ' images pour: ' + product_title, 'cyan')

        try:
            image_generator = ImageGenerator(gemini_api_key)
            yield sse_log('success', '✅', 'Gemini initialisé', 'green')
        except Exception as e:
            yield sse_log('error', '❌', 'Erreur Gemini: ' + str(e), 'red')
            yield sse_log('done', '🛑', 'Arrêt', success=False, error=str(e))
            return

        try:
            shopify_client = ShopifyClient(store_url, access_token=access_token)
            yield sse_log('success', '✅', 'Shopify connecté', 'green')
        except Exception as e:
            yield sse_log('error', '❌', 'Erreur Shopify: ' + str(e), 'red')
            yield sse_log('done', '🛑', 'Arrêt', success=False, error=str(e))
            return

        yield sse_log('step', '📥', 'Téléchargement image source...', 'yellow')
        source_bytes = image_generator.download_image_from_url(source_image_url)

        if not source_bytes:
            yield sse_log('error', '❌', 'Impossible de télécharger l\'image', 'red')
            yield sse_log('done', '🛑', 'Arrêt', success=False, error='Download failed')
            return

        yield sse_log('success', '✅', 'Image téléchargée', 'green')

        variation_types = [
            ('Lifestyle', 'lifestyle setting'),
            ('En situation', 'in a realistic setting'),
            ('Contexte', 'in context'),
            ('Mise en scène', 'styled'),
            ('Vue angle', 'different angle view'),
        ]

        generated_images = []
        for idx in range(num_variations):
            variation_name, variation_desc = variation_types[idx % len(variation_types)]
            progress_pct = int((idx / num_variations) * 100)

            yield sse_log('generating', '🔄', '[' + str(idx+1) + '/' + str(num_variations) + '] ' + variation_name + '...', 'cyan', progress=progress_pct)

            prompt = 'Create a realistic product photo of this exact same product ' + variation_desc + '. Keep the product IDENTICAL. Pinterest style, aesthetic, inspiring. No text, no logos, no fantasy.'

            image_data = None
            for attempt in range(3):
                image_data = image_generator.generate_product_variation(source_bytes, prompt, idx + 1)
                if image_data:
                    break
                if attempt < 2:
                    yield sse_log('warning', '🔄', 'Retry...', 'orange')
                    time_module.sleep(1)

            if image_data:
                generated_images.append(image_data)
                progress_done = int(((idx + 1) / num_variations) * 100)
                yield sse_log('success', '✅', '[' + str(idx+1) + '/' + str(num_variations) + '] ' + variation_name + ' générée', 'green', progress=progress_done)
            else:
                yield sse_log('warning', '⚠️', variation_name + ' échouée', 'orange')

            if idx < num_variations - 1:
                time_module.sleep(1)

        if not generated_images:
            yield sse_log('error', '❌', 'Aucune image générée', 'red')
            yield sse_log('done', '🛑', 'Arrêt', success=False, error='No images')
            return

        yield sse_log('step', '📤', 'Upload de ' + str(len(generated_images)) + ' images...', 'yellow')

        # AJOUTER les images sans supprimer les existantes
        uploaded_count = 0
        for i, img_data in enumerate(generated_images):
            result = shopify_client.upload_image_to_product(product_id, img_data, filename='ai_extra_' + str(i+1) + '.png')
            if result['success']:
                uploaded_count += 1
                yield sse_log('info', '⬆️', 'Image ' + str(i+1) + ' uploadée', 'gray')

        if uploaded_count > 0:
            yield sse_log('success', '✅', str(uploaded_count) + ' images ajoutées!', 'green')
            yield sse_log('done', '🏁', 'Terminé', success=True, uploaded_count=uploaded_count)
        else:
            yield sse_log('error', '❌', 'Erreur upload', 'red')
            yield sse_log('done', '🛑', 'Arrêt', success=False, error='Upload failed')

    return Response(stream_with_context(generate_with_logs()), mimetype='text/event-stream')


@app.route('/api/shopify/reorder-images', methods=['POST'])
def reorder_images():
    """Réorganise les images d'un produit"""
    try:
        data = request.json
        product_id = data.get('product_id')
        image_ids = data.get('image_ids', [])

        print(f"🔄 Reorder images - Product: {product_id}, Images: {image_ids}")

        if not product_id or not image_ids:
            return jsonify({'error': 'Données manquantes'}), 400

        settings = load_settings()
        store_url = settings.get('shopify_store_url')
        access_token = settings.get('shopify_access_token')

        if not store_url or not access_token:
            return jsonify({'error': 'Shopify non connecté'}), 400

        client = ShopifyClient(store_url, access_token=access_token)

        # Convertir product_id en int si c'est un string
        if isinstance(product_id, str):
            product_id = int(product_id.replace('gid://shopify/Product/', ''))

        errors = []
        success_count = 0
        
        # Mettre à jour la position de chaque image
        for position, image_id in enumerate(image_ids, start=1):
            try:
                # Convertir image_id en int si nécessaire
                if isinstance(image_id, str):
                    image_id = int(image_id.replace('gid://shopify/ProductImage/', '').replace('gid://shopify/MediaImage/', ''))
                
                url = f"{client.base_url}/products/{product_id}/images/{image_id}.json"
                print(f"  📍 PUT {url} -> position {position}")
                
                response = requests.put(
                    url,
                    headers=client.headers,
                    json={'image': {'id': image_id, 'position': position}},
                    timeout=10
                )
                
                if response.status_code == 200:
                    success_count += 1
                    print(f"  ✅ Image {image_id} -> position {position}")
                else:
                    print(f"  ❌ Image {image_id}: {response.status_code} - {response.text}")
                    errors.append(f"Image {image_id}: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Erreur image {image_id}: {e}")
                errors.append(str(e))

        print(f"✅ Reorder terminé: {success_count}/{len(image_ids)} images repositionnées")
        
        if success_count > 0:
            return jsonify({'success': True, 'message': f'{success_count} positions mises à jour', 'errors': errors})
        else:
            return jsonify({'success': False, 'error': 'Aucune image repositionnée', 'errors': errors}), 400

    except Exception as e:
        print(f"❌ Erreur reorder_images: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/add-product-images-stream', methods=['POST'])
def add_product_images_stream():
    """
    Ajoute de nouvelles images à un produit avec Gemini AI (streaming des logs)
    Utilise l'image existante comme référence pour générer de nouvelles images
    """
    from flask import Response, stream_with_context
    
    data = request.json
    product_id = data.get('product_id')
    product_title = data.get('product_title', 'Produit')
    source_image_url = data.get('source_image_url')
    prompt = data.get('prompt')  # None pour mode auto
    num_images = data.get('num_images', 5)
    mode = data.get('mode', 'auto')  # 'auto' ou 'custom'
    
    def generate():
        if not all([product_id, source_image_url]):
            yield sse_log('error', '❌', 'Paramètres manquants', 'red')
            yield sse_log('done', '', '', '', success=False, error='Paramètres manquants')
            return
        
        # Charger les settings
        settings = load_settings()
        gemini_api_key = settings.get('gemini_api_key')
        store_url = settings.get('shopify_store_url')
        access_token = settings.get('shopify_access_token')
        
        if not gemini_api_key:
            yield sse_log('error', '🔑', 'Clé API Gemini manquante! Allez dans Paramètres > Clé API Gemini pour configurer votre clé.', 'red')
            yield sse_log('done', '', '', '', success=False, error='Clé API Gemini manquante')
            return
        
        if not store_url or not access_token:
            yield sse_log('error', '🛒', 'Shopify non connecté!', 'red')
            yield sse_log('done', '', '', '', success=False, error='Shopify non connecté')
            return
        
        try:
            # 🚀 DÉMARRAGE
            yield sse_log('info', '🚀', f'Démarrage génération pour: {product_title}', 'cyan')
            yield sse_log('info', '📦', f'Product ID: {product_id}', 'gray')
            yield sse_log('info', '🎯', f'Mode: {mode}', 'gray')
            yield sse_log('info', '📊', f'Images demandées: {num_images}', 'gray')
            
            # 🔑 INITIALISATION GEMINI
            yield sse_log('step', '🔑', 'Initialisation Gemini 2.5 Flash Image (Nano Banana)...', 'yellow')
            
            try:
                image_generator = ImageGenerator(gemini_api_key)
                yield sse_log('success', '✅', 'Gemini initialisé avec succès', 'green')
            except Exception as e:
                yield sse_log('error', '❌', f'Erreur initialisation Gemini: {str(e)}', 'red')
                yield sse_log('done', '', '', '', success=False, error=str(e))
                return
            
            # 🎨 GÉNÉRATION IMAGES (le téléchargement est fait dans generate_product_variations)
            yield sse_log('step', '🎨', f'Génération de {num_images} images...', 'purple')
            generated_images = []
            
            for progress in image_generator.generate_product_variations(source_image_url, num_images, custom_prompt=prompt):
                status = progress.get('status')
                message = progress.get('message', '')
                
                # Transmettre tous les logs intermédiaires
                if status == 'downloading':
                    yield sse_log('info', '📥', message, 'blue', progress=progress.get('progress', 0))
                elif status == 'analyzing':
                    yield sse_log('info', '🔍', message, 'yellow', progress=progress.get('progress', 5))
                elif status == 'prompts_ready':
                    yield sse_log('success', '✅', message, 'green', progress=progress.get('progress', 10))
                elif status == 'prompt_info':
                    yield sse_log('info', '📝', message, 'gray', progress=progress.get('progress', 10))
                elif status == 'generating_start':
                    yield sse_log('step', '🎨', message, 'purple', progress=progress.get('progress', 15))
                elif status == 'generating':
                    yield sse_log('info', '🎨', message, 'purple', progress=progress.get('progress', 50))
                elif status == 'generated' and 'image_data' in progress:
                    generated_images.append(progress['image_data'])
                    yield sse_log('success', '✅', f'Image générée ({len(generated_images)}/{num_images})', 'green', progress=len(generated_images)/num_images*100)
                elif status == 'warning':
                    yield sse_log('warning', '⚠️', message, 'orange', progress=progress.get('progress', 50))
                elif status == 'complete':
                    yield sse_log('success', '🎉', message, 'green', progress=100)
                elif status == 'error':
                    error_msg = message or 'Erreur inconnue'
                    # Gérer les erreurs spécifiques à l'API Gemini
                    if 'API key not valid' in error_msg or 'API_KEY_INVALID' in error_msg:
                        yield sse_log('error', '🔑', 'Clé API Gemini invalide! Vérifiez votre clé sur https://aistudio.google.com/app/apikey', 'red')
                    elif 'quota' in error_msg.lower() or 'RESOURCE_EXHAUSTED' in error_msg:
                        yield sse_log('error', '📊', 'Quota API Gemini dépassé. Attendez ou augmentez votre quota sur Google AI.', 'red')
                    elif 'permission' in error_msg.lower() or 'PERMISSION_DENIED' in error_msg:
                        yield sse_log('error', '🚫', 'Permission refusée. Activez l\'API Gemini sur votre compte Google Cloud.', 'red')
                    else:
                        yield sse_log('error', '❌', f'Erreur génération: {error_msg}', 'red')
                    yield sse_log('done', '', '', '', success=False, error=error_msg)
                    return
            
            if not generated_images:
                yield sse_log('error', '❌', 'Aucune image générée', 'red')
                yield sse_log('done', '', '', '', success=False, error='Aucune image générée')
                return
            
            yield sse_log('success', '✅', f'{len(generated_images)} images générées avec succès', 'green')
            
            # 📤 UPLOAD SHOPIFY
            yield sse_log('step', '📤', f'Upload de {len(generated_images)} images vers Shopify...', 'blue')
            
            # Initialiser le client Shopify
            shopify_client = ShopifyClient(store_url, access_token=access_token)
            
            upload_results = []
            for i, image_data in enumerate(generated_images):
                yield sse_log('info', '📤', f'Upload image {i+1}/{len(generated_images)}...', 'blue', progress=(i+1)/len(generated_images)*100)
                
                try:
                    upload_result = shopify_client.upload_image_to_product(product_id, image_data)
                    
                    if upload_result['success']:
                        upload_results.append(upload_result)
                        yield sse_log('success', '✅', f'Image {i+1} uploadée avec succès', 'green')
                    else:
                        yield sse_log('error', '❌', f'Erreur upload image {i+1}: {upload_result["error"]}', 'red')
                except Exception as e:
                    yield sse_log('error', '❌', f'Erreur upload image {i+1}: {str(e)}', 'red')
            
            # 🎉 FIN
            if upload_results:
                yield sse_log('success', '🎉', f'{len(upload_results)} images uploadées sur Shopify avec succès!', 'green')
                yield sse_log('done', '', '', '', success=True, uploaded_count=len(upload_results), total_generated=len(generated_images))
            else:
                yield sse_log('error', '❌', 'Aucune image n\'a pu être uploadée', 'red')
                yield sse_log('done', '', '', '', success=False, error='Aucune image n\'a pu être uploadée')
            
        except Exception as e:
            yield sse_log('error', '❌', f'Erreur inattendue: {str(e)}', 'red')
            yield sse_log('done', '', '', '', success=False, error=str(e))
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@app.route('/api/add-product-images', methods=['POST'])
def add_product_images():
    """
    Ajoute de nouvelles images à un produit avec Gemini AI
    Utilise l'image existante comme référence pour générer de nouvelles images
    """
    try:
        data = request.json
        product_id = data.get('product_id')
        source_image_url = data.get('source_image_url')
        prompt = data.get('prompt')  # None pour mode auto
        num_images = data.get('num_images', 5)
        mode = data.get('mode', 'auto')  # 'auto' ou 'custom'
        
        if not all([product_id, source_image_url]):
            return jsonify({'error': 'Paramètres manquants'}), 400
        
        # Charger les settings
        settings = load_settings()
        gemini_api_key = settings.get('gemini_api_key')
        store_url = settings.get('shopify_store_url')
        access_token = settings.get('shopify_access_token')
        
        if not gemini_api_key:
            return jsonify({'error': '🔑 Clé API Gemini manquante! Allez dans Paramètres > Clé API Gemini pour configurer votre clé. Visitez https://aistudio.google.com/app/apikey pour obtenir une clé.'}), 400
        
        if not store_url or not access_token:
            return jsonify({'error': '🛒 Shopify non connecté!'}), 400
        
        print(f"🎨 Ajout d'images pour produit {product_id}")
        print(f"   Mode: {mode}")
        print(f"   Nombre d'images: {num_images}")
        if prompt:
            print(f"   Prompt: {prompt[:100]}...")
        
        # Initialiser les clients
        shopify_client = ShopifyClient(store_url, access_token=access_token)
        image_generator = ImageGenerator(gemini_api_key)
        
        # Générer les nouvelles images avec Gemini
        print(f"🤖 Génération avec Gemini...")
        generated_images = []
        
        for progress in image_generator.generate_product_variations(source_image_url, num_images, custom_prompt=prompt):
            if progress['status'] == 'generated' and 'image_data' in progress:
                generated_images.append(progress['image_data'])
                print(f"   ✅ Image générée ({len(generated_images)}/{num_images})")
            elif progress['status'] == 'error':
                error_msg = progress.get('message', 'Erreur inconnue')
                # Gérer les erreurs spécifiques à l'API Gemini
                if 'API key not valid' in error_msg or 'API_KEY_INVALID' in error_msg:
                    return jsonify({'error': '🔑 Clé API Gemini invalide! Vérifiez votre clé sur https://aistudio.google.com/app/apikey'}), 400
                elif 'quota' in error_msg.lower() or 'RESOURCE_EXHAUSTED' in error_msg:
                    return jsonify({'error': '📊 Quota API Gemini dépassé. Attendez ou augmentez votre quota sur Google AI.'}), 400
                elif 'permission' in error_msg.lower() or 'PERMISSION_DENIED' in error_msg:
                    return jsonify({'error': '🚫 Permission refusée. Activez l\'API Gemini sur votre compte Google Cloud.'}), 400
                else:
                    return jsonify({'error': f"Erreur génération: {error_msg}"}), 400
        
        if not generated_images:
            return jsonify({'error': 'Aucune image générée'}), 400
        
        # Upload des nouvelles images sur Shopify
        print(f"📤 Upload de {len(generated_images)} images sur Shopify...")
        upload_results = []
        
        for i, image_data in enumerate(generated_images):
            print(f"   Upload image {i+1}/{len(generated_images)}...")
            upload_result = shopify_client.upload_image_to_product(product_id, image_data)
            
            if upload_result['success']:
                upload_results.append(upload_result)
                print(f"   ✅ Image {i+1} uploadée")
            else:
                print(f"   ❌ Erreur upload image {i+1}: {upload_result['error']}")
        
        if upload_results:
            print(f"✅ {len(upload_results)} images uploadées sur Shopify")
            return jsonify({
                'success': True,
                'message': f'{len(upload_results)} images ajoutées avec succès',
                'uploaded_count': len(upload_results),
                'image_urls': [r.get('image_url') for r in upload_results]
            })
        else:
            return jsonify({'error': "Aucune image n'a pu être uploadée"}), 400
        
    except Exception as e:
        print(f"❌ Erreur add_product_images: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/replace-image-stream', methods=['POST'])
def replace_image_stream():
    """
    Remplace ou ajoute une image de produit avec Gemini AI (streaming des logs)
    Utilise l'image existante comme référence pour générer une nouvelle image
    """
    from flask import Response, stream_with_context
    
    data = request.json
    product_id = data.get('product_id')
    product_title = data.get('product_title', 'Produit')
    image_id = data.get('image_id')
    source_image_url = data.get('source_image_url')
    prompt = data.get('prompt')
    mode = data.get('mode', 'replace')  # 'replace' ou 'new'
    
    def generate():
        import requests
        
        if not all([product_id, image_id, source_image_url, prompt]):
            yield sse_log('error', '❌', 'Paramètres manquants', 'red')
            yield sse_log('done', '', '', '', success=False, error='Paramètres manquants')
            return
        
        # Charger les settings
        settings = load_settings()
        gemini_api_key = settings.get('gemini_api_key')
        store_url = settings.get('shopify_store_url')
        access_token = settings.get('shopify_access_token')
        
        if not gemini_api_key:
            yield sse_log('error', '🔑', 'Clé API Gemini manquante! Allez dans Paramètres > Clé API Gemini pour configurer votre clé.', 'red')
            yield sse_log('done', '', '', '', success=False, error='Clé API Gemini manquante')
            return
        
        if not store_url or not access_token:
            yield sse_log('error', '🛒', 'Shopify non connecté!', 'red')
            yield sse_log('done', '', '', '', success=False, error='Shopify non connecté')
            return
        
        try:
            # 🚀 DÉMARRAGE
            yield sse_log('info', '🚀', f'Démarrage remplacement pour: {product_title}', 'cyan')
            yield sse_log('info', '📦', f'Product ID: {product_id}', 'gray')
            yield sse_log('info', '🎯', f'Mode: {mode}', 'gray')
            yield sse_log('info', '🆔', f'Image ID: {image_id}', 'gray')
            
            # 🔑 INITIALISATION GEMINI
            yield sse_log('step', '🔑', 'Initialisation Gemini 2.5 Flash Image (Nano Banana)...', 'yellow')
            
            try:
                image_generator = ImageGenerator(gemini_api_key)
                yield sse_log('success', '✅', 'Gemini initialisé avec succès', 'green')
            except Exception as e:
                yield sse_log('error', '❌', f'Erreur initialisation Gemini: {str(e)}', 'red')
                yield sse_log('done', '', '', '', success=False, error=str(e))
                return
            
            # 🎨 GÉNÉRATION IMAGE (le téléchargement est fait dans generate_product_variations)
            yield sse_log('step', '🎨', 'Génération de la nouvelle image...', 'purple')
            generated_images = []
            
            for progress in image_generator.generate_product_variations(source_image_url, 1, custom_prompt=prompt):
                status = progress.get('status')
                message = progress.get('message', '')
                
                # Transmettre tous les logs intermédiaires
                if status == 'downloading':
                    yield sse_log('info', '📥', message, 'blue', progress=progress.get('progress', 0))
                elif status == 'analyzing':
                    yield sse_log('info', '🔍', message, 'yellow', progress=progress.get('progress', 5))
                elif status == 'prompts_ready':
                    yield sse_log('success', '✅', message, 'green', progress=progress.get('progress', 10))
                elif status == 'prompt_info':
                    yield sse_log('info', '📝', message, 'gray', progress=progress.get('progress', 10))
                elif status == 'generating_start':
                    yield sse_log('step', '🎨', message, 'purple', progress=progress.get('progress', 15))
                elif status == 'generating':
                    yield sse_log('info', '🎨', message, 'purple', progress=progress.get('progress', 50))
                elif status == 'generated' and 'image_data' in progress:
                    generated_images.append(progress['image_data'])
                    yield sse_log('success', '✅', 'Nouvelle image générée avec succès', 'green', progress=100)
                elif status == 'warning':
                    yield sse_log('warning', '⚠️', message, 'orange', progress=progress.get('progress', 50))
                elif status == 'complete':
                    yield sse_log('success', '🎉', message, 'green', progress=100)
                elif status == 'error':
                    error_msg = message or 'Erreur inconnue'
                    # Gérer les erreurs spécifiques à l'API Gemini
                    if 'API key not valid' in error_msg or 'API_KEY_INVALID' in error_msg:
                        yield sse_log('error', '🔑', 'Clé API Gemini invalide! Vérifiez votre clé sur https://aistudio.google.com/app/apikey', 'red')
                    elif 'quota' in error_msg.lower() or 'RESOURCE_EXHAUSTED' in error_msg:
                        yield sse_log('error', '📊', 'Quota API Gemini dépassé. Attendez ou augmentez votre quota sur Google AI.', 'red')
                    elif 'permission' in error_msg.lower() or 'PERMISSION_DENIED' in error_msg:
                        yield sse_log('error', '🚫', 'Permission refusée. Activez l\'API Gemini sur votre compte Google Cloud.', 'red')
                    else:
                        yield sse_log('error', '❌', f'Erreur génération: {error_msg}', 'red')
                    yield sse_log('done', '', '', '', success=False, error=error_msg)
                    return
            
            if not generated_images:
                yield sse_log('error', '❌', 'Aucune image générée', 'red')
                yield sse_log('done', '', '', '', success=False, error='Aucune image générée')
                return
            
            # 📤 UPLOAD SHOPIFY
            yield sse_log('step', '📤', 'Upload de la nouvelle image vers Shopify...', 'blue')
            
            # Initialiser le client Shopify
            shopify_client = ShopifyClient(store_url, access_token=access_token)
            
            if mode == 'replace':
                # Mode remplacement : supprimer l'ancienne image d'abord
                yield sse_log('info', '🗑️', f'Suppression de l\'ancienne image {image_id}...', 'orange')
                
                try:
                    delete_url = f"https://{store_url}/admin/api/2023-10/products/{product_id}/images/{image_id}.json"
                    headers = {
                        'Content-Type': 'application/json',
                        'X-Shopify-Access-Token': access_token
                    }
                    delete_response = requests.delete(delete_url, headers=headers, timeout=30)
                    
                    if delete_response.status_code not in [200, 204]:
                        error_msg = f"Erreur suppression ancienne image: {delete_response.status_code}"
                        try:
                            error_data = delete_response.json()
                            error_msg = error_data.get('error', error_data.get('errors', error_msg))
                        except:
                            if delete_response.text:
                                error_msg = delete_response.text[:200]
                        yield sse_log('error', '❌', error_msg, 'red')
                        yield sse_log('done', '', '', '', success=False, error=error_msg)
                        return
                    
                    yield sse_log('success', '✅', 'Ancienne image supprimée avec succès', 'green')
                except Exception as e:
                    yield sse_log('error', '❌', f'Erreur suppression: {str(e)}', 'red')
                    yield sse_log('done', '', '', '', success=False, error=str(e))
                    return
            
            # Upload de la nouvelle image
            try:
                upload_result = shopify_client.upload_image_to_product(product_id, generated_images[0])
                
                if upload_result['success']:
                    yield sse_log('success', '✅', 'Nouvelle image uploadée avec succès', 'green')
                    yield sse_log('success', '🎉', 'REMPLACEMENT TERMINÉ AVEC SUCCÈS!', 'green')
                    yield sse_log('done', '', '', '', success=True, new_image_url=upload_result.get('image_url'))
                else:
                    yield sse_log('error', '❌', f"Erreur upload: {upload_result['error']}", 'red')
                    yield sse_log('done', '', '', '', success=False, error=upload_result['error'])
            except Exception as e:
                yield sse_log('error', '❌', f'Erreur upload: {str(e)}', 'red')
                yield sse_log('done', '', '', '', success=False, error=str(e))
            
        except Exception as e:
            yield sse_log('error', '❌', f'Erreur inattendue: {str(e)}', 'red')
            yield sse_log('done', '', '', '', success=False, error=str(e))
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@app.route('/api/replace-image', methods=['POST'])
def replace_image():
    """
    Remplace ou ajoute une image de produit avec Gemini AI
    Utilise l'image existante comme référence pour générer une nouvelle image
    """
    try:
        data = request.json
        product_id = data.get('product_id')
        image_id = data.get('image_id')
        source_image_url = data.get('source_image_url')
        prompt = data.get('prompt')
        mode = data.get('mode', 'replace')  # 'replace' ou 'new'
        
        if not all([product_id, image_id, source_image_url, prompt]):
            return jsonify({'error': 'Paramètres manquants'}), 400
        
        # Charger les settings
        settings = load_settings()
        gemini_api_key = settings.get('gemini_api_key')
        store_url = settings.get('shopify_store_url')
        access_token = settings.get('shopify_access_token')
        
        if not gemini_api_key:
            return jsonify({'error': '🔑 Clé API Gemini manquante! Allez dans Paramètres > Clé API Gemini pour configurer votre clé. Visitez https://aistudio.google.com/app/apikey pour obtenir une clé.'}), 400
        
        if not store_url or not access_token:
            return jsonify({'error': '🛒 Shopify non connecté!'}), 400
        
        print(f"🎨 Remplacement d'image pour produit {product_id}, image {image_id}")
        print(f"   Mode: {mode}")
        print(f"   Prompt: {prompt[:100]}...")
        
        # Initialiser les clients
        shopify_client = ShopifyClient(store_url, access_token=access_token)
        image_generator = ImageGenerator(gemini_api_key)
        
        # Générer une nouvelle image avec Gemini
        print(f"🤖 Génération avec Gemini...")
        generated_images = []
        
        for progress in image_generator.generate_product_variations(source_image_url, 1, custom_prompt=prompt):
            if progress['status'] == 'generated' and 'image_data' in progress:
                generated_images.append(progress['image_data'])
                print(f"   ✅ Image générée")
            elif progress['status'] == 'error':
                error_msg = progress.get('message', 'Erreur inconnue')
                # Gérer les erreurs spécifiques à l'API Gemini
                if 'API key not valid' in error_msg or 'API_KEY_INVALID' in error_msg:
                    return jsonify({'error': '🔑 Clé API Gemini invalide! Vérifiez votre clé sur https://aistudio.google.com/app/apikey'}), 400
                elif 'quota' in error_msg.lower() or 'RESOURCE_EXHAUSTED' in error_msg:
                    return jsonify({'error': '📊 Quota API Gemini dépassé. Attendez ou augmentez votre quota sur Google AI.'}), 400
                elif 'permission' in error_msg.lower() or 'PERMISSION_DENIED' in error_msg:
                    return jsonify({'error': '🚫 Permission refusée. Activez l\'API Gemini sur votre compte Google Cloud.'}), 400
                else:
                    return jsonify({'error': f"Erreur génération: {error_msg}"}), 400
        
        if not generated_images:
            return jsonify({'error': 'Aucune image générée'}), 400
        
        # Upload de la nouvelle image sur Shopify
        print(f"📤 Upload sur Shopify...")
        
        if mode == 'replace':
            # Mode remplacement : supprimer l'ancienne image et uploader la nouvelle
            print(f"   Suppression de l'ancienne image {image_id}...")
            
            # Supprimer l'ancienne image
            delete_url = f"https://{store_url}/admin/api/2023-10/products/{product_id}/images/{image_id}.json"
            headers = {
                'Content-Type': 'application/json',
                'X-Shopify-Access-Token': access_token
            }
            delete_response = requests.delete(delete_url, headers=headers, timeout=30)
            
            if delete_response.status_code not in [200, 204]:
                error_msg = f"Erreur suppression ancienne image: {delete_response.status_code}"
                try:
                    error_data = delete_response.json()
                    error_msg = error_data.get('error', error_data.get('errors', error_msg))
                except:
                    if delete_response.text:
                        error_msg = delete_response.text[:200]
                return jsonify({'error': error_msg}), 400
            
            print(f"   ✅ Ancienne image supprimée")
            
            # Uploader la nouvelle image
            upload_result = shopify_client.upload_image_to_product(product_id, generated_images[0])
            
            if upload_result['success']:
                print(f"   ✅ Nouvelle image uploadée")
                return jsonify({
                    'success': True,
                    'message': 'Image remplacée avec succès',
                    'new_image_url': upload_result.get('image_url')
                })
            else:
                return jsonify({'error': f"Erreur upload: {upload_result['error']}"}), 400
                
        else:
            # mode 'new' : simplement ajouter la nouvelle image
            upload_result = shopify_client.upload_image_to_product(product_id, generated_images[0])
            
            if upload_result['success']:
                print(f"   ✅ Nouvelle image ajoutée")
                return jsonify({
                    'success': True,
                    'message': 'Nouvelle image ajoutée avec succès',
                    'new_image_url': upload_result.get('image_url')
                })
            else:
                return jsonify({'error': f"Erreur upload: {upload_result['error']}"}), 400
        
    except Exception as e:
        print(f"❌ Erreur replace_image: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
