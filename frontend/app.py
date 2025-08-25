import streamlit as st
import requests

st.set_page_config(page_title="VEENDER", page_icon="🎥", layout="wide")

st.markdown("<h1 style='text-align: center;'>VEENDER</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic; margin: 0;'>been there?</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em; font-style: bold; margin: 0;'>self stalker - find yourself in a video</b></p>", unsafe_allow_html=True)

# Initialize session state
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# -----------------------------
# Backend URL input
# -----------------------------
backend_url = st.text_input(
    "🔗 Backend URL",
    value="http://localhost:8000/process",
    help="Enter the full URL of the backend API endpoint"
)

# -----------------------------
# Input section
# -----------------------------
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

# -----------------------------
# Submit to backend
# -----------------------------
if st.button("🚀 RUN VEENDER", type="primary"):
    if not face_files:
        st.error("⚠️ Please upload at least one face image.")
    elif not youtube_url:
        st.error("⚠️ Please paste a YouTube link.")
    else:
        st.session_state.submitted = True

if st.session_state.submitted:
    with st.spinner("🔄 Sending request to backend..."):
        try:
            files = [('faces', (f.name, f.read(), f.type)) for f in face_files]
            data = {
                'youtube_url': youtube_url,
                'skip': skip,
                'tolerance': tolerance
            }
            response = requests.post(backend_url, files=files, data=data)

            if response.status_code == 200:
                st.success("✅ Request submitted successfully!")
                result = response.json()
                st.json(result)
            else:
                st.error(f"❌ Backend returned error {response.status_code}: {response.text}")

        except Exception as e:
            st.error(f"❌ Failed to send request: {e}")

        finally:
            st.session_state.submitted = False
