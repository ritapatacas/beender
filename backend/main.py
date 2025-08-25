from fastapi import FastAPI, UploadFile, File, Form
from typing import List
from pathlib import Path
import datetime
import subprocess
import json
import asyncio
import face_recognition
import numpy as np
from fastapi.responses import StreamingResponse
import cv2 
import base64
from PIL import Image
import io

app = FastAPI()

OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(exist_ok=True)

def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

async def stream_frames(youtube_url: str, skip: int, tolerance: float, faces: List[Path]):
    # Carregar imagens de referência
    known_encodings = []
    for face_path in faces:
        img = face_recognition.load_image_file(face_path)
        encs = face_recognition.face_encodings(img)
        if encs:
            known_encodings.append(encs[0])
            log(f"Loaded face encoding from {face_path}")
        else:
            log(f"⚠️ Nenhuma face encontrada em {face_path}")
    log(f"Total de encodings carregados: {len(known_encodings)}")

    if not known_encodings:
        log("⚠️ Nenhum encoding conhecido carregado, abortando.")
        yield f"data: {json.dumps({'error': 'no_known_faces'})}\n\n"
        return

    # Obter URL direto do vídeo
    log(f"Getting direct video URL for: {youtube_url}")
    direct_url = subprocess.run(
        ["yt-dlp", "-g", "-f", "best[ext=mp4]", youtube_url],
        capture_output=True,
        text=True
    ).stdout.strip()

    # Mantém resolução original (sem scale)
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", direct_url,
        "-f", "image2pipe",
        "-pix_fmt", "rgb24",
        "-vcodec", "rawvideo",
        "-"
    ]

    log("Starting ffmpeg pipe...")
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**8)

    frame_index = 0
    frame_bytes_accum = b""
    width, height = None, None

    while True:
        # ⚠️ Primeiro precisamos saber o tamanho original do vídeo.
        if width is None or height is None:
            # Extrair info de vídeo com ffprobe
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=width,height", "-of", "json", direct_url],
                capture_output=True, text=True
            )
            info = json.loads(probe.stdout)
            width = info["streams"][0]["width"]
            height = info["streams"][0]["height"]
            log(f"Video resolution detected: {width}x{height}")

        raw_frame = process.stdout.read(width * height * 3)
        if len(raw_frame) < width * height * 3:
            break  # fim do vídeo

        frame_index += 1

        if frame_index % skip != 0:
            continue  # salta frames conforme parâmetro skip

        img = np.frombuffer(raw_frame, dtype=np.uint8).reshape((height, width, 3))
        encs = face_recognition.face_encodings(img)

        if not encs:
            log(f"No faces detected on frame {frame_index}")
        else:
            log(f"Detected {len(encs)} face(s) on frame {frame_index}")

        match_found = False
        for enc in encs:
            results = face_recognition.compare_faces(known_encodings, enc, tolerance=tolerance)
            if any(results):
                match_found = True
                break

        if match_found:
            log(f"✅ Match found on frame {frame_index}")

            # Converter para JPEG em memória
            buf = io.BytesIO()
            im = Image.fromarray(img)
            im.save(buf, format="JPEG")
            frame_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

            data = {
                "frame_index": frame_index,
                "frame_base64": frame_base64
            }
            yield f"data: {json.dumps(data)}\n\n"

        if frame_index % 10 == 0:
            log(f"Processed {frame_index} frames...")

        await asyncio.sleep(0.01)

    log("Video processing done")
    yield f"data: {json.dumps({'message': 'processing_done'})}\n\n"

@app.post("/process")
async def process_video(
    youtube_url: str = Form(...),
    skip: int = Form(25),  # por default processa 1 frame/seg (≈25fps)
    tolerance: float = Form(0.5),
    faces: List[UploadFile] = File(None)
):
    # Salvar faces localmente
    face_paths = []
    if faces:
        face_dir = OUTPUT_DIR / "faces"
        face_dir.mkdir(exist_ok=True)
        for face in faces:
            path = face_dir / face.filename
            with open(path, "wb") as f:
                f.write(await face.read())
            face_paths.append(path)

    return StreamingResponse(
        stream_frames(youtube_url, skip, tolerance, face_paths),
        media_type="text/event-stream"
    )
