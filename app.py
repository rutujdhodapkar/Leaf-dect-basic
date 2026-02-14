import streamlit as st
import requests
import base64
from PIL import Image
from geopy.geocoders import Nominatim
import json

# ---------------- CONFIG ----------------

OPENROUTER_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

VISION_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"
REASON_MODEL = "openai/gpt-oss-120b:free"

st.set_page_config(layout="wide")
st.title("🌾 Smart Farming AI")

# ---------------- MODEL CALL ----------------

def call_model(model, prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [{"role":"user","content":prompt}],
        "temperature":0.3
    }

    try:
        r = requests.post(OPENROUTER_URL, headers=headers, json=payload)
        data = r.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        else:
            return "Model error. Try again."
    except:
        return "Connection error."

# ---------------- LANGUAGE ----------------

language = st.selectbox("Language", ["English","Hindi","Marathi"])

def translate(text, target_lang):
    if target_lang == "English":
        return text
    prompt = f"Translate this into {target_lang}:\n{text}"
    return call_model(REASON_MODEL, prompt)

# ---------------- MODE ----------------

mode = st.radio("Select Option", ["🌿 Detect Leaf Disease", "🌱 Get Farming Recommendation"])

# ================= LEAF MODE =================

if mode == "🌿 Detect Leaf Disease":

    uploaded_file = st.file_uploader("Upload Leaf Image", type=["jpg","png","jpeg"])

    if uploaded_file:

        image = Image.open(uploaded_file)
        st.image(image, width=300)

        if st.button("Analyze"):

            img_b64 = base64.b64encode(uploaded_file.getvalue()).decode()

            vision_prompt = [
                {
                    "role":"user",
                    "content":[
                        {"type":"text","text":"Identify plant leaf species and condition. Give short bullet points."},
                        {"type":"image_url","image_url":{"url":f"data:image/png;base64,{img_b64}"}}
                    ]
                }
            ]

            headers = {
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": VISION_MODEL,
                "messages": vision_prompt
            }

            r = requests.post(OPENROUTER_URL, headers=headers, json=payload)
            data = r.json()

            if "choices" in data:
                result = data["choices"][0]["message"]["content"]
                result = translate(result, language)
                st.markdown(result)
            else:
                st.error("Vision model failed")

# ================= RECOMMENDATION MODE =================

if mode == "🌱 Get Farming Recommendation":

    location_input = st.text_input("Enter village / city / district")

    crop_type = st.selectbox("About", ["Plant Disease","Growing Crop"])

    if location_input:

        geolocator = Nominatim(user_agent="farm_app")
        loc = geolocator.geocode(location_input)

        if loc:

            lat, lon = loc.latitude, loc.longitude

            st.sidebar.header("📍 Location Data")
            st.sidebar.write(f"Latitude: {lat}")
            st.sidebar.write(f"Longitude: {lon}")

            # WEATHER
            weather_url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date=2023-01-01&end_date=2023-12-31&daily=temperature_2m_mean,precipitation_sum&timezone=auto"
            weather = requests.get(weather_url).json()

            # SOIL
            soil_url = f"https://rest.isric.org/soilgrids/v2.0/properties/query?lat={lat}&lon={lon}&property=phh2o&property=soc&depth=0-5cm&value=mean"
            soil = requests.get(soil_url).json()

            st.sidebar.header("🌦 Weather Summary")
            st.sidebar.write("• Avg temp & rainfall data collected")

            st.sidebar.header("🌱 Soil Summary")
            st.sidebar.write("• pH & organic carbon extracted")

            if st.button("Generate Recommendation"):

                base_prompt = f"""
                Location: {location_input}
                Weather data: {weather}
                Soil data: {soil}
                Task: {crop_type}

                Give short bullet point farming advice.
                """

                response = call_model(REASON_MODEL, base_prompt)
                response = translate(response, language)

                st.markdown(response)

        else:
            st.error("Location not found")
