import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  BookHeart, 
  MessageCircleHeart, 
  Feather, 
  LayoutDashboard, 
  LogOut, 
  LogIn, 
  UserPlus 
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    async function checkBackend() {
      try {
        const res = await fetch('/api/health', { method: 'GET' });
        if (res.ok) {
          const data = await res.json();
          setBackendOnline(data.status === 'healthy');
        } else {
          setBackendOnline(false);
        }
      } catch {
        setBackendOnline(false);
      }
    }
    checkBackend();
    const interval = setInterval(checkBackend, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-50 bg-[#FAF8F5]/90 backdrop-blur-md border-b border-amber-900/10">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        
        {/* Brand */}
        <Link to="/dashboard" className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-amber-700 to-amber-500 flex items-center justify-center text-white shadow-md shadow-amber-900/15">
            <BookHeart className="w-6 h-6 stroke-[2.2]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold font-serif-warm text-stone-900 tracking-tight">
                LegadoVivo
              </h1>
              <span className="text-[10px] font-sans uppercase tracking-widest bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-semibold">
                MVP
              </span>
            </div>
            
            {/* Indicador de Estado del Backend */}
            <div className="flex items-center gap-2 mt-0.5">
              <span className={`w-2 h-2 rounded-full ${backendOnline ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`} />
              <span className="text-[11px] text-stone-500">
                {backendOnline ? 'Backend Activo (FastAPI)' : 'Modo Demostración Local'}
              </span>
            </div>
          </div>
        </Link>

        {/* Navigation */}
        <nav className="flex items-center gap-1 sm:gap-2">
          
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all ${
                isActive
                  ? 'bg-amber-100 text-amber-900 shadow-sm'
                  : 'text-stone-600 hover:text-stone-900 hover:bg-stone-200/50'
              }`
            }
          >
            <LayoutDashboard className="w-4 h-4" />
            <span className="hidden md:inline">Dashboard Doble Rol</span>
          </NavLink>

          <NavLink
            to="/capture"
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all ${
                isActive
                  ? 'bg-amber-100 text-amber-900 shadow-sm'
                  : 'text-stone-600 hover:text-stone-900 hover:bg-stone-200/50'
              }`
            }
          >
            <Feather className="w-4 h-4" />
            <span className="hidden sm:inline">Capturar</span>
          </NavLink>

          <NavLink
            to="/capsules"
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all ${
                isActive
                  ? 'bg-amber-100 text-amber-900 shadow-sm'
                  : 'text-stone-600 hover:text-stone-900 hover:bg-stone-200/50'
              }`
            }
          >
            <BookHeart className="w-4 h-4" />
            <span className="hidden sm:inline">Biblioteca</span>
          </NavLink>

          <NavLink
            to="/chat"
            className={({ isActive }) =>
              `flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all ${
                isActive
                  ? 'bg-amber-800 text-white shadow-md shadow-amber-900/20'
                  : 'bg-amber-600/10 text-amber-800 hover:bg-amber-600/20'
              }`
            }
          >
            <MessageCircleHeart className="w-4 h-4" />
            <span>Chat</span>
          </NavLink>

          {/* Estado de Usuario / Auth */}
          <div className="pl-2 border-l border-stone-200 ml-1 flex items-center gap-2">
            {isAuthenticated ? (
              <div className="flex items-center gap-2">
                <div className="hidden lg:block text-right">
                  <div className="text-xs font-bold text-stone-800 leading-tight">
                    {user?.full_name || 'Alberto'}
                  </div>
                  <div className="text-[10px] text-amber-800 font-semibold">
                    Titular / Beneficiario
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  title="Cerrar sesión"
                  className="p-2 rounded-xl text-stone-500 hover:text-rose-700 hover:bg-rose-50 transition cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-1">
                <Link
                  to="/login"
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-stone-700 hover:bg-stone-200/50 transition"
                >
                  <LogIn className="w-3.5 h-3.5" />
                  <span>Ingresar</span>
                </Link>
                <Link
                  to="/register"
                  className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-amber-800 text-white hover:bg-amber-900 transition shadow-sm"
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  <span>Registro</span>
                </Link>
              </div>
            )}
          </div>

        </nav>
      </div>
    </header>
  );
};
