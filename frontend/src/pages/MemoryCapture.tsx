import React, { useRef, useState } from 'react';
import { api } from '../services/api';
import { Feather, Sparkles, CheckCircle2, HeartHandshake, Tag, Mic, Square, Upload, X } from 'lucide-react';

export const MemoryCapture: React.FC = () => {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('Anécdotas');
  const [emotionalTone, setEmotionalTone] = useState('nostálgico y cariñoso');
  const [tagsInput, setTagsInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [audio, setAudio] = useState<File | Blob | null>(null);
  const [audioName, setAudioName] = useState('');
  const [pendingAudioCapsuleId, setPendingAudioCapsuleId] = useState<string | null>(null);
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState('');
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Detección simple en vivo de modismos para ilustrar el Learning Loop
  const detectedPhrases = ['mijito', 'mi vida', 'oye', 'fíjate', 'sabes qué', 'con todo mi cariño', 'te cuento']
    .filter(phrase => content.toLowerCase().includes(phrase));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;

    setLoading(true);
    setSuccess(false);
    setError('');

    try {
      let capsuleId = pendingAudioCapsuleId;
      if (!capsuleId) {
        const tags = tagsInput.split(',').map(t => t.trim()).filter(Boolean);
        const created = await api.createCapsule({
          title,
          content,
          category,
          emotional_tone: emotionalTone,
          tags: tags.length ? tags : ['familia', 'recuerdos']
        });
        capsuleId = created._id;
        if (audio) setPendingAudioCapsuleId(capsuleId);
      }
      if (audio && capsuleId) {
        const extension = audioName.match(/\.[^.]+$/)?.[0] || '.webm';
        const safeTitle = title.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
          .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 50) || 'recuerdo';
        const filename = audio instanceof File ? audio.name : `${safeTitle}${extension}`;
        await api.uploadCapsuleAudio(capsuleId, audio, filename);
      }

      setSuccess(true);
      setPendingAudioCapsuleId(null);
      setTitle('');
      setContent('');
      setTagsInput('');
      setAudio(null);
      setAudioName('');
      setTimeout(() => setSuccess(false), 4000);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : 'No se pudo guardar el recuerdo.');
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    setError('');
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setError('Este navegador no permite grabar audio. Puedes seleccionar un archivo.');
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      const chunks: BlobPart[] = [];
      recorder.ondataavailable = (event) => { if (event.data.size) chunks.push(event.data); };
      recorder.onstop = () => {
        const type = recorder.mimeType || 'audio/webm';
        const extension = type.includes('ogg') ? 'ogg' : type.includes('mp4') ? 'm4a' : 'webm';
        setAudio(new Blob(chunks, { type }));
        setAudioName(`recuerdo.${extension}`);
        stream.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      };
      recorderRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch {
      setError('No se pudo acceder al micrófono. Revisa el permiso del navegador.');
    }
  };

  const stopRecording = () => {
    if (recorderRef.current?.state === 'recording') recorderRef.current.stop();
    setRecording(false);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Encabezado empático */}
      <div className="text-center mb-8">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-100/80 text-amber-800 mb-3 border border-amber-200/60">
          <HeartHandshake className="w-3.5 h-3.5" />
          Para el Titular del Legado
        </span>
        <h2 className="text-3xl sm:text-4xl font-serif-warm font-bold text-stone-900 tracking-tight">
          Preserva tus recuerdos tal como los contarías tú
        </h2>
        <p className="mt-2 text-stone-600 max-w-xl mx-auto text-sm sm:text-base leading-relaxed">
          Cada palabra, muletilla y emoción que escribas aquí alimentará el motor neuronal. Tu familia escuchará tu verdadera voz.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Formulario Principal */}
        <div className="lg:col-span-2 bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-stone-200/80">
          {success && (
            <div className="mb-6 p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-center gap-3 animate-fade-in">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
              <div className="text-sm">
                <span className="font-semibold">¡Cápsula guardada e indexada!</span>
                <p className="text-xs text-emerald-700 mt-0.5">Vectorizada en ChromaDB y sincronizada con el perfil de estilo.</p>
              </div>
            </div>
          )}
          {error && <div role="alert" className="mb-5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</div>}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-stone-700 mb-2">
                Título del recuerdo o enseñanza
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Ej. El día que compramos la primera bicicleta..."
                className="w-full px-4 py-3 rounded-2xl bg-stone-50 border border-stone-200 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-600 text-stone-900 placeholder-stone-400 text-sm transition"
                required
              />
            </div>

            <section className="rounded-2xl border border-amber-200/70 bg-amber-50/50 p-4" aria-label="Audio del recuerdo">
              <div className="mb-3">
                <h3 className="text-sm font-semibold text-stone-800">Audio del recuerdo <span className="font-normal text-stone-500">(opcional)</span></h3>
                <p className="mt-1 text-xs text-stone-500">Graba con el micrófono o selecciona un audio de hasta 25 MB.</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {recording ? (
                  <button type="button" onClick={stopRecording} className="inline-flex items-center gap-2 rounded-xl bg-rose-700 px-3 py-2 text-xs font-medium text-white">
                    <Square className="h-3.5 w-3.5" /> Detener grabación
                  </button>
                ) : (
                  <button type="button" onClick={startRecording} className="inline-flex items-center gap-2 rounded-xl border border-amber-300 bg-white px-3 py-2 text-xs font-medium text-amber-900">
                    <Mic className="h-3.5 w-3.5" /> Grabar audio
                  </button>
                )}
                <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-stone-200 bg-white px-3 py-2 text-xs font-medium text-stone-700">
                  <Upload className="h-3.5 w-3.5" /> Subir archivo
                  <input type="file" accept="audio/*,.m4a,.mp3,.wav,.ogg,.webm,.aac" className="sr-only" disabled={recording} onChange={event => {
                    const file = event.target.files?.[0];
                    if (!file) return;
                    const allowed = /\.(webm|ogg|wav|mp3|m4a|aac|mp4)$/i.test(file.name);
                    if (!allowed || !file.type.startsWith('audio/')) { setError('Selecciona un archivo de audio compatible.'); return; }
                    if (file.size > 25 * 1024 * 1024) { setError('El audio debe pesar menos de 25 MB.'); return; }
                    setError(''); setAudio(file); setAudioName(file.name); event.target.value = '';
                  }} />
                </label>
                {audioName && <span className="inline-flex items-center gap-1.5 text-xs text-stone-600"><Mic className="h-3.5 w-3.5" />{audio instanceof File ? audio.name : 'Grabación lista'}<button type="button" aria-label="Quitar audio" onClick={() => { setAudio(null); setAudioName(''); }}><X className="h-3.5 w-3.5" /></button></span>}
              </div>
            </section>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-stone-700 mb-2">
                  Categoría
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-4 py-3 rounded-2xl bg-stone-50 border border-stone-200 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-600 text-stone-800 text-sm transition"
                >
                  <option value="Anécdotas">Anécdotas de Vida</option>
                  <option value="Consejos y Valores">Consejos y Valores</option>
                  <option value="Infancia y Familia">Infancia y Familia</option>
                  <option value="Cocina y Tradición">Cocina y Tradición</option>
                  <option value="Momentos Difíciles">Superación y Resiliencia</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-stone-700 mb-2">
                  Tono Emocional
                </label>
                <input
                  type="text"
                  value={emotionalTone}
                  onChange={(e) => setEmotionalTone(e.target.value)}
                  placeholder="Ej. nostálgico, protector, risueño"
                  className="w-full px-4 py-3 rounded-2xl bg-stone-50 border border-stone-200 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-600 text-stone-800 text-sm transition"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-stone-700">
                  Tu relato (Escribe tal como hablas)
                </label>
                <span className="text-[11px] text-stone-400">
                  {content.length} caracteres
                </span>
              </div>
              <textarea
                rows={6}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Escribe con tus propias palabras... 'Mijito, te cuento que en esa época no teníamos teléfono, pero nos veíamos todos los domingos en la plaza...'"
                className="w-full p-4 rounded-2xl bg-stone-50 border border-stone-200 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-600 text-stone-900 placeholder-stone-400 text-sm leading-relaxed transition resize-none font-serif-warm"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-stone-700 mb-2 flex items-center gap-1.5">
                <Tag className="w-3.5 h-3.5" />
                Etiquetas temáticas (separadas por coma)
              </label>
              <input
                type="text"
                value={tagsInput}
                onChange={(e) => setTagsInput(e.target.value)}
                placeholder="navidad, juventud, abuela, consejos"
                className="w-full px-4 py-2.5 rounded-2xl bg-stone-50 border border-stone-200 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-600 text-stone-800 text-xs transition"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !title.trim() || !content.trim()}
              className="w-full py-3.5 px-6 rounded-2xl bg-gradient-to-r from-amber-700 to-amber-800 hover:from-amber-800 hover:to-amber-900 text-white font-medium text-sm flex items-center justify-center gap-2 shadow-lg shadow-amber-900/15 disabled:opacity-50 transition-all cursor-pointer"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Vectorizando en ChromaDB...</span>
                </>
              ) : (
                <>
                  <Feather className="w-4 h-4" />
                  <span>Guardar e Inyectar en el Legado</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Panel lateral: Learning Loop en vivo */}
        <div className="space-y-6">
          <div className="bg-gradient-to-br from-amber-50/80 to-stone-100 rounded-3xl p-6 border border-amber-200/50 shadow-sm">
            <div className="flex items-center gap-2 text-amber-900 font-semibold text-sm mb-3">
              <Sparkles className="w-4 h-4 text-amber-600" />
              <span>Análisis de Estilo en Vivo</span>
            </div>
            <p className="text-xs text-stone-600 leading-relaxed mb-4">
              El motor de NLP extrae tus muletillas y patrones para que la IA adopte tu calidez sin inventar hechos.
            </p>

            <div className="space-y-3">
              <div>
                <span className="text-[11px] uppercase tracking-wider text-stone-500 font-bold block mb-1.5">
                  Muletillas detectadas en este texto:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {detectedPhrases.length > 0 ? (
                    detectedPhrases.map((phrase, i) => (
                      <span key={i} className="px-2.5 py-1 rounded-lg bg-amber-200/80 text-amber-900 text-xs font-medium">
                        "{phrase}"
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-stone-400 italic">
                      Escribe expresiones cotidianas como "oye", "te cuento" o "mijito"...
                    </span>
                  )}
                </div>
              </div>

              <div className="pt-3 border-t border-amber-200/60">
                <span className="text-[11px] uppercase tracking-wider text-stone-500 font-bold block mb-1">
                  Regla de Cero Alucinación
                </span>
                <p className="text-[11px] text-stone-600 leading-normal">
                  Este recuerdo será indexado con embeddings semánticos. El asistente solo responderá con datos exactos extraídos de tus cápsulas.
                </p>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

