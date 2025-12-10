/**
 * SCRIPT JAVASCRIPT POUR CONSOLE NAVIGATEUR
 * Extrait TOUS les tooltips (chemins complets) des catégories Etsy
 * 
 * INSTRUCTIONS:
 * 1. Allez sur: https://www.etsy.com/sell
 * 2. Cliquez sur une catégorie pour ouvrir le sélecteur
 * 3. Ouvrez la console (F12)
 * 4. Collez ce script et appuyez sur Entrée
 * 5. Le JSON sera copié dans votre presse-papier
 */

(function() {
    console.log('🔍 Extraction des catégories Etsy avec tooltips...');
    
    const categories = new Set(); // Utiliser un Set pour éviter les doublons
    
    // Méthode 1: Chercher tous les éléments avec attribut title contenant ">"
    console.log('📋 Méthode 1: Recherche par attribut title...');
    document.querySelectorAll('[title]').forEach(elem => {
        const title = elem.getAttribute('title');
        if (title && title.includes('>')) {
            categories.add(title.trim());
        }
    });
    
    // Méthode 2: Chercher dans les data attributes
    console.log('📋 Méthode 2: Recherche par data attributes...');
    document.querySelectorAll('[data-category], [data-path], [data-taxonomy]').forEach(elem => {
        ['data-category', 'data-path', 'data-taxonomy'].forEach(attr => {
            const value = elem.getAttribute(attr);
            if (value && value.includes('>')) {
                categories.add(value.trim());
            }
        });
    });
    
    // Méthode 3: Chercher dans les aria-label
    console.log('📋 Méthode 3: Recherche par aria-label...');
    document.querySelectorAll('[aria-label]').forEach(elem => {
        const label = elem.getAttribute('aria-label');
        if (label && label.includes('>')) {
            categories.add(label.trim());
        }
    });
    
    // Méthode 4: Chercher dans le texte visible qui contient ">"
    console.log('📋 Méthode 4: Recherche dans le texte visible...');
    document.querySelectorAll('*').forEach(elem => {
        // Seulement les éléments de texte (pas les conteneurs)
        if (elem.children.length === 0) {
            const text = elem.textContent.trim();
            if (text && text.includes('>') && text.length < 200) {
                // Vérifier que c'est bien un chemin de catégorie
                const parts = text.split('>').map(p => p.trim());
                if (parts.length >= 2 && parts.every(p => p.length > 0 && p.length < 50)) {
                    categories.add(text);
                }
            }
        }
    });
    
    // Méthode 5: Chercher dans les options de select
    console.log('📋 Méthode 5: Recherche dans les select/options...');
    document.querySelectorAll('select option, [role="option"]').forEach(option => {
        const text = option.textContent.trim();
        const value = option.value;
        const title = option.getAttribute('title');
        
        [text, value, title].forEach(str => {
            if (str && str.includes('>')) {
                categories.add(str.trim());
            }
        });
    });
    
    // Méthode 6: Chercher dans les tooltips Bootstrap/Material UI
    console.log('📋 Méthode 6: Recherche dans les tooltips UI...');
    document.querySelectorAll('.tooltip, [data-tooltip], [data-bs-title], [data-original-title]').forEach(elem => {
        ['data-tooltip', 'data-bs-title', 'data-original-title', 'title'].forEach(attr => {
            const value = elem.getAttribute(attr);
            if (value && value.includes('>')) {
                categories.add(value.trim());
            }
        });
    });
    
    // Convertir en array et trier
    const result = Array.from(categories).sort();
    
    console.log(`\n✅ ${result.length} catégories uniques trouvées!`);
    
    if (result.length === 0) {
        console.log('\n⚠️ Aucune catégorie trouvée!');
        console.log('💡 Assurez-vous d\'être sur la bonne page Etsy');
        console.log('💡 Essayez d\'ouvrir le sélecteur de catégories avant de lancer le script');
        return null;
    }
    
    // Afficher quelques exemples
    console.log('\n📋 Exemples de catégories trouvées:');
    result.slice(0, 10).forEach(cat => {
        console.log(`  - ${cat}`);
    });
    
    // Créer le JSON
    const json = JSON.stringify(result, null, 2);
    
    // Copier dans le presse-papier
    try {
        // Méthode moderne
        navigator.clipboard.writeText(json).then(() => {
            console.log('\n✅ JSON copié dans le presse-papier!');
            console.log('📝 Collez-le dans votre fichier Categories Etsy.txt');
        }).catch(err => {
            // Fallback: afficher le JSON
            console.log('\n⚠️ Impossible de copier automatiquement');
            console.log('📋 Copiez manuellement le JSON ci-dessous:\n');
            console.log(json);
        });
    } catch (err) {
        // Fallback pour anciens navigateurs
        console.log('\n📋 Copiez manuellement le JSON ci-dessous:\n');
        console.log(json);
    }
    
    // Retourner les résultats pour inspection
    return result;
})();
