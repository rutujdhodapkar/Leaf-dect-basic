import streamlit as st
import requests
import base64
from PIL import Image
import io
import pandas as pd

# ================= CONFIG ================= #

OPENROUTER_API_KEY = "YOUR_OPENROUTER_KEY"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

VISION_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"
REASONING_MODEL = "deepseek/deepseek-r1-0528:free"

# ================= CORE FUNCTIONS ================= #

def call_openrouter(messages, model):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages
    }

    r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=300)
    response = r.json()

    if "choices" in response:
        return response["choices"][0]["message"]["content"]

    if "error" in response:
        return f"Model Error: {response['error']}"

    return str(response)


def encode_image(uploaded_file):
    image = Image.open(uploaded_file)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode()


def detect_crop_and_disease(image_base64):
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": """
                Identify:
                1. Crop name
                2. Disease name
                3. Short description (2 lines)

                Respond in this format:
                Crop:
                Disease:
                Description:
                """},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
        }
    ]
    return call_openrouter(messages, VISION_MODEL)


def reasoning_task(system, user):
    return call_openrouter([
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ], REASONING_MODEL)


# ================= STREAMLIT UI ================= #

st.set_page_config(layout="wide")
st.title("🌾 Agricultural Intelligence System")

location = st.text_input("Farm Location")
uploaded_image = st.file_uploader("Upload Leaf Image", type=["jpg", "jpeg", "png"])

if st.button("Analyze Crop"):

    if not uploaded_image:
        st.error("Upload an image first.")
        st.stop()

    image_base64 = encode_image(uploaded_image)

    # -------- Vision Detection --------
    result = detect_crop_and_disease(image_base64)

    lines = result.split("\n")
    crop = ""
    disease = ""
    description = ""

    for line in lines:
        if "Crop:" in line:
            crop = line.replace("Crop:", "").strip()
        if "Disease:" in line:
            disease = line.replace("Disease:", "").strip()
        if "Description:" in line:
            description = line.replace("Description:", "").strip()

    # -------- Display Top Section --------
    st.markdown(f"# {crop}")
    st.markdown(f"## {disease}")

    st.markdown("### Description")
    st.write(description)

    # -------- Weather Table --------
    weather_data = reasoning_task(
        "You are an agricultural meteorologist.",
        f"""
        Provide 7-day agricultural weather forecast for {location}
        Return strictly in CSV format:
        Day,Temp(C),Humidity(%),Rainfall(mm),Wind(km/h)
        """
    )

    try:
        from io import StringIO
        df = pd.read_csv(StringIO(weather_data))
        st.markdown("### 7-Day Weather Forecast")
        st.table(df)
    except:
        st.write(weather_data)

    # -------- Disease Analysis --------
    disease_analysis = reasoning_task(
        "You are a plant pathologist.",
        f"""
        Crop: {crop}
        Disease: {disease}

        Provide:
        - Cause
        - Symptoms
        - Spread Mechanism
        - Risk Level (Low/Medium/High)
        """
    )

    st.markdown("### Disease Analysis")
    st.write(disease_analysis)

    # -------- Treatment Plan --------
    treatment = reasoning_task(
        "You are an agricultural treatment planner.",
        f"""
        Crop: {crop}
        Disease: {disease}

        Provide:
        - Fertilizer schedule
        - Irrigation plan
        - Preventive measures
        - Estimated recovery time
        """
    )

    st.markdown("### Treatment Plan")
    st.write(treatment)

    st.success("Analysis Complete.")
