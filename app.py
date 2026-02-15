import streamlit as st
import requests
import base64
from PIL import Image
import io

# ================= CONFIG ================= #

OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

VISION_MODEL = "mistralai/mistral-small-3.1-24b-instruct:free"
FAST_MODEL = "mistralai/mistral-small-3.1-24b-instruct:free"
HEAVY_MODEL = "mistralai/mistral-small-3.1-24b-instruct:free"

# ================= UTILITIES ================= #

def safe_extract_content(response_json):
    if "choices" in response_json:
        return response_json["choices"][0]["message"]["content"]

    if "error" in response_json:
        return f"Model Error: {response_json['error']}"

    return f"Unknown response format: {response_json}"


def call_openrouter(messages, model):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": messages
    }

    try:
        r = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=300)
        return safe_extract_content(r.json())
    except Exception as e:
        return f"API Error: {e}"


def encode_image(uploaded_file):
    image = Image.open(uploaded_file)
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()


def call_vision_model(image_base64, prompt):
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
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


# ================= STREAMLIT UI ================= #

st.set_page_config(layout="wide")
st.title("🌾 Vision-Based Agricultural Intelligence System")

location = st.text_input("Farm Location")
uploaded_image = st.file_uploader("Upload Plant Image", type=["jpg", "jpeg", "png"])
include_pests = st.checkbox("Include Pest Analysis")

if st.button("Run Full Vision Pipeline"):

    if not uploaded_image:
        st.error("Please upload an image.")
        st.stop()

    st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
    image_base64 = encode_image(uploaded_image)

    # 1️⃣ Plant & Disease Detection
    st.subheader("🪴 Plant & Disease Detection")
    disease = call_vision_model(
        image_base64,
        "Identify plant type and any disease. Be specific and structured."
    )
    st.write(disease)

    # 2️⃣ Weather Analysis
    st.subheader("🌦 Weather Analysis (1 Year)")
    weather = call_openrouter([
        {"role": "system", "content": "You are an agricultural weather expert."},
        {"role": "user", "content": f"Provide 1 year agricultural weather analysis for {location}"}
    ], FAST_MODEL)
    st.write(weather)

    # 3️⃣ Soil Report
    st.subheader("🌱 Soil & Water Report")
    soil = call_openrouter([
        {"role": "system", "content": "You are a soil chemistry expert."},
        {"role": "user", "content": f"Provide soil chemistry and groundwater report for {location}"}
    ], FAST_MODEL)
    st.write(soil)

    # 4️⃣ Environmental Disease Explanation
    st.subheader("🧬 Environmental Disease Explanation")
    explanation = call_openrouter([
        {"role": "system", "content": "You are a plant pathology scientist."},
        {"role": "user", "content": f"""
        Disease: {disease}
        Weather: {weather}
        Soil: {soil}

        Explain biological cause and environmental influence.
        """}
    ], HEAVY_MODEL)
    st.write(explanation)

    # 5️⃣ Full Scientific Report
    st.subheader("📄 Full Scientific Crop Report")
    report = call_openrouter([
        {"role": "system", "content": "You are a scientific crop researcher."},
        {"role": "user", "content": f"Generate full scientific agricultural pathology report for: {disease}"}
    ], HEAVY_MODEL)
    st.write(report)

    # 6️⃣ Treatment Plan
    st.subheader("💧 Fertilizer & Irrigation Plan")
    plan = call_openrouter([
        {"role": "system", "content": "You are an agricultural planner."},
        {"role": "user", "content": f"""
        Based on this disease report:
        {report}

        Generate:
        - Fertilizer schedule
        - Water quantity per week
        - Monthly timeline
        - Preventive plan
        """}
    ], HEAVY_MODEL)
    st.write(plan)

    # 7️⃣ Pest Analysis
    if include_pests:
        st.subheader("🐛 Pest Risk Analysis")
        pest = call_openrouter([
            {"role": "system", "content": "You are an agricultural entomologist."},
            {"role": "user", "content": f"Analyze pest risks for this crop condition: {disease}"}
        ], FAST_MODEL)
        st.write(pest)

    # 8️⃣ Fertilizer Price Search
    st.subheader("💰 Fertilizer Price Search")
    prices = call_openrouter([
        {"role": "system", "content": "You are an agricultural supply analyst."},
        {"role": "user", "content": f"Search fertilizer prices near {location} based on this plan: {plan}"}
    ], FAST_MODEL)
    st.write(prices)

    # 9️⃣ Delivery Planning
    st.subheader("🚚 Delivery Planning & Cost")
    delivery = call_openrouter([
        {"role": "system", "content": "You are a logistics planner."},
        {"role": "user", "content": f"Plan delivery logistics and total cost to {location} based on: {prices}"}
    ], FAST_MODEL)
    st.write(delivery)

    # 🔟 Doctor Search
    st.subheader("👨‍⚕️ Agricultural Doctors Nearby")
    doctors = call_openrouter([
        {"role": "system", "content": "You are an agricultural consultant directory system."},
        {"role": "user", "content": f"Find agricultural crop doctors near {location}. Include name, contact, and education."}
    ], FAST_MODEL)
    st.write(doctors)

    st.success("Full Vision-Based Agricultural Intelligence Completed.")
