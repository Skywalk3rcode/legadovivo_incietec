# Motor de voz de LegadoVivo

Este servicio separado genera respuestas habladas a partir de una grabación de referencia autorizada por el titular. Se mantiene en otro entorno Python para no mezclar las dependencias pesadas de voz con las del backend principal.

## Instalación en Windows

Usa Python 3.12 de 64 bits, igual que el entorno del backend. Desde PowerShell, en la carpeta del repositorio:

```powershell
backend\venv\Scripts\python.exe -m venv voice-engine\.venv
voice-engine\.venv\Scripts\python.exe -m pip install --upgrade pip
voice-engine\.venv\Scripts\python.exe -m pip install -r voice-engine\requirements.txt
```

Luego inicia el motor en otra ventana de PowerShell:

```powershell
cd D:\Documentos\INCIENTEC
.\voice-engine\start.ps1
```

El modelo multilingüe se descarga la primera vez que se solicita una voz y puede tardar; la inferencia funciona con CPU y usa CUDA cuando PyTorch la detecta. La API principal espera el motor en `http://127.0.0.1:5003` (`VOICE_TTS_URL`). Mantén el motor ligado a `127.0.0.1`, no lo publiques directamente en la red.

En la Biblioteca, el titular elige una cápsula con audio y confirma que autoriza su uso como referencia de voz. Las personas beneficiarias vinculadas pueden pedir respuestas habladas desde el chat; las grabaciones originales no se modifican.
