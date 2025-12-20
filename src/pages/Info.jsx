import { Sparkles, Zap, Target, Tag, Image, Clock, Shield, TrendingUp } from 'lucide-react'

const Info = () => {
  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-6 text-white mb-6 shadow-lg">
        <div className="flex items-center gap-3 mb-3">
          <div className="bg-white/20 p-2 rounded-xl backdrop-blur">
            <Sparkles className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Shopify → Etsy Converter</h1>
            <p className="text-sm text-blue-100 mt-1">Powered by Gemini AI 2.5 Flash</p>
          </div>
        </div>
        <p className="text-sm text-blue-50 leading-relaxed">
          Convertissez automatiquement vos produits Shopify en listings Etsy optimisés avec l'intelligence artificielle. 
          Titres SEO, descriptions engageantes, tags pertinents et catégories automatiques.
        </p>
      </div>

      {/* Fonctionnalités principales */}
      <div className="grid md:grid-cols-2 gap-4 mb-6">
        {/* Conversion automatique */}
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-300 rounded-xl p-4 shadow-md">
          <div className="flex items-center gap-2 mb-3">
            <div className="bg-green-500 p-2 rounded-lg">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-lg font-bold text-gray-900">Conversion Automatique</h2>
          </div>
          <ul className="space-y-3 text-gray-700">
            <li className="flex items-start gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span><strong>Format Etsy:</strong> Conversion du CSV Shopify au format Etsy avec toutes les colonnes requises</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span><strong>Prix automatique:</strong> Multiplicateur personnalisable avec arrondi à X.99</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span><strong>SKU séquentiel:</strong> Génération automatique (00001, 00002, etc.)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span><strong>Variantes:</strong> Gestion complète des variantes Shopify (tailles, couleurs, etc.)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span><strong>Images:</strong> Jusqu'à 10 photos par produit</span>
            </li>
          </ul>
        </div>

        {/* IA Gemini */}
        <div className="bg-gradient-to-br from-purple-50 to-pink-50 border-2 border-purple-300 rounded-xl p-4 shadow-md">
          <div className="flex items-center gap-2 mb-3">
            <div className="bg-purple-500 p-2 rounded-lg">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-lg font-bold text-gray-900">Intelligence Artificielle</h2>
          </div>
          <ul className="space-y-3 text-gray-700">
            <li className="flex items-start gap-2">
              <span className="text-purple-600 font-bold">✓</span>
              <span><strong>Gemini 2.5 Flash:</strong> Modèle le plus récent (2025) avec 1M tokens input</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-purple-600 font-bold">✓</span>
              <span><strong>Analyse visuelle:</strong> Génération basée sur l'image du produit</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-purple-600 font-bold">✓</span>
              <span><strong>Parallélisation:</strong> 10 produits traités simultanément</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-purple-600 font-bold">✓</span>
              <span><strong>Retry automatique:</strong> 3 tentatives en cas d'échec avec backoff</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-purple-600 font-bold">✓</span>
              <span><strong>Vitesse:</strong> ~8 secondes par produit</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Ce qui est généré */}
      <div className="bg-white border-2 border-gray-200 rounded-xl p-5 shadow-md mb-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Image className="w-6 h-6 text-blue-600" />
          Contenu Généré par IA
        </h2>
        
        <div className="grid md:grid-cols-3 gap-4">
          {/* Titres */}
          <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
            <div className="text-2xl mb-2">📝</div>
            <h3 className="text-base font-bold text-blue-900 mb-2">Titres SEO</h3>
            <ul className="space-y-2 text-sm text-gray-700">
              <li>• Max 140 caractères</li>
              <li>• 3 phrases séparées par " | "</li>
              <li>• Mots-clés optimisés</li>
              <li>• Couleur/matériau en premier</li>
            </ul>
            <div className="mt-4 bg-white rounded-lg p-3 border border-blue-300">
              <p className="text-xs font-mono text-blue-800">
                "Wooden Table Lamp | Scandinavian Minimalist Design | USB Charging Bedside Light"
              </p>
            </div>
          </div>

          {/* Descriptions */}
          <div className="bg-orange-50 border-2 border-orange-200 rounded-lg p-4">
            <div className="text-2xl mb-2">💬</div>
            <h3 className="text-base font-bold text-orange-900 mb-2">Descriptions</h3>
            <ul className="space-y-2 text-sm text-gray-700">
              <li>• Hook avec emoji + titre</li>
              <li>• 2 paragraphes détaillés</li>
              <li>• Section Features (5-6 points)</li>
              <li>• FAQ (5-6 Q&A)</li>
              <li>• Formatage emojis uniquement</li>
            </ul>
            <div className="mt-4 bg-white rounded-lg p-3 border border-orange-300">
              <p className="text-xs font-mono text-orange-800">
                "Create the perfect ambiance...<br/>
                ✨ Transform Your Space<br/>
                This elegant wooden lamp..."
              </p>
            </div>
          </div>

          {/* Tags */}
          <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
            <div className="text-2xl mb-2">🏷️</div>
            <h3 className="text-base font-bold text-green-900 mb-2">Tags</h3>
            <ul className="space-y-2 text-sm text-gray-700">
              <li>• 13 mots-clés</li>
              <li>• Recherche directe (8 tags)</li>
              <li>• Attributs spécifiques (3 tags)</li>
              <li>• Niche large (2 tags)</li>
              <li>• Espaces dans les mots</li>
            </ul>
            <div className="mt-4 bg-white rounded-lg p-3 border border-green-300">
              <p className="text-xs font-mono text-green-800">
                "table lamp,wooden lamp,bedside light,scandinavian decor,minimalist lighting..."
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Catégorisation automatique */}
      <div className="bg-gradient-to-br from-indigo-50 to-purple-50 border-2 border-indigo-300 rounded-xl p-5 shadow-md mb-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="bg-indigo-500 p-2 rounded-lg">
            <Target className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">🎯 Catégorisation Automatique</h2>
            <p className="text-indigo-700 text-sm mt-1">Détection intelligente des catégories Etsy</p>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <h3 className="text-base font-bold text-gray-900 mb-3">Comment ça marche?</h3>
            <ol className="space-y-3 text-gray-700">
              <li className="flex items-start gap-3">
                <span className="bg-indigo-500 text-white font-bold rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 text-sm">1</span>
                <span><strong>Pré-filtrage:</strong> Analyse du titre pour réduire 2503 catégories à ~30 pertinentes</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="bg-indigo-500 text-white font-bold rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 text-sm">2</span>
                <span><strong>IA Gemini:</strong> Analyse le titre + description pour choisir la catégorie la plus spécifique</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="bg-indigo-500 text-white font-bold rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 text-sm">3</span>
                <span><strong>Catégories feuilles:</strong> Sélection uniquement des catégories finales (pas de catégories parentes)</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="bg-indigo-500 text-white font-bold rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 text-sm">4</span>
                <span><strong>Fallback:</strong> Détection de mots-clés digitaux pour produits numériques</span>
              </li>
            </ol>
          </div>

          <div className="bg-white rounded-lg p-4 border-2 border-indigo-200">
            <h3 className="text-base font-bold text-gray-900 mb-3">Exemples</h3>
            <div className="space-y-4">
              <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
                <p className="font-semibold text-gray-900 mb-2">💡 "Wooden Table Lamp"</p>
                <p className="text-sm text-indigo-700">→ Home & Living &gt; Lighting &gt; Lamps &gt; Table Lamps</p>
              </div>
              <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
                <p className="font-semibold text-gray-900 mb-2">💍 "Gold Diamond Ring"</p>
                <p className="text-sm text-indigo-700">→ Jewelry &gt; Rings &gt; Wedding & Engagement &gt; Engagement Rings</p>
              </div>
              <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
                <p className="font-semibold text-gray-900 mb-2">💻 "Wedding Invitation Template"</p>
                <p className="text-sm text-indigo-700">→ Weddings &gt; Invitations & Paper &gt; Templates</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Paramètres par défaut */}
      <div className="bg-white border-2 border-gray-200 rounded-xl p-5 shadow-md mb-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Shield className="w-6 h-6 text-green-600" />
          Paramètres par Défaut
        </h2>
        
        <div className="grid md:grid-cols-2 gap-4">
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <h4 className="font-bold text-gray-900 mb-2">📦 Quantité</h4>
              <p className="text-gray-700">Toujours <span className="font-bold text-blue-600">8</span> par produit/variante</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <h4 className="font-bold text-gray-900 mb-2">🚚 Livraison</h4>
              <p className="text-gray-700">Profil: <span className="font-bold text-blue-600">Free Delivery</span></p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <h4 className="font-bold text-gray-900 mb-2">🏭 Fabrication</h4>
              <p className="text-gray-700">Who made it: <span className="font-bold text-blue-600">I did</span></p>
            </div>
          </div>
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <h4 className="font-bold text-gray-900 mb-2">📅 Date</h4>
              <p className="text-gray-700">When made: <span className="font-bold text-blue-600">2020-2024</span></p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <h4 className="font-bold text-gray-900 mb-2">🔄 Renouvellement</h4>
              <p className="text-gray-700">Options: <span className="font-bold text-blue-600">Automatic</span></p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <h4 className="font-bold text-gray-900 mb-2">🧪 Matériaux</h4>
              <p className="text-gray-700">Laissé <span className="font-bold text-blue-600">vide</span> (à remplir manuellement)</p>
            </div>
          </div>
        </div>
      </div>

      {/* Performance */}
      <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border-2 border-yellow-300 rounded-xl p-5 shadow-md">
        <div className="flex items-center gap-3 mb-4">
          <div className="bg-yellow-500 p-2 rounded-lg">
            <TrendingUp className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">⚡ Performance</h2>
            <p className="text-yellow-700 text-sm mt-1">Optimisé pour la vitesse</p>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-4 border-2 border-yellow-200">
            <div className="text-2xl mb-2">🚀</div>
            <h3 className="text-base font-bold text-gray-900 mb-2">Parallélisation</h3>
            <p className="text-gray-700">10 produits traités simultanément pour une vitesse maximale</p>
          </div>
          <div className="bg-white rounded-lg p-4 border-2 border-yellow-200">
            <div className="text-2xl mb-2">🔄</div>
            <h3 className="text-base font-bold text-gray-900 mb-2">Retry Auto</h3>
            <p className="text-gray-700">3 tentatives avec délai croissant (2s, 4s, 6s) en cas d'échec</p>
          </div>
          <div className="bg-white rounded-lg p-4 border-2 border-yellow-200">
            <div className="text-2xl mb-2">⏱️</div>
            <h3 className="text-base font-bold text-gray-900 mb-2">Temps Estimé</h3>
            <p className="text-gray-700">~8 secondes par produit<br/>50 produits ≈ 7 minutes</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Info
