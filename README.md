# 🚀 Shopify 2 Etsy - CSV Converter avec AI

Application web moderne pour convertir automatiquement vos produits Shopify vers Etsy avec optimisation AI via Gemini.

## ✨ Fonctionnalités

- 📤 **Import CSV Shopify** : Supporte toutes les colonnes Shopify (images multiples, variantes, etc.)
- 💰 **Multiplicateur de prix intelligent** : Arrondi automatique à X,90€
- 🤖 **Optimisation AI Gemini** : Génération automatique de titres, descriptions et tags optimisés SEO
- 📸 **Analyse d'images** : Gemini analyse la première image de chaque produit
- 🎨 **Interface moderne** : Design sobre avec sidebar et icônes
- ⚙️ **Configuration facile** : Paramètres pour API Gemini

## 🛠️ Installation

### Prérequis
- Node.js 18+ 
- Python 3.9+
- Clé API Google Gemini ([Obtenir ici](https://makersuite.google.com/app/apikey))

### Étape 1 : Installer les dépendances

```bash
# Frontend (React + Vite)
npm install

# Backend (Flask)
pip install -r requirements.txt
```

### Étape 2 : Configuration

Créez un fichier `.env` à la racine :

```env
GEMINI_API_KEY=votre_cle_api_gemini
FLASK_ENV=development
```

## 🚀 Lancement

### Développement Local

#### Démarrer le backend (Terminal 1)

```bash
python backend/app.py
```

Le serveur Flask démarre sur `http://localhost:5000`

#### Démarrer le frontend (Terminal 2)

```bash
npm run dev
```

L'application React démarre sur `http://localhost:3000`

### Déploiement sur Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/VOTRE-USERNAME/shopify-2-etsy)

#### Étapes de déploiement :

1. **Push sur GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/VOTRE-USERNAME/shopify-2-etsy.git
   git push -u origin main
   ```

2. **Déployer sur Vercel**
   - Connectez-vous sur [vercel.com](https://vercel.com)
   - Cliquez sur "New Project"
   - Importez votre repository GitHub
   - Vercel détectera automatiquement la configuration
   - Cliquez sur "Deploy"

3. **Configurer les variables d'environnement sur Vercel**
   - Dans votre projet Vercel, allez dans "Settings" → "Environment Variables"
   - Ajoutez : `VERCEL_URL` (sera automatiquement défini par Vercel)

4. **Mettre à jour l'URL de redirection Shopify**
   - Dans votre app Shopify, mettez à jour "Allowed redirection URL(s)"
   - Remplacez `http://localhost:3000/auth/callback` par `https://votre-app.vercel.app/auth/callback`

## 📖 Utilisation

1. **Configurer l'API Gemini**
   - Cliquez sur "Paramètres" en bas de la sidebar
   - Entrez votre clé API Gemini
   - Cliquez sur "Enregistrer"

2. **Convertir vos produits**
   - Retournez sur "Conversion"
   - Importez votre CSV Shopify
   - Définissez le multiplicateur de prix (ex: 2.5)
   - Cliquez sur "Convertir avec Gemini AI"

3. **Télécharger le résultat**
   - Une fois la conversion terminée, téléchargez votre CSV Etsy
   - Importez-le directement dans Etsy !

## 💡 Système de Prix

Le multiplicateur de prix fonctionne ainsi :

- **Prix de base** : 10€
- **Multiplicateur** : 2.5
- **Calcul** : 10 × 2.5 = 25€
- **Arrondi automatique** : 24,90€

Tous les prix se terminent automatiquement par `,90€` pour optimiser les conversions.

## 🎨 Structure du Projet

```
shopify-to-etsy/
├── backend/
│   ├── app.py                 # Serveur Flask
│   ├── converter.py           # Logique conversion Shopify → Etsy
│   └── gemini_enhancer.py     # Intégration Gemini AI
├── src/
│   ├── components/
│   │   └── Layout.jsx         # Layout avec sidebar
│   ├── pages/
│   │   ├── Dashboard.jsx      # Page conversion
│   │   └── Settings.jsx       # Page paramètres
│   ├── App.jsx
│   └── main.jsx
├── uploads/                   # CSV Shopify importés
├── outputs/                   # CSV Etsy générés
├── package.json
├── requirements.txt
└── README.md
```

## 🔧 Technologies

### Frontend
- **React 18** : Framework UI
- **Vite** : Build tool ultra-rapide
- **TailwindCSS** : Styling moderne
- **Lucide React** : Icônes
- **Axios** : Requêtes HTTP

### Backend
- **Flask** : Framework Python
- **Pandas** : Manipulation CSV
- **Google Gemini AI** : Génération de contenu
- **Pillow** : Traitement d'images

## 📝 Format CSV

### Shopify (Input)
- Supporte toutes les colonnes Shopify standard
- Gère les images multiples (une ligne par image)
- Gère les variantes (une ligne par variante)

### Etsy (Output)
- Format compatible import Etsy
- Max 10 photos par produit
- Support des variations (2 niveaux)
- Métadonnées optimisées

## 🤖 Optimisation Gemini AI

Pour chaque produit, Gemini analyse la première image et génère :

1. **Titre optimisé** (max 140 caractères)
   - SEO-friendly
   - Mots-clés pertinents
   - Attractif pour les acheteurs

2. **Description complète** (200-300 mots)
   - Caractéristiques détaillées
   - Matériaux et fabrication
   - Instructions d'utilisation

3. **Tags** (13 tags)
   - Termes recherchés sur Etsy
   - Mix de mots-clés larges et spécifiques

## 🔒 Sécurité

- Les clés API sont stockées localement (fichier `settings.json`)
- Jamais exposées dans le code frontend
- `.env` et `settings.json` dans `.gitignore`

## 📄 Licence

MIT License - Libre d'utilisation

## 🆘 Support

Pour toute question ou problème, créez une issue sur GitHub.

---

Fait avec ❤️ pour simplifier la vie des vendeurs Shopify → Etsy
