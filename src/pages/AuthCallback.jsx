import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import axios from 'axios'
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react'

const AuthCallback = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState('processing')
  const [message, setMessage] = useState('Connexion à Shopify en cours...')
  const [error, setError] = useState(null)

  useEffect(() => {
    const processCallback = async () => {
      const code = searchParams.get('code')
      const state = searchParams.get('state')
      const shop = searchParams.get('shop')
      const errorParam = searchParams.get('error')
      const errorDescription = searchParams.get('error_description')

      // Vérifier si Shopify a retourné une erreur
      if (errorParam) {
        setStatus('error')
        setError(errorDescription || errorParam || 'Autorisation refusée')
        return
      }

      if (!code || !state) {
        setStatus('error')
        setError('Paramètres OAuth manquants (code ou state)')
        return
      }

      try {
        setMessage('Échange du code d\'autorisation...')
        
        const response = await axios.post('/api/shopify/oauth/callback', {
          code,
          state,
          shop
        })

        if (response.data.success) {
          setStatus('success')
          setMessage(`Connecté à ${response.data.shop_name} !`)
          
          // Rediriger vers les paramètres après 2 secondes
          setTimeout(() => {
            navigate('/settings', { 
              state: { 
                shopifyConnected: true, 
                shopName: response.data.shop_name 
              } 
            })
          }, 2000)
        } else {
          setStatus('error')
          setError(response.data.error || 'Erreur inconnue')
        }
      } catch (err) {
        setStatus('error')
        setError(err.response?.data?.error || err.message || 'Erreur de connexion')
      }
    }

    processCallback()
  }, [searchParams, navigate])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full mx-4">
        <div className="text-center">
          {status === 'processing' && (
            <>
              <Loader2 className="w-16 h-16 text-green-500 animate-spin mx-auto mb-4" />
              <h1 className="text-xl font-bold text-gray-900 mb-2">Connexion Shopify</h1>
              <p className="text-gray-600">{message}</p>
            </>
          )}

          {status === 'success' && (
            <>
              <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <h1 className="text-xl font-bold text-green-700 mb-2">Connexion réussie !</h1>
              <p className="text-gray-600">{message}</p>
              <p className="text-sm text-gray-500 mt-2">Redirection en cours...</p>
            </>
          )}

          {status === 'error' && (
            <>
              <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
              <h1 className="text-xl font-bold text-red-700 mb-2">Erreur de connexion</h1>
              <p className="text-red-600 mb-4">{error}</p>
              <button
                onClick={() => navigate('/settings')}
                className="bg-gray-600 hover:bg-gray-700 text-white font-semibold py-2 px-6 rounded-lg transition-colors"
              >
                Retour aux paramètres
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default AuthCallback
