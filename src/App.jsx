import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Settings from './pages/Settings'
import Info from './pages/Info'
import AuthCallback from './pages/AuthCallback'
import ImageGeneration from './pages/ImageGeneration'

function App() {
  return (
    <Router>
      <Routes>
        {/* Route OAuth callback sans Layout */}
        <Route path="/auth/callback" element={<AuthCallback />} />
        
        {/* Routes avec Layout */}
        <Route path="/" element={<Layout><Dashboard /></Layout>} />
        <Route path="/images" element={<Layout><ImageGeneration /></Layout>} />
        <Route path="/settings" element={<Layout><Settings /></Layout>} />
        <Route path="/info" element={<Layout><Info /></Layout>} />
      </Routes>
    </Router>
  )
}

export default App
