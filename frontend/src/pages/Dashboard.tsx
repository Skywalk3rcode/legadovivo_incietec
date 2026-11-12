import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  api, 
  LegacyConnectionSummary, 
  BeneficiaryInvite, 
  CapsuleResponse 
} from '../services/api';
import { 
  Sparkles, 
  BookHeart, 
  Users, 
  UserCheck, 
  KeyRound, 
  Plus, 
  Copy, 
  Check, 
  MessageCircleHeart, 
  Calendar, 
  ArrowRight,
  ShieldCheck
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  // Selector de Doble Rol: 'mi-legado' (Titular) | 'seres-queridos' (Beneficiario)
  const [activeTab, setActiveTab] = useState<'mi-legado' | 'seres-queridos'>('mi-legado');

  // Estados de "Mi Legado" (Titular)
  const [myCapsules, setMyCapsules] = useState<CapsuleResponse[]>([]);
  const [myBeneficiaries, setMyBeneficiaries] = useState<BeneficiaryInvite[]>([]);
  const [generatedCode, setGeneratedCode] = useState<string | null>(null);
  const [codeCopied, setCodeCopied] = useState(false);
  const [generatingCode, setGeneratingCode] = useState(false);

  // Estados de "Seres Queridos" (Beneficiario)
  const [connections, setConnections] = useState<LegacyConnectionSummary[]>([]);
  const [linkInputCode, setLinkInputCode] = useState('');
  const [linking, setLinking] = useState(false);
  const [linkMessage, setLinkMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const [loading, setLoading] = useState(true);
  const [dashboardError, setDashboardError] = useState('');
  const [inviteError, setInviteError] = useState('');

  // Carga inicial
  useEffect(() => {
    async function loadDashboardData() {
      setLoading(true);
      try {
        const [caps, benefs, conns] = await Promise.all([
          api.getCapsules(),
          api.getMyBeneficiaries(),
          api.getMyConnections()
        ]);
        setMyCapsules(caps);
        setMyBeneficiaries(benefs);
        setConnections(conns);
      } catch (err) {
        console.error("Error cargando dashboard:", err);
        setDashboardError(err instanceof Error ? err.message : 'No se pudo conectar con el servidor.');
      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, []);

  // Generar Código de Invitación (Titular)
  const handleGenerateCode = async () => {
    setGeneratingCode(true);
    setInviteError('');
    try {
      const res = await api.generateInviteCode();
      setGeneratedCode(res.connection_code);
      // Refrescar lista de invitaciones
      try {
        const updated = await api.getMyBeneficiaries();
        setMyBeneficiaries(updated);
      } catch {
        setInviteError('El código se creó, pero no se pudo actualizar la lista. Recarga el panel.');
      }
    } catch (err) {
      console.error(err);
      setInviteError(err instanceof Error ? err.message : 'No se pudo generar el código.');
    } finally {
      setGeneratingCode(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCodeCopied(true);
    setTimeout(() => setCodeCopied(false), 2500);
  };

  // Vincularse con Código (Beneficiario)
  const handleLinkCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!linkInputCode.trim()) return;

    setLinking(true);
    setLinkMessage(null);

    try {
      const res = await api.linkWithCode(linkInputCode);
      setLinkMessage({
        text: `¡Vinculación exitosa con el legado de ${res.owner_name}!`,
        type: 'success'
      });
      setLinkInputCode('');
      setConnections(current => [res, ...current.filter(connection => connection.connection_id !== res.connection_id)]);
    } catch (err: any) {
      setLinkMessage({
        text: err?.message || 'Código de vinculación inválido o expirado.',
        type: 'error'
      });
    } finally {
      setLinking(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-20 text-center text-stone-400 text-sm">
        <div className="w-6 h-6 border-2 border-amber-800/30 border-t-amber-800 rounded-full animate-spin mx-auto mb-3" />
        <span>Cargando tu espacio de legado...</span>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      
      {/* Bienvenida y Saludo */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-stone-200/90 shadow-sm mb-8 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-900 mb-2">
            <Sparkles className="w-3.5 h-3.5 text-amber-700" />
            Panel Contextual Doble Rol
          </span>
          <h2 className="text-2xl sm:text-3xl font-serif-warm font-bold text-stone-900 tracking-tight">
            Hola, {user?.full_name || 'tu cuenta'}
          </h2>
          <p className="text-stone-500 text-sm mt-1">
            Desde aquí puedes gestionar tu propio legado y conectarte con las memorias de tu familia.
          </p>
        </div>

        {/* Selector de Pestaña Principal (Doble Rol) */}
        <div className="flex items-center bg-stone-100 p-1.5 rounded-2xl border border-stone-200/80 self-start md:self-center">
          <button
            onClick={() => setActiveTab('mi-legado')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition cursor-pointer ${
              activeTab === 'mi-legado'
                ? 'bg-amber-800 text-white shadow-sm'
                : 'text-stone-600 hover:text-stone-900'
            }`}
          >
            <BookHeart className="w-4 h-4" />
            <span>Mi Legado</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-white/20 text-white font-normal hidden sm:inline">
              Titular
            </span>
          </button>

          <button
            onClick={() => setActiveTab('seres-queridos')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition cursor-pointer ${
              activeTab === 'seres-queridos'
                ? 'bg-amber-800 text-white shadow-sm'
                : 'text-stone-600 hover:text-stone-900'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>Seres Queridos</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-white/20 text-white font-normal hidden sm:inline">
              Beneficiario
            </span>
          </button>
        </div>
      </div>
      {dashboardError && <div role="alert" className="mb-6 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{dashboardError}</div>}

      {/* ============================================================
          TAB A: MI LEGADO (ROL TITULAR)
          ============================================================ */}
      {activeTab === 'mi-legado' && (
        <div className="space-y-8 animate-fade-in">
          
          {/* Barra de Acciones del Titular */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Tarjeta 1: Crear Recuerdos */}
            <div className="bg-gradient-to-br from-amber-50/90 to-stone-50 rounded-3xl p-6 border border-amber-200/60 shadow-sm flex flex-col justify-between">
              <div>
                <span className="p-2.5 rounded-2xl bg-amber-100 text-amber-900 inline-block mb-3">
                  <Plus className="w-5 h-5" />
                </span>
                <h3 className="font-serif-warm font-bold text-stone-900 text-lg">
                  Capturar Nuevo Recuerdo
                </h3>
                <p className="text-xs text-stone-600 mt-1 leading-relaxed">
                  Redacta tus anécdotas, consejos de vida o recetas con tus propias palabras y muletillas.
                </p>
              </div>
              <button
                onClick={() => navigate('/')}
                className="mt-4 w-full py-2.5 px-4 rounded-xl bg-amber-800 hover:bg-amber-900 text-white text-xs font-semibold flex items-center justify-center gap-2 transition cursor-pointer"
              >
                <span>Ir al Redactor</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Tarjeta 2: Generar Código de Invitación */}
            <div className="md:col-span-2 bg-white rounded-3xl p-6 border border-stone-200/90 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="p-2.5 rounded-2xl bg-amber-100 text-amber-900 inline-block">
                    <KeyRound className="w-5 h-5" />
                  </span>
                  <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200/60 flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Acceso Seguro Criptográfico
                  </span>
                </div>
                <h3 className="font-serif-warm font-bold text-stone-900 text-lg">
                  Invitar a un Ser Querido a tu Legado
                </h3>
                <p className="text-xs text-stone-600 mt-1 leading-relaxed">
                  Genera un código alfanumérico único para que tus hijos, nietos o seres queridos se vinculen a tu cuenta y puedan conversar con tu IA.
                </p>
              </div>

              <div className="mt-4 pt-4 border-t border-stone-100 flex flex-col sm:flex-row items-center gap-3">
                {generatedCode ? (
                  <div className="w-full flex items-center gap-2 bg-amber-50 border border-amber-300/80 rounded-2xl p-2.5 px-4">
                    <div className="flex-1">
                      <span className="text-[10px] uppercase font-bold text-amber-800 block">
                        Código de Invitación Generado:
                      </span>
                      <span className="font-mono text-base font-bold text-amber-950 tracking-wider">
                        {generatedCode}
                      </span>
                    </div>
                    <button
                      onClick={() => copyToClipboard(generatedCode)}
                      className="p-2 rounded-xl bg-amber-800 hover:bg-amber-900 text-white text-xs font-medium flex items-center gap-1.5 transition cursor-pointer"
                    >
                      {codeCopied ? <Check className="w-4 h-4 text-emerald-300" /> : <Copy className="w-4 h-4" />}
                      <span>{codeCopied ? '¡Copiado!' : 'Copiar'}</span>
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={handleGenerateCode}
                    disabled={generatingCode}
                    className="w-full sm:w-auto py-2.5 px-5 rounded-xl bg-amber-800 hover:bg-amber-900 text-white text-xs font-semibold flex items-center justify-center gap-2 transition cursor-pointer shadow-sm"
                  >
                    <KeyRound className="w-4 h-4" />
                    <span>{generatingCode ? 'Generando...' : 'Generar Código de Invitación'}</span>
                  </button>
                )}
              </div>
              {inviteError && <div role="alert" className="mt-3 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-800">{inviteError}</div>}
            </div>

          </div>

          {/* Lista de Invitaciones y Beneficiarios Vinculados */}
          <div className="bg-white rounded-3xl p-6 sm:p-8 border border-stone-200/90 shadow-sm">
            <h3 className="font-serif-warm font-bold text-stone-900 text-lg mb-2 flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-amber-700" />
              Seres Queridos con Acceso a tu Legado
            </h3>
            <p className="text-xs text-stone-500 mb-6">
              Familiares autorizados mediante código de vinculación para interactuar con tus recuerdos.
            </p>

            {myBeneficiaries.length === 0 ? (
              <div className="text-center py-8 text-stone-400 text-xs">
                Aún no has generado códigos de invitación para tus familiares.
              </div>
            ) : (
              <div className="divide-y divide-stone-100">
                {myBeneficiaries.map((b) => (
                  <div key={b.connection_id} className="py-3.5 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center font-bold text-xs">
                        {b.beneficiary_name ? b.beneficiary_name[0] : '#'}
                      </div>
                      <div>
                        <h4 className="text-sm font-semibold text-stone-800">
                          {b.beneficiary_name || 'Código pendiente de canje'}
                        </h4>
                        <div className="flex items-center gap-2 text-[11px] text-stone-500">
                          <span className="font-mono bg-stone-100 px-1.5 py-0.5 rounded text-stone-700 font-medium">
                            {b.connection_code}
                          </span>
                          <span>•</span>
                          <span>{b.beneficiary_email || 'Sin canjear'}</span>
                        </div>
                      </div>
                    </div>

                    <span className={`text-[11px] px-2.5 py-1 rounded-full font-medium ${
                      b.beneficiary_id
                        ? 'bg-emerald-50 text-emerald-800 border border-emerald-200/60'
                        : 'bg-amber-50 text-amber-800 border border-amber-200/60'
                    }`}>
                      {b.beneficiary_id ? 'Vinculado' : 'Pendiente'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Resumen de Mis Cápsulas Creadas */}
          <div className="bg-white rounded-3xl p-6 sm:p-8 border border-stone-200/90 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="font-serif-warm font-bold text-stone-900 text-lg">
                  Mis Cápsulas Registradas ({myCapsules.length})
                </h3>
                <p className="text-xs text-stone-500">Recuerdos indexados en ChromaDB y MongoDB.</p>
              </div>
              <button
                onClick={() => navigate('/capsules')}
                className="text-xs font-semibold text-amber-800 hover:text-amber-900 underline cursor-pointer"
              >
                Ver biblioteca completa
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {myCapsules.slice(0, 4).map((c) => (
                <div key={c._id} className="p-4 rounded-2xl bg-stone-50 border border-stone-200/70">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-bold uppercase text-amber-800 bg-amber-100/70 px-2 py-0.5 rounded-md">
                      {c.category}
                    </span>
                    <span className="text-[10px] text-stone-400">
                      {new Date(c.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <h4 className="font-serif-warm font-bold text-stone-800 text-sm mb-1 line-clamp-1">
                    {c.title}
                  </h4>
                  <p className="text-xs text-stone-500 font-serif-warm line-clamp-2">
                    "{c.content}"
                  </p>
                </div>
              ))}
            </div>
          </div>

        </div>
      )}

      {/* ============================================================
          TAB B: MIS SERES QUERIDOS (ROL BENEFICIARIO)
          ============================================================ */}
      {activeTab === 'seres-queridos' && (
        <div className="space-y-8 animate-fade-in">
          
          {/* Formulario de Vinculación con Código */}
          <div className="bg-gradient-to-br from-amber-900 via-amber-800 to-stone-900 rounded-3xl p-6 sm:p-8 text-white shadow-md">
            <div className="max-w-xl">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-white/10 text-amber-200 mb-3 border border-white/10">
                <KeyRound className="w-3.5 h-3.5" />
                Vincular Nuevo Titular
              </span>
              <h3 className="font-serif-warm font-bold text-2xl text-white">
                ¿Recibiste un código de invitación familiar?
              </h3>
              <p className="text-xs sm:text-sm text-amber-200/80 mt-1.5 leading-relaxed">
                Ingresa el código alfanumérico proporcionado por tu padre, madre o abuelo para conectarte a su memoria viva y acceder a su Chat RAG.
              </p>

              <form onSubmit={handleLinkCode} className="mt-5 flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  value={linkInputCode}
                  onChange={(e) => setLinkInputCode(e.target.value)}
                  placeholder="Ej. LEG-A7K92M"
                  className="flex-1 px-4 py-3 rounded-2xl bg-white/10 border border-white/20 text-white placeholder-amber-200/50 text-sm focus:outline-none focus:bg-white/20 uppercase tracking-widest font-mono"
                  required
                />
                <button
                  type="submit"
                  disabled={linking || !linkInputCode.trim()}
                  className="py-3 px-6 rounded-2xl bg-white text-amber-950 hover:bg-amber-100 font-bold text-xs uppercase tracking-wider transition cursor-pointer shadow-md disabled:opacity-50"
                >
                  {linking ? 'Vinculando...' : 'Vincularse'}
                </button>
              </form>

              {linkMessage && (
                <div className={`mt-3 text-xs p-2.5 rounded-xl ${
                  linkMessage.type === 'success' 
                    ? 'bg-emerald-500/20 text-emerald-200 border border-emerald-500/30' 
                    : 'bg-rose-500/20 text-rose-200 border border-rose-500/30'
                }`}>
                  {linkMessage.text}
                </div>
              )}
            </div>
          </div>

          {/* Tarjetas de Legados Disponibles para Conversar */}
          <div>
            <div className="mb-4">
              <h3 className="font-serif-warm font-bold text-stone-900 text-xl">
                Legados a los que Tienes Acceso
              </h3>
              <p className="text-xs text-stone-500">
                Haz clic en cualquiera de tus seres queridos para iniciar una conversación empática con sus recuerdos.
              </p>
            </div>

            {connections.length === 0 ? (
              <div className="bg-white rounded-3xl p-10 text-center border border-stone-200">
                <Users className="w-10 h-10 text-stone-300 mx-auto mb-2" />
                <h4 className="font-semibold text-stone-700 text-sm">No estás vinculado a ningún legado aún</h4>
                <p className="text-xs text-stone-400 mt-1 max-w-sm mx-auto">
                  Pídele a tu familiar su código de invitación (formato LEG-XXXX) e ingrésalo en el formulario superior.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {connections.map((conn) => (
                  <div
                    key={conn.connection_id}
                    className="bg-white rounded-3xl p-6 border border-stone-200/90 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-2xl bg-amber-700 text-amber-100 flex items-center justify-center font-serif-warm font-bold text-xl shadow-sm">
                            {conn.owner_name[0]}
                          </div>
                          <div>
                            <h4 className="font-serif-warm font-bold text-stone-900 text-lg">
                              {conn.owner_name}
                            </h4>
                            <span className="text-xs text-stone-500">{conn.owner_email}</span>
                          </div>
                        </div>

                        <span className="text-[11px] font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200/60 flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                          Activo
                        </span>
                      </div>

                      <div className="p-3.5 bg-stone-50 rounded-2xl text-xs text-stone-600 mb-4 border border-stone-100 font-serif-warm leading-relaxed">
                        "Todas las respuestas provendrán estrictamente de las anécdotas y aprendizajes registrados por {conn.owner_name}."
                      </div>
                    </div>

                    <div className="pt-4 border-t border-stone-100 flex items-center justify-between">
                      <div className="flex items-center gap-1 text-[11px] text-stone-400">
                        <Calendar className="w-3.5 h-3.5" />
                        <span>Vinculado el {new Date(conn.linked_at || conn.created_at).toLocaleDateString()}</span>
                      </div>

                      <button
                        onClick={() => navigate('/chat', { state: { titularId: conn.owner_id, titularName: conn.owner_name } })}
                        className="py-2.5 px-4 rounded-xl bg-amber-800 hover:bg-amber-900 text-white text-xs font-semibold flex items-center gap-2 transition cursor-pointer shadow-sm"
                      >
                        <MessageCircleHeart className="w-4 h-4" />
                        <span>Conversar con su Legado</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      )}

    </div>
  );
};
