import { useState } from 'react'
import { Upload, Sparkles, Image as ImageIcon, FileText, CheckCircle2, AlertCircle, Download, Columns } from 'lucide-react'
import axios from 'axios'

const Titles = () => {
  const [file, setFile] = useState(null)
  const [columns, setColumns] = useState([])
  const [imageColumn, setImageColumn] = useState('')
  const [identifierColumn, setIdentifierColumn] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [preview, setPreview] = useState(null)
  const [resultMeta, setResultMeta] = useState(null)

  const resetState = () => {
    setError(null)
    setSuccess(null)
    setPreview(null)
    setResultMeta(null)
  }

  const parseHeaders = (text) => {
    const firstLine = text.split(/\r?\n/).find(line => line.trim().length)
    if (!firstLine) return []
    const sanitized = firstLine.replace(/^\ufeff/, '')
    return sanitized
      .split(/,(?=(?:[^"]*"[^"]*")*[^"]*$)/)
      .map((header) => header.replace(/^"|"$/g, '').trim())
      .filter(Boolean)
  }

  const handleFileChange = (e) => {
    const selected = e.target.files[0]
    if (!selected) return

    if (!selected.name.endsWith('.csv')) {
      setError('Veuillez importer un fichier CSV valide.')
      return
    }

    setFile(selected)
    resetState()

    const reader = new FileReader()
    reader.onload = (event) => {
      const headers = parseHeaders(event.target.result || '')
      setColumns(headers)

      if (headers.length) {
        const imageGuess = headers.find((h) => /photo|image|img|picture|url/i.test(h)) || headers[0]
        const identifierGuess = headers.find((h) => /sku|id|title|handle|name/i.test(h) && h !== imageGuess) || ''
        setImageColumn(imageGuess)
        setIdentifierColumn(identifierGuess)
      } else {
        setImageColumn('')
        setIdentifierColumn('')
      }
    }
    reader.readAsText(selected)
  }

  const handleGenerateTitles = async () => {
    if (!file) {
      setError('Commencez par importer un CSV.')
      return
    }

    if (!imageColumn) {
      setError('Sélectionnez la colonne qui contient vos images.')
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('image_column', imageColumn)
      formData.append('identifier_column', identifierColumn)

      const { data } = await axios.post('/api/title-generator', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      setSuccess(data.message || 'Titres générés')
      setPreview({ columns: data.preview_columns, rows: data.preview_rows })
      setResultMeta({
        generated: data.generated_count,
        skipped: data.skipped_count,
        total: data.total_rows,
        output: data.output_file,
      })
    } catch (err) {
      const message = err.response?.data?.error || err.message || 'Erreur lors de la génération.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadFile = async (filename) => {
    try {
      const response = await axios.get(`/api/download/${filename}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename || 'ai_titles.csv')
      document.body.appendChild(link)
      link.click()
      link.remove()
      setTimeout(() => window.URL.revokeObjectURL(url), 200)
    } catch (e) {
      setError('Impossible de télécharger le fichier généré.')
    }
  }

  const ColumnSelection = () => {
    if (!columns.length) {
      return (
        <div className="bg-gray-50 border border-dashed border-gray-300 rounded-xl p-6 text-center text-gray-500">
          Importez un CSV pour afficher vos colonnes et choisir celles à utiliser.
        </div>
      )
    }

    return (
      <div className="bg-white border-2 border-gray-200 rounded-2xl shadow-sm p-6">
        <div className="flex items-center gap-3 mb-4">
          <Columns className="w-6 h-6 text-purple-500" />
          <div>
            <h3 className="text-lg font-bold text-gray-900">Sélection des colonnes</h3>
            <p className="text-sm text-gray-500">
              Cochez la colonne image obligatoire + (optionnel) la colonne identifiant pour les logs.
            </p>
          </div>
        </div>

        <div className="max-h-[360px] overflow-y-auto space-y-3 pr-2 custom-scrollbar">
          {columns.map((col) => (
            <div
              key={col}
              className={`border rounded-xl px-4 py-3 flex flex-col md:flex-row md:items-center md:justify-between gap-3 ${
                imageColumn === col || identifierColumn === col ? 'border-purple-400 bg-purple-50/60' : 'border-gray-200 bg-gray-50'
              }`}
            >
              <div>
                <p className="font-semibold text-gray-900">{col}</p>
                <p className="text-xs text-gray-500">Cliquez pour définir son rôle</p>
              </div>
              <div className="flex flex-wrap items-center gap-4">
                <label className="inline-flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="image-column"
                    value={col}
                    checked={imageColumn === col}
                    onChange={() => setImageColumn(col)}
                    className="accent-blue-600 w-4 h-4"
                  />
                  <span className="text-sm font-semibold text-blue-700">Image principale</span>
                </label>
                <label className="inline-flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="identifier-column"
                    value={col}
                    checked={identifierColumn === col}
                    onChange={() => setIdentifierColumn(col)}
                    className="accent-purple-600 w-4 h-4"
                  />
                  <span className="text-sm font-semibold text-purple-700">Identifiant (optionnel)</span>
                </label>
              </div>
            </div>
          ))}
        </div>

        {identifierColumn && (
          <button
            type="button"
            onClick={() => setIdentifierColumn('')}
            className="mt-4 text-xs text-purple-600 font-semibold underline"
          >
            Retirer la colonne identifiant
          </button>
        )}
      </div>
    )
  }

  const PreviewTable = () => {
    if (!preview) return null

    const rows = preview.rows || []

    if (!rows.length) {
      return (
        <div className="bg-white border-2 border-gray-200 rounded-2xl p-6 text-center text-gray-500">
          Aucun aperçu disponible pour le moment.
        </div>
      )
    }

    return (
      <div className="bg-white border-2 border-gray-200 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-sm uppercase tracking-wide text-green-600 font-semibold">Aperçu rapide</p>
            <h3 className="text-2xl font-bold text-gray-900">Titres générés</h3>
          </div>
          {resultMeta?.output && (
            <button
              onClick={() => handleDownloadFile(resultMeta.output)}
              className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-semibold"
            >
              <Download className="w-4 h-4" />
              Télécharger le CSV
            </button>
          )}
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm border-collapse">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left font-bold text-gray-700">Identifiant</th>
                <th className="px-4 py-2 text-left font-bold text-gray-700">Image</th>
                <th className="px-4 py-2 text-left font-bold text-gray-700">Titre AI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {rows.map((row, idx) => (
                <tr key={`${row.identifier}-${idx}`} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-semibold text-gray-900">{row.identifier}</td>
                  <td className="px-4 py-3">
                    {row.image_url ? (
                      <img src={row.image_url} alt={row.identifier} className="w-20 h-20 object-cover rounded-lg border border-gray-200" />
                    ) : (
                      <span className="text-gray-400 text-xs">Pas d'image</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-800">{row.ai_title}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm flex flex-col gap-4 md:flex-row md:items-center md:gap-6">
        <div className="bg-gradient-to-br from-blue-600 to-indigo-500 text-white w-16 h-16 rounded-2xl flex items-center justify-center shadow-lg">
          <Sparkles className="w-7 h-7" />
        </div>
        <div>
          <p className="text-sm font-semibold text-blue-600 uppercase tracking-wide">Titres Express</p>
          <h1 className="text-3xl font-black text-gray-900">Génération de titres à partir des images</h1>
          <p className="text-gray-600 mt-2">
            Importez votre CSV, cochez simplement la colonne contenant vos images, et Gemini crée instantanément des titres Etsy optimisés.
          </p>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 flex items-center gap-3">
          <AlertCircle className="w-5 h-5" />
          <span className="font-semibold">{error}</span>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 rounded-xl px-4 py-3 flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5" />
          <span className="font-semibold">{success}</span>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <div className="bg-white border-2 border-gray-200 rounded-2xl p-6 shadow-sm space-y-4">
            <div className="flex items-center gap-3">
              <div className="bg-blue-50 text-blue-600 p-3 rounded-2xl">
                <Upload className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">1. Importer votre CSV</h2>
                <p className="text-sm text-gray-500">Format Shopify ou personnalisé accepté</p>
              </div>
            </div>

            <label
              htmlFor="titles-file-upload"
              className={`block border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition ${
                file ? 'border-green-400 bg-green-50' : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-white'
              }`}
            >
              <input
                id="titles-file-upload"
                type="file"
                accept=".csv"
                className="hidden"
                onChange={handleFileChange}
              />

              {file ? (
                <>
                  <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-2" />
                  <p className="text-lg font-semibold text-gray-900">{file.name}</p>
                  <p className="text-sm text-gray-600">{(file.size / 1024).toFixed(1)} Ko</p>
                </>
              ) : (
                <>
                  <ImageIcon className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                  <p className="text-lg font-semibold text-gray-700">Déposez votre CSV ou cliquez pour parcourir</p>
                  <p className="text-sm text-gray-500">Nous détecterons automatiquement vos colonnes.</p>
                </>
              )}
            </label>
          </div>

          <ColumnSelection />

          <div className="bg-white border-2 border-gray-200 rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <FileText className="w-6 h-6 text-emerald-500" />
              <div>
                <h3 className="text-xl font-bold text-gray-900">2. Lancer la génération</h3>
                <p className="text-sm text-gray-500">Gemini 2.5 Flash s’occupe du reste</p>
              </div>
            </div>

            <button
              onClick={handleGenerateTitles}
              disabled={loading || !file || !imageColumn}
              className="w-full inline-flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-500 to-blue-500 hover:from-indigo-600 hover:to-blue-600 text-white font-semibold py-3 rounded-xl transition disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <span className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Génération en cours...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Générer les titres AI
                </>
              )}
            </button>

            {resultMeta && (
              <div className="grid grid-cols-2 gap-4 mt-6">
                <div className="bg-gradient-to-br from-green-100 to-emerald-100 rounded-xl p-4 border border-green-300">
                  <p className="text-xs uppercase text-green-700 font-semibold">Titres générés</p>
                  <p className="text-3xl font-black text-green-800">{resultMeta.generated}</p>
                </div>
                <div className="bg-gradient-to-br from-amber-100 to-yellow-100 rounded-xl p-4 border border-amber-300">
                  <p className="text-xs uppercase text-amber-700 font-semibold">Lignes ignorées</p>
                  <p className="text-3xl font-black text-amber-800">{resultMeta.skipped}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <PreviewTable />

          {!preview && (
            <div className="bg-gradient-to-br from-purple-50 to-blue-50 border-2 border-purple-200 rounded-2xl p-6 shadow-inner text-center">
              <Sparkles className="w-10 h-10 text-purple-500 mx-auto mb-3" />
              <h3 className="text-xl font-bold text-gray-900 mb-1">Besoin uniquement des titres ?</h3>
              <p className="text-sm text-gray-600">
                Cette page se concentre sur la rédaction de titres en se basant uniquement sur les images. Aucun champ “niche” n’est nécessaire.
              </p>
              <p className="text-xs text-gray-500 mt-3">
                Assurez-vous que vos images sont accessibles via des URLs publiques (Shopify CDN, etc.).
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Titles
