import React, { useEffect, useState } from 'react';
import { api, CapsuleResponse, StyleProfile } from '../services/api';
import { BookHeart, Sparkles, Calendar, Tag, ShieldCheck, Heart, Headphones, Pencil, Check, X } from 'lucide-react';

const CapsuleAudio: React.FC<{ capsuleId: string; title: string }> = ({ capsuleId, title }) => {
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioError, setAudioError] = useState('');
  const [loadingAudio, setLoadingAudio] = useState(false);

  useEffect(() => {
    return () => { if (audioUrl) URL.revokeObjectURL(audioUrl); };
  }, [audioUrl]);

  const loadAudio = async () => {
    setLoadingAudio(true);
    try {
      const blob = await api.getCapsuleAudio(capsuleId);
      setAudioUrl(URL.createObjectURL(blob));
      setAudioError('');
    } catch (error) {
      setAudioError(error instanceof Error ? error.message : 'No se pudo conectar con el servidor.');
    } finally {
      setLoadingAudio(false);
    }
  };

  if (audioError) return <div className="mt-3 text-xs text-rose-700"><p>No se pudo cargar el audio ({audioError}).</p><button type="button" onClick={() => { setAudioError(''); void loadAudio(); }} disabled={loadingAudio} className="mt-1 underline">Intentar de nuevo</button></div>;
  if (!audioUrl) return <button type="button" onClick={loadAudio} disabled={loadingAudio} className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-stone-50 px-2.5 py-2 text-xs font-medium text-stone-600 disabled:opacity-60"><Headphones className="h-3.5 w-3.5" />{loadingAudio ? 'Cargando audio…' : `Cargar audio: ${title}`}</button>;
  return <div className="mt-3 rounded-xl bg-stone-50 p-2.5">
    <p className="mb-2 inline-flex items-center gap-1.5 text-xs font-medium text-stone-600"><Headphones className="h-3.5 w-3.5" />{title}</p>
    <audio controls preload="none" src={audioUrl} className="h-9 w-full" aria-label={`Reproducir audio: ${title}`} />
  </div>;
};

