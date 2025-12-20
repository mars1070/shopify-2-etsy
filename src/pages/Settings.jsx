import { useState, useEffect } from 'react'
import { Save, Key, AlertCircle, CheckCircle2, Store, Link2, Unlink } from 'lucide-react'
import axios from 'axios'

const Settings = () => {
  const [apiKey, setApiKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const [error, setError] = useState(null)
  
  // Shopify settings
  const [shopifyStoreUrl, setShopifyStoreUrl] = useState('')
  const [shopifyAccessToken, setShopifyAccessToken] = useState('')
  const [shopifyApiKey, setShopifyApiKey] = useState('')
  const [shopifyApiSecret, setShopifyApiSecret] = useState('')
  const [shopifyConnected, setShopifyConnected] = useState(false)
  const [shopifyShopName, setShopifyShopName] = useState('')
  const [shopifyLoading, setShopifyLoading] = useState(false)
  const [shopifyMessage, setShopifyMessage] = useState(null)
  const [shopifyError, setShopifyError] = useState(null)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const response = await axios.get('/api/settings')
      if (response.data.has_api_key) {
        setApiKey('••••••••••••••••')
      }
      // Charger les settings Shopify
      if (response.data.shopify_connected) {
        setShopifyConnected(true)
        setShopifyShopName(response.data.shopify_shop_name || '')
        setShopifyStoreUrl(response.data.shopify_store_url || '')
        setShopifyAccessToken('••••••••••••••••')
      }
    } catch (err) {
      console.error('Erreur détaillée loadSettings:', err)
      if (err.response) {
        console.error('Status:', err.response.status)
        console.error('Data:', err.response.data)
      }
    }
  }

  const handleSave = async () => {
    // Ne pas envoyer si c'est la clé masquée
    if (apiKey === '••••••••••••••••' || apiKey.includes('••••')) {
      setError('Veuillez entrer une nouvelle clé API (pas la clé masquée)')
      return
    }
    
    setLoading(true)
    setMessage(null)
    setError(null)

    try {
      const response = await axios.post('/api/settings', {
        gemini_api_key: apiKey,
      })

      setMessage(response.data.message || 'Clé API Gemini validée et enregistrée avec succès!')
      setTimeout(() => setMessage(null), 5000)
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'Erreur lors de l\'enregistrement'
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const handleShopifyConnect = async () => {
    setShopifyLoading(true)
    setShopifyMessage(null)
    setShopifyError(null)

    // Si on a Client ID + Secret, utiliser OAuth
    if (shopifyApiKey && shopifyApiSecret && !shopifyAccessToken) {
      try {
        const response = await axios.post('/api/shopify/oauth/start', {
          store_url: shopifyStoreUrl,
          client_id: shopifyApiKey,
          client_secret: shopifyApiSecret,
        })

        if (response.data.success && response.data.auth_url) {
          // Rediriger vers Shopify pour l'autorisation
          setShopifyMessage('Redirection vers Shopify...')
          window.location.href = response.data.auth_url
          return
        }
      } catch (err) {
        const errorMsg = err.response?.data?.error || 'Erreur OAuth Shopify'
        setShopifyError(errorMsg)
        setShopifyLoading(false)
        return
      }
    }

    // Sinon, utiliser l'Access Token directement
    try {
      const response = await axios.post('/api/shopify/connect', {
        store_url: shopifyStoreUrl,
        access_token: shopifyAccessToken,
        api_key: shopifyApiKey,
        api_secret: shopifyApiSecret,
      })

      if (response.data.success) {
        setShopifyConnected(true)
        setShopifyShopName(response.data.shop_name)
        setShopifyMessage(`✅ Connecté à ${response.data.shop_name}`)
        setTimeout(() => setShopifyMessage(null), 5000)
      }
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'Erreur de connexion Shopify'
      setShopifyError(errorMsg)
    } finally {
      setShopifyLoading(false)
    }
  }

  const handleShopifyDisconnect = async () => {
    try {
      await axios.post('/api/shopify/disconnect')
      setShopifyConnected(false)
      setShopifyShopName('')
      setShopifyStoreUrl('')
      setShopifyAccessToken('')
      setShopifyApiKey('')
      setShopifyApiSecret('')
      setShopifyMessage('Déconnecté de Shopify')
      setTimeout(() => setShopifyMessage(null), 3000)
    } catch (err) {
      setShopifyError('Erreur lors de la déconnexion')
    }
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Paramètres</h1>
        <p className="text-gray-600">
          Configurez Shopify et Gemini AI pour la génération d'images et l'optimisation
        </p>
      </div>

      {/* Shopify Connection Section - EN PREMIER */}
      <div className="bg-white rounded-xl shadow-sm border-2 border-green-300 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Store className="w-6 h-6 text-green-600" />
            <h2 className="text-xl font-bold text-gray-900">🛒 Connexion Shopify</h2>
          </div>
          {shopifyConnected && (
            <span className="bg-green-100 text-green-800 text-xs font-semibold px-3 py-1 rounded-full flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" />
              Connecté
            </span>
          )}
        </div>

        {shopifyConnected ? (
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm text-green-800">
                <strong>Boutique connectée:</strong> {shopifyShopName}
              </p>
              <p className="text-xs text-green-600 mt-1">{shopifyStoreUrl}</p>
            </div>
            <button
              onClick={handleShopifyDisconnect}
              className="bg-red-100 hover:bg-red-200 text-red-700 font-semibold py-2 px-4 rounded-lg transition-colors flex items-center gap-2"
            >
              <Unlink className="w-4 h-4" />
              Déconnecter
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                🏪 URL de la boutique Shopify
              </label>
              <input
                type="text"
                value={shopifyStoreUrl}
                onChange={(e) => setShopifyStoreUrl(e.target.value)}
                placeholder="votre-boutique.myshopify.com"
                className="w-full px-4 py-3 border-2 border-green-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 text-lg"
              />
              <p className="mt-2 text-sm text-gray-600">
                👉 Exemple: <code className="bg-green-100 px-2 py-1 rounded font-bold">ma-boutique.myshopify.com</code>
              </p>
              <p className="mt-1 text-xs text-gray-500">
                Trouvez-le dans votre URL Shopify Admin: https://admin.shopify.com/store/<strong>VOTRE-NOM</strong>
              </p>
            </div>
            
            {/* Version API */}
            <div className="bg-gray-100 rounded-lg px-3 py-2 text-xs text-gray-600 flex items-center gap-2">
              <span>📡 API Version:</span>
              <code className="bg-white px-2 py-0.5 rounded font-mono font-bold">2025-10</code>
            </div>

            {/* Option 1: Client ID + Secret (recommandé) */}
            <div className="border-2 border-blue-400 rounded-lg p-4 bg-blue-50">
              <p className="text-sm font-semibold text-blue-800 mb-3">🔐 Option 1 : Client ID + API Secret (recommandé)</p>
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Client ID (API Key)</label>
                  <input
                    type="text"
                    value={shopifyApiKey}
                    onChange={(e) => setShopifyApiKey(e.target.value)}
                    placeholder="ex: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
                    className="w-full px-3 py-2 border-2 border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">API Secret Key</label>
                  <input
                    type="password"
                    value={shopifyApiSecret}
                    onChange={(e) => setShopifyApiSecret(e.target.value)}
                    placeholder="shpss_xxxxxxxxxxxxx"
                    className="w-full px-3 py-2 border-2 border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                  />
                </div>
              </div>
            </div>

            {/* OU séparateur */}
            <div className="flex items-center gap-3">
              <div className="flex-1 border-t border-gray-300"></div>
              <span className="text-xs text-gray-500 font-medium">OU</span>
              <div className="flex-1 border-t border-gray-300"></div>
            </div>

            {/* Option 2: Access Token */}
            <div className="border-2 border-gray-300 rounded-lg p-4 bg-gray-50">
              <p className="text-sm font-semibold text-gray-700 mb-3">🔑 Option 2 : Access Token (Admin API)</p>
              <input
                type="password"
                value={shopifyAccessToken}
                onChange={(e) => setShopifyAccessToken(e.target.value)}
                placeholder="shpat_xxxxxxxxxxxxx"
                className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 font-mono text-sm"
              />
            </div>

            {/* Tuto avec URL de redirection */}
            <div className="bg-yellow-50 border border-yellow-300 rounded-lg p-4">
              <p className="text-sm font-semibold text-yellow-800 mb-3">📖 Comment configurer l'app Shopify :</p>
              <ol className="text-xs text-yellow-800 space-y-2 list-decimal list-inside">
                <li>Shopify Admin → <strong>Settings</strong> → <strong>Apps and sales channels</strong> → <strong>Develop apps</strong></li>
                <li>Cliquez sur <strong>"Create an app"</strong> ou sélectionnez votre app existante</li>
                <li>Onglet <strong>"Configuration"</strong> → Admin API integration → Cochez les scopes :</li>
              </ol>
              
              {/* Scopes copiables */}
              <div className="mt-2 mb-3 space-y-2">
                <p className="text-xs text-yellow-700 font-medium">📋 TOUS les scopes requis (cochez-les tous dans Shopify) :</p>
                <div className="bg-white border border-yellow-400 rounded-lg p-3">
                  <div className="grid grid-cols-2 gap-1 text-xs font-mono text-gray-700 mb-2">
                    <span>✅ read_products</span>
                    <span>✅ write_products</span>
                    <span>✅ read_files</span>
                    <span>✅ write_files</span>
                    <span>✅ read_inventory</span>
                    <span>✅ write_inventory</span>
                    <span>✅ read_orders</span>
                    <span>✅ write_orders</span>
                    <span>✅ read_customers</span>
                    <span>✅ write_customers</span>
                    <span>✅ read_content</span>
                    <span>✅ write_content</span>
                    <span>✅ read_themes</span>
                    <span>✅ write_themes</span>
                    <span>✅ read_locales</span>
                    <span>✅ write_locales</span>
                    <span>✅ read_locations</span>
                    <span>✅ read_price_rules</span>
                    <span>✅ write_price_rules</span>
                    <span>✅ read_discounts</span>
                    <span>✅ write_discounts</span>
                    <span>✅ read_metaobjects</span>
                    <span>✅ write_metaobjects</span>
                    <span>✅ read_shipping</span>
                    <span>✅ write_shipping</span>
                    <span>✅ read_fulfillments</span>
                    <span>✅ write_fulfillments</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => navigator.clipboard.writeText('read_products,write_products,read_files,write_files,read_inventory,write_inventory,read_orders,write_orders,read_customers,write_customers,read_content,write_content,read_themes,write_themes,read_locales,write_locales,read_locations,read_price_rules,write_price_rules,read_discounts,write_discounts,read_metaobjects,write_metaobjects,read_shipping,write_shipping,read_fulfillments,write_fulfillments')}
                    className="w-full bg-yellow-200 hover:bg-yellow-300 text-yellow-800 px-3 py-2 rounded text-xs font-medium transition-colors"
                  >
                    📋 Copier tous les scopes
                  </button>
                </div>
              </div>

              <ol start="4" className="text-xs text-yellow-800 space-y-2 list-decimal list-inside">
                <li>Dans <strong>"App URL"</strong>, entrez :</li>
              </ol>
              <div className="mt-2 mb-3 flex items-center gap-2">
                <code className="flex-1 bg-white border border-yellow-400 px-3 py-2 rounded text-sm font-mono select-all">http://localhost:3000</code>
                <button
                  type="button"
                  onClick={() => navigator.clipboard.writeText('http://localhost:3000')}
                  className="bg-yellow-200 hover:bg-yellow-300 text-yellow-800 px-3 py-2 rounded text-xs font-medium transition-colors"
                >
                  📋 Copier
                </button>
              </div>

              <ol start="5" className="text-xs text-yellow-800 space-y-2 list-decimal list-inside">
                <li>Dans <strong>"Allowed redirection URL(s)"</strong>, entrez :</li>
              </ol>
              <div className="mt-2 mb-3 flex items-center gap-2">
                <code className="flex-1 bg-white border border-yellow-400 px-3 py-2 rounded text-sm font-mono select-all">http://localhost:3000/auth/callback</code>
                <button
                  type="button"
                  onClick={() => navigator.clipboard.writeText('http://localhost:3000/auth/callback')}
                  className="bg-yellow-200 hover:bg-yellow-300 text-yellow-800 px-3 py-2 rounded text-xs font-medium transition-colors"
                >
                  📋 Copier
                </button>
              </div>

              <ol start="6" className="text-xs text-yellow-800 space-y-2 list-decimal list-inside">
                <li>Cliquez sur <strong>"Save"</strong> puis <strong>"Install app"</strong></li>
                <li>Onglet <strong>"API credentials"</strong> → Copiez le <strong>Client ID</strong> et <strong>API Secret Key</strong></li>
              </ol>
              <p className="text-xs text-red-600 font-medium mt-2">⚠️ L'Access Token ne s'affiche qu'une seule fois après "Reveal token once" !</p>
            </div>

            <button
              onClick={handleShopifyConnect}
              disabled={shopifyLoading || !shopifyStoreUrl || (!shopifyAccessToken && !(shopifyApiKey && shopifyApiSecret))}
              className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-bold py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2 text-lg"
            >
              {shopifyLoading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Connexion en cours...
                </>
              ) : (
                <>
                  <Link2 className="w-5 h-5" />
                  Connecter Shopify
                </>
              )}
            </button>
          </div>
        )}

        {/* Shopify Messages */}
        {shopifyMessage && (
          <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-3 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-600" />
            <p className="text-sm text-green-700">{shopifyMessage}</p>
          </div>
        )}
        {shopifyError && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-600" />
            <p className="text-sm text-red-700">{shopifyError}</p>
          </div>
        )}
      </div>

      {/* API Key Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center gap-3 mb-4">
          <Key className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Clé API Gemini</h2>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              API Key
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Entrez votre clé API Gemini"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="mt-2 text-sm text-gray-500">
              Obtenez votre clé API sur{' '}
              <a
                href="https://makersuite.google.com/app/apikey"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                Google AI Studio
              </a>
            </p>
          </div>

          <button
            onClick={handleSave}
            disabled={loading || !apiKey}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-semibold py-2 px-6 rounded-lg transition-colors flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Validation en cours...
              </>
            ) : (
              <>
                <Save className="w-5 h-5" />
                Valider et Enregistrer
              </>
            )}
          </button>
          
          {loading && (
            <p className="text-sm text-gray-600 mt-2">
              🔍 Vérification de la clé API avec Gemini...
            </p>
          )}
        </div>
      </div>

      {/* Success Message */}
      {message && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
          <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-green-700">{message}</p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Info Shopify */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
        <h3 className="font-semibold text-green-900 mb-2">🛒 Pourquoi connecter Shopify ?</h3>
        <p className="text-sm text-green-800 mb-3">
          La connexion Shopify permet de :
        </p>
        <ul className="text-sm text-green-800 space-y-1 list-disc list-inside">
          <li><strong>Lire les images CDN</strong> de vos produits</li>
          <li><strong>Générer des variations AI</strong> avec Gemini 2.5 Flash Image</li>
          <li><strong>Uploader automatiquement</strong> les nouvelles images</li>
          <li><strong>Récupérer les URLs CDN</strong> pour le CSV Etsy</li>
        </ul>
        
        <div className="mt-4 pt-4 border-t border-green-300">
          <p className="text-sm text-green-900 font-semibold mb-1">📋 Scopes requis pour l'app Shopify :</p>
          <code className="text-xs bg-green-100 px-2 py-1 rounded">read_products, write_products</code>
        </div>
      </div>

      {/* Info Section */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mt-6">
        <h3 className="font-semibold text-blue-900 mb-2">À propos de Gemini AI</h3>
        <p className="text-sm text-blue-800 mb-3">
          Gemini AI analyse automatiquement la première image de chaque produit pour générer :
        </p>
        <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
          <li>🖼️ <strong>Variations d'images</strong> (15 angles différents, réalistes)</li>
          <li>Titres optimisés pour Etsy (max 140 caractères)</li>
          <li>Descriptions SEO attractives avec FAQ</li>
          <li>Tags pertinents et recherchés (13 tags)</li>
          <li>🎯 <strong>Catégories Etsy automatiques</strong> (les plus spécifiques)</li>
        </ul>
        
        <div className="mt-4 pt-4 border-t border-blue-300">
          <p className="text-sm text-blue-900 font-semibold mb-1">🔒 Validation de la clé</p>
          <p className="text-sm text-blue-800">
            Votre clé API sera testée en temps réel avec Gemini avant d'être enregistrée. Seules les clés valides sont acceptées.
          </p>
        </div>
      </div>
    </div>
  )
}

export default Settings
