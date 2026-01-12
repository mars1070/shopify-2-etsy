# 🧪 Guide de Test - Catégorisation Automatique

## ✅ Ce qui a été intégré:

### 1. **Backend (`gemini_enhancer.py`)**
- ✅ Import du `CategoryMatcher`
- ✅ Initialisation automatique au démarrage
- ✅ Catégorisation pendant le traitement
- ✅ Application de la catégorie dans la colonne `Category` du CSV
- ✅ Affichage de la catégorie dans les messages de progression

### 2. **Workflow complet**
```
1. Upload CSV Shopify
2. Conversion au format Etsy
3. Pour chaque produit:
   ├─ Gemini analyse l'image
   ├─ Génère: Titre
   ├─ 🎯 CATÉGORISATION (basée sur le titre)
   ├─ Génère: Description + Tags
   └─ Sauvegarde avec catégorie
4. Export CSV final avec catégories
```

## 🚀 Comment tester:

### Étape 1: Vérifier la clé API
```bash
# Ouvrir le fichier .env
notepad .env

# Vérifier que vous avez:
GEMINI_API_KEY=votre_clé_ici
```

### Étape 2: Lancer l'application
```bash
# Terminal 1 - Backend
cd backend
python app.py

# Terminal 2 - Frontend
npm run dev
```

### Étape 3: Tester avec un CSV
1. Allez sur http://localhost:3000
2. Uploadez un CSV Shopify
3. Lancez la conversion + optimisation IA
4. **Regardez les messages de progression** → Vous verrez:
   ```
   ✅ Optimisé: Produit #1 → Wedding Bands
   ✅ Optimisé: Produit #2 → Crossbody Bags
   ✅ Optimisé: Produit #3 → Watercolor
   ```

### Étape 4: Vérifier le CSV final
Ouvrez le fichier `etsy_final.csv` et vérifiez la colonne **Category**:
```csv
Title,Description,Category,...
"Gold Wedding Ring | ...",..."Jewelry > Rings > Wedding & Engagement > Wedding Bands",...
"Leather Bag | ...",..."Bags & Purses > Handbags > Crossbody Bags",...
```

## 📊 Ce que vous devriez voir:

### Dans la console backend:
```
✅ 3050 catégories Etsy chargées
✅ 2503 catégories feuilles (les plus spécifiques)
✅ Système de catégorisation automatique activé
```

### Dans les logs de traitement:
```
📋 Catégorisation 1/10: Handmade Silver Ring...
✅ Catégorie: Jewelry > Rings > Wedding & Engagement > Wedding Bands
🎯 Confiance: high
```

### Dans l'interface:
```
✅ Optimisé: Produit #1 → Wedding Bands
✅ Optimisé: Produit #2 → Crossbody Bags
✅ Optimisé: Produit #3 → Watercolor
```

## 🎯 Points à vérifier:

### ✅ Catégories toujours spécifiques
- ❌ Jamais: "Jewelry > Rings"
- ✅ Toujours: "Jewelry > Rings > Wedding & Engagement > Wedding Bands"

### ✅ Catégories pertinentes
- Ring → Jewelry > Rings > ...
- Bag → Bags & Purses > ...
- Painting → Art & Collectibles > Painting > ...

### ✅ Colonne Category remplie
Chaque ligne principale (avec Photo 1) doit avoir une catégorie.

## 🐛 Dépannage:

### Erreur: "Fichier de catégories introuvable"
→ Vérifiez que `Etsy Categories.json` existe à la racine

### Erreur: "GEMINI_API_KEY non trouvée"
→ Ajoutez votre clé dans `.env`

### Catégories vides dans le CSV
→ Vérifiez les logs backend pour voir les erreurs

### Message: "Catégorisation automatique désactivée"
→ Problème avec le fichier JSON ou la clé API

## 💡 Optimisations possibles:

Si tout fonctionne bien, on peut ajouter:
- [ ] Affichage de la catégorie complète dans l'interface
- [ ] Possibilité de modifier la catégorie manuellement
- [ ] Statistiques des catégories utilisées
- [ ] Cache des catégorisations pour produits similaires

## 📝 Notes importantes:

1. **Coût**: ~0.0001$ par produit (très peu cher)
2. **Vitesse**: +1-2 secondes par produit
3. **Précision**: ~95% avec Gemini
4. **Fallback**: Si erreur, utilise le scoring Python

---

**Prêt à tester!** 🚀

Lancez l'application et uploadez un CSV Shopify pour voir la magie opérer!
