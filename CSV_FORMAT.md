# 📋 Format des CSV - Shopify vs Etsy

## 📥 Format Shopify (Input)

### Structure
Le CSV Shopify utilise une structure **multi-lignes par produit** :
- **Ligne 1** : Informations principales du produit (titre, description, prix, etc.)
- **Lignes suivantes** : Variantes et images supplémentaires

### Colonnes Principales

| Colonne | Description | Exemple |
|---------|-------------|---------|
| `Handle` | Identifiant unique du produit | `gold-tooth-grillz` |
| `Title` | Titre du produit | `Gold Tooth Grillz \| DripTeeth` |
| `Body (HTML)` | Description HTML | `<p>💎 Shine without limits...</p>` |
| `Vendor` | Marque/Vendeur | `DripTeeth` |
| `Tags` | Tags séparés par virgules | `grillz, gold, teeth` |
| `Option1 Name` | Nom de la variation 1 | `Color` |
| `Option1 Value` | Valeur de la variation 1 | `Gold` |
| `Variant Price` | Prix de la variante | `19.90` |
| `Variant SKU` | SKU de la variante | `200001033:361181#Gold` |
| `Image Src` | URL CDN de l'image | `https://cdn.shopify.com/...` |
| `Variant Image` | Image de la variante | `https://cdn.shopify.com/...` |

### Exemple de Structure

```csv
Handle,Title,Body (HTML),Vendor,Tags,Option1 Name,Option1 Value,Variant Price,Image Src
gold-grillz,Gold Grillz,<p>Description</p>,DripTeeth,grillz,Color,Gold,19.90,https://cdn.../img1.png
gold-grillz,,,,,Color,Silver,19.90,https://cdn.../img2.png
gold-grillz,,,,,,,,,https://cdn.../img3.png
gold-grillz,,,,,,,,,https://cdn.../img4.png
```

**Explication** :
- Ligne 1 : Produit principal + variante Gold + image 1
- Ligne 2 : Variante Silver + image 2
- Ligne 3 : Image supplémentaire 3
- Ligne 4 : Image supplémentaire 4

---

## 📤 Format Etsy (Output)

### Structure
Le CSV Etsy utilise également une structure **multi-lignes** mais organisée différemment :
- **Ligne principale** : Informations du produit + toutes les photos
- **Lignes variantes** : Une ligne par option de variation

### Colonnes Principales

| Colonne | Description | Valeur par défaut |
|---------|-------------|-------------------|
| `Title` | Titre (max 140 chars) | Optimisé par Gemini |
| `Description` | Description complète | Optimisée par Gemini |
| `Tags` | 13 tags max | Générés par Gemini |
| `Who made it?` | Fabricant | `I did` |
| `What is it?` | Type | `A finished product` |
| `When was it made?` | Période | `2020_2024` |
| `Materials` | Matériaux | `Copper, Gold plating, Zircon` |
| `Price` | Prix principal | Calculé avec multiplicateur |
| `Quantity` | Stock | `999` |
| `Photo 1` à `Photo 10` | URLs des images | Max 10 images |
| `Variation 1` | Nom variation 1 | Ex: `Color` |
| `V1 Option` | Option variation 1 | Ex: `Gold` |
| `Var Price` | Prix de la variante | Calculé avec multiplicateur |
| `Var Quantity` | Stock variante | `999` |

### Exemple de Structure

```csv
Title,Description,Tags,Price,Photo 1,Photo 2,Variation 1,V1 Option,Var Price
Gold Grillz,Description optimisée,grillz;gold;teeth,24.90,https://.../img1.png,https://.../img2.png,Color,Gold,24.90
,,,,,,,Silver,24.90
```

**Explication** :
- Ligne 1 : Produit + toutes les photos + variante Gold
- Ligne 2 : Variante Silver (les autres champs sont hérités)

---

## 🔄 Mapping des Champs

### Informations Produit

