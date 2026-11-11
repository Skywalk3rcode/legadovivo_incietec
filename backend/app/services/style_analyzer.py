import re
from collections import Counter
from datetime import datetime
from typing import List, Dict, Any
from app.models.mongo_schemas import StyleProfile


class StyleAnalyzer:
    """
    Motor de análisis estilístico y lingüístico (Learning Loop).
    Extrae muletillas, términos afectivos, formalidad y modismos
    sin depender de hechos, permitiendo al LLM imitar el modo de hablar del titular.
    """

    AFFECTION_MARKERS = [
        "mi vida", "mijito", "mijita", "cariño", "hijo", "hija", "corazón",
        "mi cielo", "mi amor", "querido", "querida", "muchacho", "muchacha"
    ]

    INFORMAL_MARKERS = [
        "oye", "mira", "fíjate", "te cuento", "sabes qué", "bueno", "pues",
        "chico", "caramba", "hombre", "imagínate", "a ver"
    ]

    FORMAL_MARKERS = [
        "estimado", "le agradezco", "cordialmente", "considere", "por consiguiente",
        "en consecuencia", "usted", "le sugiero", "ciertamente"
    ]

    @classmethod
    def analyze_texts(cls, titular_id: str, texts: List[str]) -> StyleProfile:
        if not texts:
            return StyleProfile(
                titular_id=titular_id,
                typical_phrases=["hijo", "te cuento"],
                formality_level="cercano y afectuoso",
                warmth_score=0.9,
                sentiment_tendency="nostálgico y cariñoso",
                sample_excerpts=[],
                last_updated=datetime.utcnow()
            )

        combined_text = " ".join(texts).lower()

        # 1. Búsqueda de expresiones de afecto frecuentes
        found_affection = [phrase for phrase in cls.AFFECTION_MARKERS if phrase in combined_text]

        # 2. Búsqueda de modismos o muletillas conversacionales
        found_informal = [marker for marker in cls.INFORMAL_MARKERS if marker in combined_text]
        found_formal = [marker for marker in cls.FORMAL_MARKERS if marker in combined_text]

        # 3. Detección de n-gramas (bigramas/trigramas) recurrentes
        words = re.findall(r'\b[a-záéíóúñ]{3,}\b', combined_text)
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)] if len(words) > 1 else []
        bigram_counts = Counter(bigrams).most_common(5)
        top_bigrams = [b[0] for b in bigram_counts if b[1] > 1]

        # Consolidar muletillas distintivas
        typical_phrases = list(dict.fromkeys(found_affection + found_informal + top_bigrams))[:7]
        if not typical_phrases:
            typical_phrases = ["mira", "te cuento", "con todo mi cariño"]

        # 4. Cálculo del nivel de formalidad
        formal_count = len(found_formal)
        informal_count = len(found_informal) + len(found_affection)

        if formal_count > informal_count + 1:
            formality_level = "formal, respetuoso y solemne"
            warmth_score = 0.65
        elif informal_count >= formal_count:
            formality_level = "cálido, conversacional y muy afectuoso"
            warmth_score = 0.95
        else:
            formality_level = "equilibrado, amable y sereno"
            warmth_score = 0.8

        # 5. Extractos representativos breves (para few-shot prompting)
        sample_excerpts = []
        for text in texts[:3]:
            sentences = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 15]
            if sentences:
                sample_excerpts.append(sentences[0])

        return StyleProfile(
            titular_id=titular_id,
            typical_phrases=typical_phrases,
            formality_level=formality_level,
            warmth_score=warmth_score,
            sentiment_tendency="emotivo, protector y entrañable",
            sample_excerpts=sample_excerpts,
            last_updated=datetime.utcnow()
        )

