import streamlit as st
import requests
import json
from PIL import Image
from io import BytesIO
import base64
import datetime

st.set_page_config(page_title="BEENDER", page_icon="🎥", layout="wide")

st.markdown(
    """
    <style>
    /* Reduz padding top do main container */
    .stMainBlockContainer.block-container {
        padding-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown("<h1 style='text-align: center; padding-bottom: 0;'>BEENDER</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.1em; font-style: italic; margin: 0; padding-bottom: 10px;'>self stalking app - find yourself in a video</b></p>", unsafe_allow_html=True)

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
if "show_help" not in st.session_state:
    st.session_state.show_help = False

# -----------------------------
# Settings accordion
# -----------------------------
with st.expander("⚙️ Settings", expanded=st.session_state.settings_expanded):
    # Set backend URL as hardcoded value
    backend_url = "https://d4447fc0533a.ngrok-free.app"
    
    # YouTube URL takes full width now
    youtube_url = st.text_input(
        "🎬 YouTube link",
        placeholder="youtube link",
        help="Paste the YouTube video link here"
    )

    face_files = st.file_uploader(
        "📸 Face images", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True,
        help="Upload up to 5 reference face images"
    )
    if face_files and len(face_files) > 5:
        st.warning("⚠️ Maximum of 5 face images allowed.")
        face_files = face_files[:5]

    col3, col4 = st.columns(2)
    with col3:
        skip = st.slider("🎞️ Frames", min_value=1, max_value=200, value=30)
    with col4:
        tolerance = st.slider("📈 Tolerance", min_value=0.1, max_value=1.0, value=0.5)

    # Buttons
    run_clicked = st.button("🚀 RUN BEENDER", type="primary")
    if st.button("❓"):
        st.session_state.show_help = True
        st.rerun()

    # Handle RUN BEENDER button
    if run_clicked:
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

# Help popup dialog
if st.session_state.show_help:
    with st.container():
        st.markdown("---")
        st.markdown("### ❓ Help")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**📧 devritsa@gmail.com**")
            
            st.markdown("**🔗 Backend URL Configuration:**")
            help_backend_url = st.text_input(
                "Backend URL",
                value="https://d4447fc0533a.ngrok-free.app",
                help="Enter the full URL of the backend API endpoint",
                key="help_backend_url"
            )
        with col2:
            if st.button("✖️ Close Help"):
                st.session_state.show_help = False
                st.rerun()
        st.markdown("---")




# -----------------------------
# Results accordion
# -----------------------------
with st.expander("📊 Results", expanded=st.session_state.results_expanded):
    matches_placeholder = st.container()
    logs_placeholder = st.empty()

    # Display matching frames first
    if st.session_state.matches:
        with matches_placeholder:
            cols = st.columns(3)
            for i, (img, sec) in enumerate(st.session_state.matches):
                with cols[i % 3]:
                    time_str = str(datetime.timedelta(seconds=int(sec)))
                    st.image(img, caption=f"t = {time_str}", use_container_width=True)

    # Display logs at the bottom
    if st.session_state.logs:
        logs_placeholder.text_area("Logs", "\n".join(st.session_state.logs), height=200)



# -----------------------------
# Run process
# -----------------------------
if st.session_state.submitted:
    files = [('faces', (f.name, f.read(), f.type)) for f in face_files]
    data = {
        'youtube_url': youtube_url,
        'skip': skip,
        'tolerance': tolerance
    }
    if not backend_url.endswith("/process"):
        backend_url = backend_url.rstrip("/") + "/process"

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

                                # --- Update matches first ---
                                with matches_placeholder:
                                    cols = st.columns(3)
                                    for i, (m_img, sec) in enumerate(st.session_state.matches):
                                        with cols[i % 3]:
                                            time_str = str(datetime.timedelta(seconds=int(sec)))
                                            st.image(m_img, caption=f"t = {time_str}", use_container_width=True)

                                # --- Update logs at the bottom ---
                                logs_placeholder.text_area("Logs", "\n".join(st.session_state.logs), height=200)


    except Exception as e:
        st.error(f"❌ Failed to process stream: {e}")
    finally:
        st.session_state.submitted = False
