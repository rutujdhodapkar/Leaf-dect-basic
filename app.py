import streamlit as st
import requests
from PIL import Image
import json
from datetime import datetime

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

API_BASE = " https://bec6-103-249-243-47.ngrok-free.app"
DETECT_URL = f"{API_BASE}/detect"

st.set_page_config(
    page_title="Leaf Species Detection AI",
    page_icon="🌿",
    layout="centered"
)

st.title("🌿 Leaf Species Detection System")
st.caption("Powered by your local Qwen3-VL-4B Vision Server")

# ---------------------------------------------------
# SERVER STATUS CHECK
# ---------------------------------------------------

def check_server():
    try:
        r = requests.get(API_BASE, timeout=5)
        return r.status_code == 200
    except:
        return False

server_online = check_server()

if server_online:
    st.success("AI Server Connected ✅")
else:
    st.error("AI Server Offline ❌")
    st.stop()

# ---------------------------------------------------
# FILE UPLOAD
# ---------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload a Leaf Image",
    type=["jpg", "jpeg", "png"]
)

# ---------------------------------------------------
# MAIN DETECTION LOGIC
# ---------------------------------------------------

if uploaded_file:

    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Leaf", use_column_width=True)

    if st.button("Analyze Leaf"):

        with st.spinner("Sending image to Vision Model..."):

            try:
                files = {"file": uploaded_file.getvalue()}
                response = requests.post(DETECT_URL, files=files, timeout=180)

                if response.status_code == 200:

                    result = response.json()

                    st.success("Detection Complete 🚀")

                    # Display structured output
                    st.subheader("🌱 Species Name")
                    st.write(result.get("species_name", "Not detected"))

                    st.subheader("📊 Confidence Level")
                    st.write(result.get("confidence_level", "Unknown"))

                    st.subheader("🍃 Leaf Condition")
                    st.write(result.get("leaf_condition", "Not specified"))

                    # Background metadata
                    metadata = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "server": API_BASE,
                        "raw_response": result
                    }

                    st.subheader("📦 Metadata")
                    st.json(metadata)

                else:
                    st.error(f"Server returned error {response.status_code}")
                    st.write(response.text)

            except Exception as e:
                st.error("Connection Failed")
                st.write(str(e))

