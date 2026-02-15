import streamlit as st
import requests
import base64
from PIL import Image
import io

# ================= CONFIG ================= #

OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

VISION_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"
REASONING_MODEL = "deepseek/deepseek-r1-0528:free"

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


def call_reasoning_model(system_prompt, user_prompt):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    return call_openrouter(messages, REASONING_MODEL)


# ================= STREAMLIT UI ================= #

st.set_page_config(layout="wide")
st.title("🌾 Advanced Vision-Based Agricultural Intelligence System")

location = st.text_input("Farm Location")
uploaded_image = st.file_uploader("Upload Plant Image", type=["jpg", "jpeg", "png"])
include_pests = st.checkbox("Include Pest Analysis")

if st.button("Run Full Vision Pipeline"):

    if not uploaded_image:
        st.error("Please upload an image.")
        st.stop()

    st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
    image_base64 = encode_image(uploaded_image)

    # 1️⃣ Vision Detection
    st.subheader("🪴 Plant & Disease Detection (Nemotron VL)")
    disease = call_vision_model(
        image_base64,
        "Identify plant species and detect any disease. Provide structured output."
    )
    st.write(disease)

    # 2️⃣ Weather
    st.subheader("🌦 Weather Analysis (DeepSeek Reasoning)")
    weather = call_reasoning_model(
        "You are an agricultural climate analyst.",
        f"Provide 1 year agricultural weather analysis for {location}"
    )
    st.write(weather)

    # 3️⃣ Soil
    st.subheader("🌱 Soil & Water Report")
    soil = call_reasoning_model(
        "You are a soil chemistry expert.",
        f"Provide soil chemistry and groundwater report for {location}"
    )
    st.write(soil)

    # 4️⃣ Environmental Explanation
    st.subheader("🧬 Environmental Disease Explanation")
    explanation = call_reasoning_model(
        "You are a plant pathology scientist.",
        f"""
        Disease: {disease}
        Weather: {weather}
        Soil: {soil}

        Explain biological cause and environmental influence.
        """
    )
    st.write(explanation)

    # 5️⃣ Scientific Report
    st.subheader("📄 Full Scientific Crop Report")
    report = call_reasoning_model(
        "You are a crop research scientist.",
        f"Generate full scientific agricultural pathology report for: {disease}"
    )
    st.write(report)

    # 6️⃣ Treatment Plan
    st.subheader("💧 Fertilizer & Irrigation Plan")
    plan = call_reasoning_model(
        "You are an agricultural planner.",
        f"""
        Based on this disease report:
        {report}

        Generate:
        - Fertilizer schedule
        - Weekly irrigation quantity
        - Monthly timeline
        - Preventive plan
        """
    )
    st.write(plan)

    # 7️⃣ Pest Analysis
    if include_pests:
        st.subheader("🐛 Pest Risk Analysis")
        pest = call_reasoning_model(
            "You are an agricultural entomologist.",
            f"Analyze pest risks for this crop condition: {disease}"
        )
        st.write(pest)

    # 8️⃣ Price Search
    st.subheader("💰 Fertilizer Price Search")
    prices = call_reasoning_model(
        "You are an agricultural supply market analyst.",
        f"Search fertilizer prices near {location} based on this plan: {plan}"
    )
    st.write(prices)

    # 9️⃣ Delivery Planning
    st.subheader("🚚 Delivery Planning & Cost")
    delivery = call_reasoning_model(
        "You are a logistics planner.",
        f"Plan delivery logistics and total cost to {location} based on: {prices}"
    )
    st.write(delivery)

    # 🔟 Doctor Search
    st.subheader("👨‍⚕️ Agricultural Doctors Nearby")
    doctors = call_reasoning_model(
        "You are an agricultural consultant directory system.",
        f"Find agricultural crop doctors near {location}. Include name, contact, and education."
    )
    st.write(doctors)

    st.success("Full Vision-Based Agricultural Intelligence Completed.")
