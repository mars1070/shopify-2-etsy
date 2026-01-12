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

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
SETTINGS_FILE = os.path.abspath('settings.json')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                content = f.read()
                if not content or content.strip() == '':
                    print("AVERTISSEMENT: Fichier settings.json vide, retour dict vide")
                    return {}
                return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"AVERTISSEMENT: Erreur JSON dans settings.json: {e}")
            print(f"   Contenu du fichier: {content[:100] if 'content' in locals() else 'N/A'}")
            return {}
        except Exception as e:
            print(f"AVERTISSEMENT: Erreur lecture settings.json: {e}")
            return {}
    print("INFO: Fichier settings.json n'existe pas encore")
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
            'products_count': products_count
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/enhance', methods=['POST'])
def enhance():
    try:
        data = request.json
        temp_file = data.get('temp_file')
        
        if not temp_file:
            return jsonify({'error': 'Fichier temporaire manquant'}), 400
        
        settings = load_settings()
        api_key = settings.get('gemini_api_key') or os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            print("ERREUR: Cle API Gemini manquante!")
            return jsonify({'error': 'Cle API Gemini manquante! Allez dans Parametres pour configurer votre cle API.'}), 400
        
        temp_path = os.path.join(OUTPUT_FOLDER, temp_file)
        output_path = os.path.join(OUTPUT_FOLDER, 'etsy_final.csv')
        
        # Tester l'initialisation de Gemini
        try:
            enhancer = GeminiEnhancer(api_key)
        except Exception as init_error:
            error_msg = str(init_error)
            print(f"ERREUR initialisation Gemini: {error_msg}")
            
            # Détecter si c'est un problème de clé API
            if 'API' in error_msg or 'key' in error_msg.lower() or 'auth' in error_msg.lower():
                return jsonify({'error': 'Cle API Gemini invalide ou manquante! Verifiez votre cle dans Parametres.'}), 400
            else:
                return jsonify({'error': f'Erreur initialisation Gemini: {error_msg}'}), 500
        
        def generate():
            try:
                for progress in enhancer.enhance_generator(temp_path, output_path):
                    yield f"data: {json.dumps(progress)}\n\n"
            except Exception as gen_error:
                error_msg = str(gen_error)
                print(f"ERREUR generation: {error_msg}")
                
                # Détecter si c'est un problème de clé API pendant la génération
                if 'API' in error_msg or 'key' in error_msg.lower() or 'auth' in error_msg.lower() or 'quota' in error_msg.lower():
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Erreur API Gemini: Cle invalide ou quota depasse'})}\n\n"
                else:
                    yield f"data: {json.dumps({'status': 'error', 'message': f'Erreur: {error_msg}'})}\n\n"
                
        return Response(stream_with_context(generate()), mimetype='text/event-stream')
    
    except Exception as e:
        error_msg = str(e)
        print(f"ERREUR globale: {error_msg}")
        
        # Détecter si c'est un problème de clé API
        if 'API' in error_msg or 'key' in error_msg.lower() or 'auth' in error_msg.lower():
            return jsonify({'error': 'Cle API Gemini invalide! Verifiez votre cle dans Parametres.'}), 400
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
        # Prevent directory traversal
        safe_name = os.path.basename(filename)
        # Use same path as preview_csv for consistency
        file_path = os.path.join(OUTPUT_FOLDER, safe_name)
        
        if not os.path.exists(file_path):
            return jsonify({'error': f'Fichier non trouvé: {file_path}'}), 404
        
        return send_file(file_path, as_attachment=True, download_name='etsy_products.csv')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET'])
