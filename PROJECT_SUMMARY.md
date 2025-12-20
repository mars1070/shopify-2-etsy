# 📦 Shopify 2 Etsy - Résumé du Projet

## 🎯 Objectif

Application web complète pour convertir automatiquement des produits Shopify vers Etsy avec optimisation AI via Google Gemini.

---

## ✨ Fonctionnalités Principales

### 1. **Conversion CSV Shopify → Etsy**
- ✅ Parse le format Shopify multi-lignes (produits/variantes/images)
- ✅ Regroupe intelligemment par produit (Handle)
- ✅ Extrait toutes les images (max 10 pour Etsy)
- ✅ Gère les variantes (2 niveaux : Variation 1 & 2)
- ✅ Mappe tous les champs vers le format Etsy

### 2. **Système de Prix Intelligent**
- ✅ Multiplicateur configurable (ex: 2.5x)
- ✅ Arrondi automatique à **X,90€**
- ✅ Exemple : 10€ × 2.5 = 25€ → **24,90€**
- ✅ Appliqué sur tous les prix et variantes

### 3. **Optimisation AI avec Gemini**
- ✅ Analyse automatique de la première image de chaque produit
- ✅ Génération de **titres optimisés SEO** (max 140 chars)
- ✅ Création de **descriptions attractives** (200-300 mots)
- ✅ Proposition de **13 tags pertinents** pour Etsy
- ✅ Conversion d'images CDN en base64 pour Gemini

### 4. **Interface Web Moderne**
- ✅ Design sobre et professionnel
- ✅ Sidebar de navigation avec icônes (Lucide React)
- ✅ Page Conversion : Import CSV + Configuration prix
- ✅ Page Paramètres : Configuration API Gemini
- ✅ Feedback en temps réel (loading, erreurs, succès)
- ✅ Téléchargement direct du CSV Etsy généré

### 5. **Configuration Flexible**
- ✅ Valeurs par défaut Etsy configurables (`backend/config.py`)
- ✅ "Who made it?" : `I did`
- ✅ "When was it made?" : `2020_2024`
- ✅ Materials : `Copper, Gold plating, Zircon`
- ✅ Quantité par défaut : `999`

---

## 🏗️ Architecture Technique

### **Frontend (React + Vite)**
```
src/
├── components/
│   └── Layout.jsx          # Layout avec sidebar
├── pages/
│   ├── Dashboard.jsx       # Page conversion
│   └── Settings.jsx        # Page paramètres
├── App.jsx                 # Router principal
├── main.jsx                # Point d'entrée
└── index.css               # Styles Tailwind
```

**Technologies** :
- React 18
- Vite (build tool)
- TailwindCSS (styling)
- Lucide React (icônes)
- Axios (HTTP)
- React Router (navigation)

### **Backend (Flask)**
```
backend/
├── app.py                  # Serveur Flask + API endpoints
├── converter.py            # Logique conversion Shopify → Etsy
├── gemini_enhancer.py      # Intégration Gemini AI
└── config.py               # Configuration Etsy par défaut
```

**Technologies** :
- Flask (serveur web)
- Pandas (manipulation CSV)
- Google Generative AI (Gemini)
- Pillow (traitement images)
- Requests (téléchargement images CDN)

---

## 🔌 API Endpoints

### `POST /api/convert`
Convertit un CSV Shopify en format Etsy (sans optimisation AI)

**Params** :
- `file` : Fichier CSV Shopify
- `price_multiplier` : Coefficient multiplicateur

**Response** :
```json
{
  "success": true,
  "temp_file": "temp_etsy.csv",
  "products_count": 50
}
```

### `POST /api/enhance`
Optimise un CSV Etsy avec Gemini AI

**Body** :
```json
{
  "temp_file": "temp_etsy.csv"
}
```

**Response** :
```json
{
  "success": true,
  "output_file": "etsy_final.csv",
  "products_count": 50
}
```

### `GET /api/download/<filename>`
Télécharge le CSV Etsy généré

