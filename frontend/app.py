import streamlit as st
import requests
import json
from PIL import Image
from io import BytesIO
import base64
import time

st.set_page_config(page_title="BEENDER", page_icon="🎥", layout="wide")

# -----------------------------
# Init session state
# -----------------------------
if "step" not in st.session_state:
    st.session_state.step = 0
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "matches" not in st.session_state:
    st.session_state.matches = []
if "logs" not in st.session_state:
    st.session_state.logs = []
if "show_help" not in st.session_state:
    st.session_state.show_help = False

backend_url = "https://d4447fc0533a.ngrok-free.app"

# -----------------------------
# Title
# -----------------------------
st.markdown("<h1 style='text-align: center;'>BEENDER</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.1em; font-style: italic;'>self stalking app - find yourself in a video</p>", unsafe_allow_html=True)

# -----------------------------
# Arrow-link helper
# -----------------------------
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded" rel="stylesheet" />
        <style>
            p {
            margin: 0;
            }

            .material-symbols-rounded {
            font-variation-settings:
            'FILL' 0,
            'wght' 400,
            'GRAD' 0,
            'opsz' 24;
            font-size: 24px;
            vertical-align: middle;
            color: #e3e3e3;
            }
            .custom-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background-color: #1f1f1f;
            color: #e3e3e3;
            padding: 8px 16px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 500;
            border: none;
            cursor: pointer;
            }
            .custom-btn:hover {
            background-color: #2a2a2a;
            }
        </style>
    """, unsafe_allow_html=True)

def arrow_link(label: str, target_step: int, direction: str = "next", color: str = "default"):
    # Usar símbolos Unicode para as setas
    arrow_symbol = "→" if direction == "next" else "←"
    
    # CSS para esconder a borda do formulário e estilizar botões vermelhos
    st.markdown(f"""
    <style>
    .stForm {{
        border: none !important;
        background: none !important;
        padding: 0 !important;
    }}
    
    /* Estilo para botão vermelho baseado na chave do formulário */
    [data-testid="stForm"] div[data-testid*="arrow-form-{target_step}"] button {{
        background-color: {'#ff4444' if color == 'red' else 'default'} !important;
        color: {'white' if color == 'red' else 'default'} !important;
        border: none !important;
    }}
    [data-testid="stForm"] div[data-testid*="arrow-form-{target_step}"] button:hover {{
        background-color: {'#cc3333' if color == 'red' else 'default'} !important;
        color: {'white' if color == 'red' else 'default'} !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Usar um form para que o clique seja processado pelo Streamlit
    form_key = f"arrow-form-{target_step}"
    with st.form(form_key):
        # Incluir o ícone no texto do botão
        if direction == "next":
            button_text = f"{label} {arrow_symbol}"
        else:
            button_text = f"{arrow_symbol} {label}"
        
        # Usar sempre o mesmo tipo de botão (sem containers extras)
        submitted = st.form_submit_button(button_text, use_container_width=True)
            
        if submitted:
            st.session_state.step = target_step
            st.rerun()





# -----------------------------
# Step 0 – Start
# -----------------------------
if st.session_state.step == 0:
    st.subheader("Step 0 – Start")
    st.markdown("Click START to begin face detection in your video.")
    arrow_link("START", target_step=1, direction="next")


# -----------------------------
# Step 1 – Upload faces
# -----------------------------
elif st.session_state.step == 1:
    st.subheader("Step 1 – Upload your face images")
    face_files = st.file_uploader(
        "📸 Upload up to 5 face images",
        type=["jpg","jpeg","png"],
        accept_multiple_files=True
    )
    if face_files and len(face_files) > 5:
        st.warning("⚠️ Maximum of 5 face images allowed.")
        face_files = face_files[:5]
    
    col1, col2 = st.columns(2)
    with col1:
        arrow_link("Back", target_step=0, direction="back")
    with col2:
        arrow_link("Next", target_step=2, direction="next")

    if face_files:
        st.session_state.face_files = face_files

# -----------------------------
# Step 2 – YouTube URL + SETTINGS
# -----------------------------
elif st.session_state.step == 2:
    st.subheader("Step 2 – Provide the YouTube video")
    youtube_url = st.text_input("🎬 YouTube link", placeholder="https://youtube.com/...")

    # SETTINGS popover
    if st.button("⚙️ SETTINGS"):
        with st.expander("Advanced settings"):
            skip = st.slider("🎞️ Frame skip", min_value=1, max_value=200, value=30)
            tolerance = st.slider("📈 Tolerance", min_value=0.1, max_value=1.0, value=0.5)
            st.session_state.skip = skip
            st.session_state.tolerance = tolerance

    col1, col2 = st.columns(2)
    with col1:
        arrow_link("Back", target_step=1, direction="back")
    with col2:
        arrow_link("RUN", target_step=3, direction="next", color="red")

    if youtube_url:
        st.session_state.youtube_url = youtube_url

# -----------------------------
# Step 3 – Processing & Results
# -----------------------------
elif st.session_state.step == 3:
    st.subheader("Step 3 – Processing your video...")
    matches_placeholder = st.container()
    logs_placeholder = st.empty()

    if st.session_state.matches:
        with matches_placeholder:
            cols = st.columns(3)
            for i, (img, timecode) in enumerate(st.session_state.matches):
                with cols[i % 3]:
                    st.image(img, caption=f"t = {timecode}", use_container_width=True)

    if st.session_state.logs:
        logs_placeholder.text_area("Logs", "\n".join(st.session_state.logs), height=200)

    if st.session_state.submitted:
        files = [('faces', (f.name, f.read(), f.type)) for f in st.session_state.face_files]
        data = {
            'youtube_url': st.session_state.youtube_url,
            'skip': st.session_state.skip,
            'tolerance': st.session_state.tolerance
        }
        if not backend_url.endswith("/process"):
            backend_url = backend_url.rstrip("/") + "/process"

        max_retries = 3
        attempt = 0
        success = False

        while attempt < max_retries and not success:
            attempt += 1
            try:
                with requests.post(backend_url, files=files, data=data, stream=True, timeout=120) as response:
                    if response.status_code != 200:
                        st.error(f"❌ Backend returned error {response.status_code}: {response.text}")
                    else:
                        st.session_state.logs.append(f"✅ Processing started... (attempt {attempt})")
                        for line in response.iter_lines():
                            if line:
                                decoded = line.decode('utf-8')
                                if decoded.startswith("data:"):
                                    payload = decoded.replace("data:", "").strip()
                                    if payload == "DONE":
                                        st.session_state.logs.append("🎉 Processing completed!")
                                        success = True
                                        break
                                    else:
                                        frame_data = json.loads(payload)
                                        frame_bytes = BytesIO(base64.b64decode(frame_data['frame_base64']))
                                        img = Image.open(frame_bytes)
                                        timecode = frame_data['timecode']

                                        st.session_state.matches.append((img, timecode))
                                        st.session_state.logs.append(
                                            f"✅ Match at {timecode} (frame {frame_data['frame_index']})"
                                        )

                                        with matches_placeholder:
                                            cols = st.columns(3)
                                            for i, (m_img, tc) in enumerate(st.session_state.matches):
                                                with cols[i % 3]:
                                                    st.image(m_img, caption=f"t = {tc}", use_container_width=True)

                                        logs_placeholder.text_area("Logs", "\n".join(st.session_state.logs), height=200)

            except Exception as e:
                st.session_state.logs.append(f"⚠️ Attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    st.session_state.logs.append("🔄 Retrying in 3 seconds...")
                    time.sleep(3)
                else:
                    st.error(f"❌ Failed after {max_retries} attempts: {e}")
            finally:
                if success or attempt == max_retries:
                    st.session_state.submitted = False
