import streamlit as st
import requests
import base64
from PIL import Image
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
import folium
import json
from datetime import datetime

# -----------------------------------
# CONFIG
# -----------------------------------

OPENROUTER_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

VISION_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"
REASON_MODEL = "openai/gpt-oss-120b:free"

st.set_page_config(layout="wide")
st.title("🌾 AI Agricultural Intelligence System")

# -----------------------------------
# SAFE OPENROUTER CALL
# -----------------------------------

def call_openrouter(model, messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.3
    }

    try:
        r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
        data = r.json()

        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        else:
            st.error("OpenRouter returned error")
            st.json(data)
            return None

    except Exception as e:
        st.error("OpenRouter request failed")
        st.write(str(e))
        return None

# -----------------------------------
# LOCATION INPUT
# -----------------------------------

st.header("📍 Farmer Location")

location_mode = st.radio("Select Location Mode", ["Text Input", "Map"])

lat, lon = None, None

if location_mode == "Text Input":
    location_text = st.text_input("Enter city / village name")
    if location_text:
        geolocator = Nominatim(user_agent="agri_app")
        loc = geolocator.geocode(location_text)
        if loc:
            lat, lon = loc.latitude, loc.longitude
            st.success(f"Location: {lat}, {lon}")
        else:
            st.error("Location not found")

else:
    m = folium.Map(location=[20, 78], zoom_start=4)
    map_data = st_folium(m, height=400)

    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.success(f"Selected: {lat}, {lon}")

# -----------------------------------
# WEATHER API (1 Year Historical)
# -----------------------------------

def get_weather(lat, lon):
    try:
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date=2023-01-01&end_date=2023-12-31&daily=temperature_2m_mean,precipitation_sum&timezone=auto"
        r = requests.get(url, timeout=20)
        return r.json()
    except:
        return {"error": "Weather API failed"}

# -----------------------------------
# SOIL API
# -----------------------------------

def get_soil(lat, lon):
    try:
        url = f"https://rest.isric.org/soilgrids/v2.0/properties/query?lat={lat}&lon={lon}&property=phh2o&property=soc&depth=0-5cm&value=mean"
        r = requests.get(url, timeout=20)
        return r.json()
    except:
        return {"error": "Soil API failed"}

# -----------------------------------
# LEAF VISION
# -----------------------------------

st.header("🌿 Leaf Detection")

uploaded_file = st.file_uploader("Upload Leaf Image", type=["jpg","jpeg","png"])

leaf_result = None

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image)

    if st.button("Analyze Leaf"):

        with st.spinner("Analyzing leaf with Vision Model..."):

            buffered = base64.b64encode(uploaded_file.getvalue()).decode()

            messages = [{
                "role": "user",
                "content": [
                    {"type":"text","text":"Identify the leaf species and disease condition."},
                    {"type":"image_url","image_url":{"url":f"data:image/png;base64,{buffered}"}}
                ]
            }]

            leaf_result = call_openrouter(VISION_MODEL, messages)

            if leaf_result:
                st.subheader("Leaf Analysis")
                st.write(leaf_result)

# -----------------------------------
# FULL AGRI ANALYSIS
# -----------------------------------

if lat and lon and leaf_result:

    st.header("🌦 Weather Data")
    weather = get_weather(lat, lon)
    st.json(weather)

    st.header("🌱 Soil Data")
    soil = get_soil(lat, lon)
    st.json(soil)

    st.header("🧠 Agricultural Recommendation")

    combined_prompt = f"""
    Location: {lat}, {lon}
    Weather Data: {json.dumps(weather)}
    Soil Data: {json.dumps(soil)}
    Leaf Diagnosis: {leaf_result}

    Provide:
    - Crop recommendation
    - Irrigation strategy
    - Soil treatment plan
    - Disease solution
    - 5 year sustainability strategy
    """

    final_analysis = call_openrouter(
        REASON_MODEL,
        [{"role":"user","content":combined_prompt}]
    )

    if final_analysis:
        st.write(final_analysis)

st.caption("⚠️ Free models may rate limit or fail occasionally.")
