import streamlit as st
import requests
import json
from PIL import Image
from io import BytesIO
import base64

st.set_page_config(page_title="BEENDER", page_icon="🎥", layout="wide")

st.markdown("<h1 style='text-align: center;'>BEENDER</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic; margin: 0;'>been there?</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em; font-style: bold; margin: 0;'>self stalker - find yourself in a video</b></p>", unsafe_allow_html=True)

# -----------------------------
# Init session state
# -----------------------------
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "matches" not in st.session_state:
    st.session_state.matches = []
if "logs" not in st.session_state:
    st.session_state.logs = []
if "settings_expanded" not in st.session_state:
    st.session_state.settings_expanded = True
if "results_expanded" not in st.session_state:
    st.session_state.results_expanded = False

# -----------------------------
# Settings accordion
# -----------------------------
with st.expander("⚙️ Settings", expanded=st.session_state.settings_expanded):
    backend_url = st.text_input(
        "🔗 Backend URL",
        value="http://localhost:8000/process",
        help="Enter the full URL of the backend API endpoint"
    )

    st.write("Upload face images and a YouTube link.")

    face_files = st.file_uploader(
        "📸 Face images", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True,
        help="Upload up to 5 reference face images"
    )
    if face_files and len(face_files) > 5:
        st.warning("⚠️ Maximum of 5 face images allowed.")
        face_files = face_files[:5]

    youtube_url = st.text_input("🎬 YouTube link", placeholder="https://youtube.com/watch?v=...")

    col1, col2 = st.columns(2)
    with col1:
        skip = st.slider("⏭️ Frame skip", min_value=1, max_value=200, value=30)
    with col2:
        tolerance = st.slider("🎯 Match tolerance", min_value=0.1, max_value=1.0, value=0.5)

    if st.button("🚀 RUN BEENDER", type="primary"):
        if not face_files:
            st.error("⚠️ Please upload at least one face image.")
        elif not youtube_url:
            st.error("⚠️ Please paste a YouTube link.")
        else:
            st.session_state.submitted = True
            st.session_state.matches = []
            st.session_state.logs = []
            st.session_state.settings_expanded = False
            st.session_state.results_expanded = True
            st.rerun()


# -----------------------------
# Results accordion
# -----------------------------
with st.expander("📊 Results", expanded=st.session_state.results_expanded):
    logs_placeholder = st.empty()
    matches_placeholder = st.container()

    if st.session_state.logs:
        logs_placeholder.text_area("Logs", "\n".join(st.session_state.logs), height=200)
    if st.session_state.matches:
        with matches_placeholder:
            cols = st.columns(3)  # mostrar em grelha de 3 colunas
            for i, (img, sec) in enumerate(st.session_state.matches):
                with cols[i % 3]:
                    st.image(img, caption=f"t = {sec}s", use_container_width=True)

# -----------------------------
# Run process
# -----------------------------
if st.session_state.submitted:
    # não desligamos submitted até terminar
    files = [('faces', (f.name, f.read(), f.type)) for f in face_files]
    data = {
        'youtube_url': youtube_url,
        'skip': skip,
        'tolerance': tolerance
    }

    try:
        with requests.post(backend_url, files=files, data=data, stream=True) as response:
            if response.status_code != 200:
                st.error(f"❌ Backend returned error {response.status_code}: {response.text}")
            else:
                st.session_state.logs.append("✅ Processing started...")
                for line in response.iter_lines():
                    if line:
                        decoded = line.decode('utf-8')
                        if decoded.startswith("data:"):
                            payload = decoded.replace("data:", "").strip()
                            if payload == "DONE":
                                st.session_state.logs.append("🎉 Processing completed!")
                                break
                            else:
                                frame_data = json.loads(payload)

                                frame_bytes = BytesIO(base64.b64decode(frame_data['frame_base64']))
                                img = Image.open(frame_bytes)

                                second = frame_data['frame_index'] // skip

                                st.session_state.matches.append((img, second))
                                st.session_state.logs.append(f"✅ Match at {second}s (frame {frame_data['frame_index']})")

                                # atualizar interface em tempo real
                                logs_placeholder.text_area("Logs", "\n".join(st.session_state.logs), height=200)
                                with matches_placeholder:
                                    cols = st.columns(3)
                                    for i, (m_img, sec) in enumerate(st.session_state.matches):
                                        with cols[i % 3]:
                                            st.image(m_img, caption=f"t = {sec}s", use_container_width=True)

    except Exception as e:
        st.error(f"❌ Failed to process stream: {e}")
    finally:
        st.session_state.submitted = False
