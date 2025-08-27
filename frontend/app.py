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
# Title Container
# -----------------------------
with st.container():
    st.markdown("<h1 style='text-align: center;'>BEENDER</h1>", unsafe_allow_html=True)

# -----------------------------
# Arrow-link helper
# -----------------------------
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded" rel="stylesheet" />
        <style>
            p {
            margin: 0;
            }

            .stMainBlockContainer.block-container.st-emotion-cache-zy6yx3.e4man114 {
                padding-bottom: 0 !important;
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

            .st-key-selfie-container {
                padding-right: 16px!important;
            }

            .st-key-popover-container,
            .st-key-settings-container {
                padding-right: 16px!important;
            }

            div:has(> .st-key-smth) {
                height: 45vh !important;
                display: flex;
                flex-direction: column;
            }

            .st-key-smth > [data-testid="stLayoutWrapper"] {
                display: flex !important;           /* make the wrapper a flex container */
                flex-direction: column !important;  /* stack children vertically */
                justify-content: space-between !important; /* distribute children evenly */
                height: 100% !important;            /* fill the parent height */
                min-height: 0;                       /* prevent overflow issues */
            }


            .st-emotion-cache-1weic72.e1gk92lc0 {
                height: auto !important;   /* reset any fixed height */
                min-height: 0 !important;  /* allow it to shrink if needed */
                padding: 0 !important;     /* remove extra spacing */
            }




            .st-key-selfie-container > .stElementContainer:first-of-type p {
                display: none !important;
            }
            
            
            .st-emotion-cache-14503gc {
                display: none !important;
            }

            .st-key-file_uploader [data-testid="stMarkdownContainer"] > p {
                display: none !important;
            }


            .st-key-file_uploader .st-emotion-cache-u8hs99.eamlidg1 > span {
               display: none !important;
            }

            /* hide the "Limit 200MB per file • JPG, JPEG, PNG" text */
            .st-key-file_uploader .st-emotion-cache-b1errp.eamlidg4 {
                display: none !important;
            }
                        
            .stVerticalBlock.st-emotion-cache-10km526.e52wr8w2 {
                gap: 0 !important;
            }

            .stPopover.st-emotion-cache-8atqhb.e1mlolmg0 button {
                text-size-adjust: 80% !important;
                height: 80% !important;
                border: none;

            }
            .stPopover.st-emotion-cache-8atqhb.e1mlolmg0 {
                display: flex;
                
            }

            
            /* Estilo para botão tertiary verde */
            button[kind="tertiary"] {
                background-color: #28a745 !important;
                color: white !important;
                border: 1px solid #28a745 !important;
                font-weight: 600 !important;
            }
            
            button[kind="tertiary"]:hover {
                background-color: #218838 !important;
                color: white !important;
                border: 1px solid #218838 !important;
            }
            
            button[kind="tertiary"]:focus {
                background-color: #218838 !important;
                color: white !important;
                box-shadow: 0 0 0 2px rgba(40, 167, 69, 0.3) !important;
            }

        </style>
    """, unsafe_allow_html=True)

def arrow_link(button1_config: list, button2_config: list):
    """
    Cria dois botões lado a lado usando container horizontal
    button1_config: [label, target_step] para o botão da esquerda
    button2_config: [label, target_step] para o botão da direita
    """
    
    
    # Container horizontal para os dois botões
    flex = st.container(horizontal=True, height="stretch", width="stretch")
    
    # Botão 1 (Back)
    label1, target_step1 = button1_config
    button_text1 = f"← {label1}"
    key1 = f"back-{target_step1}-{st.session_state.step}"
    
    if flex.button(button_text1, key=key1, use_container_width=True):
        st.session_state.step = target_step1
        st.rerun()
    
    # Botão 2 (Next/Run)
    label2, target_step2 = button2_config
    button_text2 = f"{label2} →"
    key2 = f"next-{target_step2}-{st.session_state.step}"
    type = "secondary"
    
    # Aplicar key especial para botão RUN (para CSS)
    if label2 == "RUN":
        key2 = f"run-button-{target_step2}"
        type = "primary"
    
    if flex.button(button_text2, key=key2, use_container_width=True, type=type):
        st.session_state.step = target_step2
        st.rerun()


def run_link(label: str, target_step: int, direction: str = "next"):
    # Usar símbolos Unicode para as setas
    arrow_symbol = "→" if direction == "next" else "←"
    
    # CSS para esconder a borda do formulário, botão vermelho e min-width
    st.markdown(f"""
        <style>
            .stForm {{
                border: none !important;
                background: none !important;
                padding: 0 !important;
            }}
            
            /* Garantir que as colunas não se empilhem em mobile */
            [data-testid="column"] {{
                min-width: 120px !important;
                flex: 0 0 auto !important;
            }}
            
            .st-key-FormSubmitter-run-form-3-RUN-- button {{
                background-color: #ff4444 !important;
                color: white !important;
                border: none !important;
            }}

            .st-key-FormSubmitter-run-form-3-RUN-- button:hover {{
                background-color: #cc3333 !important;
                color: white !important;
            }}
        </style>
        """, unsafe_allow_html=True)
    
    # Usar um form para que o clique seja processado pelo Streamlit
    form_key = f"run-form-{target_step}"
    with st.form(form_key):
        # Incluir o ícone no texto do botão
        if direction == "next":
            button_text = f"{label} {arrow_symbol}"
        else:
            button_text = f"{arrow_symbol} {label}"
        
        submitted = st.form_submit_button(button_text, use_container_width=None, width=120)
            
        if submitted:
            st.session_state.step = target_step
            st.rerun()


def start_link(label: str, target_step: int, direction: str = "next"):
    # Usar símbolos Unicode para as setas
    arrow_symbol = "→" if direction == "next" else "←"
    
    # CSS para esconder a borda do formulário e garantir min-width
    st.markdown("""
    <style>
    .stForm {
        border: none !important;
        background: none !important;
        padding: 0 !important;
    }
    
    .st-emotion-cache-wfksaw {
        flex-direction: column !important;
        align-items: flex-end;
    }

    /* Garantir que as colunas não se empilhem em mobile */
    [data-testid="column"] {
        min-width: 120px !important;
    }
    
    /* Container flexível para alinhamento à direita */
    .start-button-container {
        display: flex !important;
        justify-content: flex-end !important;
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Container com flexbox para alinhar à direita
    st.markdown('<div class="start-button-container">', unsafe_allow_html=True)
    
    # Usar um form para que o clique seja processado pelo Streamlit
    form_key = f"start-form-{target_step}"
    with st.form(form_key, width="stretch"):
        # Incluir o ícone no texto do botão
        if direction == "next":
            button_text = f"{label} {arrow_symbol}"
        else:
            button_text = f"{arrow_symbol} {label}"
        
        submitted = st.form_submit_button(button_text, use_container_width=None, width="stretch")
            
        if submitted:
            st.session_state.step = target_step
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)





# -----------------------------
# Step 0 – Start
# -----------------------------
if st.session_state.step == 0:
    with st.container(key="smth", border=None, vertical_alignment="center"):
        st.markdown("<p style='text-align: center; font-size: 1.8em; font-style: bold; padding-bottom: 1.5em; font-weight: 600;'>a self stalking app</p>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.2em; font-style: italic;'>have you been there? <br> find yourself in a youtube video</p>", unsafe_allow_html=True)

    
    with st.container():
        if st.button("START →", type="tertiary", use_container_width=True, key="start-button-0"):
            st.session_state.step = 1
            st.rerun()


# -----------------------------
# Step 1 – Upload faces
# -----------------------------
elif st.session_state.step == 1:
    # Initialize face_files in session state if not exists
    if "face_files" not in st.session_state:
        st.session_state.face_files = []
    
    # Content Container
    with st.container(key="smth", border=True):
        st.subheader("1. SHOW ME YOUR FACE", divider="gray")
        
        with st.container(key="step1-container", border=None, vertical_alignment="distribute"):
            # File uploader
            uploaded_files = st.file_uploader(
                "📸 Upload your photo",
                type=["jpg","jpeg","png"],
                accept_multiple_files=True,
                key="file_uploader"
            )
            
            # Update face_files with uploaded files
            if uploaded_files:
                # Combine uploaded files with existing camera photos, but limit to 5 total
                total_files = list(uploaded_files) + [f for f in st.session_state.face_files if hasattr(f, '_camera_photo')]
                if len(total_files) > 5:
                    st.warning("⚠️ Maximum of 5 face images allowed.")
                    total_files = total_files[:5]
                st.session_state.face_files = total_files


            with st.container(horizontal_alignment="right", border=None, gap=None, key="selfie-container"):
                # st.markdown("<center style='margin-bottom: 25px; font-weight: bold;' >OR</center>", unsafe_allow_html=True)
                @st.dialog("Take a selfie")
                def take_selfie():
                    enable = st.checkbox("Enable camera")
                    picture = st.camera_input("Take a picture", disabled=not enable)


                        
                    if st.button("Submit", disabled=not picture):
                        if picture:
                            # Create a file-like object for the camera photo
                            picture._camera_photo = True  # Mark as camera photo
                            picture.name = f"camera_selfie_{len([f for f in st.session_state.face_files if hasattr(f, '_camera_photo')])}.jpg"
                            
                            # Add to face_files list
                            current_files = [f for f in st.session_state.face_files if not hasattr(f, '_camera_photo')]  # Keep uploaded files
                            camera_files = [f for f in st.session_state.face_files if hasattr(f, '_camera_photo')]  # Keep existing camera files
                            camera_files.append(picture)
                            
                            # Combine and limit to 5
                            total_files = current_files + camera_files
                            if len(total_files) > 5:
                                st.warning("⚠️ Maximum of 5 face images allowed.")
                                total_files = total_files[:5]
                            
                            st.session_state.face_files = total_files
                            st.rerun()

                # Display current face files count
                current_count = len(st.session_state.face_files) if st.session_state.face_files else 0
                remaining_slots = max(0, 5 - current_count)
                
                if remaining_slots > 0:
                    st.write(f"📷 Take a selfie ({current_count}/5 images)")
                    if st.button("Take a selfie"):
                        take_selfie()
                else:
                    st.info("✅ Maximum number of images reached (5/5)")

            # CHECK IMAGES popover - positioned at bottom right
            # Instead of container, use columns or empty space
            
            if st.session_state.face_files and current_count > 0:
                with st.container(horizontal=True, key="popover-container", width="stretch", horizontal_alignment="right", vertical_alignment="bottom"):
                    with st.popover("👀", use_container_width=None):
                        st.write("Current images:")
                        cols = st.columns(min(len(st.session_state.face_files), 5))
                        for i, file in enumerate(st.session_state.face_files):
                            with cols[i]:
                                try:
                                    image = Image.open(file)
                                    st.image(image, caption=f"{file.name}", use_container_width=True)
                                except Exception as e:
                                    st.error(f"Error displaying {file.name}")
            else:
                st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)


    with st.container(width="stretch"):
        arrow_link(["Back", 0], ["Next", 2])


