import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { api, ChatResponse } from '../services/api';
import {
  Send,
  Sparkles,
  BookOpen,
  AlertCircle,
  RefreshCw,
  ArrowLeft,
  Volume2,
  VolumeX,
  Mic,
  MicOff
} from 'lucide-react';

interface MessageItem {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  sources?: string[];
  confidence?: number;
}

export const LegacyChat: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const activeTitularName = (location.state as any)?.titularName || "Abuelo Alberto";
  const activeTitularId = (location.state as any)?.titularId;

  const [messages, setMessages] = useState<MessageItem[]>([
    {
      id: 'init-msg',
      sender: 'assistant',
      text: `Mijito lindo, qué alegría que estés aquí. Aunque el tiempo pase, siempre estaré contigo a través de mis recuerdos. ¿De qué te gustaría que conversemos hoy?`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      sources: ['Mensaje de bienvenida afectuosa']
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [speakingId, setSpeakingId] = useState<string | null>(null);
  const [listening, setListening] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Cancelar voz al desmontar
  useEffect(() => {
    return () => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // Síntesis de voz cálida (Web Speech API)
  const handleSpeak = (messageId: string, text: string) => {
    if (!('speechSynthesis' in window)) return;

    if (speakingId === messageId) {
      window.speechSynthesis.cancel();
      setSpeakingId(null);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'es-ES';
    utterance.rate = 0.92; // Ritmo pausado y sosegado
    utterance.pitch = 0.95; // Tono más grave y cálido

    utterance.onend = () => setSpeakingId(null);
    utterance.onerror = () => setSpeakingId(null);

    setSpeakingId(messageId);
    window.speechSynthesis.speak(utterance);
  };

  // Reconocimiento de voz para dictar preguntas (Speech Recognition)
  const handleVoiceInput = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Tu navegador no soporta entrada de voz directa. Puedes escribir tu pregunta en el campo de texto.");
      return;
    }

    if (listening) {
      setListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = 'es-ES';
      recognition.interimResults = false;
      recognition.continuous = false;

      recognition.onstart = () => setListening(true);
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInput(prev => (prev ? `${prev} ${transcript}` : transcript));
        setListening(false);
      };
      recognition.onerror = () => setListening(false);
      recognition.onend = () => setListening(false);

      recognition.start();
    } catch {
      setListening(false);
    }
  };

  const handleSend = async (textToSend?: string) => {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    const userMsg: MessageItem = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const res: ChatResponse = await api.sendChatMessage(query, activeTitularName, activeTitularId);
      const botMsg: MessageItem = {
        id: `bot-${Date.now()}`,
        sender: 'assistant',
        text: res.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources: res.sources,
        confidence: res.confidence
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const quickPrompts = [
    { text: "¿Cómo fue tu viaje a Cusco con el tío Carlos?", type: "hit", label: "Pregunta con recuerdo registrado (RAG Hit)" },
    { text: "Cuéntame el secreto para preparar el estofado", type: "hit", label: "Pregunta sobre receta familiar (RAG Hit)" },
    { text: "¿Cuánto dinero ganaste en la lotería en París?", type: "miss", label: "Tema no registrado (Prueba Cero Alucinación)" }
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 h-[calc(100vh-5rem)] flex flex-col">

      {/* Encabezado del Legado */}
      <div className="bg-white rounded-3xl p-4 sm:p-5 border border-stone-200/90 shadow-sm flex items-center justify-between mb-4">
        <div className="flex items-center gap-3.5">
          <button
            onClick={() => navigate('/dashboard')}
            className="p-2 rounded-xl text-stone-500 hover:text-stone-800 hover:bg-stone-100 transition cursor-pointer"
            title="Volver al Dashboard"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>

          <div className="relative">
            <div className="w-12 h-12 rounded-2xl bg-amber-700 text-amber-100 flex items-center justify-center font-serif-warm text-xl font-bold shadow-md">
              {activeTitularName[0]}
            </div>
            <span className="absolute -bottom-1 -right-1 w-4 h-4 bg-emerald-500 border-2 border-white rounded-full"></span>
          </div>
          <div>
            <h3 className="font-serif-warm font-bold text-stone-900 text-base flex items-center gap-2">
              {activeTitularName}
              <span className="text-[10px] bg-amber-100 text-amber-900 px-2 py-0.5 rounded-full font-medium">
                Voz Sintética Afectuosa
              </span>
            </h3>
            <p className="text-xs text-stone-500">
              Respuestas basadas estrictamente en sus recuerdos registrados.
            </p>
          </div>
        </div>

        <div className="hidden sm:flex items-center gap-1.5 text-xs text-stone-400 bg-stone-50 px-3 py-1.5 rounded-xl border border-stone-200">
          <Sparkles className="w-3.5 h-3.5 text-amber-600" />
          <span>Motor RAG + Ollama</span>
        </div>
      </div>

      {/* Prompts Rápidos de Prueba */}
      <div className="mb-4 flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        <span className="text-stone-400 flex-shrink-0 font-medium">Probar:</span>
        {quickPrompts.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(q.text)}
            className={`px-3 py-1.5 rounded-xl border transition flex-shrink-0 cursor-pointer ${q.type === 'hit'
                ? 'bg-amber-50 border-amber-200 text-amber-900 hover:bg-amber-100'
                : 'bg-rose-50 border-rose-200 text-rose-900 hover:bg-rose-100'
              }`}
          >
            {q.label}
          </button>
        ))}
      </div>

      {/* Historial de Mensajes */}
      <div className="flex-1 bg-stone-100/50 rounded-3xl p-4 sm:p-6 border border-stone-200/70 overflow-y-auto space-y-4">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[85%] sm:max-w-[75%] rounded-3xl p-4 sm:p-5 shadow-sm text-sm leading-relaxed ${m.sender === 'user'
                  ? 'bg-amber-800 text-white rounded-br-none'
                  : 'bg-white text-stone-800 border border-stone-200/80 rounded-bl-none font-serif-warm'
                }`}
            >
              <div className="flex items-start justify-between gap-3">
                <p className="whitespace-pre-wrap flex-1">{m.text}</p>

                {/* Botón de Escuchar con Voz Cálida */}
                {m.sender === 'assistant' && (
                  <button
                    onClick={() => handleSpeak(m.id, m.text)}
                    className="p-1.5 rounded-lg text-stone-400 hover:text-amber-800 hover:bg-amber-50 transition cursor-pointer flex-shrink-0"
                    title={speakingId === m.id ? "Detener voz" : "Escuchar con voz sintética"}
                  >
                    {speakingId === m.id ? (
                      <VolumeX className="w-4 h-4 text-amber-700 animate-pulse" />
                    ) : (
                      <Volume2 className="w-4 h-4" />
                    )}
                  </button>
                )}
              </div>

              {/* Fuentes y Regla de Negocio */}
              {m.sender === 'assistant' && (
                <div className="mt-3 pt-2.5 border-t border-stone-100 flex items-center justify-between text-[11px] text-stone-400 font-sans">
                  <div className="flex items-center gap-1.5">
                    {m.sources && m.sources.length > 0 ? (
                      <>
                        <BookOpen className="w-3 h-3 text-amber-600" />
                        <span className="text-amber-900/80 font-medium">
                          Fuente: {m.sources.join(', ')}
                        </span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-3 h-3 text-rose-500" />
                        <span className="text-rose-700 font-medium">
                          Regla Cero Alucinación Aplicada
                        </span>
                      </>
                    )}
                  </div>
                  <span className="text-[10px] text-stone-400">{m.timestamp}</span>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-start">
            <div className="bg-white rounded-3xl rounded-bl-none p-4 border border-stone-200 shadow-sm flex items-center gap-2 text-stone-500 text-xs font-serif-warm">
              <RefreshCw className="w-4 h-4 animate-spin text-amber-700" />
              <span>Recordando con cariño...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input de Envío con Micrófono y Dictado */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="mt-4 flex items-center gap-2 sm:gap-3"
      >
        <div className="flex-1 relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={listening ? "Escuchando tu voz..." : "Escribe tu pregunta o saludo a tu ser querido..."}
            className={`w-full pl-5 pr-12 py-4 rounded-2xl bg-white border text-stone-900 placeholder-stone-400 text-sm shadow-sm transition focus:outline-none focus:ring-2 focus:ring-amber-500/20 ${listening ? 'border-rose-400 ring-2 ring-rose-200' : 'border-stone-200 focus:border-amber-600'
              }`}
          />

          <button
            type="button"
            onClick={handleVoiceInput}
            title={listening ? "Detener dictado" : "Dictar con tu voz"}
            className={`absolute right-3 p-2 rounded-xl transition cursor-pointer ${listening
                ? 'bg-rose-100 text-rose-700 animate-pulse'
                : 'text-stone-400 hover:text-stone-700 hover:bg-stone-100'
              }`}
          >
            {listening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </button>
        </div>

        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="p-4 rounded-2xl bg-amber-800 hover:bg-amber-900 text-white shadow-md shadow-amber-900/20 disabled:opacity-40 transition cursor-pointer flex-shrink-0"
        >
          <Send className="w-5 h-5" />
        </button>
      </form>
    </div>
  );
};
