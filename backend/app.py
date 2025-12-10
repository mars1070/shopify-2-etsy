from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from flask_cors import CORS
import os
from dotenv import load_dotenv
from converter import ShopifyToEtsyConverter
from gemini_enhancer import GeminiEnhancer
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
                for progress in enhancer.enhance_generator(temp_path, output_path):
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
        print(f"✅ Settings loaded successfully")
        print(f"   Has API key: {bool(settings.get('gemini_api_key'))}")
        return jsonify({
            'has_api_key': bool(settings.get('gemini_api_key'))
        })
    except Exception as e:
        print(f"❌ Error in GET /api/settings: {e}")
        import traceback
        traceback.print_exc()
        # Retourner un résultat par défaut au lieu d'une erreur
        return jsonify({
            'has_api_key': False
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