def get_settings():
    print(f"GET /api/settings called. Using file: {SETTINGS_FILE}")
    try:
        settings = load_settings()
        print(f"Settings loaded successfully")
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
        print(f"ERREUR in GET /api/settings: {e}")
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
        
        # VALIDATION: Tester la clé avec Gemini
        print("Validation de la clé API avec Gemini...")
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Test avec Gemini 2.5 Flash
            print("   Tentative de connexion à Gemini 2.5 Flash...")
            model = genai.GenerativeModel('gemini-2.5-flash')
            test_response = model.generate_content("Hello", generation_config={'max_output_tokens': 10})
            
            # Si on arrive ici, la clé est valide
            print("SUCCES Clé API validée avec succès!")
            # Pas besoin de lire la réponse, juste vérifier qu'il n'y a pas d'erreur
            if test_response:
                print("   Test de connexion réussi!")
            
        except Exception as validation_error:
            error_msg = str(validation_error)
            print(f"ERREUR Validation echouee: {error_msg}")
            print(f"   Type d'erreur: {type(validation_error).__name__}")
            
            # Messages d'erreur personnalisés
            if 'API_KEY_INVALID' in error_msg or 'invalid' in error_msg.lower():
                return jsonify({'error': 'Cle API invalide. Verifiez votre cle sur Google AI Studio (https://aistudio.google.com/app/apikey)'}), 400
            elif 'quota' in error_msg.lower() or 'RESOURCE_EXHAUSTED' in error_msg:
                return jsonify({'error': 'Quota API depasse. Attendez ou augmentez votre quota sur Google AI.'}), 400
            elif 'permission' in error_msg.lower() or 'PERMISSION_DENIED' in error_msg:
                return jsonify({'error': 'Permission refusee. Activez l\'API Gemini sur votre compte Google Cloud.'}), 400
            elif 'not found' in error_msg.lower() or '404' in error_msg:
                return jsonify({'error': 'Modele Gemini 2.5 Flash non trouve. Verifiez que votre cle a acces a ce modele.'}), 400
            else:
                return jsonify({'error': f'Erreur validation: {error_msg[:200]}'}), 400
        
        # Vérifier que le fichier settings.json existe, sinon le créer
        if not os.path.exists(SETTINGS_FILE):
            print(f"Création du fichier {SETTINGS_FILE}")
            with open(SETTINGS_FILE, 'w') as f:
                json.dump({}, f)
        
        settings = load_settings()
        settings['gemini_api_key'] = api_key
        save_settings(settings)
        print(f"SUCCES Parametres sauvegardes avec succes dans {SETTINGS_FILE}")
        
        return jsonify({'success': True, 'message': 'Clé API validée et enregistrée avec succès!'})
    
    except Exception as e:
        print(f"ERREUR dans save_settings_route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500

# ==================== SHOPIFY OAUTH ENDPOINTS ====================

# Variable globale pour stocker le state OAuth temporairement
# Utiliser un fichier temporaire pour persister entre les redémarrages Flask
import tempfile
import pickle

OAUTH_STATES_FILE = os.path.join(tempfile.gettempdir(), 'shopify_oauth_states.pkl')

def load_oauth_states():
    """Charge les states OAuth depuis le fichier"""
    try:
        if os.path.exists(OAUTH_STATES_FILE):
            with open(OAUTH_STATES_FILE, 'rb') as f:
                return pickle.load(f)
    except Exception as e:
        print(f"Erreur chargement oauth states: {e}")
    return {}

def save_oauth_states(states):
    """Sauvegarde les states OAuth dans le fichier"""
    try:
        with open(OAUTH_STATES_FILE, 'wb') as f:
            pickle.dump(states, f)
    except Exception as e:
        print(f"Erreur sauvegarde oauth states: {e}")

oauth_states = load_oauth_states()

@app.route('/api/shopify/oauth/start', methods=['POST'])
def shopify_oauth_start():
    """
    Démarre le flux OAuth Shopify.
    Retourne l'URL d'autorisation vers laquelle rediriger l'utilisateur.
    """
    try:
        print("=== DEBUG OAuth Start ===")
        
        data = request.json
        print(f"OAuth start request: {data}")
        
        store_url = data.get('store_url', '').strip()
        client_id = data.get('client_id', '').strip()
        client_secret = data.get('client_secret', '').strip()
        
        print(f"Store URL: {store_url}")
        print(f"Client ID: {client_id[:10]}...")
        print(f"Client Secret: {client_secret[:10]}...")
        
        if not store_url:
            print("ERROR: URL boutique manquante")
            return jsonify({'error': 'URL de la boutique manquante'}), 400
        if not client_id:
            print("ERROR: Client ID manquant")
            return jsonify({'error': 'Client ID manquant'}), 400
        if not client_secret:
            print("ERROR: API Secret manquant")
            return jsonify({'error': 'API Secret manquant'}), 400
        
        # Nettoyer l'URL du store
        clean_url = store_url.replace('https://', '').replace('http://', '').rstrip('/')
        if '.myshopify.com' not in clean_url and '.' not in clean_url:
            clean_url = f"{clean_url}.myshopify.com"
        
        print(f"Clean URL: {clean_url}")
        
        # Générer un state unique pour la sécurité
        state = secrets.token_urlsafe(32)
        print(f"Generated state: {state}")
        
        # Sauvegarder temporairement les credentials et le state
        oauth_states[state] = {
            'store_url': clean_url,
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        # Persister sur disque
        save_oauth_states(oauth_states)
        
        print(f"States in memory after adding: {list(oauth_states.keys())}")
        print(f"Total states: {len(oauth_states)}")
        print(f"State saved to file: {OAUTH_STATES_FILE}")
        
        # Construire l'URL d'autorisation Shopify
        # Utiliser l'URL de production si disponible, sinon localhost
        base_url = os.getenv('VERCEL_URL', 'http://localhost:3000')
        if not base_url.startswith('http'):
            base_url = f'https://{base_url}'
        redirect_uri = f'{base_url}/auth/callback'
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
        
        print(f"OAuth demarre pour: {clean_url}")
        print(f"   Auth URL: {auth_url}")
        
        return jsonify({
            'success': True,
            'auth_url': auth_url,
            'state': state
        })
        
    except Exception as e:
        print(f"ERREUR oauth_start: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/shopify/oauth/callback', methods=['POST'])
def shopify_oauth_callback():
    """
    Traite le callback OAuth après autorisation.
    Échange le code contre un access_token.
    """
    try:
        global oauth_states
        
        print("=== DEBUG OAuth Callback ===")
        
        data = request.json
        print(f"Request data: {data}")
        
        code = data.get('code', '').strip()
        state = data.get('state', '').strip()
        shop = data.get('shop', '').strip()
        
        print(f"Code: {code[:20] if code else 'None'}...")
        print(f"State: {state}")
        print(f"Shop: {shop}")
        print(f"States in memory: {list(oauth_states.keys())}")
        
        if not code:
            print("ERROR: Code manquant")
            return jsonify({'error': 'Code d\'autorisation manquant'}), 400
        if not state:
            print("ERROR: State manquant")
            return jsonify({'error': 'State manquant'}), 400
        
        # Recharger les states depuis le fichier au cas où Flask aurait redémarré
        oauth_states = load_oauth_states()
        
        print(f"States loaded from file: {list(oauth_states.keys())}")
        
        # Vérifier que le state existe et récupérer les credentials
        if state not in oauth_states:
            print(f"ERROR: State {state} non trouvé dans {list(oauth_states.keys())}")
            return jsonify({'error': 'State invalide ou expiré. Recommencez le processus.'}), 400
        
        oauth_data = oauth_states.pop(state)  # Récupérer et supprimer
        save_oauth_states(oauth_states)  # Sauvegarder après suppression
        print(f"OAuth data trouvé pour: {oauth_data['store_url']}")
        
        store_url = oauth_data['store_url']
        client_id = oauth_data['client_id']
        client_secret = oauth_data['client_secret']
        
        print(f"Echange du code OAuth pour: {store_url}")
        
        # Échanger le code contre un access_token
        import requests
        token_url = f"https://{store_url}/admin/oauth/access_token"
        
        print(f"Token URL: {token_url}")
        
        response = requests.post(token_url, data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code
        }, headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }, timeout=30)
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text[:500]}")
        
        if response.status_code != 200:
            error_msg = f"Erreur Shopify: {response.status_code}"
            try:
                error_data = response.json()
                error_msg = error_data.get('error_description', error_data.get('error', error_msg))
            except:
                error_msg = response.text[:200]
            print(f"ERREUR echange token: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        token_data = response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            return jsonify({'error': 'Access token non reçu de Shopify'}), 400
        
        print(f"SUCCES Access token obtenu pour: {store_url}")
        
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
            
            print(f"SUCCES Connecte a Shopify via OAuth: {result['shop_name']}")
            return jsonify({
                'success': True,
                'shop_name': result['shop_name'],
                'shop_domain': result.get('shop_domain', ''),
                'auth_mode': 'OAuth'
            })
        else:
            print(f"ERREUR Token obtenu mais connexion echouee: {result['error']}")
            return jsonify({'error': result['error']}), 400
        
    except Exception as e:
        print(f"ERREUR oauth_callback: {e}")
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
            print(f"Test connexion Shopify (API Key + Secret): {store_url}")
            client = ShopifyClient(store_url, api_key=api_key, api_secret=api_secret)
        else:
            print(f"Test connexion Shopify (Access Token): {store_url}")
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
            print(f"SUCCES Connecte a Shopify ({auth_mode}): {result['shop_name']}")
            return jsonify({
                'success': True,
                'shop_name': result['shop_name'],
                'shop_domain': result.get('shop_domain', ''),
                'auth_mode': auth_mode
            })
        else:
            print(f"ERREUR Echec connexion Shopify: {result['error']}")
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        print(f"ERREUR shopify_connect: {e}")
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
        
        print(f"GET /api/shopify/products")
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
        print(f"   SUCCES {len(products)} produits recuperes")
        
        return jsonify({
            'success': True,
            'products': products,
            'count': len(products)
        })
    except Exception as e:
        print(f"ERREUR shopify_get_products: {e}")
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
            return jsonify({'error': 'Cle API Gemini manquante! Configurez-la dans Parametres.'}), 400
        
        if not store_url or not access_token:
            return jsonify({'error': 'Shopify non connecte! Connectez votre boutique dans Parametres.'}), 400
        
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
                
                yield f"data: {json.dumps({'status': 'starting', 'message': f'Demarrage generation pour {total_products} produits', 'total': total_products})}\n\n"
                
                processed = 0
                for idx, row in products_with_images.iterrows():
                    processed += 1
                    source_url = row['Photo 1']
                    sku = row.get('SKU', f'Produit-{processed}')
                    
                    yield f"data: {json.dumps({'status': 'processing', 'message': f'Traitement {sku} ({processed}/{total_products})', 'progress': int((processed-1)/total_products*100)})}\n\n"
                    
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
                            
                            yield f"data: {json.dumps({'status': 'product_done', 'message': f'{sku}: {len(generated_urls)} images generees', 'progress': int(processed/total_products*100)})}\n\n"
                        
                        if progress['status'] == 'error':
                            error_msg = progress.get('message', 'Erreur inconnue')
                            yield f"data: {json.dumps({'status': 'warning', 'message': f'AVERTISSEMENT {sku}: {error_msg}'})}\n\n"
                            break
                
                # Sauvegarder le CSV mis à jour
                df.to_csv(temp_path, index=False)
                
                yield f"data: {json.dumps({'status': 'complete', 'message': f'Generation terminee pour {total_products} produits', 'progress': 100})}\n\n"
                
            except Exception as e:
                print(f"ERREUR generation images: {e}")
                import traceback
                traceback.print_exc()
                yield f"data: {json.dumps({'status': 'error', 'message': f'Erreur: {str(e)}'})}\n\n"
        
        return Response(stream_with_context(generate()), mimetype='text/event-stream')
        
    except Exception as e:
        print(f"ERREUR generate_images: {e}")
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
            return jsonify({'error': 'Cle API Gemini manquante! Configurez-la dans Parametres.'}), 400
        
        if not store_url:
            return jsonify({'error': 'Shopify non connecte!'}), 400
        
        # Initialiser le client Shopify avec le bon mode d'auth
        if api_key and api_secret and access_token:
            shopify_client = ShopifyClient(store_url, access_token=access_token)
        elif access_token:
            shopify_client = ShopifyClient(store_url, access_token=access_token)
        else:
            return jsonify({'error': 'Credentials Shopify manquants!'}), 400
        
        # Initialiser le générateur d'images
        image_generator = ImageGenerator(gemini_api_key)
        
        print(f"Generation de {num_variations} images pour produit {product_id}")
        print(f"   Source: {source_image_url[:80]}...")
        
        # Générer les images et les uploader sur Shopify
        generated_images = []
        generated_urls = []
        
        for progress in image_generator.generate_product_variations(source_image_url, num_variations):
            if progress['status'] == 'generated' and 'image_data' in progress:
                generated_images.append(progress['image_data'])
                print(f"   SUCCES Variation {progress['variation']} generee")
            
            if progress['status'] == 'error':
                return jsonify({
                    'success': False,
                    'error': progress.get('message', 'Erreur génération')
                }), 400
            
            if progress['status'] == 'complete':
                print(f"   Total {len(generated_images)} images generees au total")
        
        if not generated_images:
            return jsonify({
                'success': False,
                'error': 'Aucune image générée'
            }), 400
        
        # Uploader les images sur Shopify
        print(f"Upload de {len(generated_images)} images vers Shopify...")
        
        upload_result = shopify_client.replace_product_images(product_id, generated_images)
        
        if upload_result['success']:
            print(f"SUCCES {upload_result['uploaded_count']} images uploadées sur Shopify")
            return jsonify({
                'success': True,
                'total_generated': len(generated_images),
                'uploaded_count': upload_result['uploaded_count'],
                'new_urls': upload_result['new_urls']
            })
        else:
            print(f"ERREUR upload: {upload_result['error']}")
            return jsonify({
                'success': False,
                'error': f"Erreur upload Shopify: {upload_result['error']}",
                'total_generated': len(generated_images)
            }), 400
        
    except Exception as e:
        print(f"ERREUR generate_images_for_product: {e}")
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
        
        # DEMARRAGE
        yield sse_log('info', 'START', 'Demarrage generation pour: ' + product_title, 'cyan')
        yield sse_log('info', 'PROD', 'Product ID: ' + str(product_id), 'gray')
        yield sse_log('info', 'TARGET', 'Variations demandees: ' + str(num_variations), 'gray')
        
        # INITIALISATION GEMINI
        yield sse_log('step', 'INIT', 'Initialisation Gemini 2.5 Flash Image (Nano Banana)...', 'yellow')
        
        try:
            image_generator = ImageGenerator(gemini_api_key)
            yield sse_log('success', 'OK', 'Gemini initialise avec succes', 'green')
        except Exception as e:
            yield sse_log('error', 'ERR', 'Erreur init Gemini: ' + str(e), 'red')
            yield sse_log('done', 'STOP', 'Arret', success=False, error=str(e))
            return
        
        # INITIALISATION SHOPIFY
        yield sse_log('step', 'SHOP', 'Connexion a Shopify: ' + store_url, 'yellow')
        
        try:
            shopify_client = ShopifyClient(store_url, access_token=access_token)
            yield sse_log('success', 'OK', 'Shopify connecte', 'green')
        except Exception as e:
            yield sse_log('error', 'ERR', 'Erreur Shopify: ' + str(e), 'red')
            yield sse_log('done', 'STOP', 'Arret', success=False, error=str(e))
            return
        
        # TELECHARGEMENT IMAGE SOURCE
        yield sse_log('step', 'DL', 'Telechargement image source depuis CDN Shopify...', 'yellow')
        yield sse_log('info', 'URL', 'URL: ' + source_image_url[:80] + '...', 'gray')
        
        source_bytes = image_generator.download_image_from_url(source_image_url)
        
        if not source_bytes:
            yield sse_log('error', 'ERR', "Impossible de telecharger l'image source", 'red')
            yield sse_log('done', 'STOP', 'Arret', success=False, error='Download failed')
            return
        
        size_kb = len(source_bytes) / 1024
        yield sse_log('success', 'OK', 'Image telechargee: ' + str(round(size_kb, 1)) + ' KB', 'green')
        
        # CONVERSION EN PIL IMAGE
        yield sse_log('step', 'IMG', 'Conversion en PIL Image pour Gemini...', 'yellow')
        
        source_pil = PILImage.open(BytesIO(source_bytes))
        yield sse_log('success', 'OK', 'Image convertie: ' + str(source_pil.size[0]) + 'x' + str(source_pil.size[1]) + ' pixels', 'green')
        
        # 🔍 ÉTAPE 1: ANALYSE IA ET GÉNÉRATION DES PROMPTS
        yield sse_log('step', 'RECHERCHE', 'Etape 1/2: Gemini analyse le produit et crée les prompts personnalisés...', 'magenta')
        
        custom_prompts = image_generator.analyze_and_generate_prompts(source_bytes, num_variations)
        
        if not custom_prompts:
            yield sse_log('error', 'ERR', 'Echec de la generation des prompts par Gemini', 'red')
            yield sse_log('done', 'STOP', 'Arret', success=False, error='Prompt generation failed')
            return
        
        yield sse_log('success', 'SUCCES', str(len(custom_prompts)) + ' prompts personnalisés créés par l\'IA', 'green')
        
        # Afficher les prompts générés
        for i, prompt in enumerate(custom_prompts, 1):
            short_prompt = prompt[:100] + '...' if len(prompt) > 100 else prompt
            yield sse_log('info', 'PROMPT', 'Prompt ' + str(i) + ': ' + short_prompt, 'gray')
        
        # 🎨 ÉTAPE 2: GÉNÉRATION DES IMAGES
        yield sse_log('step', 'ETAPE', 'Etape 2/2: Generation de ' + str(len(custom_prompts)) + ' images avec les prompts IA...', 'magenta')
        
        generated_images = []
        
        for idx, prompt in enumerate(custom_prompts):
            variation_num = idx + 1
            progress_pct = int((idx / len(custom_prompts)) * 100)
            
            yield sse_log('generating', 'RETRY', '[' + str(variation_num) + '/' + str(len(custom_prompts)) + '] Generation image...', 'cyan', progress=progress_pct)
            yield sse_log('info', 'ROBOT', 'Envoi a Gemini 2.5 Flash Image...', 'gray')
            
            # Générer l'image avec retry automatique
            image_data = None
            max_retries = 2
            for attempt in range(max_retries + 1):
                image_data = image_generator.generate_product_variation(source_bytes, prompt, variation_num)
                if image_data:
                    break
                if attempt < max_retries:
                    yield sse_log('warning', 'RETRY', 'Retry ' + str(attempt + 1) + '/' + str(max_retries) + '...', 'orange')
                    time_module.sleep(1)
            
            if image_data:
                generated_images.append(image_data)
                img_size_kb = len(image_data) / 1024
                progress_done = int(((idx + 1) / len(custom_prompts)) * 100)
                yield sse_log('success', 'SUCCES', '[' + str(variation_num) + '/' + str(len(custom_prompts)) + '] Image generee (' + str(round(img_size_kb, 1)) + ' KB)', 'green', progress=progress_done)
            else:
                yield sse_log('warning', 'AVERTISSEMENT', '[' + str(variation_num) + '/' + str(len(custom_prompts)) + '] Image echouee apres ' + str(max_retries) + ' retries', 'orange')
            
            # Pause entre les requêtes
            if idx < len(custom_prompts) - 1:
                yield sse_log('info', 'WAIT', 'Pause 1s...', 'gray')
                time_module.sleep(1)
        
        yield sse_log('step', 'TOTAL', 'Generation terminee: ' + str(len(generated_images)) + '/' + str(len(custom_prompts)) + ' images creees', 'cyan')
        
        if not generated_images:
            yield sse_log('error', 'ERR', 'Aucune image generee', 'red')
            yield sse_log('done', 'ARRET', 'Arret', success=False, error='No images generated')
            return
        
        # UPLOAD VERS SHOPIFY
        yield sse_log('step', 'UPLOAD', 'Upload de ' + str(len(generated_images)) + ' images vers Shopify CDN...', 'yellow')
        
        for i in range(len(generated_images)):
            yield sse_log('info', 'UP', 'Upload image ' + str(i+1) + '/' + str(len(generated_images)) + '...', 'gray')
        
        upload_result = shopify_client.replace_product_images(product_id, generated_images)
        
        if upload_result['success']:
            yield sse_log('success', 'OK', str(upload_result['uploaded_count']) + ' images uploadees sur Shopify', 'green')
            yield sse_log('success', 'SUCCESS', 'GENERATION TERMINEE AVEC SUCCES!', 'green')
            yield sse_log('done', 'DONE', 'Termine', success=True, total_generated=len(generated_images), uploaded_count=upload_result['uploaded_count'], new_urls=upload_result.get('new_urls', []))
        else:
            yield sse_log('error', 'ERR', 'Erreur upload: ' + str(upload_result.get('error', 'Unknown')), 'red')
            yield sse_log('done', 'STOP', 'Arret', success=False, error=upload_result.get('error', 'Upload failed'), total_generated=len(generated_images))
    
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

        yield sse_log('info', 'ADD', 'Ajout de ' + str(num_variations) + ' images pour: ' + product_title, 'cyan')

        try:
            image_generator = ImageGenerator(gemini_api_key)
            yield sse_log('success', 'OK', 'Gemini initialise', 'green')
        except Exception as e:
            yield sse_log('error', 'ERR', 'Erreur Gemini: ' + str(e), 'red')
            yield sse_log('done', 'STOP', 'Arret', success=False, error=str(e))
            return

        try:
            shopify_client = ShopifyClient(store_url, access_token=access_token)
            yield sse_log('success', 'OK', 'Shopify connecte', 'green')
        except Exception as e:
            yield sse_log('error', 'ERR', 'Erreur Shopify: ' + str(e), 'red')
            yield sse_log('done', 'STOP', 'Arret', success=False, error=str(e))
            return

        yield sse_log('step', 'DL', 'Telechargement image source...', 'yellow')
        source_bytes = image_generator.download_image_from_url(source_image_url)

        if not source_bytes:
            yield sse_log('error', 'ERR', 'Impossible de télécharger l\'image', 'red')
            yield sse_log('done', 'STOP', 'Arret', success=False, error='Download failed')
            return

        yield sse_log('success', 'OK', 'Image téléchargée', 'green')

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

            yield sse_log('generating', 'RETRY', '[' + str(idx+1) + '/' + str(num_variations) + '] ' + variation_name + '...', 'cyan', progress=progress_pct)

            prompt = 'Create a realistic product photo of this exact same product ' + variation_desc + '. Keep the product IDENTICAL. Pinterest style, aesthetic, inspiring. No text, no logos, no fantasy.'

            image_data = None
            for attempt in range(3):
                image_data = image_generator.generate_product_variation(source_bytes, prompt, idx + 1)
                if image_data:
                    break
                if attempt < 2:
                    yield sse_log('warning', 'RETRY', 'Retry...', 'orange')
                    time_module.sleep(1)

            if image_data:
                generated_images.append(image_data)
                progress_done = int(((idx + 1) / num_variations) * 100)
                yield sse_log('success', 'SUCCES', '[' + str(idx+1) + '/' + str(num_variations) + '] ' + variation_name + ' generee', 'green', progress=progress_done)
            else:
                yield sse_log('warning', 'AVERTISSEMENT', variation_name + ' echouee', 'orange')

            if idx < num_variations - 1:
                time_module.sleep(1)

        if not generated_images:
            yield sse_log('error', 'ERR', 'Aucune image generee', 'red')
            yield sse_log('done', 'ARRET', 'Arret', success=False, error='No images')
            return

        yield sse_log('step', 'UPLOAD', 'Upload de ' + str(len(generated_images)) + ' images...', 'yellow')

        # AJOUTER les images sans supprimer les existantes
        uploaded_count = 0
        for i, img_data in enumerate(generated_images):
            result = shopify_client.upload_image_to_product(product_id, img_data, filename='ai_extra_' + str(i+1) + '.png')
            if result['success']:
                uploaded_count += 1
                yield sse_log('info', 'UP', 'Image ' + str(i+1) + ' uploadee', 'gray')

        if uploaded_count > 0:
            yield sse_log('success', 'SUCCES', str(uploaded_count) + ' images ajoutees!', 'green')
            yield sse_log('done', 'DONE', 'Termine', success=True, uploaded_count=uploaded_count)
        else:
            yield sse_log('error', 'ERR', 'Erreur upload', 'red')
            yield sse_log('done', 'STOP', 'Arret', success=False, error='Upload failed')

    return Response(stream_with_context(generate_with_logs()), mimetype='text/event-stream')


@app.route('/api/shopify/reorder-images', methods=['POST'])
def reorder_images():
    """Réorganise les images d'un produit"""
    try:
        data = request.json
        product_id = data.get('product_id')
        image_ids = data.get('image_ids', [])

        print(f"Reorder images - Product: {product_id}, Images: {image_ids}")

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
                    print(f"  SUCCES Image {image_id} -> position {position}")
                else:
                    print(f"  ERREUR Image {image_id}: {response.status_code} - {response.text}")
                    errors.append(f"Image {image_id}: {response.status_code}")
                    
            except Exception as e:
                print(f"  ERREUR Erreur image {image_id}: {e}")
                errors.append(str(e))

        print(f"SUCCES Reorder termine: {success_count}/{len(image_ids)} images repositionnees")
        
        if success_count > 0:
            return jsonify({'success': True, 'message': f'{success_count} positions mises à jour', 'errors': errors})
        else:
            return jsonify({'success': False, 'error': 'Aucune image repositionnée', 'errors': errors}), 400

    except Exception as e:
        print(f"ERREUR reorder_images: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
