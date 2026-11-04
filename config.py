"""
Configuraciones globales y constantes para la aplicación LegadoVivo.
"""

import os
from pathlib import Path

# Nombre y versión de la aplicación
APP_NAME = "LegadoVivo"
APP_VERSION = "2.0.0"
APP_SUBTITLE = "Preservación y Consulta Responsable de Memoria Personal"

# Dimensiones estándar para emulación de pantalla móvil en entorno de escritorio
MOBILE_WINDOW_WIDTH = 412
MOBILE_WINDOW_HEIGHT = 860

# Temas predefinidos para la clasificación de cápsulas
AVAILABLE_TOPICS = [
    "Valores y Principios",
    "Infancia y Familia",
    "Trabajo y Carrera",
    "Mensajes para el Futuro",
    "Anécdotas y Consejos",
    "Filosofía de Vida"
]

# Mensaje legal y ético obligatorio para las consultas
DISCLAIMER_TEXT = (
    "AVISO IMPORTANTE: Esta consulta es una representación generada exclusivamente "
    "a partir del material autorizado por el titular. No constituye una comunicación "
    "auténtica de la persona en tiempo real ni asesoramiento médico, jurídico o financiero."
)

# Mensaje formal de abstención ante falta de información autorizada
ABSTENTION_MESSAGE = (
    "El sistema no encontró registros o fuentes autorizadas que respondan a esta inquietud. "
    "Para garantizar la máxima fidelidad y honestidad con el titular, el sistema se "
    "abstiene deliberadamente de inventar, suponer o extrapolar respuestas."
)

# Mensaje de operatividad sin sincronización remota
OFFLINE_NOTICE = (
    "Modo Local Autónomo: Todos los datos residen exclusivamente en la base de datos "
    "local del dispositivo. No existe backend ni sincronización con servidores externos."
)

def get_database_path() -> str:
    """
    Determina la ruta de almacenamiento de la base de datos SQLite.
    En Android, python-for-android define ANDROID_APP_PATH con el directorio
    privado de la aplicación (aislado por sandbox de Android): es el lugar
    correcto y seguro para los datos íntimos del legado.
    En entorno de desarrollo local, utiliza la carpeta del workspace.
    """
    android_app_path = os.environ.get("ANDROID_APP_PATH")
    if android_app_path:
        base_dir = Path(android_app_path)
    else:
        # Directorio base del proyecto
        base_dir = Path(__file__).resolve().parent

    # Garantizar que el directorio exista y sea escribible antes de crear la BD
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Último recurso (p. ej. directorio de solo lectura): memoria temporal
        import tempfile
        base_dir = Path(tempfile.gettempdir()) / "legadovivo"
        base_dir.mkdir(parents=True, exist_ok=True)

    db_path = base_dir / "legado_vivo.db"
    return str(db_path)

