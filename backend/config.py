"""
Configuration par défaut pour les champs Etsy
Modifiez ces valeurs selon vos besoins
"""

ETSY_DEFAULTS = {
    # Qui a fabriqué le produit
    'who_made_it': 'I did',  # Options: 'I did', 'A member of my shop', 'Another company or person'
    
    # Type de produit
    'what_is_it': 'A finished product',  # Options: 'A finished product', 'A supply or tool to make things'
    
    # Quand a-t-il été fabriqué
    'when_made': '2020_2024',  # Format: 'YYYY_YYYY' ou 'made_to_order', 'YYYY', etc.
    
    # Options de renouvellement
    'renewal_options': 'Automatic',  # Options: 'Automatic', 'Manual'
    
    # Type de produit
    'product_type': 'physical',  # Options: 'physical', 'digital'
    
    # Matériaux par défaut (laissez vide pour remplir manuellement sur Etsy)
    'materials': '',
    
    # Quantité par défaut
    'default_quantity': 8,
    
    # Catégorie par défaut (sera remplie par l'utilisateur)
    'category': '',
    
    # Partenaires de production
    'production_partners': '',
    
    # Section (peut être vide)
    'section': '',
    
    # Profil d'expédition par défaut
    'shipping_profile': 'Free Delivery',
    
    # Politique de retour (peut être vide)
    'return_policy': '',
}

# Configuration pour le multiplicateur de prix
PRICE_CONFIG = {
    'default_multiplier': 4.0,
    'round_to': 0.99,  # Arrondir à X.99
}

# Configuration Gemini AI
GEMINI_CONFIG = {
    'model': 'gemini-1.5-flash',
    'max_image_size': (1024, 1024),
    'image_quality': 85,
    'rate_limit_delay': 2,  # Secondes entre chaque requête
}
