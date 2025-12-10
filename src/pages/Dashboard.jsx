import { useState, useRef, useEffect } from 'react'
import { Upload, Download, Sparkles, AlertCircle, CheckCircle2, Info, ArrowLeftRight } from 'lucide-react'
import axios from 'axios'

const Dashboard = () => {
  const [file, setFile] = useState(null)
  const [priceMultiplier, setPriceMultiplier] = useState(4.0)
  const [productType, setProductType] = useState('physical')
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [tempPreview, setTempPreview] = useState(null)
  const [finalPreview, setFinalPreview] = useState(null)
  const [previewLoading, setPreviewLoading] = useState(false)

  const handleFileChange = async (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile && selectedFile.name.endsWith('.csv')) {
      setFile(selectedFile)
      setError(null)
      
      // Lire les stats du CSV
      const reader = new FileReader()
      reader.onload = (event) => {
        const text = event.target.result
        const lines = text.split('\n').filter(line => line.trim())
        
        // Compter les produits uniques (lignes avec Title non vide)
        let productsCount = 0
        let totalLines = 0
        
        for (let i = 1; i < lines.length; i++) {
          const line = lines[i]
          if (!line.trim()) continue
          
          totalLines++
          
          // Détecter si la ligne a un Title (colonne 2 en général)
          // Format CSV: Handle,Title,Body,...
          const match = line.match(/^[^,]*,([^,]+),/)
          if (match && match[1] && match[1].trim() && match[1] !== '""' && match[1] !== '') {
            productsCount++
          }
        }
        
        // Temps estimé: ~8 secondes par produit avec Gemini
        const estimatedMinutes = Math.ceil((productsCount * 8) / 60)
        
        setCsvStats({
          products: productsCount,
          variants: totalLines,
          estimatedTime: estimatedMinutes
        })
      }
      reader.readAsText(selectedFile)
    } else {
      setError('Veuillez sélectionner un fichier CSV valide')
    }
  }

  const fetchPreview = async (filename, setter) => {
    if (!filename) return
    try {
      setPreviewLoading(true)
      const response = await axios.get(`/api/preview/${filename}`)
      setter(response.data)
    } catch (err) {
      setter({ error: err.response?.data?.error || "Impossible de charger l'aperçu" })
    } finally {
      setPreviewLoading(false)
    }
  }

  const [notification, setNotification] = useState(null)
  const [productCount, setProductCount] = useState(null)
  const [csvStats, setCsvStats] = useState(null)
  const [logs, setLogs] = useState([])
  const logsEndRef = useRef(null)
  
  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString('fr-FR')
    const uniqueId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    setLogs(prev => [...prev, { message, type, timestamp, id: uniqueId }])
  }
  
  // Auto-scroll des logs vers le bas
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const handleConvert = async () => {
    if (!file) {
      setError('Veuillez sélectionner un fichier CSV')
      return
    }

    setLoading(true)
    setError(null)
    setProgress('1/2 - Conversion des données...')
    setTempPreview(null)
    setFinalPreview(null)
    setResult(null)
    setLogs([]) // Réinitialiser les logs
    setNotification({ type: 'info', message: 'Démarrage du processus...', progress: 0 })
    addLog('🚀 Démarrage de la conversion...', 'info')

    const formData = new FormData()
    formData.append('file', file)
    formData.append('price_multiplier', priceMultiplier)
    formData.append('category', '')  // Catégorie automatique par Gemini
    formData.append('product_type', productType)

    try {
      // Étape 1 : Conversion
      addLog('📄 Lecture du fichier CSV Shopify...', 'processing')
      const response = await axios.post('/api/convert', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      
      // Compter les produits uniques
      if (response.data.products_count) {
        setProductCount(response.data.products_count)
        addLog(`✅ ${response.data.products_count} produits détectés dans le CSV`, 'success')
        addLog(`🔄 Conversion au format Etsy terminée`, 'success')
        setNotification({ 
          type: 'info', 
          message: `📦 ${response.data.products_count} produits détectés`, 
          progress: 10 
        })
      }

      // Étape 2 : Optimisation AI (STREAMING)
      setProgress('2/2 - Optimisation AI en cours...')
      addLog('✨ Initialisation de Gemini AI 2.5 Flash...', 'processing')
      setNotification({ type: 'processing', message: 'Initialisation de Gemini AI...', progress: 5 })
      
      const streamResponse = await fetch('/api/enhance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ temp_file: response.data.temp_file })
      })

      // Vérifier si erreur (ex: clé API manquante)
      if (!streamResponse.ok) {
        const errorData = await streamResponse.json()
        throw new Error(errorData.error || 'Erreur serveur')
      }

      const reader = streamResponse.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6))
              
              if (data.status === 'error') {
                // Erreur dans le stream
                addLog(`❌ ${data.message}`, 'error')
                setError(data.message)
                setNotification({ type: 'error', message: data.message, progress: 0 })
                setLoading(false)
                break
              } else if (data.status === 'processing') {
                // Ajouter log pour chaque produit traité
                if (data.message.includes('Produit')) {
                  addLog(data.message, 'processing')
                }
                setNotification({ 
                  type: 'processing', 
                  message: data.message, 
                  progress: data.progress 
                })
              } else if (data.status === 'complete') {
                console.log('✅ Complete data:', data)
                addLog(`✅ Traitement terminé : ${data.products_count} produits`, 'success')
                addLog(`💾 Fichier final généré : ${data.output_file}`, 'success')
                setResult({
                  output_file: data.output_file,
                  products_count: data.products_count,
                  errors_report: data.errors_report
                })
                setNotification({ type: 'success', message: data.message || 'Terminé!', progress: 100 })
                fetchPreview('etsy_final.csv', setFinalPreview)
              }
            } catch (e) {
              console.error('Erreur parsing stream', e)
            }
          }
        }
      }

      setProgress(null)
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.message || 'Erreur lors de la conversion'
      addLog(`❌ Erreur: ${errorMsg}`, 'error')
      setError(errorMsg)
      
      // Message spécifique si clé API manquante
      if (errorMsg.includes('Clé API') || errorMsg.includes('API key')) {
        setNotification({ 
          type: 'error', 
          message: '🔑 Clé API Gemini manquante! Configurez-la dans Paramètres.', 
          progress: 0 
        })
      } else {
        setNotification({ type: 'error', message: errorMsg, progress: 0 })
      }
    } finally {
      setLoading(false)
    }
  }

  // ... (reste du code)

  // Notification Component
  const NotificationBubble = () => {
    if (!notification) return null

    const isSuccess = notification.type === 'success'
    const isError = notification.type === 'error'
    
    return (
      <div className={`fixed bottom-24 right-6 max-w-sm w-full bg-white rounded-2xl shadow-2xl border-2 p-4 transform transition-all duration-500 animate-slide-in z-[60] ${
        isSuccess ? 'border-green-500' : isError ? 'border-red-500' : 'border-blue-500'
      }`}>
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-full ${
            isSuccess ? 'bg-green-100 text-green-600' : isError ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'
          }`}>
            {isSuccess ? <CheckCircle2 className="w-6 h-6" /> : isError ? <AlertCircle className="w-6 h-6" /> : <Sparkles className="w-6 h-6 animate-pulse" />}
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <h4 className="font-bold text-gray-900">
                {isSuccess ? 'Optimisation Terminée' : isError ? 'Erreur' : 'Gemini AI 2.5 Flash'}
              </h4>
              {!isSuccess && !isError && notification.progress > 0 && (
                <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded-full">
                  {notification.progress}%
                </span>
              )}
            </div>
            
            <p className="text-sm text-gray-600 font-medium">
              {notification.message}
            </p>
            
            {!isSuccess && !isError && productCount && notification.progress > 0 && (
              <div className="mt-2 flex items-center gap-2 text-xs text-gray-500">
                <span className="font-semibold text-blue-600">
                  {Math.ceil((notification.progress / 100) * productCount)}/{productCount}
                </span>
                <span>produits optimisés</span>
              </div>
            )}
            
            {!isSuccess && !isError && (
              <div className="w-full bg-gray-200 rounded-full h-2.5 mt-3 overflow-hidden shadow-inner">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-purple-500 h-full transition-all duration-500 ease-out"
                  style={{ width: `${notification.progress}%` }}
                />
              </div>
            )}

            {isSuccess && notification.output_file && (
              <button
                onClick={() => handleDownloadFile(notification.output_file)}
                className="mt-3 w-full bg-green-600 hover:bg-green-700 text-white text-sm font-bold py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                <Download className="w-4 h-4" />
                Télécharger CSV
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  const handleDownloadFile = async (filename) => {
    try {
       const response = await axios.get(`/api/download/${filename}`, { responseType: 'blob' })
       const url = window.URL.createObjectURL(new Blob([response.data]))
       const link = document.createElement('a')
       link.href = url
       link.setAttribute('download', 'etsy_products.csv')
       document.body.appendChild(link)
       link.click()
       link.remove()
    } catch(e) {
       console.error(e)
    }
  }

  const renderPreviewCard = (title, previewData, color, emptyMessage) => {
    if (!previewData) {
      return (
        <div className="bg-gray-50 border-2 border-gray-200 rounded-xl p-6">
          <p className="text-gray-500 text-center">{emptyMessage}</p>
        </div>
      )
    }

    if (previewData.error) {
      return (
        <div className="bg-red-50 border-2 border-red-200 rounded-xl p-6">
          <p className="text-red-600 text-center font-semibold">{previewData.error}</p>
        </div>
      )
    }

    const columns = previewData.columns || []
    const rows = previewData.rows || []
    
    // Limiter à 50 produits pour performance
    const displayRows = rows.slice(0, 50)
    
    return (
      <div className="bg-white border-2 border-gray-300 rounded-xl overflow-hidden shadow-md">
        <div className="bg-gray-50 border-b-2 border-gray-300 px-4 py-3 flex items-center justify-between">
          <h4 className="font-bold text-gray-900 text-base flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-green-600" />
            {title}
          </h4>
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold text-gray-700">
              {displayRows.length} {displayRows.length > 1 ? 'lignes' : 'ligne'}
            </span>
            {rows.length > 50 && (
              <span className="text-xs bg-amber-100 text-amber-800 px-2 py-1 rounded-full font-semibold">
                Limité à 50
              </span>
            )}
          </div>
        </div>
        
        {displayRows.length > 0 ? (
          <div className="overflow-x-auto overflow-y-auto max-h-[600px] custom-scrollbar">
            <table className="min-w-full text-sm border-collapse">
              <thead className="bg-gray-100 sticky top-0 z-10 shadow-sm">
                <tr>
                  <th className="px-4 py-3 text-left font-bold text-gray-900 border-b-2 border-gray-300 whitespace-nowrap bg-gray-100">
                    #
                  </th>
                  {columns.map((col) => (
                    <th key={col} className="px-4 py-3 text-left font-bold text-gray-900 border-b-2 border-gray-300 whitespace-nowrap bg-gray-100">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {displayRows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-blue-50 transition-colors">
                    <td className="px-4 py-3 font-semibold text-gray-700 border-r border-gray-200">
                      {idx + 1}
                    </td>
                    {columns.map((col) => {
                      const isLongText = col === 'Description' || col === 'Tags' || col === 'Title'
                      return (
                        <td key={col} className={`px-4 py-3 text-gray-800 font-medium border-r border-gray-100 align-top ${isLongText ? '' : 'whitespace-nowrap'}`}>
                          {col === 'Photo 1' && row[col] ? (
                            <img src={row[col]} alt="Product" className="w-16 h-16 object-cover rounded border border-gray-200" />
                          ) : col === 'Description' ? (
                            <div className="min-w-[300px] max-w-[500px] text-sm leading-relaxed" title={row[col]}>
                              {String(row[col] || '').substring(0, 200)}{String(row[col] || '').length > 200 ? '...' : ''}
                            </div>
                          ) : col === 'Tags' ? (
                            <div className="min-w-[250px] max-w-[400px] text-sm" title={row[col]}>
                              {String(row[col] || '')}
                            </div>
                          ) : col === 'Title' ? (
                            <div className="min-w-[200px] max-w-[350px] font-semibold text-gray-900" title={row[col]}>
                              {String(row[col] || '')}
                            </div>
                          ) : (
                            <span className="text-gray-700">{String(row[col] || '')}</span>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">Aucune donnée disponible</p>
        )}
      </div>
    )
  }

  return (
    <div className="p-8 max-w-7xl mx-auto relative pb-32">
      <NotificationBubble />
      
      <div className="mb-8 bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="bg-blue-600/10 text-blue-700 p-3 rounded-2xl">
            <ArrowLeftRight className="w-10 h-10" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Conversion Shopify → Etsy
            </h1>
            <p className="text-gray-600 text-sm mt-2">
              ✨ Importez votre CSV Shopify et convertissez-le automatiquement en format Etsy avec optimisation AI Gemini
            </p>
          </div>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 mb-6">
        {/* Upload Section */}
        <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl shadow-md border-2 border-purple-200 p-6 flex flex-col gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-white text-purple-600 font-black text-2xl flex items-center justify-center shadow-sm">
              1
            </div>
            <div>
              <p className="text-sm uppercase tracking-wide text-purple-500 font-semibold">Étape 1</p>
              <h2 className="text-2xl font-bold text-gray-900">Importer le CSV Shopify</h2>
            </div>
          </div>

          <div className={`border-2 border-dashed ${file ? 'border-green-400 bg-green-50' : 'border-purple-300 bg-white'} rounded-lg p-8 text-center hover:border-purple-500 transition-all cursor-pointer`}>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              {file ? (
                <>
                  <CheckCircle2 className="w-16 h-16 text-green-600 mx-auto mb-3" />
                  <p className="text-lg font-bold text-green-700 mb-1">
                    ✅ {file.name}
                  </p>
                  <p className="text-sm text-green-600 mb-3">
                    Fichier prêt à être converti
                  </p>
                  
                  {/* Stats CSV */}
                  {csvStats && (
                    <div className="flex gap-4 justify-center mt-6">
                      <div className="bg-gradient-to-br from-blue-100 to-blue-200 border-2 border-blue-400 rounded-xl px-6 py-4 shadow-md min-w-[120px]">
                        <div className="text-4xl font-black text-blue-800 mb-1">{csvStats.products}</div>
                        <div className="text-sm font-medium text-blue-700">📦 Produits</div>
                      </div>
                      <div className="bg-gradient-to-br from-purple-100 to-purple-200 border-2 border-purple-400 rounded-xl px-6 py-4 shadow-md min-w-[120px]">
                        <div className="text-4xl font-black text-purple-800 mb-1">{csvStats.variants}</div>
                        <div className="text-sm font-medium text-purple-700">🔄 Variantes</div>
                      </div>
                      <div className="bg-gradient-to-br from-green-100 to-green-200 border-2 border-green-400 rounded-xl px-6 py-4 shadow-md min-w-[120px]">
                        <div className="text-4xl font-black text-green-800 mb-1">~{csvStats.estimatedTime}</div>
                        <div className="text-sm font-medium text-green-700">⏱️ Minutes</div>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <>
                  <Upload className="w-16 h-16 text-purple-400 mx-auto mb-3" />
                  <p className="text-lg font-bold text-gray-700 mb-1">
                    📂 Cliquez pour sélectionner un fichier CSV
                  </p>
                  <p className="text-sm text-gray-500">
                    Format Shopify CSV uniquement
                  </p>
                </>
              )}
            </label>
          </div>
          
          {/* Console de logs en temps réel */}
          {(productCount || logs.length > 0) && (
            <div className="mt-4 bg-gray-900 rounded-lg p-4 border border-gray-700 shadow-lg">
              {/* Header */}
              <div className="flex items-center justify-between mb-3 pb-2 border-b border-gray-700">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-green-400 font-mono text-sm font-semibold">Console Live</span>
                </div>
                {productCount && (
                  <span className="text-blue-400 font-mono text-sm">
                    📦 {productCount} produits
                  </span>
                )}
              </div>
              
              {/* Logs */}
              <div className="space-y-1 max-h-64 overflow-y-auto custom-scrollbar">
                {logs.map((log) => (
                  <div key={log.id} className="flex items-start gap-2 text-sm font-mono">
                    <span className="text-gray-500 text-xs flex-shrink-0">{log.timestamp}</span>
                    <span className={`flex-1 ${
                      log.type === 'success' ? 'text-green-400' :
                      log.type === 'error' ? 'text-red-400' :
                      log.type === 'processing' ? 'text-yellow-400' :
                      'text-blue-400'
                    }`}>
                      {log.message}
                    </span>
                  </div>
                ))}
                {/* Ref pour auto-scroll */}
                <div ref={logsEndRef} />
              </div>
            </div>
          )}
        </div>

        {/* Price & Category Section */}
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl shadow-md border-2 border-blue-200 p-6 flex flex-col gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-white text-blue-600 font-black text-2xl flex items-center justify-center shadow-sm">
              2
            </div>
            <div>
              <p className="text-sm uppercase tracking-wide text-blue-500 font-semibold">Étape 2</p>
              <h2 className="text-2xl font-bold text-gray-900">Configuration Prix & Catégorie</h2>
            </div>
          </div>

          <div className="grid gap-4">
            <div className="bg-white rounded-lg p-4 border-2 border-gray-200 shadow-sm">
              <label className="text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                <span className="text-lg">📦</span>
                Type de produit
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setProductType('physical')}
                  className={`py-2 px-4 rounded-lg border-2 font-bold text-sm transition-all flex items-center justify-center gap-2 ${
                    productType === 'physical'
                      ? 'border-purple-500 bg-purple-50 text-purple-700 shadow-sm'
                      : 'border-gray-200 text-gray-500 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <span>👕</span> Physique
                </button>
                <button
                  type="button"
                  onClick={() => setProductType('digital')}
                  className={`py-2 px-4 rounded-lg border-2 font-bold text-sm transition-all flex items-center justify-center gap-2 ${
                    productType === 'digital'
                      ? 'border-blue-500 bg-blue-50 text-blue-700 shadow-sm'
                      : 'border-gray-200 text-gray-500 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <span>💻</span> Digital
                </button>
              </div>
            </div>

            <div className="bg-white rounded-lg p-4 border-2 border-green-200 shadow-sm">
              <label className="flex items-center gap-2 text-base font-bold text-gray-900 mb-3">
                💰 Multiplicateur de Prix
              </label>
              <input
                type="number"
                step="0.1"
                min="1"
                value={priceMultiplier}
                onChange={(e) => setPriceMultiplier(parseFloat(e.target.value))}
                className="w-full px-4 py-3 text-lg font-semibold border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
              <p className="mt-2 text-xs text-gray-600">
                ✨ Arrondi automatique à X.99
              </p>
            </div>

            {file && (
              <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-lg p-5 space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">📊</span>
                  <h3 className="text-lg font-bold text-gray-900">Aperçu des Prix</h3>
                </div>

                <div className="bg-white rounded-lg p-3 border border-green-200">
                  <p className="text-sm text-gray-700">
                    <span className="font-semibold">Exemple 1:</span> 10 × {priceMultiplier} = {(10 * priceMultiplier).toFixed(2)}
                  </p>
                  <p className="text-lg font-bold text-green-700 mt-1">
                    → {(Math.ceil((10 * priceMultiplier) / 10) * 10 - 0.01).toFixed(2)}
                  </p>
                </div>

                <div className="bg-white rounded-lg p-3 border border-green-200">
                  <p className="text-sm text-gray-700">
                    <span className="font-semibold">Exemple 2:</span> 33.43 × {priceMultiplier} = {(33.43 * priceMultiplier).toFixed(2)}
                  </p>
                  <p className="text-lg font-bold text-green-700 mt-1">
                    → {(Math.ceil((33.43 * priceMultiplier) / 10) * 10 - 0.01).toFixed(2)}
                  </p>
                </div>

                <div className="bg-gradient-to-r from-yellow-100 to-amber-100 rounded-lg p-4 border-2 border-yellow-400">
                  <p className="text-base font-bold text-gray-900 flex items-center gap-2">
                    <span className="text-xl">💎</span>
                    Rentabilité: Marge de {((priceMultiplier - 1) * 100).toFixed(0)}%
                  </p>
                  <p className="text-sm text-gray-700 mt-1">
                    Profit de <span className="font-bold text-green-700">{((10 * priceMultiplier) - 10).toFixed(2)}</span> sur un produit à 10
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Preview Section - Only Final Result */}
      {finalPreview && (
        <div className="space-y-4 mb-8 animate-fade-in">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm uppercase tracking-wide text-green-600 font-semibold">Résultat Final</p>
              <h3 className="text-2xl font-bold text-gray-900">Aperçu optimisé Gemini</h3>
            </div>
          </div>

          <div className="w-full bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-300 rounded-xl p-6 shadow-lg">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-green-500 p-2 rounded-lg">
                <CheckCircle2 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-green-900">✨ Fichier Final Optimisé</h3>
                <p className="text-sm text-green-700">Prêt pour l'import sur Etsy</p>
              </div>
            </div>
            
            {renderPreviewCard(
              'Aperçu du CSV Final',
              finalPreview,
              'green',
              'Lancez la conversion pour générer l\'aperçu final.'
            )}
          </div>
        </div>
      )}

      {/* Convert Button - Hidden when done */}
      {!result && (
        <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl shadow-md border-2 border-indigo-200 p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-gradient-to-r from-purple-600 to-pink-600 p-2 rounded-lg">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">3️⃣ Conversion & Optimisation</h2>
          </div>

          <button
            onClick={handleConvert}
            disabled={!file || loading}
            className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed text-white font-bold py-4 px-8 rounded-xl transition-all transform hover:scale-[1.02] disabled:scale-100 shadow-lg text-lg flex items-center justify-center gap-3"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                <span className="font-semibold">{progress}</span>
              </>
            ) : (
              <>
                <Sparkles className="w-6 h-6" />
                <span>🚀 Lancer la Conversion + Catégorisation Auto</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-300 rounded-xl p-5 mb-6 shadow-md">
          <div className="flex items-start gap-3">
            <div className="bg-red-500 p-2 rounded-lg">
              <AlertCircle className="w-6 h-6 text-white flex-shrink-0" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-red-900 mb-2 flex items-center gap-2">
                ❌ Erreur
              </h3>
              <p className="text-base text-red-700 font-medium">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Success Result - Sticky Bottom Bar */}
      {result && (
        <>
          {/* Rapport d'erreurs si nécessaire */}
          {result.errors_report && (result.errors_report.missing_title.length > 0 || result.errors_report.missing_description.length > 0 || result.errors_report.missing_tags.length > 0 || result.errors_report.missing_category.length > 0) && (
            <div className="mb-24 bg-gradient-to-br from-red-50 to-orange-50 border-4 border-red-400 rounded-2xl p-8 shadow-2xl">
              {/* Header avec stats */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                  <div className="bg-red-500 p-3 rounded-full animate-pulse">
                    <AlertCircle className="w-8 h-8 text-white" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-black text-red-900">
                      ⚠️ Attention - Erreurs Détectées
                    </h3>
                    <p className="text-red-700 font-semibold mt-1">
                      {result.errors_report.total_processed - (result.errors_report.missing_title.length + result.errors_report.missing_description.length + result.errors_report.missing_tags.length + result.errors_report.missing_category.length) / 4} produits OK / {result.errors_report.total_processed} total
                    </p>
                  </div>
                </div>
                
                {/* Badges de statistiques */}
                <div className="flex gap-3">
                  {result.errors_report.missing_title.length > 0 && (
                    <div className="bg-red-600 text-white px-4 py-2 rounded-full font-bold text-sm">
                      {result.errors_report.missing_title.length} Titres
                    </div>
                  )}
                  {result.errors_report.missing_description.length > 0 && (
                    <div className="bg-orange-600 text-white px-4 py-2 rounded-full font-bold text-sm">
                      {result.errors_report.missing_description.length} Descriptions
                    </div>
                  )}
                  {result.errors_report.missing_tags.length > 0 && (
                    <div className="bg-yellow-600 text-white px-4 py-2 rounded-full font-bold text-sm">
                      {result.errors_report.missing_tags.length} Tags
                    </div>
                  )}
                  {result.errors_report.missing_category.length > 0 && (
                    <div className="bg-purple-600 text-white px-4 py-2 rounded-full font-bold text-sm">
                      {result.errors_report.missing_category.length} Catégories
                    </div>
                  )}
                </div>
              </div>
              
              {/* Grid d'erreurs */}
              <div className="grid md:grid-cols-2 gap-4 mb-6">
                {result.errors_report.missing_title.length > 0 && (
                  <div className="bg-white rounded-xl p-5 border-l-4 border-red-600 shadow-lg">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-3xl">📝</span>
                      <h4 className="font-black text-red-900 text-lg">Titres Manquants</h4>
                      <span className="ml-auto bg-red-100 text-red-800 px-3 py-1 rounded-full font-bold text-sm">
                        {result.errors_report.missing_title.length}
                      </span>
                    </div>
                    <div className="bg-red-50 rounded-lg p-3 max-h-32 overflow-y-auto">
                      <p className="text-sm text-gray-800 font-mono">{result.errors_report.missing_title.join(', ')}</p>
                    </div>
                  </div>
                )}
                
                {result.errors_report.missing_description.length > 0 && (
                  <div className="bg-white rounded-xl p-5 border-l-4 border-orange-600 shadow-lg">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-3xl">💬</span>
                      <h4 className="font-black text-orange-900 text-lg">Descriptions Manquantes</h4>
                      <span className="ml-auto bg-orange-100 text-orange-800 px-3 py-1 rounded-full font-bold text-sm">
                        {result.errors_report.missing_description.length}
                      </span>
                    </div>
                    <div className="bg-orange-50 rounded-lg p-3 max-h-32 overflow-y-auto">
                      <p className="text-sm text-gray-800 font-mono">{result.errors_report.missing_description.join(', ')}</p>
                    </div>
                  </div>
                )}
                
                {result.errors_report.missing_tags.length > 0 && (
                  <div className="bg-white rounded-xl p-5 border-l-4 border-yellow-600 shadow-lg">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-3xl">🏷️</span>
                      <h4 className="font-black text-yellow-900 text-lg">Tags Manquants</h4>
                      <span className="ml-auto bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full font-bold text-sm">
                        {result.errors_report.missing_tags.length}
                      </span>
                    </div>
                    <div className="bg-yellow-50 rounded-lg p-3 max-h-32 overflow-y-auto">
                      <p className="text-sm text-gray-800 font-mono">{result.errors_report.missing_tags.join(', ')}</p>
                    </div>
                  </div>
                )}
                
                {result.errors_report.missing_category.length > 0 && (
                  <div className="bg-white rounded-xl p-5 border-l-4 border-purple-600 shadow-lg">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-3xl">🎯</span>
                      <h4 className="font-black text-purple-900 text-lg">Catégories Manquantes</h4>
                      <span className="ml-auto bg-purple-100 text-purple-800 px-3 py-1 rounded-full font-bold text-sm">
                        {result.errors_report.missing_category.length}
                      </span>
                    </div>
                    <div className="bg-purple-50 rounded-lg p-3 max-h-32 overflow-y-auto">
                      <p className="text-sm text-gray-800 font-mono">{result.errors_report.missing_category.join(', ')}</p>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Action box */}
              <div className="bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl p-5 text-white">
                <div className="flex items-start gap-3">
                  <span className="text-3xl">💡</span>
                  <div>
                    <h4 className="font-bold text-lg mb-2">Que faire maintenant?</h4>
                    <ul className="space-y-1 text-sm">
                      <li>• Vérifiez ces produits dans le CSV final avant l'upload</li>
                      <li>• Les produits sans erreur sont prêts à être importés</li>
                      <li>• Vous pouvez compléter manuellement sur Etsy après import</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div className="fixed bottom-0 left-0 right-0 bg-white border-t-4 border-green-500 shadow-[0_-4px_20px_rgba(0,0,0,0.1)] p-4 z-50 animate-slide-up">
            <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="bg-green-100 p-2 rounded-full hidden sm:block">
                  <CheckCircle2 className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-green-900 flex items-center gap-2">
                    <span className="sm:hidden">✅</span> Conversion Terminée !
                  </h3>
                  <p className="text-sm text-green-700 font-medium">
                    🎉 {result.products_count} produits convertis et prêts
                  </p>
                </div>
              </div>
              
              <button
                onClick={() => handleDownloadFile(result.output_file)}
                className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-bold py-3 px-6 sm:px-8 rounded-xl transition-all transform hover:scale-105 shadow-lg text-base flex items-center gap-2 whitespace-nowrap"
              >
                <Download className="w-5 h-5" />
                <span>Télécharger CSV</span>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default Dashboard
