import { useState, useEffect, useRef } from 'react'
import { Image, RefreshCw, CheckCircle2, AlertCircle, Loader2, Store, Sparkles, Download, Eye, Terminal, ExternalLink, Pencil, Plus, GripVertical, X, ChevronLeft, ChevronRight, Wand2 } from 'lucide-react'
import axios from 'axios'

const ImageGeneration = () => {
  // États
  const [shopifyConnected, setShopifyConnected] = useState(false)
  const [shopifyShopName, setShopifyShopName] = useState('')
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(false)
  const [loadingProducts, setLoadingProducts] = useState(false)
  const [selectedProducts, setSelectedProducts] = useState([])
  const [numVariations, setNumVariations] = useState(10)
  const [generationProgress, setGenerationProgress] = useState({})
  const [generationResults, setGenerationResults] = useState({})
  const [error, setError] = useState(null)
  const [message, setMessage] = useState(null)
  const [hasGeminiKey, setHasGeminiKey] = useState(false)
  const [logs, setLogs] = useState([])
  const [showConsole, setShowConsole] = useState(false)
  const [currentProgress, setCurrentProgress] = useState(0)
  const [shopifyStoreUrl, setShopifyStoreUrl] = useState('')
  const [currentStatus, setCurrentStatus] = useState(null)
  const [carouselProduct, setCarouselProduct] = useState(null)
  const [carouselImages, setCarouselImages] = useState([])
  const [draggedIndex, setDraggedIndex] = useState(null)
  const logsEndRef = useRef(null)
  const consoleRef = useRef(null)

  // Auto-scroll des logs (moins intrusif - scroll interne seulement)
  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight
    }
  }, [logs])

  // Couleurs pour la console
  const getLogColor = (color) => {
    const colors = {
      cyan: 'text-cyan-400',
      green: 'text-green-400',
      yellow: 'text-yellow-400',
      red: 'text-red-400',
      orange: 'text-orange-400',
      magenta: 'text-fuchsia-400',
      gray: 'text-gray-400',
      white: 'text-white',
    }
    return colors[color] || 'text-white'
  }

  useEffect(() => {
    checkConnection()
  }, [])

  const checkConnection = async () => {
    try {
      const response = await axios.get('/api/settings')
      setShopifyConnected(response.data.shopify_connected || false)
      setShopifyShopName(response.data.shopify_shop_name || '')
      setShopifyStoreUrl(response.data.shopify_store_url || '')
      setHasGeminiKey(response.data.has_api_key || false)
      
      if (response.data.shopify_connected) {
        loadProducts()
      }
    } catch (err) {
      console.error('Erreur vérification connexion:', err)
    }
  }

  const loadProducts = async () => {
    setLoadingProducts(true)
    setError(null)
    try {
      const response = await axios.get('/api/shopify/products')
      if (response.data.success) {
        setProducts(response.data.products || [])
        setMessage(`✅ ${response.data.count} produits chargés`)
        setTimeout(() => setMessage(null), 3000)
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Erreur chargement produits')
    } finally {
      setLoadingProducts(false)
    }
  }

  const toggleProductSelection = (productId) => {
    setSelectedProducts(prev => 
      prev.includes(productId) 
        ? prev.filter(id => id !== productId)
        : [...prev, productId]
    )
  }

  const selectAllProducts = () => {
    if (selectedProducts.length === products.length) {
      setSelectedProducts([])
    } else {
      setSelectedProducts(products.map(p => p.id))
    }
  }

  const getProductImage = (product) => {
    if (product.images && product.images.length > 0) {
      return product.images[0].src
    }
    if (product.image && product.image.src) {
      return product.image.src
    }
    return null
  }

  const addLog = (logData) => {
    const timestamp = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    setLogs(prev => [...prev, { ...logData, timestamp }])
    // Mettre à jour le statut pour la notification
    if (logData.type !== 'info' || logData.emoji === '🎬') {
      setCurrentStatus({ emoji: logData.emoji, message: logData.message, color: logData.color })
    }
  }

  // Générer 5 images supplémentaires sans écraser les existantes
  const generateMoreImages = async (productId, productTitle, imageUrl) => {
    if (!imageUrl) {
      setError('Pas d\'image source pour ce produit')
      return
    }
    if (!hasGeminiKey) {
      setError('Configurez votre clé API Gemini dans les Paramètres')
      return
    }

    setLoading(true)
    setError(null)
    setLogs([])
    setShowConsole(true)
    setCurrentProgress(0)

    addLog({ type: 'info', emoji: '➕', message: `Génération de 5 images supplémentaires pour: ${productTitle}`, color: 'cyan' })

    try {
      const response = await fetch('/api/generate-images-add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: productId,
          product_title: productTitle,
          source_image_url: imageUrl,
          num_variations: 5
        })
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.type !== 'done') {
                addLog(data)
              }
              if (data.progress !== undefined) {
                setCurrentProgress(data.progress)
              }
              if (data.type === 'done') {
                if (data.success) {
                  addLog({ type: 'success', emoji: '🎉', message: `${data.uploaded_count || 5} images ajoutées!`, color: 'green' })
                  loadProducts() // Rafraîchir pour voir les nouvelles images
                } else {
                  addLog({ type: 'error', emoji: '❌', message: `Erreur: ${data.error}`, color: 'red' })
                }
              }
            } catch (e) {
              console.error('Erreur parsing SSE:', e)
            }
          }
        }
      }
    } catch (err) {
      addLog({ type: 'error', emoji: '❌', message: `Erreur: ${err.message}`, color: 'red' })
    }

    setLoading(false)
  }

  // Ouvrir le carrousel pour réorganiser les images
  const openImageCarousel = async (product) => {
    setCarouselProduct(product)
    setCarouselImages(product.images || [])
  }

  // Fermer le carrousel
  const closeCarousel = () => {
    setCarouselProduct(null)
    setCarouselImages([])
    setDraggedIndex(null)
  }

  // Drag and drop pour réorganiser
  const handleDragStart = (index) => {
    setDraggedIndex(index)
  }

  const handleDragOver = (e, index) => {
    e.preventDefault()
    if (draggedIndex === null || draggedIndex === index) return
    
    const newImages = [...carouselImages]
    const draggedItem = newImages[draggedIndex]
    newImages.splice(draggedIndex, 1)
    newImages.splice(index, 0, draggedItem)
    setCarouselImages(newImages)
    setDraggedIndex(index)
  }

  const handleDragEnd = async () => {
    setDraggedIndex(null)
    // Sauvegarde automatique après chaque drag & drop
    if (carouselProduct && carouselImages.length > 0) {
      await saveImagePositions(false) // false = pas de message ni fermeture
    }
  }

  // Sauvegarder les nouvelles positions
  const saveImagePositions = async (showFeedback = true) => {
    if (!carouselProduct) return
    
    try {
      const response = await axios.post('/api/shopify/reorder-images', {
        product_id: carouselProduct.id,
        image_ids: carouselImages.map(img => img.id)
      })
      
      if (response.data.success && showFeedback) {
        setMessage('✅ Positions des images mises à jour!')
        loadProducts()
        closeCarousel()
      }
    } catch (err) {
      if (showFeedback) {
        setError(err.response?.data?.error || 'Erreur lors de la mise à jour')
      }
    }
  }

  const startGeneration = async () => {
    if (selectedProducts.length === 0) {
      setError('Sélectionnez au moins un produit')
      return
    }

    if (!hasGeminiKey) {
      setError('Configurez votre clé API Gemini dans les Paramètres')
      return
    }

    setLoading(true)
    setError(null)
    setGenerationProgress({})
    setGenerationResults({})
    setLogs([])
    setShowConsole(true)
    setCurrentProgress(0)

    addLog({ type: 'info', emoji: '🎬', message: `Démarrage génération pour ${selectedProducts.length} produit(s)`, color: 'cyan' })

    for (let i = 0; i < selectedProducts.length; i++) {
      const productId = selectedProducts[i]
      const product = products.find(p => p.id === productId)
      const imageUrl = getProductImage(product)

      addLog({ type: 'step', emoji: '📦', message: `[Produit ${i + 1}/${selectedProducts.length}] ${product.title}`, color: 'magenta' })

      if (!imageUrl) {
        addLog({ type: 'error', emoji: '❌', message: 'Pas d\'image source pour ce produit', color: 'red' })
        setGenerationProgress(prev => ({
          ...prev,
          [productId]: { status: 'error', message: '❌ Pas d\'image source' }
        }))
        continue
      }

      setGenerationProgress(prev => ({
        ...prev,
        [productId]: { status: 'starting', message: '🚀 Démarrage...', progress: 0 }
      }))

      try {
        // Utiliser SSE pour le streaming des logs
        const response = await fetch('/api/generate-images-stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            product_id: productId,
            product_title: product.title,
            source_image_url: imageUrl,
            num_variations: numVariations
          })
        })

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                
                // Ajouter le log
                if (data.type !== 'done') {
                  addLog(data)
                }

                // Mettre à jour la progression
                if (data.progress !== undefined) {
                  setCurrentProgress(data.progress)
                  setGenerationProgress(prev => ({
                    ...prev,
                    [productId]: { status: 'generating', message: data.message, progress: data.progress }
                  }))
                }

                // Gérer la fin
                if (data.type === 'done') {
                  if (data.success) {
                    addLog({ type: 'success', emoji: '🎉', message: `Produit terminé: ${data.uploaded_count || data.total_generated} images`, color: 'green' })
                    setGenerationProgress(prev => ({
                      ...prev,
                      [productId]: { status: 'complete', message: '✅ Terminé', progress: 100 }
                    }))
                    setGenerationResults(prev => ({
                      ...prev,
                      [productId]: data
                    }))
                  } else {
                    addLog({ type: 'error', emoji: '❌', message: `Erreur: ${data.error}`, color: 'red' })
                    setGenerationProgress(prev => ({
                      ...prev,
                      [productId]: { status: 'error', message: data.error || '❌ Erreur' }
                    }))
                  }
                }
              } catch (e) {
                console.error('Erreur parsing SSE:', e)
              }
            }
          }
        }
      } catch (err) {
        addLog({ type: 'error', emoji: '❌', message: `Erreur réseau: ${err.message}`, color: 'red' })
        setGenerationProgress(prev => ({
          ...prev,
          [productId]: { status: 'error', message: err.message || '❌ Erreur' }
        }))
      }
    }

    addLog({ type: 'success', emoji: '🏁', message: `Génération terminée pour ${selectedProducts.length} produit(s)`, color: 'green' })
    setLoading(false)
    setMessage(`✅ Génération terminée pour ${selectedProducts.length} produit(s)`)
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="bg-purple-600 p-2 rounded-lg">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">🖼️ Génération d'Images AI</h1>
        </div>
        <p className="text-gray-600">
          Générez des variations d'images professionnelles pour vos produits Shopify avec Gemini AI
        </p>
      </div>

      {/* Explication du fonctionnement */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-xl p-6 mb-6">
        <h2 className="text-lg font-bold text-purple-900 mb-3">🎯 Comment ça marche ?</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl mb-2">1️⃣</div>
            <p className="text-sm text-gray-700"><strong>Connexion Shopify</strong><br/>Vos produits sont automatiquement chargés</p>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl mb-2">2️⃣</div>
            <p className="text-sm text-gray-700"><strong>Sélection</strong><br/>Choisissez les produits à traiter</p>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl mb-2">3️⃣</div>
            <p className="text-sm text-gray-700"><strong>Génération AI</strong><br/>Gemini crée des variations réalistes</p>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl mb-2">4️⃣</div>
            <p className="text-sm text-gray-700"><strong>Upload Auto</strong><br/>Images uploadées sur Shopify CDN</p>
          </div>
        </div>
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            <strong>💡 Astuce :</strong> La première image de chaque produit est utilisée comme source. 
            Gemini génère jusqu'à <strong>10 angles différents</strong> (vue de face, côté, 3/4, lifestyle, etc.)
          </p>
        </div>
      </div>

      {/* Statut connexion */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Store className="w-6 h-6 text-green-600" />
            <div>
              <h3 className="font-semibold text-gray-900">Connexion Shopify</h3>
              {shopifyConnected ? (
                <p className="text-sm text-green-600">✅ Connecté à {shopifyShopName}</p>
              ) : (
                <p className="text-sm text-red-600">❌ Non connecté - Allez dans Paramètres</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3">
            {hasGeminiKey ? (
              <span className="bg-green-100 text-green-700 text-xs font-medium px-3 py-1 rounded-full">
                ✅ Gemini API OK
              </span>
            ) : (
              <span className="bg-red-100 text-red-700 text-xs font-medium px-3 py-1 rounded-full">
                ❌ Gemini API manquante
              </span>
            )}
            {shopifyConnected && (
              <button
                onClick={loadProducts}
                disabled={loadingProducts}
                className="bg-blue-100 hover:bg-blue-200 text-blue-700 font-medium py-2 px-4 rounded-lg transition-colors flex items-center gap-2"
              >
                {loadingProducts ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
                Rafraîchir
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Console de Logs en temps réel */}
      {showConsole && (
        <div className="mb-6 rounded-xl overflow-hidden shadow-lg border border-gray-700">
          {/* Header de la console */}
          <div className="bg-gray-800 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Terminal className="w-5 h-5 text-green-400" />
              <span className="text-white font-mono font-semibold">Console de Génération</span>
              {loading && (
                <span className="flex items-center gap-2 text-cyan-400 text-sm">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  En cours...
                </span>
              )}
            </div>
            <div className="flex items-center gap-3">
              {currentProgress > 0 && (
                <div className="flex items-center gap-2">
                  <div className="w-32 bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-cyan-500 to-purple-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${currentProgress}%` }}
                    />
                  </div>
                  <span className="text-cyan-400 text-sm font-mono">{currentProgress}%</span>
                </div>
              )}
              <button
                onClick={() => setShowConsole(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>
          </div>
          
          {/* Corps de la console - fond noir */}
          <div ref={consoleRef} className="bg-black p-4 h-80 overflow-y-auto font-mono text-sm">
            {logs.map((log, index) => (
              <div key={index} className={`flex items-start gap-2 mb-1 ${getLogColor(log.color)}`}>
                <span className="text-gray-500 select-none">[{log.timestamp}]</span>
                <span className="select-none">{log.emoji}</span>
                <span className="flex-1">{log.message}</span>
              </div>
            ))}
            {loading && (
              <div className="flex items-center gap-2 text-cyan-400 animate-pulse">
                <span className="text-gray-500">[{new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}]</span>
                <span>⏳</span>
                <span>En attente...</span>
                <span className="inline-block w-2 h-4 bg-cyan-400 animate-pulse"></span>
              </div>
            )}
            <div ref={logsEndRef} />
          </div>
        </div>
      )}

      {/* Messages */}
      {message && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6 flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-green-600" />
          <p className="text-green-700">{message}</p>
        </div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Liste des produits */}
      {shopifyConnected && products.length > 0 && (
        <>
          {/* Contrôles - Design amélioré */}
          <div className="bg-gradient-to-r from-slate-50 to-purple-50 rounded-2xl shadow-md border border-purple-100 p-6 mb-6">
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
              
              {/* Section Sélection */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
                <button
                  onClick={selectAllProducts}
                  className={`flex items-center gap-3 px-4 py-2.5 rounded-xl font-medium transition-all duration-200 ${
                    selectedProducts.length === products.length 
                      ? 'bg-purple-600 text-white shadow-lg shadow-purple-200 hover:bg-purple-700' 
                      : 'bg-white text-gray-700 border-2 border-dashed border-gray-300 hover:border-purple-400 hover:text-purple-600'
                  }`}
                >
                  <div className={`w-5 h-5 rounded-md flex items-center justify-center ${
                    selectedProducts.length === products.length 
                      ? 'bg-white/20' 
                      : 'border-2 border-current'
                  }`}>
                    {selectedProducts.length === products.length && <CheckCircle2 className="w-4 h-4" />}
                  </div>
                  {selectedProducts.length === products.length ? 'Tout désélectionner' : 'Tout sélectionner'}
                </button>
                
                <div className="flex items-center gap-3 bg-white rounded-xl px-4 py-2.5 shadow-sm border border-gray-200">
                  <div className={`w-3 h-3 rounded-full ${selectedProducts.length > 0 ? 'bg-green-500 animate-pulse' : 'bg-gray-300'}`}></div>
                  <span className="text-gray-600 font-medium">
                    <span className={`text-xl font-bold ${selectedProducts.length > 0 ? 'text-purple-600' : 'text-gray-400'}`}>
                      {selectedProducts.length}
                    </span>
                    <span className="text-gray-400 mx-1">/</span>
                    <span className="text-gray-500">{products.length}</span>
                    <span className="text-gray-400 ml-2 text-sm">sélectionné(s)</span>
                  </span>
                </div>
              </div>
              
              {/* Section Configuration & Action */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 w-full lg:w-auto">
                
                {/* Sélecteur de variations */}
                <div className="bg-white rounded-xl px-4 py-3 shadow-sm border border-gray-200 flex items-center gap-3">
                  <Image className="w-5 h-5 text-purple-500" />
                  <div className="flex flex-col">
                    <span className="text-xs text-gray-400 font-medium uppercase tracking-wide">Variations</span>
                    <select
                      value={numVariations}
                      onChange={(e) => setNumVariations(Number(e.target.value))}
                      className="bg-transparent text-gray-800 font-semibold text-sm focus:outline-none cursor-pointer -mt-0.5"
                    >
                      <option value={5}>5 images</option>
                      <option value={10}>10 images (max Etsy)</option>
                      <option value={15}>15 images</option>
                    </select>
                  </div>
                </div>
                
                {/* Bouton Générer */}
                <button
                  onClick={startGeneration}
                  disabled={loading || selectedProducts.length === 0 || !hasGeminiKey}
                  className={`relative overflow-hidden font-bold py-3.5 px-8 rounded-xl transition-all duration-300 flex items-center justify-center gap-3 min-w-[220px] ${
                    loading || selectedProducts.length === 0 || !hasGeminiKey
                      ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                      : 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg shadow-purple-300 hover:shadow-xl hover:shadow-purple-400 hover:scale-[1.02] active:scale-[0.98]'
                  }`}
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Génération en cours...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5" />
                      <span>Générer les images</span>
                      {selectedProducts.length > 0 && (
                        <span className="bg-white/20 px-2.5 py-0.5 rounded-full text-sm">
                          {selectedProducts.length}
                        </span>
                      )}
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Grille de produits */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {products.map((product) => {
              const imageUrl = getProductImage(product)
              const isSelected = selectedProducts.includes(product.id)
              const progress = generationProgress[product.id]
              const result = generationResults[product.id]

              return (
                <div
                  key={product.id}
                  className={`bg-white rounded-xl shadow-sm border-2 transition-all cursor-pointer ${
                    isSelected ? 'border-purple-500 ring-2 ring-purple-200' : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => toggleProductSelection(product.id)}
                >
                  {/* Image */}
                  <div className="relative aspect-square bg-gray-100 rounded-t-xl overflow-hidden">
                    {imageUrl ? (
                      <img
                        src={imageUrl}
                        alt={product.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-gray-400">
                        <Image className="w-12 h-12" />
                      </div>
                    )}
                    
                    {/* Checkbox */}
                    <div className={`absolute top-3 left-3 w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                      isSelected ? 'bg-purple-600 border-purple-600' : 'bg-white border-gray-300'
                    }`}>
                      {isSelected && <CheckCircle2 className="w-4 h-4 text-white" />}
                    </div>

                    {/* Progress overlay */}
                    {progress && (
                      <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                        <div className="text-center text-white p-4">
                          {progress.status === 'starting' && <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2" />}
                          {progress.status === 'complete' && <CheckCircle2 className="w-8 h-8 text-green-400 mx-auto mb-2" />}
                          {progress.status === 'error' && <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />}
                          <p className="text-sm">{progress.message}</p>
                          {progress.progress > 0 && progress.progress < 100 && (
                            <div className="w-full bg-white/30 rounded-full h-2 mt-2">
                              <div 
                                className="bg-purple-500 h-2 rounded-full transition-all"
                                style={{ width: `${progress.progress}%` }}
                              />
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Info */}
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-900 truncate">{product.title}</h3>
                    <p className="text-sm text-gray-500">
                      {product.images?.length || 0} image(s) • {product.variants?.length || 1} variante(s)
                    </p>
                    
                    {result && result.success && (
                      <div className="mt-2 p-2 bg-green-50 rounded-lg">
                        <p className="text-xs text-green-700">
                          ✅ {result.uploaded_count || result.total_generated} nouvelles images
                        </p>
                      </div>
                    )}
                    
                    {/* Boutons d'action - 2 par ligne */}
                    <div className="mt-3 grid grid-cols-2 gap-2">
                      <a
                        href={`https://${shopifyStoreUrl.replace('.myshopify.com', '')}.myshopify.com/products/${product.handle}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="flex items-center justify-center gap-1 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-medium py-2 px-2 rounded-lg transition-colors"
                      >
                        <ExternalLink className="w-3 h-3" />
                        Voir en ligne
                      </a>
                      <a
                        href={`https://${shopifyStoreUrl.replace('.myshopify.com', '')}.myshopify.com/admin/products/${product.id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="flex items-center justify-center gap-1 bg-green-50 hover:bg-green-100 text-green-700 text-xs font-medium py-2 px-2 rounded-lg transition-colors"
                      >
                        <Store className="w-3 h-3" />
                        Voir Shopify
                      </a>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          generateMoreImages(product.id, product.title, getProductImage(product))
                        }}
                        disabled={loading}
                        className="flex items-center justify-center gap-1 bg-purple-50 hover:bg-purple-100 text-purple-700 text-xs font-medium py-2 px-2 rounded-lg transition-colors disabled:opacity-50"
                      >
                        <Wand2 className="w-3 h-3" />
                        +5 images
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          openImageCarousel(product)
                        }}
                        className="flex items-center justify-center gap-1 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-medium py-2 px-2 rounded-lg transition-colors"
                      >
                        <GripVertical className="w-3 h-3" />
                        Réorganiser
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}

      {/* État vide */}
      {shopifyConnected && products.length === 0 && !loadingProducts && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <Image className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Aucun produit trouvé</h3>
          <p className="text-gray-500 mb-4">Votre boutique Shopify ne contient pas de produits.</p>
          <button
            onClick={loadProducts}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-lg transition-colors"
          >
            Réessayer
          </button>
        </div>
      )}

      {/* Non connecté */}
      {!shopifyConnected && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <Store className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Connectez votre boutique Shopify</h3>
          <p className="text-gray-500 mb-4">
            Pour générer des images AI, vous devez d'abord connecter votre boutique Shopify.
          </p>
          <a
            href="/settings"
            className="inline-block bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-6 rounded-lg transition-colors"
          >
            ⚙️ Aller aux Paramètres
          </a>
        </div>
      )}

      {/* Info footer */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-xl p-6">
        <h3 className="font-semibold text-blue-900 mb-2">📸 Types de mises en situation générées :</h3>
        <p className="text-sm text-blue-700 mb-3">L'IA adapte automatiquement le décor selon le type de produit</p>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-sm text-blue-800">
          <span className="bg-blue-100 px-3 py-1 rounded-full text-center">Vue principale</span>
          <span className="bg-blue-100 px-3 py-1 rounded-full text-center">En situation</span>
          <span className="bg-blue-100 px-3 py-1 rounded-full text-center">Lifestyle</span>
          <span className="bg-blue-100 px-3 py-1 rounded-full text-center">Contexte</span>
          <span className="bg-blue-100 px-3 py-1 rounded-full text-center">Ambiance</span>
          <span className="bg-blue-100 px-3 py-1 rounded-full text-center">Décor adapté</span>
          <span className="bg-blue-100 px-3 py-1 rounded-full text-center">Environnement</span>
          <span className="bg-blue-100 px-3 py-1 rounded-full text-center">Mise en scène</span>
          <span className="bg-blue-100 px-3 py-1 rounded-full text-center">Close-up</span>
        </div>
      </div>

      {/* Modal Carrousel pour réorganiser les images */}
      {carouselProduct && (
        <div className="fixed inset-0 bg-black/85 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-[85vw] h-[85vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="bg-gray-100 px-6 py-4 flex items-center justify-between border-b flex-shrink-0">
              <div>
                <h3 className="font-semibold text-gray-900 text-lg">{carouselProduct.title}</h3>
                <p className="text-sm text-gray-500">Glissez-déposez pour réorganiser • {carouselImages.length} images • <span className="text-green-600">Sauvegarde auto ✓</span></p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={closeCarousel}
                  className="bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium py-2.5 px-6 rounded-lg transition-colors flex items-center gap-2"
                >
                  <X className="w-5 h-5" />
                  Fermer
                </button>
              </div>
            </div>
            
            {/* Grille d'images drag & drop - Images plus grosses */}
            <div className="p-6 overflow-y-auto flex-1">
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {carouselImages.map((image, index) => (
                  <div
                    key={image.id}
                    draggable
                    onDragStart={() => handleDragStart(index)}
                    onDragOver={(e) => handleDragOver(e, index)}
                    onDragEnd={handleDragEnd}
                    className={`relative aspect-square rounded-2xl overflow-hidden cursor-grab active:cursor-grabbing border-4 transition-all ${
                      draggedIndex === index ? 'border-purple-500 scale-105 shadow-2xl' : 'border-gray-200 hover:border-purple-300'
                    }`}
                  >
                    <img
                      src={image.src}
                      alt={`Image ${index + 1}`}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute top-3 left-3 bg-black/80 text-white text-sm font-bold px-3 py-1.5 rounded-lg">
                      {index + 1}
                    </div>
                    <div className="absolute inset-0 flex items-center justify-center opacity-0 hover:opacity-100 bg-black/40 transition-opacity">
                      <GripVertical className="w-12 h-12 text-white" />
                    </div>
                  </div>
                ))}
              </div>
              
              {carouselImages.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  <Image className="w-20 h-20 mx-auto mb-4 opacity-50" />
                  <p className="text-lg">Aucune image pour ce produit</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Notification flottante en bas à droite */}
      {loading && currentStatus && (
        <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-right">
          <div className="bg-gray-900 text-white rounded-xl shadow-2xl border border-gray-700 p-4 max-w-sm">
            <div className="flex items-center gap-3">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center text-xl">
                  {currentStatus.emoji}
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium truncate ${getLogColor(currentStatus.color)}`}>
                  {currentStatus.message}
                </p>
                <div className="mt-2 flex items-center gap-2">
                  <div className="flex-1 bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-purple-500 to-cyan-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${currentProgress}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-400 font-mono">{currentProgress}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ImageGeneration
