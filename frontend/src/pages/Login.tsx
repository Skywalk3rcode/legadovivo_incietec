import React, { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { BookHeart, Lock, Mail, ArrowRight, AlertCircle, Shield, Volume2, VolumeX } from 'lucide-react';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [musicPlaying, setMusicPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    audio.volume = 0.3;
    void audio.play().catch(() => setMusicPlaying(false));

    return () => {
      audio.pause();
      audio.currentTime = 0;
    };
  }, []);

  const toggleMusic = async () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (audio.paused) {
      try {
        await audio.play();
      } catch {
        setMusicPlaying(false);
      }
    } else {
      audio.pause();
    }
  };

  const { login, isConfigured } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as any)?.from?.pathname || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err?.message || 'Error al iniciar sesión con Supabase. Verifique sus credenciales.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md bg-white rounded-3xl p-8 sm:p-10 shadow-sm border border-stone-200/90">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-amber-700 to-amber-500 flex items-center justify-center text-white mx-auto shadow-md shadow-amber-900/15 mb-4">
            <BookHeart className="w-7 h-7 stroke-[2.2]" />
          </div>
          <h2 className="text-2xl sm:text-3xl font-serif-warm font-bold text-stone-900 tracking-tight">
            Bienvenido a LegadoVivo
          </h2>
          <p className="text-stone-500 text-xs sm:text-sm mt-1">
            Ingresa a tu espacio para cuidar tus recuerdos o conversar con tus seres queridos.
          </p>
        </div>

        {/* Alerta si falta configurar las variables de entorno de Supabase */}
        {!isConfigured && (
          <div className="mb-6 p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-xs leading-relaxed flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-amber-950 mb-1">Configuración de Supabase pendiente</p>
              <p className="text-amber-800">
                Para autenticarte con Supabase Auth, define <code className="bg-amber-100 px-1 py-0.5 rounded font-mono text-[11px]">VITE_SUPABASE_URL</code> y <code className="bg-amber-100 px-1 py-0.5 rounded font-mono text-[11px]">VITE_SUPABASE_ANON_KEY</code> en tu archivo <code className="bg-amber-100 px-1 py-0.5 rounded font-mono text-[11px]">.env</code>.
              </p>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-6 p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-stone-700 mb-2">
              Correo Electrónico
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-stone-400 absolute left-4 top-3.5" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="ejemplo@familia.com"
                required
                className="w-full pl-11 pr-4 py-3 rounded-2xl bg-stone-50 border border-stone-200 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-600 text-stone-900 text-sm transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-stone-700 mb-2">
              Contraseña
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-stone-400 absolute left-4 top-3.5" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full pl-11 pr-4 py-3 rounded-2xl bg-stone-50 border border-stone-200 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-600 text-stone-900 text-sm transition"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !email || !password || !isConfigured}
            className="w-full py-3.5 px-6 rounded-2xl bg-amber-800 hover:bg-amber-900 text-white font-medium text-sm flex items-center justify-center gap-2 shadow-md shadow-amber-900/20 disabled:opacity-50 transition cursor-pointer"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <span>Ingresar</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-stone-100 text-center text-xs text-stone-500">
          ¿Aún no tienes cuenta?{' '}
          <Link to="/register" className="font-semibold text-amber-800 hover:text-amber-900 underline">
            Crear cuenta de Legado
          </Link>
        </div>

        <div className="mt-4 flex items-center justify-center gap-1.5 text-[11px] text-stone-400">
          <Shield className="w-3.5 h-3.5 text-stone-400" />
          <span>Autenticación gestionada por Supabase Auth</span>
        </div>

      </div>
      <audio
        ref={audioRef}
        src="/audio/recuerdame.mp3"
        preload="auto"
        loop
        className="hidden"
        onPlay={() => setMusicPlaying(true)}
        onPause={() => setMusicPlaying(false)}
        aria-label="Música de fondo: Recuérdame"
      />
      <button
        type="button"
        onClick={() => void toggleMusic()}
        aria-label={musicPlaying ? 'Pausar música de fondo' : 'Reproducir música de fondo'}
        title={musicPlaying ? 'Pausar música' : 'Reproducir música'}
        className="fixed bottom-5 right-5 z-50 flex h-10 w-10 items-center justify-center rounded-full border border-stone-200/80 bg-white/75 text-stone-500 shadow-sm backdrop-blur transition hover:bg-white hover:text-amber-800"
      >
        {musicPlaying ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
      </button>
    </div>
  );
};
