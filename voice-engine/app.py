import io
import os
import subprocess
import tempfile
import threading
import wave
from pathlib import Path

import numpy as np
import torch
from imageio_ffmpeg import get_ffmpeg_exe
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

app = FastAPI(title="LegadoVivo voice engine")
MAX_REFERENCE_BYTES = 25 * 1024 * 1024
MAX_TEXT_CHARACTERS = 3000
_model = None
_model_lock = threading.Lock()


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": _model is not None}


def _synthesize(text: str, language_id: str, reference_audio: bytes, suffix: str) -> bytes:
    global _model
    with _model_lock:
        if _model is None:
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS

            device = "cuda" if torch.cuda.is_available() else "cpu"
            _model = ChatterboxMultilingualTTS.from_pretrained(device=device)

        with tempfile.TemporaryDirectory(prefix="legadovivo-voice-") as temp_dir:
            reference_path = Path(temp_dir) / f"source-reference{suffix}"
            reference_path.write_bytes(reference_audio)
            wav_reference_path = Path(temp_dir) / "normalized-reference.wav"
            startupinfo = None
            creationflags = 0
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            subprocess.run(
                [
                    get_ffmpeg_exe(), "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", str(reference_path), "-vn", "-ac", "1", "-ar", "24000", "-f", "wav",
                    str(wav_reference_path),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=60,
                startupinfo=startupinfo,
                creationflags=creationflags,
            )
            audio = _model.generate(
                text,
                language_id=language_id,
                audio_prompt_path=str(wav_reference_path),
            )
            samples = audio.squeeze().detach().cpu().numpy()
            pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
            output = io.BytesIO()
            with wave.open(output, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(_model.sr)
                wav_file.writeframes(pcm.tobytes())
            return output.getvalue()


@app.post("/synthesize")
async def synthesize(
    text: str = Form(..., min_length=1, max_length=MAX_TEXT_CHARACTERS),
    language_id: str = Form(default="es"),
    reference_audio: UploadFile = File(...),
):
    if language_id != "es":
        raise HTTPException(status_code=400, detail="Este motor está configurado para español.")
    suffix = Path(reference_audio.filename or "reference.wav").suffix.lower()
    if suffix not in {".wav", ".mp3", ".m4a", ".ogg", ".webm", ".aac", ".mp4"}:
        raise HTTPException(status_code=415, detail="Formato de referencia de audio no compatible.")
    data = await reference_audio.read(MAX_REFERENCE_BYTES + 1)
    if not data or len(data) > MAX_REFERENCE_BYTES:
        raise HTTPException(status_code=413, detail="La referencia debe pesar menos de 25 MB.")

    try:
        audio_bytes = await run_in_threadpool(_synthesize, text.strip(), language_id, data, suffix)
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="Falta instalar chatterbox-tts en el entorno del motor de voz.") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="No se pudo interpretar la grabación o generar la voz.") from exc

    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )
