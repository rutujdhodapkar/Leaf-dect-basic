import streamlit as st
import requests
import base64
from PIL import Image
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
import folium
import json

OPENROUTER_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

VISION_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"
REASON_MODEL = "openai/gpt-oss-120b:free"

st.set_page_config(layout="wide")
st.title("🌾 AI Agricultural Intelligence System")

# -------------------------------
# LOCATION INPUT
# -------------------------------

st.header("📍 Farmer Location")

location_mode = st.radio("Select Location Mode", ["Text Input", "Map"])

lat, lon = None, None

if location_mode == "Text Input":
    location_text = st.text_input("Enter village / city name")
    if location_text:
        geolocator = Nominatim(user_agent="agri_app")
        loc = geolocator.geocode(location_text)
        if loc:
            lat, lon = loc.latitude, loc.longitude
            st.success(f"Location found: {lat}, {lon}")

else:
    m = folium.Map(location=[20, 78], zoom_start=4)
    map_data = st_folium(m, height=400)
    if map_data["last_clicked"]:
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.success(f"Selected: {lat}, {lon}")

# -------------------------------
# WEATHER DATA
# -------------------------------

def get_weather(lat, lon):
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date=2023-01-01&end_date=2023-12-31&daily=temperature_2m_mean,precipitation_sum&timezone=auto"
    r = requests.get(url)
    return r.json()

# -------------------------------
# SOIL DATA
# -------------------------------

def get_soil(lat, lon):
    url = f"https://rest.isric.org/soilgrids/v2.0/properties/query?lat={lat}&lon={lon}&property=phh2o&property=soc&depth=0-5cm&value=mean"
    r = requests.get(url)
    return r.json()

# -------------------------------
# OPENROUTER CALL
# -------------------------------

def call_model(model, prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    r = requests.post(OPENROUTER_URL, headers=headers, json=payload)
    return r.json()["choices"][0]["message"]["content"]

# -------------------------------
# LEAF VISION
# -------------------------------

st.header("🌿 Leaf Detection")

uploaded_file = st.file_uploader("Upload Leaf Image", type=["jpg","png","jpeg"])

leaf_result = None

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image)

    buffered = base64.b64encode(uploaded_file.getvalue()).decode()

    payload = {
        "model": VISION_MODEL,
        "messages": [{
            "role":"user",
            "content":[
                {"type":"text","text":"Identify leaf species and disease condition."},
                {"type":"image_url","image_url":{"url":f"data:image/png;base64,{buffered}"}}
            ]
        }]
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.post(OPENROUTER_URL, headers=headers, json=payload)
    leaf_result = r.json()["choices"][0]["message"]["content"]

    st.subheader("Leaf Analysis")
    st.write(leaf_result)

# -------------------------------
# FULL AGRI ANALYSIS
# -------------------------------

if lat and lon and leaf_result:

    weather = get_weather(lat, lon)
    soil = get_soil(lat, lon)

    st.header("🌦 Weather Data")
    st.json(weather)

    st.header("🌱 Soil Data")
    st.json(soil)

    combined_prompt = f"""
    Location: {lat}, {lon}
    Weather Data: {weather}
    Soil Data: {soil}
    Leaf Diagnosis: {leaf_result}

    Provide:
    - Crop recommendation
    - Irrigation strategy
    - Soil treatment
    - Disease solution
    - Long-term 5 year strategy
    """

    final_analysis = call_model(REASON_MODEL, combined_prompt)

    st.header("🧠 Agricultural Recommendation")
    st.write(final_analysis)
