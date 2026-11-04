"""
Punto de entrada principal para la aplicación móvil LegadoVivo.
Segundo Incremento: Arquitectura en Python (Kivy) con persistencia local SQLite
y consulta basada estrictamente en fuentes autorizadas.
"""

import sys
import os

# Configuración de dimensiones de pantalla móvil antes de inicializar la ventana Kivy
from kivy.config import Config
from config import MOBILE_WINDOW_WIDTH, MOBILE_WINDOW_HEIGHT, APP_NAME

# En plataformas no móviles (escritorio), configurar viewport para emular smartphone
from kivy.utils import platform

if platform not in ("android", "ios"):
    Config.set("graphics", "width", str(MOBILE_WINDOW_WIDTH))
    Config.set("graphics", "height", str(MOBILE_WINDOW_HEIGHT))
    Config.set("graphics", "resizable", "0")

from kivy.app import App
from kivy.core.window import Window

from storage.repository import CapsuleRepository
from services.capsule_service import CapsuleService
from services.query_engine import QueryEngine
from services.connectivity_service import ConnectivityService
from ui.app_ui import MainMobileLayout


class LegadoVivoApp(App):
    """
    Clase principal de la aplicación móvil LegadoVivo.
    """

    def build(self):
        self.title = f"{APP_NAME} - Preservación de Memoria"
        self.icon = "icon.png" if os.path.exists("icon.png") else ""

        # Inicialización de la capa de persistencia local (SQLite)
        self.repository = CapsuleRepository()

        # Sembrar datos ficticios de demostración si la base de datos está vacía
        self.repository.seed_initial_data()

        # Inicialización de la capa de lógica de negocio y servicios
        self.capsule_service = CapsuleService(repository=self.repository)
        self.query_engine = QueryEngine(repository=self.repository)
        self.connectivity_service = ConnectivityService()

        # Construir y retornar la jerarquía visual raíz
        return MainMobileLayout(
            capsule_service=self.capsule_service,
            query_engine=self.query_engine,
            connectivity_service=self.connectivity_service
        )

    def on_pause(self):
        """Manejo del ciclo de vida en Android: pausar sin destruir estado."""
        return True

    def on_resume(self):
        """Manejo del ciclo de vida en Android: reanudar aplicación."""
        pass


if __name__ == "__main__":
    LegadoVivoApp().run()

