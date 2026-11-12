import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  api, 
  LegacyConnectionSummary, 
  BeneficiaryInvite, 
  CapsuleResponse,
  CodePreviewResponse,
  GenerateCodeResponse
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
  ShieldCheck,
  Clock,
  AlertCircle,
  XCircle,
  RefreshCw,
  UserMinus,
  CheckCircle2,
  Trash2
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  // Selector de Doble Rol: 'mi-legado' (Titular) | 'seres-queridos' (Beneficiario)
  const [activeTab, setActiveTab] = useState<'mi-legado' | 'seres-queridos'>('mi-legado');

  // Estados de "Mi Legado" (Titular)
  const [myCapsules, setMyCapsules] = useState<CapsuleResponse[]>([]);
  const [myBeneficiaries, setMyBeneficiaries] = useState<BeneficiaryInvite[]>([]);
  const [generatedCodeData, setGeneratedCodeData] = useState<GenerateCodeResponse | null>(null);
  const [codeCopied, setCodeCopied] = useState(false);
  const [generatingCode, setGeneratingCode] = useState(false);
  const [expirationHours, setExpirationHours] = useState<number>(48);
  const [cancellingCodeId, setCancellingCodeId] = useState<string | null>(null);
  const [titularActionMessage, setTitularActionMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Estados de "Seres Queridos" (Beneficiario)
  const [connections, setConnections] = useState<LegacyConnectionSummary[]>([]);
  const [linkInputCode, setLinkInputCode] = useState('');
  const [previewData, setPreviewData] = useState<CodePreviewResponse | null>(null);
  const [validatingCode, setValidatingCode] = useState(false);
  const [confirmingLink, setConfirmingLink] = useState(false);
  const [unlinkingId, setUnlinkingId] = useState<string | null>(null);
  const [beneficiaryMessage, setBeneficiaryMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const [loading, setLoading] = useState(true);

  // Carga inicial
  useEffect(() => {
    async function loadDashboardData() {
      setLoading(true);
      try {
        const [caps, benefs, conns] = await Promise.all([
          api.getCapsules().catch(() => []),
          api.getMyBeneficiaries().catch(() => []),
          api.getMyConnections().catch(() => [])
        ]);
        setMyCapsules(caps);
        setMyBeneficiaries(benefs);
        setConnections(conns);
      } catch (err) {
        console.error("Error cargando dashboard:", err);
      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, []);

  // ==========================================
  // ROL TITULAR: ACCIONES
  // ==========================================

  // Generar Código de Invitación con vigencia configurable
  const handleGenerateCode = async () => {
    setGeneratingCode(true);
    setTitularActionMessage(null);
    try {
      const res = await api.generateInviteCode(expirationHours, false);
      setGeneratedCodeData(res);
      setTitularActionMessage({
        text: `Código generado exitosamente. Válido por ${expirationHours} horas.`,
        type: 'success'
      });
      // Refrescar lista de invitaciones
      const updated = await api.getMyBeneficiaries();
      setMyBeneficiaries(updated);
    } catch (err: any) {
      setTitularActionMessage({
        text: err?.message || 'Error al generar código de vinculación.',
        type: 'error'
      });
    } finally {
      setGeneratingCode(false);
    }
  };

  // Cancelar Código Pendiente
  const handleCancelCode = async (connectionId: string) => {
    if (!window.confirm("¿Seguro que deseas cancelar este código de invitación? Ya no podrá ser canjeado.")) {
      return;
    }
    setCancellingCodeId(connectionId);
    setTitularActionMessage(null);
    try {
      await api.cancelInviteCode(connectionId);
      if (generatedCodeData?.connection_id === connectionId) {
        setGeneratedCodeData(null);
      }
      setTitularActionMessage({
        text: 'Código de invitación cancelado exitosamente.',
        type: 'success'
      });
      const updated = await api.getMyBeneficiaries();
      setMyBeneficiaries(updated);
    } catch (err: any) {
      setTitularActionMessage({
        text: err?.message || 'Error al cancelar el código.',
        type: 'error'
      });
    } finally {
      setCancellingCodeId(null);
    }
  };

  // Desvincular Beneficiario (Titular o Beneficiario)
  const handleUnlink = async (connectionId: string, name: string) => {
    if (!window.confirm(`¿Seguro que deseas desvincular a ${name}? Se revocará el acceso a los recuerdos.`)) {
      return;
    }
    setUnlinkingId(connectionId);
    try {
      await api.unlinkConnection(connectionId);
      // Refrescar ambas listas
      const [benefs, conns] = await Promise.all([
        api.getMyBeneficiaries().catch(() => []),
        api.getMyConnections().catch(() => [])
      ]);
      setMyBeneficiaries(benefs);
      setConnections(conns);

      if (activeTab === 'mi-legado') {
        setTitularActionMessage({
          text: `Vinculación con ${name} revocada exitosamente.`,
          type: 'success'
        });
      } else {
        setBeneficiaryMessage({
          text: `Te has desvinculado exitosamente del legado de ${name}.`,
          type: 'success'
        });
      }
    } catch (err: any) {
      const msg = err?.message || 'Error al desvincular.';
      if (activeTab === 'mi-legado') {
        setTitularActionMessage({ text: msg, type: 'error' });
      } else {
        setBeneficiaryMessage({ text: msg, type: 'error' });
      }
    } finally {
      setUnlinkingId(null);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCodeCopied(true);
    setTimeout(() => setCodeCopied(false), 2500);
  };

  // ==========================================
  // ROL BENEFICIARIO: ACCIONES
  // ==========================================

  // Paso 1: Validar y previsualizar identidad del Titular
  const handlePreviewCode = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanCode = linkInputCode.trim().toUpperCase();
    if (!cleanCode) return;

    setValidatingCode(true);
    setBeneficiaryMessage(null);
    setPreviewData(null);

    try {
      const preview = await api.previewInviteCode(cleanCode);
      setPreviewData(preview);
    } catch (err: any) {
      setBeneficiaryMessage({
        text: err?.message || 'Código de vinculación inválido o expirado.',
        type: 'error'
      });
    } finally {
      setValidatingCode(false);
    }
  };

  // Paso 2: Confirmar explícitamente la vinculación
  const handleConfirmLink = async () => {
    if (!previewData) return;

    setConfirmingLink(true);
    setBeneficiaryMessage(null);

    try {
      const res = await api.confirmLink(previewData.connection_code);
      setBeneficiaryMessage({
        text: `¡Vinculación completada con éxito! Ahora tienes acceso al legado de ${res.owner_name}.`,
        type: 'success'
      });
      setLinkInputCode('');
      setPreviewData(null);
      // Refrescar conexiones activas
      const conns = await api.getMyConnections();
      setConnections(conns);
    } catch (err: any) {
      setBeneficiaryMessage({
        text: err?.message || 'Error al confirmar la vinculación.',
        type: 'error'
      });
    } finally {
      setConfirmingLink(false);
    }
  };

  const handleCancelPreview = () => {
    setPreviewData(null);
  };

  // Helper para formato de fecha amigable
  const formatDate = (isoString?: string) => {
    if (!isoString) return '';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString('es-ES', { 
        day: 'numeric', 
        month: 'short', 
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return isoString;
    }
  };

  // Helper para badge de tiempo restante
  const formatTimeRemaining = (seconds?: number) => {
    if (seconds === undefined || seconds === null) return null;
    if (seconds <= 0) return 'Expirado';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 24) {
      const days = Math.floor(hours / 24);
      return `${days}d ${hours % 24}h restantes`;
    }
    if (hours > 0) {
      return `${hours}h ${minutes}m restantes`;
    }
    return `${minutes} min restantes`;
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
            Hola, {user?.full_name || 'Alberto'}
          </h2>
          <p className="text-stone-500 text-sm mt-1">
            Gestiona tu legado personal como Titular o conéctate como Beneficiario a las memorias de tus seres queridos.
          </p>
        </div>

        {/* Selector de Pestaña Principal (Doble Rol) */}
        <div className="flex items-center bg-stone-100 p-1.5 rounded-2xl border border-stone-200/80 self-start md:self-center">
          <button
            onClick={() => { setActiveTab('mi-legado'); setBeneficiaryMessage(null); }}
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
            onClick={() => { setActiveTab('seres-queridos'); setTitularActionMessage(null); }}
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

      {/* ============================================================
          TAB A: MI LEGADO (ROL TITULAR)
          ============================================================ */}
      {activeTab === 'mi-legado' && (
        <div className="space-y-8 animate-fade-in">
          
          {/* Mensajes de feedback del Titular */}
          {titularActionMessage && (
            <div className={`p-4 rounded-2xl text-xs sm:text-sm flex items-center gap-3 ${
              titularActionMessage.type === 'success'
                ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                : 'bg-rose-50 text-rose-800 border border-rose-200'
            }`}>
              {titularActionMessage.type === 'success' ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
              ) : (
                <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
              )}
              <span>{titularActionMessage.text}</span>
            </div>
          )}

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

            {/* Tarjeta 2: Generar Código de Invitación con Expiración Configurable */}
            <div className="md:col-span-2 bg-white rounded-3xl p-6 border border-stone-200/90 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="p-2.5 rounded-2xl bg-amber-100 text-amber-900 inline-block">
                    <KeyRound className="w-5 h-5" />
                  </span>
                  <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200/60 flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Generación Criptográfica & Anti-Fuerza Bruta
                  </span>
                </div>
                <h3 className="font-serif-warm font-bold text-stone-900 text-lg">
                  Invitar a un Ser Querido a tu Legado
                </h3>
                <p className="text-xs text-stone-600 mt-1 leading-relaxed">
                  Genera un código aleatorio único y difícil de adivinar para que tus hijos o nietos se vinculen. Cada código tiene fecha de caducidad configurable.
                </p>

                {/* Selector de vigencia configurable */}
                <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
                  <span className="text-stone-500 font-medium">Vigencia del código:</span>
                  {[
                    { label: '24 horas', val: 24 },
                    { label: '48 horas (Recomendado)', val: 48 },
                    { label: '7 días', val: 168 },
                    { label: '30 días', val: 720 },
                  ].map((opt) => (
                    <button
                      key={opt.val}
                      type="button"
                      onClick={() => setExpirationHours(opt.val)}
                      className={`px-3 py-1 rounded-xl font-medium border text-xs transition cursor-pointer ${
                        expirationHours === opt.val
                          ? 'bg-amber-100 text-amber-900 border-amber-300 font-semibold shadow-xs'
                          : 'bg-stone-50 text-stone-600 border-stone-200 hover:bg-stone-100'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="mt-5 pt-4 border-t border-stone-100 flex flex-col gap-3">
                {generatedCodeData ? (
                  <div className="w-full bg-amber-50/70 border border-amber-300/80 rounded-2xl p-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <span className="text-[10px] uppercase font-bold text-amber-800 tracking-wider block mb-0.5">
                          Código de Invitación Generado:
                        </span>
                        <div className="flex items-center gap-3">
                          <span className="font-mono text-xl font-bold text-amber-950 tracking-widest bg-white px-3 py-1 rounded-xl border border-amber-200 shadow-xs">
                            {generatedCodeData.connection_code}
                          </span>
                          <button
                            onClick={() => copyToClipboard(generatedCodeData.connection_code)}
                            className="py-1.5 px-3 rounded-xl bg-amber-800 hover:bg-amber-900 text-white text-xs font-medium flex items-center gap-1.5 transition cursor-pointer shadow-xs"
                          >
                            {codeCopied ? <Check className="w-4 h-4 text-emerald-300" /> : <Copy className="w-4 h-4" />}
                            <span>{codeCopied ? '¡Copiado!' : 'Copiar'}</span>
                          </button>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleCancelCode(generatedCodeData.connection_id)}
                          className="py-1.5 px-3 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-semibold flex items-center gap-1 border border-rose-200 transition cursor-pointer"
                        >
                          <XCircle className="w-3.5 h-3.5" />
                          <span>Cancelar Código</span>
                        </button>
                        <button
                          onClick={handleGenerateCode}
                          disabled={generatingCode}
                          className="py-1.5 px-3 rounded-xl bg-stone-100 hover:bg-stone-200 text-stone-700 text-xs font-semibold flex items-center gap-1 border border-stone-300/80 transition cursor-pointer"
                        >
                          <RefreshCw className={`w-3.5 h-3.5 ${generatingCode ? 'animate-spin' : ''}`} />
                          <span>Regenerar</span>
                        </button>
                      </div>
                    </div>

                    <div className="mt-3 flex items-center gap-2 text-[11px] text-amber-900/80 font-medium">
                      <Clock className="w-3.5 h-3.5 text-amber-700" />
                      <span>
                        Válido hasta el {formatDate(generatedCodeData.expires_at)}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-between gap-3">
                    <button
                      onClick={handleGenerateCode}
                      disabled={generatingCode}
                      className="py-2.5 px-5 rounded-xl bg-amber-800 hover:bg-amber-900 text-white text-xs font-semibold flex items-center gap-2 transition cursor-pointer shadow-sm disabled:opacity-50"
                    >
                      <KeyRound className="w-4 h-4" />
                      <span>{generatingCode ? 'Generando código único...' : 'Generar Código de Invitación'}</span>
                    </button>
                    <span className="text-xs text-stone-400 hidden sm:inline">
                      Se creará un código único de alta entropía
                    </span>
                  </div>
                )}
              </div>
            </div>

          </div>

          {/* Lista de Invitaciones y Beneficiarios Vinculados */}
          <div className="bg-white rounded-3xl p-6 sm:p-8 border border-stone-200/90 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-serif-warm font-bold text-stone-900 text-lg flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-amber-700" />
                Códigos y Seres Queridos Vinculados
              </h3>
              <span className="text-xs text-stone-500 font-medium">
                {myBeneficiaries.length} {myBeneficiaries.length === 1 ? 'registro' : 'registros'}
              </span>
            </div>
            <p className="text-xs text-stone-500 mb-6">
              Supervisa quién tiene acceso a tus memorias, administra códigos vigentes y revoca accesos en cualquier momento.
            </p>

            {myBeneficiaries.length === 0 ? (
              <div className="text-center py-10 text-stone-400 text-xs bg-stone-50/60 rounded-2xl border border-dashed border-stone-200">
                <KeyRound className="w-8 h-8 text-stone-300 mx-auto mb-2" />
                <p className="font-medium text-stone-600">Aún no has generado códigos de invitación para tus familiares.</p>
                <p className="mt-1 text-stone-400">Haz clic en "Generar Código de Invitación" para compartir tu legado.</p>
              </div>
            ) : (
              <div className="divide-y divide-stone-100">
                {myBeneficiaries.map((b) => {
                  const isPending = b.status === 'PENDING';
                  const isActive = b.status === 'ACTIVE';
                  const isExpired = b.is_expired || b.status === 'EXPIRED';
                  const isCancelled = b.status === 'CANCELLED';
                  const isRevoked = b.status === 'REVOKED';

                  return (
                    <div key={b.connection_id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="flex items-start sm:items-center gap-3.5">
                        <div className={`w-10 h-10 rounded-2xl flex items-center justify-center font-bold text-xs flex-shrink-0 ${
                          isActive 
                            ? 'bg-emerald-100 text-emerald-800' 
                            : isPending 
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-stone-100 text-stone-500'
                        }`}>
                          {b.beneficiary_name ? b.beneficiary_name[0] : <KeyRound className="w-4 h-4" />}
                        </div>

                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="text-sm font-semibold text-stone-900">
                              {b.beneficiary_name || 'Código de invitación pendiente'}
                            </h4>
                            <span className="font-mono bg-stone-100 px-2 py-0.5 rounded text-stone-700 font-bold text-xs tracking-wider border border-stone-200">
                              {b.connection_code}
                            </span>
                          </div>

                          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-stone-500 mt-1">
                            {b.beneficiary_email && <span>{b.beneficiary_email}</span>}
                            <span>Creado el {formatDate(b.created_at)}</span>
                            {b.linked_at && (
                              <span className="text-emerald-700 font-medium">
                                • Vinculado el {formatDate(b.linked_at)}
                              </span>
                            )}
                            {isPending && b.expires_at && (
                              <span className="text-amber-800 font-medium flex items-center gap-1">
                                <Clock className="w-3 h-3 text-amber-600" />
                                {formatTimeRemaining(b.time_remaining_seconds) || `Expira: ${formatDate(b.expires_at)}`}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 self-end sm:self-center">
                        {/* Status Badge */}
                        <span className={`text-[11px] px-2.5 py-1 rounded-full font-semibold border ${
                          isActive
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-200/80'
                            : isPending
                            ? 'bg-amber-50 text-amber-800 border-amber-200/80'
                            : isExpired
                            ? 'bg-stone-100 text-stone-600 border-stone-200'
                            : isCancelled
                            ? 'bg-rose-50 text-rose-700 border-rose-200'
                            : 'bg-stone-100 text-stone-500 border-stone-200'
                        }`}>
                          {isActive && 'Vinculado Activo'}
                          {isPending && 'Pendiente de Canje'}
                          {isExpired && 'Expirado'}
                          {isCancelled && 'Cancelado'}
                          {isRevoked && 'Revocado'}
                        </span>

                        {/* Botón de acción para el titular: Cancelar o Desvincular */}
                        {isPending && (
                          <button
                            onClick={() => handleCancelCode(b.connection_id)}
                            disabled={cancellingCodeId === b.connection_id}
                            className="p-1.5 text-stone-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition cursor-pointer"
                            title="Cancelar código de invitación"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}

                        {isActive && (
                          <button
                            onClick={() => handleUnlink(b.connection_id, b.beneficiary_name || 'este familiar')}
                            disabled={unlinkingId === b.connection_id}
                            className="px-2.5 py-1 rounded-lg text-rose-700 hover:bg-rose-50 border border-rose-200/60 text-xs font-medium flex items-center gap-1 transition cursor-pointer"
                            title="Desvincular a este usuario"
                          >
                            <UserMinus className="w-3.5 h-3.5" />
                            <span>Desvincular</span>
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
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
          
          {/* Mensajes de feedback del Beneficiario */}
          {beneficiaryMessage && (
            <div className={`p-4 rounded-2xl text-xs sm:text-sm flex items-center gap-3 ${
              beneficiaryMessage.type === 'success'
                ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                : 'bg-rose-50 text-rose-800 border border-rose-200'
            }`}>
              {beneficiaryMessage.type === 'success' ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
              ) : (
                <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
              )}
              <span>{beneficiaryMessage.text}</span>
            </div>
          )}

          {/* Formulario de Vinculación y Previsualización */}
          <div className="bg-gradient-to-br from-amber-900 via-amber-800 to-stone-900 rounded-3xl p-6 sm:p-8 text-white shadow-md">
            <div className="max-w-2xl">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-white/10 text-amber-200 mb-3 border border-white/10">
                <KeyRound className="w-3.5 h-3.5" />
                Vincular Nuevo Titular
              </span>
              <h3 className="font-serif-warm font-bold text-2xl text-white">
                ¿Recibiste un código de invitación familiar?
              </h3>
              <p className="text-xs sm:text-sm text-amber-200/80 mt-1.5 leading-relaxed">
                Ingresa el código proporcionado por tu padre, madre o abuelo. Podrás previsualizar su identidad antes de confirmar la vinculación.
              </p>

              {/* Formulario de ingreso de código */}
              {!previewData ? (
                <form onSubmit={handlePreviewCode} className="mt-5 flex flex-col sm:flex-row gap-3">
                  <input
                    type="text"
                    value={linkInputCode}
                    onChange={(e) => setLinkInputCode(e.target.value)}
                    placeholder="Ej. LEG-A7K92M"
                    maxLength={32}
                    className="flex-1 px-4 py-3 rounded-2xl bg-white/10 border border-white/20 text-white placeholder-amber-200/50 text-sm focus:outline-none focus:bg-white/20 uppercase tracking-widest font-mono"
                    required
                  />
                  <button
                    type="submit"
                    disabled={validatingCode || !linkInputCode.trim()}
                    className="py-3 px-6 rounded-2xl bg-white text-amber-950 hover:bg-amber-100 font-bold text-xs uppercase tracking-wider transition cursor-pointer shadow-md disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {validatingCode ? (
                      <>
                        <div className="w-3.5 h-3.5 border-2 border-amber-900 border-t-transparent rounded-full animate-spin" />
                        <span>Validando...</span>
                      </>
                    ) : (
                      <>
                        <KeyRound className="w-4 h-4" />
                        <span>Verificar Código</span>
                      </>
                    )}
                  </button>
                </form>
              ) : (
                /* Card de Confirmación Explícita con Identidad del Titular */
                <div className="mt-5 bg-white/10 border border-white/20 rounded-2xl p-5 text-white animate-fade-in">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 rounded-2xl bg-amber-200 text-amber-950 font-serif-warm font-bold text-xl flex items-center justify-center shadow-sm">
                      {previewData.owner_name[0]}
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-bold text-amber-300 block tracking-wider">
                        Titular Encontrado
                      </span>
                      <h4 className="text-lg font-bold font-serif-warm text-white">
                        {previewData.owner_name}
                      </h4>
                      <p className="text-xs text-amber-100/70">
                        Código verificado: <span className="font-mono text-white font-medium">{previewData.connection_code}</span> • Válido hasta {formatDate(previewData.expires_at)}
                      </p>
                    </div>
                  </div>

                  <div className="p-3 bg-black/20 rounded-xl text-xs text-amber-100/90 leading-relaxed mb-4 border border-white/5">
                    ¿Confirmas que deseas vincular tu cuenta con <strong>{previewData.owner_name}</strong>? Podrás acceder a sus recuerdos y conversar con su mimetismo de voz e inteligencia artificial.
                  </div>

                  <div className="flex flex-col sm:flex-row items-center gap-3">
                    <button
                      onClick={handleConfirmLink}
                      disabled={confirmingLink}
                      className="w-full sm:w-auto py-2.5 px-6 rounded-xl bg-white text-amber-950 hover:bg-amber-100 font-bold text-xs uppercase tracking-wider transition cursor-pointer shadow-md disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                      {confirmingLink ? (
                        <>
                          <div className="w-3.5 h-3.5 border-2 border-amber-950 border-t-transparent rounded-full animate-spin" />
                          <span>Vinculando...</span>
                        </>
                      ) : (
                        <>
                          <Check className="w-4 h-4 text-emerald-700" />
                          <span>Confirmar Vinculación</span>
                        </>
                      )}
                    </button>
                    <button
                      onClick={handleCancelPreview}
                      disabled={confirmingLink}
                      className="w-full sm:w-auto py-2.5 px-4 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-semibold transition cursor-pointer border border-white/10"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Tarjetas de Legados Disponibles para Conversar */}
          <div>
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h3 className="font-serif-warm font-bold text-stone-900 text-xl">
                  Legados a los que Tienes Acceso
                </h3>
                <p className="text-xs text-stone-500">
                  Haz clic en cualquiera de tus seres queridos para iniciar una conversación empática con sus recuerdos.
                </p>
              </div>
              <span className="text-xs font-medium text-stone-500">
                {connections.length} {connections.length === 1 ? 'vinculación' : 'vinculaciones'}
              </span>
            </div>

            {connections.length === 0 ? (
              <div className="bg-white rounded-3xl p-10 text-center border border-stone-200">
                <Users className="w-10 h-10 text-stone-300 mx-auto mb-2" />
                <h4 className="font-semibold text-stone-700 text-sm">No estás vinculado a ningún legado aún</h4>
                <p className="text-xs text-stone-400 mt-1 max-w-sm mx-auto">
                  Pídele a tu familiar su código de invitación (formato LEG-XXXXXXXX) e ingrésalo en el formulario superior.
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
                            <span className="text-xs text-stone-500">{conn.owner_email || 'Titular de Legado'}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="text-[11px] font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200/60 flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                            Activo
                          </span>
                          <button
                            onClick={() => handleUnlink(conn.connection_id, conn.owner_name)}
                            disabled={unlinkingId === conn.connection_id}
                            className="p-1.5 text-stone-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition cursor-pointer"
                            title="Desvincularme de este legado"
                          >
                            <UserMinus className="w-4 h-4" />
                          </button>
                        </div>
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
