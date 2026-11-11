import React, { useEffect, useState } from 'react';
import { api, CapsuleResponse, StyleProfile } from '../services/api';
import { BookHeart, Sparkles, Calendar, Tag, ShieldCheck, Heart } from 'lucide-react';

export const CapsuleLibrary: React.FC = () => {
  const [capsules, setCapsules] = useState<CapsuleResponse[]>([]);
  const [profile, setProfile] = useState<StyleProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterCategory, setFilterCategory] = useState<string>('todas');

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
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-5 h-5 text-amber-300" />
            <h3 className="font-serif-warm font-bold text-lg text-white">
              Perfil Lingüístico Consolidado (Learning Loop)
            </h3>
          </div>
          <p className="text-xs text-amber-200/80 mb-4 max-w-2xl">
            Este perfil se inyecta dinámicamente en el System Prompt de Ollama cada vez que un ser querido abre el chat.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="bg-white/10 rounded-2xl p-3.5 backdrop-blur-sm border border-white/10">
              <span className="text-amber-200/70 block uppercase font-bold text-[10px] mb-1">
                Formalidad y Calidez
              </span>
              <p className="font-medium text-white">{profile.formality_level}</p>
            </div>
            <div className="bg-white/10 rounded-2xl p-3.5 backdrop-blur-sm border border-white/10">
              <span className="text-amber-200/70 block uppercase font-bold text-[10px] mb-1">
                Muletillas & Afectos Frecuentes
              </span>
              <div className="flex flex-wrap gap-1 mt-1">
                {profile.typical_phrases.map((phrase, i) => (
                  <span key={i} className="bg-amber-400/20 text-amber-200 px-2 py-0.5 rounded-md font-medium text-[11px]">
                    "{phrase}"
                  </span>
                ))}
              </div>
            </div>
            <div className="bg-white/10 rounded-2xl p-3.5 backdrop-blur-sm border border-white/10">
              <span className="text-amber-200/70 block uppercase font-bold text-[10px] mb-1">
                Tono Predominante
              </span>
              <div className="flex items-center gap-1.5 mt-1">
                <Heart className="w-4 h-4 text-rose-400" />
                <span className="font-medium text-white">{profile.sentiment_tendency}</span>
              </div>
            </div>
          </div>
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

