import streamlit as st
import requests
from PIL import Image

API_URL = "https://xxxx.ngrok-free.app/detect"  # <-- Replace

st.set_page_config(page_title="AI Leaf Detection", layout="centered")

st.title("🌿 Real-Time Leaf Species Detection")
st.markdown("Powered by your local Qwen Vision Server")

uploaded_file = st.file_uploader(
    "Upload Leaf Image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:

    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Leaf", use_column_width=True)

    if st.button("Analyze Leaf"):

        with st.spinner("Analyzing with Vision Model..."):

            try:
                files = {"file": uploaded_file.getvalue()}
                response = requests.post(API_URL, files=files, timeout=120)

                if response.status_code == 200:

                    result = response.json()

                    st.success("Detection Complete ✅")

                    st.subheader("🌱 Species Name")
                    st.write(result.get("species_name", "N/A"))

                    st.subheader("📊 Confidence Level")
                    st.write(result.get("confidence_level", "N/A"))

                    st.subheader("🍃 Leaf Condition")
                    st.write(result.get("leaf_condition", "N/A"))

                else:
                    st.error(f"Server Error: {response.status_code}")
                    st.write(response.text)

            except Exception as e:
                st.error("Connection Failed")
                st.write(str(e))