# -----------------------------
# Step 2 – YouTube URL
# -----------------------------
elif st.session_state.step == 2:
    # Content Container
    with st.container(key="smth", border=True):
        st.subheader("2. VIDEO TO STALK", divider="gray")
        
        with st.container(key="step2-container", border=None):
            youtube_url = st.text_input("🎬 YouTube link", placeholder="https://youtube.com/...")

            # SETTINGS popover
            with st.container(horizontal=True, key="settings-container", height="stretch", width="stretch", horizontal_alignment="right", vertical_alignment="bottom"):
                if st.button("⚙️", use_container_width=None):
                    with st.expander("Advanced settings"):
                        skip = st.slider("🎞️ Frame skip", min_value=1, max_value=200, value=30)
                        tolerance = st.slider("📈 Tolerance", min_value=0.1, max_value=1.0, value=0.5)
                        st.session_state.skip = skip
                        st.session_state.tolerance = tolerance

            if youtube_url:
                st.session_state.youtube_url = youtube_url

    # Navigation Container  
    with st.container():
        arrow_link(["Back", 1], ["RUN", 3])  # RUN substitui NEXT

# -----------------------------
# Step 3 – Processing & Results
# -----------------------------
elif st.session_state.step == 3:
    # Auto-trigger processing when entering step 3
    if not st.session_state.submitted and "youtube_url" in st.session_state:
        st.session_state.submitted = True
        st.rerun()
    
    # Content Container
    with st.container(key="smth", border=True):
        st.subheader("3. PROCESSING & RESULTS", divider="gray")
        
        with st.container(key="step3-container", border=None):
            matches_placeholder = st.container()
            logs_placeholder = st.empty()

            if st.session_state.matches:
                with matches_placeholder:
                    cols = st.columns(3)
                    for i, (img, timecode) in enumerate(st.session_state.matches):
                        with cols[i % 3]:
                            st.image(img, caption=f"t = {timecode}", use_container_width=None, width=100)

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
                                                            st.image(m_img, caption=f"t = {tc}", use_container_width=None, width=100)

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

    # Navigation Container
    with st.container():
        arrow_link(["Back", 2], ["Start Over", 0])