### `GET /api/settings`
Récupère les paramètres (vérifie si API key existe)

### `POST /api/settings`
Sauvegarde la clé API Gemini

**Body** :
```json
{
  "gemini_api_key": "AIza..."
}
```

---

## 📁 Structure des Fichiers

```
Shopify 2 Etsy/
├── backend/                    # Backend Flask
│   ├── app.py                 # Serveur principal
│   ├── converter.py           # Conversion Shopify → Etsy
│   ├── gemini_enhancer.py     # Optimisation AI
│   └── config.py              # Configuration
├── src/                       # Frontend React
│   ├── components/
│   ├── pages/
│   └── ...
├── uploads/                   # CSV Shopify importés
├── outputs/                   # CSV Etsy générés
├── package.json               # Dépendances Node.js
├── requirements.txt           # Dépendances Python
├── vite.config.js            # Config Vite
├── tailwind.config.js        # Config Tailwind
├── .env                      # Variables d'environnement
├── .env.example              # Template .env
├── .gitignore                # Fichiers ignorés
├── start.bat                 # Script démarrage Windows
├── test_converter.py         # Test conversion sans UI
├── README.md                 # Documentation complète
├── QUICK_START.md            # Guide démarrage rapide
├── CSV_FORMAT.md             # Documentation formats CSV
└── PROJECT_SUMMARY.md        # Ce fichier
```

---

## 🚀 Workflow Complet

### 1. **Utilisateur importe CSV Shopify**
```
Frontend → POST /api/convert → Backend
```

### 2. **Backend parse et convertit**
```python
converter = ShopifyToEtsyConverter(price_multiplier=2.5)
products = converter.parse_shopify_csv(input_file)
# Regroupe par Handle
# Extrait images, variantes, prix
# Calcule nouveaux prix (× 2.5 → X.90€)
etsy_rows = converter.convert_to_etsy_format(products)
# Génère temp_etsy.csv
```

### 3. **Frontend demande optimisation AI**
```
Frontend → POST /api/enhance → Backend
```

### 4. **Backend optimise avec Gemini**
```python
enhancer = GeminiEnhancer(api_key)
for product in products:
    image = download_image(product.photo_1)
    enhanced = gemini.generate_content([prompt, image])
    # Extrait titre, description, tags
    product.update(enhanced)
# Génère etsy_final.csv
```

### 5. **Utilisateur télécharge CSV Etsy**
```
Frontend → GET /api/download/etsy_final.csv → Backend
```

---

## 💰 Exemple de Conversion

### Input (Shopify CSV)
```csv
Handle,Title,Body (HTML),Variant Price,Image Src,Option1 Name,Option1 Value
gold-grillz,Gold Grillz,<p>Description</p>,10.00,https://.../img1.png,Color,Gold
gold-grillz,,,10.00,https://.../img2.png,Color,Silver
gold-grillz,,,,,https://.../img3.png,,
```

### Output (Etsy CSV)
```csv
Title,Description,Tags,Price,Photo 1,Photo 2,Photo 3,Variation 1,V1 Option,Var Price
Gold Plated Tooth Grillz - Hip Hop...,Premium gold plated grillz...,grillz;gold;teeth;...,24.90,https://.../img1.png,https://.../img2.png,https://.../img3.png,Color,Gold,24.90
,,,,,,,Silver,24.90
```

**Transformations** :
- ✅ 3 lignes Shopify → 2 lignes Etsy
- ✅ Images regroupées (Photo 1, 2, 3)
- ✅ Prix : 10€ × 2.5 = 25€ → **24.90€**
- ✅ Titre optimisé par Gemini
- ✅ Description générée par Gemini
- ✅ Tags créés par Gemini

---

## 🎨 Interface Utilisateur

### Page Conversion
1. **Section Import** : Drag & drop CSV Shopify
2. **Section Prix** : Slider multiplicateur + aperçu calcul
3. **Section Conversion** : Bouton "Convertir avec Gemini AI"
4. **Section Résultat** : Téléchargement CSV Etsy

