import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { BookHeart, Lock, Mail, User as UserIcon, ArrowRight, ShieldCheck, AlertCircle, CheckCircle2 } from 'lucide-react';

export const Register: React.FC = () => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [confirmationSent, setConfirmationSent] = useState(false);

  const { register, isConfigured } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres.');
      return;
    }

    setError('');
    setLoading(true);

    try {
      const result = await register(email, password, fullName);
      if (result.needsEmailVerification) {
        setConfirmationSent(true);
      } else {
        navigate('/dashboard', { replace: true });
      }
    } catch (err: any) {
      setError(err?.message || 'Error al registrar usuario en Supabase.');
    } finally {
      setLoading(false);
    }
  };

  if (confirmationSent) {
    return (
      <div className="min-h-[85vh] flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md bg-white rounded-3xl p-8 sm:p-10 shadow-sm border border-stone-200/90 text-center">
          <div className="w-14 h-14 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-4 border border-emerald-200">
            <CheckCircle2 className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-serif-warm font-bold text-stone-900 tracking-tight">
            ¡Verifica tu Correo!
          </h2>
          <p className="text-stone-600 text-sm mt-2 leading-relaxed">
            Hemos enviado un enlace de verificación a <span className="font-semibold text-stone-900">{email}</span>.
          </p>
          <p className="text-stone-500 text-xs mt-3">
            Abre el correo para confirmar tu registro en Supabase Auth y luego podrás iniciar sesión.
          </p>
          <div className="mt-8">
            <Link
              to="/login"
              className="inline-flex items-center justify-center py-3 px-6 rounded-2xl bg-amber-800 hover:bg-amber-900 text-white font-medium text-sm transition"
            >
              Ir a Iniciar Sesión
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md bg-white rounded-3xl p-8 sm:p-10 shadow-sm border border-stone-200/90">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-amber-700 to-amber-500 flex items-center justify-center text-white mx-auto shadow-md shadow-amber-900/15 mb-4">
            <BookHeart className="w-7 h-7 stroke-[2.2]" />
          </div>
          <h2 className="text-2xl sm:text-3xl font-serif-warm font-bold text-stone-900 tracking-tight">
            Crea tu Cuenta de Legado
          </h2>
          <p className="text-stone-500 text-xs sm:text-sm mt-1">
            Una sola cuenta para crear tus memorias o vincularte a los legados de tu familia.
          </p>
        </div>

        {/* Alerta si falta configurar Supabase */}
        {!isConfigured && (
          <div className="mb-6 p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-xs leading-relaxed flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-amber-950 mb-1">Configuración de Supabase pendiente</p>
              <p className="text-amber-800">
                Para registrar usuarios con Supabase Auth, define <code className="bg-amber-100 px-1 py-0.5 rounded font-mono text-[11px]">VITE_SUPABASE_URL</code> y <code className="bg-amber-100 px-1 py-0.5 rounded font-mono text-[11px]">VITE_SUPABASE_ANON_KEY</code> en tu archivo <code className="bg-amber-100 px-1 py-0.5 rounded font-mono text-[11px]">.env</code>.
              </p>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-6 p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-stone-700 mb-2">
              Nombre Completo
            </label>
            <div className="relative">
              <UserIcon className="w-4 h-4 text-stone-400 absolute left-4 top-3.5" />
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Alberto Gómez"
                required
                className="w-full pl-11 pr-4 py-3 rounded-2xl bg-stone-50 border border-stone-200 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-600 text-stone-900 text-sm transition"
              />
            </div>
          </div>

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
                placeholder="alberto@familia.com"
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
                placeholder="Mínimo 6 caracteres"
                required
                minLength={6}
                className="w-full pl-11 pr-4 py-3 rounded-2xl bg-stone-50 border border-stone-200 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-600 text-stone-900 text-sm transition"
              />
            </div>
          </div>

          <div className="pt-2">
            <div className="flex items-center gap-2 text-xs text-stone-500 mb-4 bg-stone-50 p-2.5 rounded-xl border border-stone-100">
              <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <span>Autenticación y cifrado seguro gestionado por Supabase Auth.</span>
            </div>

            <button
              type="submit"
              disabled={loading || !fullName || !email || !password || !isConfigured}
              className="w-full py-3.5 px-6 rounded-2xl bg-amber-800 hover:bg-amber-900 text-white font-medium text-sm flex items-center justify-center gap-2 shadow-md shadow-amber-900/20 disabled:opacity-50 transition cursor-pointer"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>Registrarme</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>

        <div className="mt-8 pt-6 border-t border-stone-100 text-center text-xs text-stone-500">
          ¿Ya tienes cuenta?{' '}
          <Link to="/login" className="font-semibold text-amber-800 hover:text-amber-900 underline">
            Iniciar Sesión
          </Link>
        </div>

      </div>
    </div>
  );
};