export const CapsuleLibrary: React.FC = () => {
  const [capsules, setCapsules] = useState<CapsuleResponse[]>([]);
  const [profile, setProfile] = useState<StyleProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterCategory, setFilterCategory] = useState<string>('todas');
  const [editingProfile, setEditingProfile] = useState(false);
  const [profileDraft, setProfileDraft] = useState<StyleProfile | null>(null);
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileError, setProfileError] = useState('');

  useEffect(() => {
    async function loadData() {
      try {
        const [capsData, profData] = await Promise.all([
          api.getCapsules(),
          api.getStyleProfile()
        ]);
        setCapsules(capsData);
        setProfile(profData);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const categories = ['todas', ...Array.from(new Set(capsules.map(c => c.category)))];

  const filtered = filterCategory === 'todas'
    ? capsules
    : capsules.filter(c => c.category === filterCategory);

  const startEditingProfile = () => {
    if (!profile) return;
    setProfileDraft({ ...profile, typical_phrases: [...profile.typical_phrases], voice_sample_capsule_id: profile.voice_sample_capsule_id || '', voice_cloning_consent: profile.voice_cloning_consent || false });
    setProfileError('');
    setEditingProfile(true);
  };

  const saveProfile = async () => {
    if (!profileDraft) return;
    setSavingProfile(true);
    setProfileError('');
    try {
      const saved = await api.updateStyleProfile({
        ...profileDraft,
        typical_phrases: profileDraft.typical_phrases.map(phrase => phrase.trim()).filter(Boolean).slice(0, 8),
      });
      setProfile(saved);
      setProfileDraft(null);
      setEditingProfile(false);
    } catch (error) {
      setProfileError(error instanceof Error ? error.message : 'No se pudo guardar el perfil.');
    } finally {
      setSavingProfile(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
        <div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-stone-200/80 text-stone-700 mb-2">
            <BookHeart className="w-3.5 h-3.5" />
            Almacén MongoDB & ChromaDB
          </span>
          <h2 className="text-3xl font-serif-warm font-bold text-stone-900 tracking-tight">
            Biblioteca de Cápsulas de Memoria
          </h2>
          <p className="text-stone-600 text-sm mt-1">
            Los cimientos de la personalidad y los recuerdos verificados del titular.
          </p>
        </div>

        {/* Filtros */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2 md:pb-0">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setFilterCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium capitalize transition cursor-pointer ${
                filterCategory === cat
                  ? 'bg-amber-800 text-white shadow-sm'
                  : 'bg-white text-stone-600 border border-stone-200 hover:bg-stone-50'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Tarjeta del Perfil de Estilo Extraído */}
      {profile && (
        <div className="mb-8 p-6 rounded-3xl bg-gradient-to-r from-amber-900 via-amber-800 to-stone-900 text-amber-50 shadow-md">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-amber-300" />
              <h3 className="font-serif-warm font-bold text-lg text-white">Mi forma de hablar</h3>
            </div>
            {!editingProfile ? (
              <button type="button" onClick={startEditingProfile} className="inline-flex items-center gap-1.5 rounded-xl border border-white/20 bg-white/10 px-3 py-2 text-xs font-medium text-white hover:bg-white/20">
                <Pencil className="h-3.5 w-3.5" />Editar perfil
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button type="button" onClick={() => { setEditingProfile(false); setProfileDraft(null); setProfileError(''); }} className="inline-flex items-center gap-1 rounded-xl border border-white/20 px-3 py-2 text-xs text-white hover:bg-white/10"><X className="h-3.5 w-3.5" />Cancelar</button>
                <button type="button" onClick={saveProfile} disabled={savingProfile || !profileDraft} className="inline-flex items-center gap-1 rounded-xl bg-amber-200 px-3 py-2 text-xs font-semibold text-amber-950 hover:bg-amber-100 disabled:opacity-60"><Check className="h-3.5 w-3.5" />{savingProfile ? 'Guardando…' : 'Guardar'}</button>
              </div>
            )}
          </div>
          <p className="text-xs text-amber-200/80 mb-4 max-w-2xl">
            El chat usa estas preferencias para acercarse a tu manera de expresarte. Puedes cambiarlas cuando quieras.
          </p>
          <p className="mb-4 text-xs text-amber-100/90">Voz propia: {profile.voice_cloning_consent && profile.voice_sample_capsule_id ? 'configurada' : 'pendiente de configurar'}. La primera generación puede tardar mientras se descarga el modelo de voz.</p>
          {editingProfile && profileDraft ? (
            <div className="grid grid-cols-1 gap-3 text-xs sm:grid-cols-2">
              <label className="space-y-1.5"><span className="block font-medium text-amber-100">Estilo al hablar</span><select value={profileDraft.formality_level} onChange={event => setProfileDraft({ ...profileDraft, formality_level: event.target.value })} className="w-full rounded-xl border border-white/20 bg-stone-900/30 px-3 py-2.5 text-white"><option className="text-stone-900" value="formal, respetuoso y claro">Formal y respetuoso</option><option className="text-stone-900" value="cercano, conversacional y amable">Cercano y conversacional</option><option className="text-stone-900" value="coloquial, espontáneo y familiar">Coloquial y familiar</option><option className="text-stone-900" value="sereno, solemne y reflexivo">Sereno y solemne</option><option className="text-stone-900" value={profileDraft.formality_level}>{profileDraft.formality_level}</option></select></label>
              <label className="space-y-1.5"><span className="block font-medium text-amber-100">Tono emocional</span><select value={profileDraft.sentiment_tendency} onChange={event => setProfileDraft({ ...profileDraft, sentiment_tendency: event.target.value })} className="w-full rounded-xl border border-white/20 bg-stone-900/30 px-3 py-2.5 text-white"><option className="text-stone-900" value="sereno y reflexivo">Sereno y reflexivo</option><option className="text-stone-900" value="alegre y optimista">Alegre y optimista</option><option className="text-stone-900" value="nostálgico y cariñoso">Nostálgico y cariñoso</option><option className="text-stone-900" value="directo y práctico">Directo y práctico</option><option className="text-stone-900" value="protector y afectuoso">Protector y afectuoso</option><option className="text-stone-900" value={profileDraft.sentiment_tendency}>{profileDraft.sentiment_tendency}</option></select></label>
              <label className="space-y-1.5"><span className="flex justify-between font-medium text-amber-100"><span>Calidez</span><span>{Math.round(profileDraft.warmth_score * 100)}%</span></span><input type="range" min="0" max="1" step="0.05" value={profileDraft.warmth_score} onChange={event => setProfileDraft({ ...profileDraft, warmth_score: Number(event.target.value) })} className="w-full accent-amber-200" /></label>
              <label className="space-y-1.5"><span className="block font-medium text-amber-100">Expresiones propias (separadas por coma)</span><input type="text" maxLength={240} value={profileDraft.typical_phrases.join(', ')} onChange={event => setProfileDraft({ ...profileDraft, typical_phrases: event.target.value.split(',').map(phrase => phrase.trim()).slice(0, 8) })} placeholder="mira, te cuento" className="w-full rounded-xl border border-white/20 bg-stone-900/30 px-3 py-2.5 text-white placeholder:text-white/50" /></label>
              <label className="space-y-1.5 sm:col-span-2"><span className="block font-medium text-amber-100">Grabación para crear tu voz</span><select value={profileDraft.voice_sample_capsule_id || ''} onChange={event => setProfileDraft({ ...profileDraft, voice_sample_capsule_id: event.target.value || null, voice_cloning_consent: event.target.value ? profileDraft.voice_cloning_consent : false })} className="w-full rounded-xl border border-white/20 bg-stone-900/30 px-3 py-2.5 text-white"><option className="text-stone-900" value="">No usar voz clonada</option>{capsules.filter(capsule => capsule.audio_path).map(capsule => <option className="text-stone-900" key={capsule._id} value={capsule._id}>{capsule.title}</option>)}</select><span className="block text-[11px] text-amber-100/70">Elige una grabación clara de tu propia voz, idealmente de 10 segundos o más.</span></label>
              <label className="flex items-start gap-2 text-amber-50 sm:col-span-2"><input type="checkbox" checked={profileDraft.voice_cloning_consent || false} disabled={!profileDraft.voice_sample_capsule_id} onChange={event => setProfileDraft({ ...profileDraft, voice_cloning_consent: event.target.checked })} className="mt-0.5 accent-amber-200" /><span>Autorizo usar esta grabación para generar respuestas con una voz sintética parecida a la mía. Solo se usará en mi legado y por las personas vinculadas con permiso.</span></label>
              {profileError && <p role="alert" className="text-rose-200 sm:col-span-2">{profileError}</p>}
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 text-xs sm:grid-cols-3">
              <div className="rounded-2xl border border-white/10 bg-white/10 p-3.5 backdrop-blur-sm"><span className="mb-1 block text-[10px] font-bold uppercase text-amber-200/70">Estilo y calidez</span><p className="font-medium text-white">{profile.formality_level} · {Math.round(profile.warmth_score * 100)}%</p></div>
              <div className="rounded-2xl border border-white/10 bg-white/10 p-3.5 backdrop-blur-sm"><span className="mb-1 block text-[10px] font-bold uppercase text-amber-200/70">Expresiones propias</span><div className="mt-1 flex flex-wrap gap-1">{profile.typical_phrases.length ? profile.typical_phrases.map((phrase, index) => <span key={`${phrase}-${index}`} className="rounded-md bg-amber-400/20 px-2 py-0.5 text-[11px] font-medium text-amber-200">“{phrase}”</span>) : <span className="text-white/80">Aún no has añadido expresiones.</span>}</div></div>
              <div className="rounded-2xl border border-white/10 bg-white/10 p-3.5 backdrop-blur-sm"><span className="mb-1 block text-[10px] font-bold uppercase text-amber-200/70">Tono predominante</span><div className="mt-1 flex items-center gap-1.5"><Heart className="h-4 w-4 text-rose-400" /><span className="font-medium text-white">{profile.sentiment_tendency}</span></div></div>
            </div>
          )}
        </div>
      )}

      {/* Grid de Cápsulas */}
      {loading ? (
        <div className="text-center py-16 text-stone-400 text-sm">
          Cargando biblioteca de recuerdos...
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-3xl border border-stone-200">
          <BookHeart className="w-10 h-10 text-stone-300 mx-auto mb-3" />
          <h4 className="font-semibold text-stone-700">No hay cápsulas en esta categoría</h4>
          <p className="text-xs text-stone-400 mt-1">Ve a "Captura de Recuerdos" para registrar una nueva anécdota.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((capsule) => (
            <article
              key={capsule._id}
              className="bg-white rounded-3xl p-6 shadow-sm border border-stone-200/90 hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="px-2.5 py-1 rounded-lg bg-amber-50 text-amber-900 font-semibold text-[11px] border border-amber-200/50">
                    {capsule.category}
                  </span>
                  <div className="flex items-center gap-1 text-[11px] text-stone-400">
                    <Calendar className="w-3.5 h-3.5" />
                    {new Date(capsule.created_at).toLocaleDateString()}
                  </div>
                </div>

                <h3 className="font-serif-warm font-bold text-stone-900 text-lg leading-snug mb-3">
                  {capsule.title}
                </h3>

                <p className="text-xs text-stone-600 font-serif-warm leading-relaxed line-clamp-4 mb-4">
                  "{capsule.content}"
                </p>
                {capsule.audio_path && <CapsuleAudio capsuleId={capsule._id} title={capsule.title} />}
              </div>

              <div>
                <div className="flex flex-wrap gap-1 mb-4">
                  {capsule.tags.map((tag, idx) => (
                    <span key={idx} className="inline-flex items-center gap-1 text-[10px] text-stone-500 bg-stone-100 px-2 py-0.5 rounded-md">
                      <Tag className="w-2.5 h-2.5" />
                      {tag}
                    </span>
                  ))}
                </div>

                <div className="pt-3 border-t border-stone-100 flex items-center justify-between text-[11px] text-stone-500">
                  <span className="italic text-stone-400">Tono: {capsule.emotional_tone || 'Cariñoso'}</span>
                  <span className="inline-flex items-center gap-1 text-emerald-700 font-medium bg-emerald-50 px-2 py-0.5 rounded-md">
                    <ShieldCheck className="w-3 h-3" />
                    Indexado RAG
                  </span>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
};

