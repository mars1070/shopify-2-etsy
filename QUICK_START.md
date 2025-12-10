# 🚀 Démarrage Rapide - Shopify 2 Etsy

## ⚡ Installation en 3 étapes

### 1️⃣ Installer les dépendances

Ouvrez un terminal PowerShell dans le dossier du projet et exécutez :

```powershell
# Installer les dépendances frontend
npm install

# Installer les dépendances backend
pip install -r requirements.txt
```

### 2️⃣ Configurer l'API Gemini

1. Obtenez votre clé API sur [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Copiez `.env.example` vers `.env`
3. Ajoutez votre clé API dans `.env` :

```env
GEMINI_API_KEY=votre_cle_api_ici
FLASK_ENV=development
```

**OU** configurez-la directement dans l'interface web (Paramètres)

### 3️⃣ Lancer l'application

**Option A : Script automatique (Windows)**
```powershell
.\start.bat
```

**Option B : Manuellement**

Terminal 1 - Backend :
```powershell
python backend/app.py
```

Terminal 2 - Frontend :
```powershell
npm run dev
```

## 🎯 Utilisation

1. Ouvrez http://localhost:3000
2. Allez dans **Paramètres** (en bas) et entrez votre clé API Gemini
3. Retournez sur **Conversion**
4. Importez votre CSV Shopify
5. Définissez le multiplicateur de prix (ex: 2.5)
6. Cliquez sur **Convertir avec Gemini AI**
7. Téléchargez votre CSV Etsy optimisé !

## 💰 Exemple de Prix

| Prix Shopify | Multiplicateur | Calcul | Prix Final Etsy |
|--------------|----------------|--------|-----------------|
| 10,00€       | 2.5            | 25,00€ | **24,90€**      |
| 15,00€       | 2.5            | 37,50€ | **37,90€**      |
| 20,00€       | 3.0            | 60,00€ | **59,90€**      |

Tous les prix sont automatiquement arrondis à **X,90€**

## 🤖 Ce que fait Gemini AI

Pour chaque produit, Gemini :
- 📸 Analyse la première image
- ✍️ Génère un titre optimisé SEO (max 140 caractères)
- 📝 Crée une description attractive (200-300 mots)
- 🏷️ Propose 13 tags pertinents pour Etsy

## 📁 Fichiers Importants

- `backend/config.py` : Modifier les valeurs par défaut Etsy
- `.env` : Clé API Gemini
- `uploads/` : CSV Shopify importés
- `outputs/` : CSV Etsy générés

## ⚠️ Dépannage

**Erreur "Module not found"**
```powershell
pip install -r requirements.txt
npm install
```

**Port déjà utilisé**
- Backend : Modifiez le port dans `backend/app.py` (ligne `app.run(port=5000)`)
- Frontend : Modifiez le port dans `vite.config.js`

**Gemini API ne fonctionne pas**
- Vérifiez que votre clé API est valide
- Assurez-vous d'avoir activé l'API Gemini sur Google Cloud

## 📞 Support

Besoin d'aide ? Vérifiez :
1. Les logs dans le terminal backend
2. La console du navigateur (F12)
3. Le fichier README.md pour plus de détails

---

**Prêt à convertir vos produits ? Let's go! 🚀**
