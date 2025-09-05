import cv2
import face_recognition
import os
import sys
import glob
import argparse
import unicodedata
from tqdm import tqdm
import numpy as np


# ========================
# Utils
# ========================
def normalize_name(name: str) -> str:
    """Normalize a filename (remove spaces, accents, extension)."""
    name = os.path.splitext(os.path.basename(name))[0]
    name = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode()
    name = name.replace(" ", "_")
    return name


def load_reference_faces(face_dir):
    """Load all reference faces into a list of encodings."""
    encodings = []
    names = []

    for file_path in glob.glob(os.path.join(face_dir, "*")):
        img = face_recognition.load_image_file(file_path)
        face_encs = face_recognition.face_encodings(img)

        if face_encs:
            encodings.append(face_encs[0])
            names.append(normalize_name(file_path))
            print(f"[INFO] Loaded reference face: {file_path}")
        else:
            print(f"[WARNING] No face found in {file_path}")

    if not encodings:
        raise ValueError("No reference faces found in face directory.")

    return encodings, names


def process_image(image_path, ref_encodings, ref_names, tolerance, output_dir):
    """Check if reference faces appear in an image."""
    print(f"[INFO] Processing image: {image_path}")
    img = face_recognition.load_image_file(image_path)
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if img.ndim == 3 else img

    face_locations = face_recognition.face_locations(rgb_img)
    face_encodings = face_recognition.face_encodings(rgb_img, face_locations)

    matches = []
    for face_encoding, loc in zip(face_encodings, face_locations):
        results = face_recognition.compare_faces(ref_encodings, face_encoding, tolerance=tolerance)
        for i, match in enumerate(results):
            if match:
                print(f"[MATCH] Found {ref_names[i]} in {image_path}")
                matches.append(ref_names[i])

                # Save cropped face
                top, right, bottom, left = loc
                face_img = rgb_img[top:bottom, left:right]
                out_dir = os.path.join(output_dir, "matches", normalize_name(image_path))
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, f"{ref_names[i]}.jpg")
                cv2.imwrite(out_path, cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR))

    return matches


def process_video(video_path, ref_encodings, ref_names, frame_skip, tolerance, output_dir):
    """Process a video and search for reference faces."""
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0

    print(f"[INFO] Processing video: {video_path}")
    print(f"[INFO] Duration: {duration:.2f}s, {frame_count} frames")

    frame_number = 0
    matches = []

    video_name = normalize_name(video_path)
    frames_dir = os.path.join(output_dir, "frames", video_name)
    os.makedirs(frames_dir, exist_ok=True)

    for _ in tqdm(range(frame_count), desc="Processing frames"):
        ret, frame = cap.read()
        if not ret:
            break

        if frame_number % frame_skip == 0:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for face_encoding, loc in zip(face_encodings, face_locations):
                results = face_recognition.compare_faces(ref_encodings, face_encoding, tolerance=tolerance)
                for i, match in enumerate(results):
                    if match:
                        timestamp = frame_number / fps if fps > 0 else 0
                        print(f"[MATCH] {ref_names[i]} found at {timestamp:.2f}s in {video_path}")
                        matches.append((ref_names[i], timestamp))

                        # Save frame
                        out_path = os.path.join(frames_dir, f"{ref_names[i]}_{int(timestamp)}s.jpg")
                        cv2.imwrite(out_path, frame)

        frame_number += 1

    cap.release()
    return matches


# ========================
# Main
# ========================
def main():
    parser = argparse.ArgumentParser(description="Find faces in images/videos")
    parser.add_argument("--faces", type=str, default="/input/faces",
                        help="Path to reference faces directory")
    parser.add_argument("--footage", type=str, default="/input/footage",
                        help="Path to footage directory")
    parser.add_argument("--skip", type=int, default=30,
                        help="Process 1 frame every N frames for videos")
    parser.add_argument("--tolerance", type=float, default=0.5,
                        help="Face recognition tolerance (lower = stricter)")
    parser.add_argument("--output", type=str, default="output",
                        help="Directory for results")

    args = parser.parse_args()

    # Load reference faces
    ref_encodings, ref_names = load_reference_faces(args.faces_path)

    # Process all files in footage_path
    files = glob.glob(os.path.join(args.footage_path, "*"))
    if not files:
        print("[ERROR] No files found in footage directory.")
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)

    for file_path in files:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".jpg", ".jpeg", ".png", ".bmp"]:
            process_image(file_path, ref_encodings, ref_names, args.tolerance, args.output)
        elif ext in [".mp4", ".avi", ".mov", ".mkv"]:
            process_video(file_path, ref_encodings, ref_names, args.skip, args.tolerance, args.output)
        else:
            print(f"[WARNING] Unsupported file type: {file_path}")


if __name__ == "__main__":
    main()
