"""
Servicio de monitoreo de conectividad de red e integridad offline para LegadoVivo.
Integra la detección nativa de Android y provee garantías de operación 100% local.
"""

import socket
from typing import Dict, Any
from kivy.utils import platform
from config import OFFLINE_NOTICE


class ConnectivityService:
    """
    Gestiona la verificación del estado de red en Android y plataformas de escritorio.
    
    ¿Qué necesidad de LegadoVivo resuelve?
    1. Privacidad y Seguridad: LegadoVivo preserva vivencias, valores y reflexiones íntimas.
       El usuario necesita certeza absoluta de que su material no se está transmitiendo
       silenciosamente a servidores en la nube sin su consentimiento.
    2. Resiliencia en Zonas Rurales y Entornos Desconectados: En contextos donde no hay
       cobertura de red (como visitas rurales, viajes o apagones), el titular y sus beneficiarios
       tienen la garantía de que tanto la biblioteca como el motor de consulta funcionan
       de manera completamente autónoma.
    3. Transparencia: Informa claramente que no existe backend ni sincronización oculta.
    """

    def __init__(self):
        # Permite simular el modo offline en entornos de desarrollo o demostraciones académicas
        self._simulated_offline: bool = False

    @property
    def is_simulated_offline(self) -> bool:
        return self._simulated_offline

    def set_simulated_offline(self, state: bool) -> None:
        """Activa o desactiva la simulación de desconexión para pruebas."""
        self._simulated_offline = state

    def toggle_simulation(self) -> bool:
        """Alterna el modo de simulación offline y devuelve el nuevo estado."""
        self._simulated_offline = not self._simulated_offline
        return self._simulated_offline

    def check_android_connectivity(self) -> bool:
        """
        Consulta el estado de red nativo de Android mediante PyJNIus / ConnectivityManager.
        Usa la API moderna (getActiveNetwork + NetworkCapabilities, Android 5+) y
        conserva la API clásica como respaldo para dispositivos antiguos.
        """
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Context = autoclass("android.content.Context")
            ConnectivityManager = autoclass("android.net.ConnectivityManager")
            activity = PythonActivity.mActivity
            conn_mgr = activity.getSystemService(Context.CONNECTIVITY_SERVICE)

            # API moderna: red activa + capacidades (no deprecada)
            active_network = conn_mgr.getActiveNetwork()
            if active_network is not None:
                capabilities = conn_mgr.getNetworkCapabilities(active_network)
                if capabilities is not None:
                    return bool(
                        capabilities.hasCapability(
                            ConnectivityManager.NET_CAPABILITY_INTERNET
                        )
                    )

            # Respaldo: API clásica (obsoleta pero todavía disponible)
            active_info = conn_mgr.getActiveNetworkInfo()
            return active_info is not None and active_info.isConnected()
        except Exception:
            # Fallback a verificación mediante socket si JNI no está disponible en el entorno
            return self.check_socket_connectivity()

    def check_socket_connectivity(self, host: str = "8.8.8.8", port: int = 53, timeout: float = 0.5) -> bool:
        """
        Verificación de conectividad agnóstica mediante intento de conexión TCP con timeout breve.
        """
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.timeout, OSError):
            return False

    def is_connected(self) -> bool:
        """
        Determina si el dispositivo tiene acceso a red en este instante.
        Considera la anulación manual si está activa la simulación offline.
        """
        if self._simulated_offline:
            return False

        if platform == "android":
            return self.check_android_connectivity()
        else:
            return self.check_socket_connectivity()

    def get_status_summary(self) -> Dict[str, Any]:
        """
        Retorna un informe completo del estado de red y las garantías locales de la aplicación.
        """
        connected = self.is_connected()
        status_label = "Conectado a la red" if connected else "Sin conexión de red"
        sync_note = (
            "Dispositivo en línea. Sin embargo, LegadoVivo opera en modo local autónomo: "
            "no se transmiten datos ni existe sincronización con servidores externos."
            if connected
            else "Dispositivo fuera de línea. La biblioteca y las consultas funcionan "
            "con normalidad utilizando la base de datos SQLite interna."
        )

        return {
            "is_connected": connected,
            "status_label": status_label,
            "is_simulated": self._simulated_offline,
            "platform": platform,
            "sync_note": sync_note,
            "offline_notice": OFFLINE_NOTICE
        }

