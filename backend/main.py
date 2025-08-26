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
import base64
from PIL import Image
import io
from tqdm import tqdm
import math

app = FastAPI()

OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(exist_ok=True)

def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)



def seconds_to_timecode(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:06.3f}"  # hh:mm:ss.mmm


async def stream_frames(youtube_url: str, skip: int, tolerance: float, faces: List[Path]):
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
        yield f"data: {json.dumps({'error': 'no_known_faces'})}\n\n"
        return

    direct_url = subprocess.run(
        ["yt-dlp", "-g", "-f", "best[ext=mp4]", youtube_url],
        capture_output=True,
        text=True
    ).stdout.strip()

    ffmpeg_cmd = [
        "ffmpeg",
        "-i", direct_url,
        "-f", "image2pipe",
        "-pix_fmt", "rgb24",
        "-vcodec", "rawvideo",
        "-"
    ]

    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**8)

    frame_index = 0
    width, height, fps = None, None, None
    matches = []  # store matches with frame index + timecode

    pbar = None

    while True:
        if width is None or height is None:

            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height,nb_frames,r_frame_rate",
                "-of", "json", direct_url],
                capture_output=True, text=True
            )

            info = json.loads(probe.stdout or "{}")

            if "streams" not in info or not info["streams"]:
                log(f"❌ ffprobe failed for URL: {direct_url}")
                yield f"data: {json.dumps({'error': 'ffprobe_failed'})}\n\n"
                return

            width = info["streams"][0]["width"]
            height = info["streams"][0]["height"]


            fps_str = info["streams"][0]["r_frame_rate"]  # ex: "25/1"
            num, den = map(int, fps_str.split("/"))
            fps = num / den

            total_frames = int(info["streams"][0].get("nb_frames", 0)) or None
            pbar = tqdm(total=total_frames, desc="Processing frames", unit="frame")

        raw_frame = process.stdout.read(width * height * 3)
        if len(raw_frame) < width * height * 3:
            break

        frame_index += 1
        if pbar:
            pbar.update(1)

        if frame_index % skip != 0:
            continue

        img = np.frombuffer(raw_frame, dtype=np.uint8).reshape((height, width, 3))
        encs = face_recognition.face_encodings(img)

        match_found = False
        for enc in encs:
            results = face_recognition.compare_faces(known_encodings, enc, tolerance=tolerance)
            if any(results):
                match_found = True
                break

        if match_found:
            time_seconds = frame_index / fps
            timecode = seconds_to_timecode(time_seconds)

            print(f"✅ Match found on frame {frame_index} ({timecode})")
            matches.append({"frame_index": frame_index, "timecode": timecode})

            buf = io.BytesIO()
            im = Image.fromarray(img)
            im.save(buf, format="JPEG")
            frame_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

            data = {
                "frame_index": frame_index,
                "timecode": timecode,
                "frame_base64": frame_base64
            }
            yield f"data: {json.dumps(data)}\n\n"

        await asyncio.sleep(0.01)

    if pbar:
        pbar.close()

    log("Video processing done")
    print(f"\nTotal matches: {len(matches)}")
    if matches:
        print("Matches:")
        for m in matches:
            print(f"- Frame {m['frame_index']} @ {m['timecode']}")

    yield f"data: {json.dumps({'message': 'processing_done', 'matches': matches})}\n\n"



@app.post("/process")
async def process_video(
    youtube_url: str = Form(...),
    skip: int = Form(25),  # default 1 frame/sec
    tolerance: float = Form(0.5),
    faces: List[UploadFile] = File(None)
):
    # save faces locally
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
