"""
Script de generación automatizada de capturas visuales de escritorio para LegadoVivo.
Utiliza Window.screenshot de Kivy para registrar evidencia del flujo de interfaz.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kivy.clock import Clock
from kivy.core.window import Window
from main import LegadoVivoApp

OUTPUT_DIR = ROOT / "docs" / "capturas_desktop"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class ScreenshotApp(LegadoVivoApp):
    def on_start(self):
        super().on_start()
        layout = self.root

        # 1. Captura de Inicio / Conectividad en Biblioteca
        Clock.schedule_once(lambda dt: self._shot("01_inicio_conectividad"), 1.0)

        # 2. Captura de Formulario con Validación de Error
        Clock.schedule_once(lambda dt: layout.navigate_to_form(None), 1.3)
        Clock.schedule_once(lambda dt: self._trigger_validation_error(layout), 1.6)
        Clock.schedule_once(lambda dt: self._shot("02_formulario_validacion"), 2.2)

        # 3. Captura de Biblioteca con tarjetas
        Clock.schedule_once(lambda dt: layout.navigate_to_library(), 2.5)
        Clock.schedule_once(lambda dt: self._shot("03_biblioteca_capsulas"), 3.0)

        # 4. Captura de Consulta con Fuente Aprobada
        Clock.schedule_once(lambda dt: layout.navigate_to_query(), 3.3)
        Clock.schedule_once(lambda dt: layout.screen_query.quick_search("honestidad"), 3.6)
        Clock.schedule_once(lambda dt: self._shot("04_consulta_con_fuente"), 4.3)

        # 5. Captura de Consulta con Abstención Estricta
        Clock.schedule_once(lambda dt: layout.screen_query.quick_search("viaje a Marte y física cuántica"), 4.7)
        Clock.schedule_once(lambda dt: self._shot("05_abstencion_estricta"), 5.4)

        # 6. Captura de Modo Offline (Sin Conexión)
        Clock.schedule_once(lambda dt: layout.toggle_offline_simulation(None), 5.8)
        Clock.schedule_once(lambda dt: layout.navigate_to_library(), 6.2)
        Clock.schedule_once(lambda dt: self._shot("06_modo_offline"), 6.8)

        # 7. Finalizar ejecución
        Clock.schedule_once(lambda dt: self.stop(), 7.4)

    def _trigger_validation_error(self, layout):
        layout.screen_form.txt_title.text = ""
        layout.screen_form.txt_content.text = ""
        layout.screen_form.save_capsule(None)

    def _shot(self, name: str):
        shot_path = Window.screenshot(name=str(OUTPUT_DIR / f"{name}.png"))
        target = OUTPUT_DIR / f"{name}.png"
        if Path(shot_path) != target:
            if target.exists():
                target.unlink()
            Path(shot_path).replace(target)
        print(f"[CAPTURA REGISTRADA] {target}")


if __name__ == "__main__":
    ScreenshotApp().run()
