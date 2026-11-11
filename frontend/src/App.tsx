import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Navbar } from './components/Navbar';
import { Dashboard } from './pages/Dashboard';
import { MemoryCapture } from './pages/MemoryCapture';
import { CapsuleLibrary } from './pages/CapsuleLibrary';
import { LegacyChat } from './pages/LegacyChat';
import { Login } from './pages/Login';
import { Register } from './pages/Register';

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="min-h-screen flex flex-col bg-[#FAF8F5]">
          <Navbar />
          <main className="flex-1">
            <Routes>
              {/* Rutas Públicas de Autenticación */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              {/* Rutas Principales Protegidas */}
              <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/capture" element={<ProtectedRoute><MemoryCapture /></ProtectedRoute>} />
              <Route path="/capsules" element={<ProtectedRoute><CapsuleLibrary /></ProtectedRoute>} />
              <Route path="/chat" element={<ProtectedRoute><LegacyChat /></ProtectedRoute>} />

              {/* Redirección por defecto */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
