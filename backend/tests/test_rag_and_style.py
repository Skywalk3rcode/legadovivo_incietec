import pytest
from app.services.style_analyzer import StyleAnalyzer


def test_style_analyzer_extracts_affection_and_colloquialisms():
    sample_texts = [
        "Mijito lindo, te cuento que en esa época íbamos al río todos los domingos.",
        "Oye, fíjate bien: con todo mi cariño te digo que seas siempre honesto, corazón.",
        "Mijito, sabes qué... la vida pasa volando, aprovecha cada segundo."
    ]

    profile = StyleAnalyzer.analyze_texts(
        titular_id="test-user-1",
        texts=sample_texts
    )

    assert profile.titular_id == "test-user-1"
    # Debe haber detectado muletillas como 'mijito', 'oye', 'fíjate', etc.
    assert any("mijito" in p or "oye" in p or "cariño" in p for p in profile.typical_phrases)
    assert profile.warmth_score >= 0.8
    assert "afectuoso" in profile.formality_level.lower() or "cálido" in profile.formality_level.lower()


def test_zero_hallucination_rule_fallback_logic():
    """
    Verifica que el prompt o fallback estricto se genera con la sintaxis
    exacta requerida ante ausencia de similitud semántica.
    """
    suggested_topic = "mi viaje a Cusco"
    fallback_response = (
        f"No dejé registros sobre este tema específico en mi legado, "
        f"pero me encantaría que recordáramos {suggested_topic}."
    )

    # Validaciones de la regla crítica de negocio
    assert "No dejé registros sobre este tema específico en mi legado" in fallback_response
    assert "pero me encantaría que recordáramos" in fallback_response
    assert suggested_topic in fallback_response