| Shopify | → | Etsy | Transformation |
|---------|---|------|----------------|
| `Title` | → | `Title` | Optimisé par Gemini (max 140 chars) |
| `Body (HTML)` | → | `Description` | Optimisé par Gemini (HTML → texte) |
| `Tags` | → | `Tags` | Régénérés par Gemini (13 tags) |
| `Handle` | → | `SKU` | Identique |
| `Vendor` | → | - | Non utilisé |

### Prix

| Shopify | → | Etsy | Transformation |
|---------|---|------|----------------|
| `Variant Price` | → | `Price` / `Var Price` | Prix × Multiplicateur → arrondi à X.90€ |

**Exemple** :
- Shopify : `10.00€`
- Multiplicateur : `2.5`
- Calcul : `10 × 2.5 = 25€`
- Etsy : `24.90€`

### Images

| Shopify | → | Etsy | Transformation |
|---------|---|------|----------------|
| `Image Src` (lignes multiples) | → | `Photo 1` à `Photo 10` | Regroupées sur une ligne (max 10) |
| `Variant Image` | → | `Var Photo` | Image spécifique à la variante |

### Variations

| Shopify | → | Etsy | Transformation |
|---------|---|------|----------------|
| `Option1 Name` | → | `Variation 1` | Nom de la variation |
| `Option1 Value` | → | `V1 Option` | Valeur de l'option |
| `Option2 Name` | → | `Variation 2` | Nom variation 2 (si existe) |
| `Option2 Value` | → | `V2 Option` | Valeur option 2 (si existe) |

---

## 🤖 Optimisation Gemini AI

Pour chaque produit, Gemini analyse la **première image** (`Photo 1`) et génère :

### 1. Titre Optimisé
- **Max 140 caractères** (limite Etsy)
- **SEO-friendly** avec mots-clés pertinents
- **Attractif** pour les acheteurs

**Exemple** :
```
Avant : "Gold Tooth Grillz | DripTeeth"
Après : "Gold Plated Tooth Grillz - Hip Hop Teeth Caps with Zircon Stones - Adjustable Dental Grills for Men & Women"
```

### 2. Description Complète
- **200-300 mots**
- **Caractéristiques détaillées**
- **Matériaux et fabrication**
- **Instructions d'utilisation**

### 3. Tags (13 maximum)
- **Termes recherchés** sur Etsy
- **Mix de mots-clés** larges et spécifiques
- **Optimisés pour le SEO**

**Exemple** :
```
grillz, gold grillz, tooth grillz, hip hop jewelry, teeth caps, dental grills, gold teeth, rapper jewelry, bling teeth, adjustable grillz, zircon grillz, men grillz, women grillz
```

---

## 📊 Statistiques de Conversion

Pour un fichier Shopify typique :

| Métrique | Valeur |
|----------|--------|
| Produits Shopify | 50 |
| Lignes CSV Shopify | ~200 (avec variantes/images) |
| Produits Etsy | 50 |
| Lignes CSV Etsy | ~150 (avec variantes) |
| Images par produit | 2-5 en moyenne |
| Variantes par produit | 1-3 en moyenne |

---

## ⚙️ Configuration Personnalisée

Modifiez `backend/config.py` pour personnaliser :

```python
ETSY_DEFAULTS = {
    'who_made_it': 'I did',           # Qui a fabriqué
    'what_is_it': 'A finished product', # Type de produit
    'when_made': '2020_2024',          # Période de fabrication
    'materials': 'Copper, Gold plating, Zircon', # Matériaux
    'default_quantity': 999,           # Stock par défaut
}
```

---

## 🔍 Validation

Avant d'importer sur Etsy, vérifiez :

✅ Tous les titres font moins de 140 caractères  
✅ Chaque produit a au moins 1 image  
✅ Les prix sont corrects (terminant par .90)  
✅ Les tags sont pertinents (max 13)  
✅ Les variations sont correctement mappées  

---

**Prêt à convertir ? Utilisez l'application web pour une conversion optimale ! 🚀**
