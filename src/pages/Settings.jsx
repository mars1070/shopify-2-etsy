import { useState, useEffect } from 'react'
import { Save, Key, AlertCircle, CheckCircle2 } from 'lucide-react'
import axios from 'axios'

const Settings = () => {
  const [apiKey, setApiKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const response = await axios.get('/api/settings')
      if (response.data.has_api_key) {
        setApiKey('••••••••••••••••')
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
      // Ne pas effacer l'erreur automatiquement pour que l'utilisateur puisse la lire
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Paramètres</h1>
        <p className="text-gray-600">
          Configurez votre clé API Gemini pour l'optimisation automatique
        </p>
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

      {/* Info Section */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mt-6">
        <h3 className="font-semibold text-blue-900 mb-2">À propos de Gemini AI</h3>
        <p className="text-sm text-blue-800 mb-3">
          Gemini AI analyse automatiquement la première image de chaque produit pour générer :
        </p>
        <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
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
