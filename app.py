import streamlit as st
import requests
from PIL import Image

API_URL = "https://abcd1234.ngrok-free.app/detect"  # replace with yours

st.set_page_config(page_title="Leaf Detection AI", layout="centered")
st.title("🌿 Real-Time Leaf Species Detection")

uploaded_file = st.file_uploader("Upload Leaf Image", type=["jpg", "jpeg", "png"])

if uploaded_file:

    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Leaf", use_column_width=True)

    with st.spinner("Analyzing leaf..."):

        files = {"file": uploaded_file.getvalue()}
        response = requests.post(API_URL, files=files)

        if response.status_code == 200:
            result = response.json()
            st.success("Detection Complete")
            st.subheader("🧠 Model Output")
            st.json(result)
        else:
            st.error("Server Error")
