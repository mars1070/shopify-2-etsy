/**
 * SCRIPT JAVASCRIPT SUPER AGRESSIF
 * Extrait TOUTES les catégories Etsy possibles
 * À utiliser sur: https://www.etsy.com/sell (page de création de listing)
 */

(async function() {
    console.log('🚀 EXTRACTION SUPER AGRESSIVE DES CATÉGORIES ETSY');
    console.log('=' .repeat(60));
    
    const categories = new Set();
    let foundCount = 0;
    
    // Fonction pour ajouter une catégorie
    function addCategory(text) {
        if (!text || typeof text !== 'string') return false;
        text = text.trim();
        
        // Vérifier que c'est un chemin valide
        if (text.includes('>') && text.length > 5 && text.length < 300) {
            const parts = text.split('>').map(p => p.trim());
            if (parts.length >= 2 && parts.every(p => p.length > 0)) {
                if (!categories.has(text)) {
                    categories.add(text);
                    foundCount++;
                    if (foundCount <= 5) {
                        console.log(`  ✓ ${text}`);
                    }
                    return true;
                }
            }
        }
        return false;
    }
    
    // 1. Tous les attributs possibles
    console.log('\n📋 Scan des attributs HTML...');
    const attributes = ['title', 'aria-label', 'data-category', 'data-path', 'data-taxonomy', 
                       'data-tooltip', 'data-bs-title', 'data-original-title', 'alt', 'placeholder'];
    
    document.querySelectorAll('*').forEach(elem => {
        attributes.forEach(attr => {
            const value = elem.getAttribute(attr);
            if (value) addCategory(value);
        });
    });
    
    // 2. Texte visible
    console.log('\n📋 Scan du texte visible...');
    document.querySelectorAll('*').forEach(elem => {
        if (elem.children.length === 0) {
            addCategory(elem.textContent);
        }
    });
    
    // 3. Options de select
    console.log('\n📋 Scan des select/options...');
    document.querySelectorAll('select option, [role="option"], [role="menuitem"]').forEach(elem => {
        addCategory(elem.textContent);
        addCategory(elem.value);
        addCategory(elem.getAttribute('label'));
    });
    
    // 4. Scripts et données JSON dans la page
    console.log('\n📋 Scan des données JSON...');
    document.querySelectorAll('script[type="application/json"], script[type="application/ld+json"]').forEach(script => {
        try {
            const data = JSON.parse(script.textContent);
            JSON.stringify(data).match(/[^"]*>[^"]*/g)?.forEach(match => {
                addCategory(match);
            });
        } catch (e) {}
    });
    
    // 5. Variables JavaScript globales
    console.log('\n📋 Scan des variables globales...');
    try {
        const globalVars = Object.keys(window);
        globalVars.forEach(key => {
            try {
                const value = window[key];
                if (value && typeof value === 'object') {
                    JSON.stringify(value).match(/[^"]*>[^"]*/g)?.forEach(match => {
                        addCategory(match);
                    });
                }
            } catch (e) {}
        });
    } catch (e) {}
    
    // 6. LocalStorage et SessionStorage
    console.log('\n📋 Scan du storage...');
    try {
        [localStorage, sessionStorage].forEach(storage => {
            for (let i = 0; i < storage.length; i++) {
                const key = storage.key(i);
                const value = storage.getItem(key);
                if (value) {
                    value.match(/[^"]*>[^"]*/g)?.forEach(match => {
                        addCategory(match);
                    });
                }
            }
        });
    } catch (e) {}
    
    // 7. Fetch des données de l'API Etsy (si accessible)
    console.log('\n📋 Tentative de fetch API Etsy...');
    try {
        const response = await fetch('https://www.etsy.com/api/v3/application/seller-taxonomy/nodes', {
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('  ✓ Données API récupérées!');
            
            // Parser les données
            function parseNode(node, path = []) {
                const currentPath = [...path, node.name];
                const fullPath = currentPath.join(' > ');
                addCategory(fullPath);
                
                if (node.children) {
                    node.children.forEach(child => parseNode(child, currentPath));
                }
            }
            
            if (data.results) {
                data.results.forEach(node => parseNode(node));
            }
        }
    } catch (e) {
        console.log('  ⚠️ API non accessible (normal si pas connecté)');
    }
    
    // Résultats
    const result = Array.from(categories).sort();
    
    console.log('\n' + '='.repeat(60));
    console.log(`✅ ${result.length} CATÉGORIES UNIQUES TROUVÉES!`);
    console.log('='.repeat(60));
    
    if (result.length === 0) {
        console.log('\n❌ Aucune catégorie trouvée!');
        console.log('\n💡 Solutions:');
        console.log('  1. Assurez-vous d\'être sur https://www.etsy.com/sell');
        console.log('  2. Ouvrez le sélecteur de catégories');
        console.log('  3. Scrollez dans la liste des catégories');
        console.log('  4. Relancez ce script');
        return null;
    }
    
    // Afficher des exemples
    console.log('\n📋 Exemples (10 premiers):');
    result.slice(0, 10).forEach((cat, i) => {
        console.log(`  ${i + 1}. ${cat}`);
    });
    
    // Statistiques
    console.log('\n📊 Statistiques:');
    console.log(`  - Niveau 1 (X): ${result.filter(c => !c.includes('>')).length}`);
    console.log(`  - Niveau 2 (X > Y): ${result.filter(c => c.split('>').length === 2).length}`);
    console.log(`  - Niveau 3 (X > Y > Z): ${result.filter(c => c.split('>').length === 3).length}`);
    console.log(`  - Niveau 4+: ${result.filter(c => c.split('>').length >= 4).length}`);
    
    // Créer le JSON
    const json = JSON.stringify(result, null, 2);
    
    // Copier
    try {
        await navigator.clipboard.writeText(json);
        console.log('\n✅ JSON COPIÉ DANS LE PRESSE-PAPIER!');
        console.log('📝 Collez-le dans votre fichier!');
    } catch (err) {
        console.log('\n📋 COPIEZ LE JSON CI-DESSOUS:');
        console.log(json);
    }
    
    // Télécharger automatiquement
    try {
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'etsy_categories_extracted.json';
        a.click();
        URL.revokeObjectURL(url);
        console.log('\n💾 Fichier téléchargé: etsy_categories_extracted.json');
    } catch (e) {}
    
    return result;
})();
