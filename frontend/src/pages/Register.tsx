import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import type { StyleProfile } from '../services/api';
import { BookHeart, Lock, Mail, User as UserIcon, ArrowRight, ArrowLeft, ShieldCheck, AlertCircle, CheckCircle2 } from 'lucide-react';

export const Register: React.FC = () => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [formality, setFormality] = useState('cercano, conversacional y amable');
  const [phrases, setPhrases] = useState('');
  const [warmth, setWarmth] = useState(0.8);
  const [sentiment, setSentiment] = useState('sereno y reflexivo');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [confirmationSent, setConfirmationSent] = useState(false);
  const [step, setStep] = useState<1 | 2>(1);

  const { register, isConfigured } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (step === 1) {
      setError('');
      setStep(2);
      return;
    }
    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres.');
      return;
    }

    setError('');
    setLoading(true);

    try {
      const styleProfile: StyleProfile = {
        typical_phrases: phrases.split(',').map(phrase => phrase.trim()).filter(Boolean).slice(0, 8),
        formality_level: formality,
        warmth_score: warmth,
        sentiment_tendency: sentiment,
      };
      const result = await register(email, password, fullName, styleProfile);
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
            {step === 1 ? 'Primero crea tu cuenta. Después podrás elegir cómo quieres que hable tu legado.' : 'Paso 2: configura la forma de hablar de tu legado.'}
          </p>
        </div>

        <div className="mb-6 grid grid-cols-2 gap-2" aria-label="Pasos de creación de cuenta">
          <div className={`rounded-xl px-3 py-2 text-center text-xs font-semibold ${step === 1 ? 'bg-amber-800 text-white' : 'bg-stone-100 text-stone-500'}`}>1. Datos de cuenta</div>
          <div className={`rounded-xl px-3 py-2 text-center text-xs font-semibold ${step === 2 ? 'bg-amber-800 text-white' : 'bg-stone-100 text-stone-500'}`}>2. Forma de hablar</div>
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
          {step === 1 && <>
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
          </>}

          {step === 2 && <fieldset className="space-y-3 rounded-2xl border border-amber-200 bg-amber-50/60 p-4">
            <legend className="px-1 text-xs font-bold uppercase tracking-wider text-stone-700">¿Cómo quieres que hable tu legado?</legend>
            <div>
              <label htmlFor="profile-formality" className="mb-1.5 block text-xs font-medium text-stone-700">Estilo al hablar</label>
              <select id="profile-formality" value={formality} onChange={event => setFormality(event.target.value)} className="w-full rounded-xl border border-stone-200 bg-white px-3 py-2.5 text-sm text-stone-800 focus:outline-none focus:ring-2 focus:ring-amber-500/20">
                <option value="formal, respetuoso y claro">Formal y respetuoso</option>
                <option value="cercano, conversacional y amable">Cercano y conversacional</option>
                <option value="coloquial, espontáneo y familiar">Coloquial y familiar</option>
                <option value="sereno, solemne y reflexivo">Sereno y solemne</option>
              </select>
            </div>
            <div>
              <label htmlFor="profile-sentiment" className="mb-1.5 block text-xs font-medium text-stone-700">Tono emocional</label>
              <select id="profile-sentiment" value={sentiment} onChange={event => setSentiment(event.target.value)} className="w-full rounded-xl border border-stone-200 bg-white px-3 py-2.5 text-sm text-stone-800 focus:outline-none focus:ring-2 focus:ring-amber-500/20">
                <option value="sereno y reflexivo">Sereno y reflexivo</option>
                <option value="alegre y optimista">Alegre y optimista</option>
                <option value="nostálgico y cariñoso">Nostálgico y cariñoso</option>
                <option value="directo y práctico">Directo y práctico</option>
                <option value="protector y afectuoso">Protector y afectuoso</option>
              </select>
            </div>
            <div>
              <label htmlFor="profile-warmth" className="mb-1.5 flex justify-between text-xs font-medium text-stone-700"><span>Calidez</span><span>{Math.round(warmth * 100)}%</span></label>
              <input id="profile-warmth" type="range" min="0" max="1" step="0.05" value={warmth} onChange={event => setWarmth(Number(event.target.value))} className="w-full accent-amber-800" />
            </div>
            <div>
              <label htmlFor="profile-phrases" className="mb-1.5 block text-xs font-medium text-stone-700">Expresiones propias <span className="font-normal text-stone-500">(opcional, separadas por coma)</span></label>
              <input id="profile-phrases" type="text" value={phrases} onChange={event => setPhrases(event.target.value)} maxLength={240} placeholder="por ejemplo: mira, te cuento" className="w-full rounded-xl border border-stone-200 bg-white px-3 py-2.5 text-sm text-stone-800 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-amber-500/20" />
            </div>
            <p className="text-[11px] leading-relaxed text-stone-500">Podrás cambiar estas preferencias más adelante desde tu biblioteca.</p>
          </fieldset>}

          <div className="pt-2">
            <div className="flex items-center gap-2 text-xs text-stone-500 mb-4 bg-stone-50 p-2.5 rounded-xl border border-stone-100">
              <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <span>Autenticación y cifrado seguro gestionado por Supabase Auth.</span>
            </div>

            <div className="flex gap-3">
              {step === 2 && <button type="button" onClick={() => { setError(''); setStep(1); }} disabled={loading} className="inline-flex items-center justify-center gap-2 rounded-2xl border border-stone-200 px-4 py-3.5 text-sm font-medium text-stone-700 hover:bg-stone-50 disabled:opacity-50"><ArrowLeft className="h-4 w-4" />Atrás</button>}
              <button
                type="submit"
                disabled={loading || !isConfigured || (step === 1 && (!fullName.trim() || !email.trim() || !password))}
                className="flex w-full items-center justify-center gap-2 rounded-2xl bg-amber-800 px-6 py-3.5 text-sm font-medium text-white shadow-md shadow-amber-900/20 transition hover:bg-amber-900 disabled:opacity-50 cursor-pointer"
              >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>{step === 1 ? 'Continuar' : 'Crear cuenta'}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
              </button>
            </div>
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