### Page Paramètres
1. **API Gemini** : Input clé API + bouton sauvegarder
2. **Info** : Lien vers Google AI Studio
3. **Documentation** : Explication Gemini AI

---

## 🔧 Configuration Personnalisée

### Modifier les valeurs par défaut Etsy
Éditez `backend/config.py` :

```python
ETSY_DEFAULTS = {
    'who_made_it': 'I did',
    'when_made': '2024',  # Changez l'année
    'materials': 'Vos matériaux',
    'default_quantity': 100,  # Changez le stock
}
```

### Modifier le multiplicateur par défaut
Dans `backend/config.py` :

```python
PRICE_CONFIG = {
    'default_multiplier': 3.0,  # Au lieu de 2.5
    'round_to': 0.90,
}
```

---

## 📊 Performance

### Temps de Traitement (estimé)

| Étape | Temps | Détails |
|-------|-------|---------|
| Upload CSV | < 1s | Dépend de la taille du fichier |
| Conversion Shopify → Etsy | 1-3s | 50 produits |
| Optimisation Gemini | 2-5min | 50 produits (2s/produit) |
| Téléchargement | < 1s | - |

**Total pour 50 produits** : ~3-5 minutes

### Rate Limiting Gemini
- Délai entre requêtes : **2 secondes**
- Évite les erreurs 429 (Too Many Requests)
- Configurable dans `backend/config.py`

---

## 🔒 Sécurité

### Clé API Gemini
- ✅ Stockée dans `.env` (backend) ou `settings.json`
- ✅ Jamais exposée au frontend
- ✅ `.env` et `settings.json` dans `.gitignore`
- ✅ Validation côté backend

### Fichiers Uploadés
- ✅ Stockés temporairement dans `uploads/`
- ✅ Validation extension (.csv uniquement)
- ✅ Nettoyage automatique possible

---

## 🧪 Tests

### Test sans interface web
```bash
python test_converter.py
```

Teste uniquement la conversion (sans Gemini AI).

### Test complet
1. Lancer l'application (`start.bat`)
2. Importer `Shopify CSV Model.csv`
3. Vérifier le CSV Etsy généré

---

## 📝 TODO / Améliorations Futures

- [ ] Gestion des erreurs Gemini plus robuste
- [ ] Cache des résultats Gemini (éviter re-génération)
- [ ] Support de plusieurs langues (FR/EN)
- [ ] Export Excel en plus du CSV
- [ ] Historique des conversions
- [ ] Prévisualisation avant téléchargement
- [ ] Batch processing (plusieurs CSV)
- [ ] Configuration UI pour valeurs Etsy par défaut
- [ ] Logs détaillés de conversion
- [ ] Tests unitaires

---

## 🆘 Dépannage

### Erreur "Module not found"
```bash
pip install -r requirements.txt
npm install
```

### Gemini API ne répond pas
- Vérifiez votre clé API
- Vérifiez votre quota Gemini
- Augmentez le délai dans `config.py`

### CSV mal formaté
- Vérifiez que le CSV Shopify est au bon format
- Consultez `CSV_FORMAT.md`

### Port déjà utilisé
- Changez le port dans `backend/app.py` (ligne `app.run(port=5000)`)
- Changez le port dans `vite.config.js`

---

## 📚 Documentation

- **README.md** : Documentation complète
- **QUICK_START.md** : Guide démarrage rapide
- **CSV_FORMAT.md** : Format des CSV Shopify/Etsy
- **PROJECT_SUMMARY.md** : Ce fichier (vue d'ensemble)

---

## 🎉 Conclusion

Application complète et fonctionnelle pour convertir Shopify → Etsy avec :
- ✅ Interface web moderne et intuitive
- ✅ Conversion intelligente des CSV
- ✅ Système de prix automatique (X.90€)
- ✅ Optimisation AI via Gemini
- ✅ Configuration flexible
- ✅ Documentation complète

**Prêt à l'emploi ! 🚀**
