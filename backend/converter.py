import pandas as pd
import math
from collections import defaultdict
from config import ETSY_DEFAULTS

class ShopifyToEtsyConverter:
    def __init__(self, price_multiplier=4.0):
        self.price_multiplier = price_multiplier
        self.sku_counter = 1  # Compteur SKU séquentiel
    
    def calculate_price(self, base_price):
        """
        Calcule le prix avec multiplicateur et arrondit à X.99
        Exemple: 10€ * 4 = 40€ → 39.99€
        Exemple: 33.43€ * 4 = 133.72€ → 139.99€
        """
        if not base_price or base_price == 0:
            return 0
        
        # Appliquer le multiplicateur
        new_price = base_price * self.price_multiplier
        
        # Arrondir à la dizaine supérieure puis soustraire 0.01 pour obtenir X.99
        # Ex: 133.72 → 140 → 139.99
        rounded_price = math.ceil(new_price / 10) * 10 - 0.01
        
        return round(rounded_price, 2)
    
    def parse_shopify_csv(self, file_path):
        """
        Parse le CSV Shopify et regroupe par produit (Handle)
        """
        df = pd.read_csv(file_path)
        products = defaultdict(lambda: {
            'title': '',
            'description': '',
            'tags': '',
            'vendor': '',
            'type': '',
            'images': [],
            'variants': [],
            'base_price': 0,
            'total_quantity': 0
        })
        
        for _, row in df.iterrows():
            handle = row['Handle']
            
            # Première ligne du produit contient toutes les infos
            if pd.notna(row.get('Title')) and row['Title']:
                products[handle]['title'] = row['Title']
                products[handle]['description'] = row.get('Body (HTML)', '')
                products[handle]['tags'] = row.get('Tags', '')
                products[handle]['vendor'] = row.get('Vendor', '')
                products[handle]['type'] = row.get('Type', '')
            
            # Collecter les images
            if pd.notna(row.get('Image Src')) and row['Image Src']:
                img_url = row['Image Src']
                if img_url not in products[handle]['images']:
                    products[handle]['images'].append(img_url)
            
            # Collecter les variantes
            qty = 0
            try:
                qty = int(float(row.get('Variant Inventory Qty', 0)))
            except:
                qty = 0
                
            products[handle]['total_quantity'] += qty

            if pd.notna(row.get('Variant SKU')) or pd.notna(row.get('Variant Price')):
                variant = {
                    'option1_name': row.get('Option1 Name', ''),
                    'option1_value': row.get('Option1 Value', ''),
                    'option2_name': row.get('Option2 Name', ''),
                    'option2_value': row.get('Option2 Value', ''),
                    'sku': row.get('Variant SKU', ''),
                    'price': float(row.get('Variant Price', 0)) if pd.notna(row.get('Variant Price')) else 0,
                    'image': row.get('Variant Image', ''),
                    'quantity': qty
                }
                products[handle]['variants'].append(variant)
                
                # Garder le prix de base (premier prix rencontré)
                if products[handle]['base_price'] == 0 and variant['price'] > 0:
                    products[handle]['base_price'] = variant['price']
        
        return products
    
    def convert_to_etsy_format(self, products, category='', product_type='Physical'):
        """
        Convertit les produits Shopify en format Etsy
        Format Etsy: 1ère ligne = produit complet, lignes suivantes = variantes additionnelles
        """
        etsy_rows = []
        
        for handle, product in products.items():
            # Préparer les images (max 10 pour Etsy)
            images = product['images'][:10]
            photo_dict = {f'Photo {i+1}': img for i, img in enumerate(images)}
            
            variants = product['variants']
            
            # Si pas de variantes, créer une ligne simple
            if not variants or len(variants) <= 1:
                base_price = product['base_price']
                etsy_price = self.calculate_price(base_price)
                quantity = ETSY_DEFAULTS['default_quantity']  # Toujours 8
                
                # Générer SKU séquentiel simple
                sku = f"{self.sku_counter:05d}"  # Format: 00001, 00002, etc.
                self.sku_counter += 1
                
                row = self._create_etsy_row(
                    category=category,
                    product_type=product_type,
                    price=etsy_price,
                    quantity=quantity,
                    sku=sku,
                    var1_name='',
                    var1_option='',
                    var2_name='',
                    var2_option='',
                    var_price='',
                    var_quantity='',
                    var_sku='',
                    photo_dict=photo_dict,
                    is_first_row=True
                )
                etsy_rows.append(row)
            else:
                # AVEC VARIANTES: créer une ligne par variante
                var1_name = variants[0].get('option1_name', '') if variants[0].get('option1_name') and pd.notna(variants[0].get('option1_name')) else ''
                var2_name = variants[0].get('option2_name', '') if variants[0].get('option2_name') and pd.notna(variants[0].get('option2_name')) else ''
                
                for idx, variant in enumerate(variants):
                    is_first = (idx == 0)
                    
                    # Prix de la variante
                    variant_price = variant.get('price', 0)
                    etsy_price = self.calculate_price(variant_price) if variant_price > 0 else self.calculate_price(product['base_price'])
                    
                    # Quantité de la variante (toujours 8)
                    var_qty = ETSY_DEFAULTS['default_quantity']
                    
                    # SKU séquentiel pour chaque variante
                    var_sku = f"{self.sku_counter:05d}"
                    self.sku_counter += 1
                    
                    # Options de variantes
                    var1_option = variant.get('option1_value', '') if pd.notna(variant.get('option1_value')) else ''
                    var2_option = variant.get('option2_value', '') if pd.notna(variant.get('option2_value')) else ''
                    
                    row = self._create_etsy_row(
                        category=category if is_first else '',
                        product_type=product_type if is_first else '',
                        price=etsy_price if is_first else '',
                        quantity=var_qty if is_first else '',
                        sku=var_sku if is_first else '',
                        var1_name=var1_name if is_first else '',
                        var1_option=var1_option,
                        var2_name=var2_name if is_first else '',
                        var2_option=var2_option,
                        var_price=etsy_price,
                        var_quantity=var_qty,
                        var_sku=var_sku,
                        photo_dict=photo_dict if is_first else {},
                        is_first_row=is_first
                    )
                    etsy_rows.append(row)
        
        return etsy_rows
    
    def _create_etsy_row(self, category, product_type, price, quantity, sku, 
                         var1_name, var1_option, var2_name, var2_option,
                         var_price, var_quantity, var_sku, photo_dict, is_first_row):
        """
        Crée une ligne au format Etsy
        """
        row = {
            'Title': '',  # Sera généré par Gemini
            'Description': '',  # Sera généré par Gemini
            'Category': category,
            'Who made it?': ETSY_DEFAULTS['who_made_it'] if is_first_row else '',
            'What is it?': ETSY_DEFAULTS['what_is_it'] if is_first_row else '',
            'When was it made?': ETSY_DEFAULTS['when_made'] if is_first_row else '',
            'Renewal options': ETSY_DEFAULTS['renewal_options'] if is_first_row else '',
            'Product type': product_type.capitalize() if product_type else '',
            'Tags': '',  # Sera généré par Gemini
            'Materials': ETSY_DEFAULTS['materials'] if is_first_row else '',
            'Production partners': ETSY_DEFAULTS['production_partners'] if is_first_row else '',
            'Section': ETSY_DEFAULTS['section'] if is_first_row else '',
            'Price': price,
            'Quantity': int(quantity) if quantity else '',
            'SKU': sku,
            'Variation 1': var1_name,
            'V1 Option': var1_option,
            'Variation 2': var2_name,
            'V2 Option': var2_option,
            'Var Price': var_price,
            'Var Quantity': int(var_quantity) if var_quantity else '',
            'Var SKU': var_sku,
            'Var Visibility': 'Active' if var1_option or var2_option else '',
            'Var Photo': '',
            'Shipping profile': ETSY_DEFAULTS['shipping_profile'] if is_first_row else '',
            'Weight': '',
            'Length': '',
            'Width': '',
            'Height': '',
            'Return policy': ETSY_DEFAULTS['return_policy'] if is_first_row else '',
            **photo_dict,
            'Video 1': '',
            'Digital file 1': '',
            'Digital file 2': '',
            'Digital file 3': '',
            'Digital file 4': '',
            'Digital file 5': ''
        }
        return row
    
    def convert(self, input_path, output_path, category='', product_type='Physical'):
        """
        Convertit un CSV Shopify en CSV Etsy
        """
        # Parser le CSV Shopify
        products = self.parse_shopify_csv(input_path)
        
        # Convertir au format Etsy
        etsy_rows = self.convert_to_etsy_format(products, category, product_type)
        
        # Créer le DataFrame et sauvegarder
        df = pd.DataFrame(etsy_rows)
        
        # Assurer l'ordre des colonnes Etsy
        etsy_columns = [
            'Title', 'Description', 'Category', 'Who made it?', 'What is it?', 
            'When was it made?', 'Renewal options', 'Product type', 'Tags', 
            'Materials', 'Production partners', 'Section', 'Price', 'Quantity', 
            'SKU', 'Variation 1', 'V1 Option', 'Variation 2', 'V2 Option', 
            'Var Price', 'Var Quantity', 'Var SKU', 'Var Visibility', 'Var Photo',
            'Shipping profile', 'Weight', 'Length', 'Width', 'Height', 'Return policy',
            'Photo 1', 'Photo 2', 'Photo 3', 'Photo 4', 'Photo 5', 
            'Photo 6', 'Photo 7', 'Photo 8', 'Photo 9', 'Photo 10',
            'Video 1', 'Digital file 1', 'Digital file 2', 'Digital file 3', 
            'Digital file 4', 'Digital file 5'
        ]
        
        # Ajouter les colonnes manquantes
        for col in etsy_columns:
            if col not in df.columns:
                df[col] = ''
        
        # Réorganiser les colonnes
        df = df[etsy_columns]
        
        # Sauvegarder
        df.to_csv(output_path, index=False)
        
        return len(products)
