import streamlit as st
import requests
import base64
from PIL import Image
import io
import json

# ================= CONFIG ================= #

OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

LOCAL_LLM_URL = "https://288e-2401-4900-7c88-d450-445d-cf33-80bb-fa11.ngrok-free.app/v1/chat/completions"
LOCAL_VISION_MODEL = "qwen/qwen2.5-vl-7b"

MAIN_MODEL = "qwen/qwen3-next-80b-a3b-instruct:free"
HEAVY_MODEL = "openai/gpt-oss-120b:free"
FAST_MODEL = "openai/gpt-oss-120b:free"

# ================= SAFE CALLERS ================= #

def safe_extract_content(response_json):
    if "choices" in response_json:
        return response_json["choices"][0]["message"]["content"]

    if "output_text" in response_json:
        return response_json["output_text"]

    if "output" in response_json:
        try:
            return response_json["output"][0]["content"][0]["text"]
        except:
            return str(response_json)

    if "error" in response_json:
        return f"Model Error: {response_json['error']}"

    return f"Unknown response format: {response_json}"


def call_openrouter(model, prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are advanced agricultural intelligence system."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        r = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=300)
        return safe_extract_content(r.json())
    except Exception as e:
        return f"OpenRouter Error: {e}"


def encode_image(uploaded_file):
    image = Image.open(uploaded_file)
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()


def call_local_vision_model(image_base64, user_prompt):

    payload = {
        "model": LOCAL_VISION_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
    }

    try:
        r = requests.post(LOCAL_LLM_URL, json=payload, timeout=300)
        response_json = r.json()
        return safe_extract_content(response_json)
    except Exception as e:
        return f"Local Vision Model Error: {e}"


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

    # 1️⃣ Vision Detection
    st.subheader("🪴 Plant & Disease Detection")
    disease = call_local_vision_model(
        image_base64,
        "Identify plant type and any disease. Be specific and structured."
    )
    st.write(disease)

    # 2️⃣ Weather
    st.subheader("🌦 Weather Analysis (1 Year)")
    weather = call_openrouter(
        FAST_MODEL,
        f"Provide 1 year agricultural weather analysis for {location}"
    )
    st.write(weather)

    # 3️⃣ Soil
    st.subheader("🌱 Soil & Water Report")
    soil = call_openrouter(
        FAST_MODEL,
        f"Provide soil chemistry and groundwater report for {location}"
    )
    st.write(soil)

    # 4️⃣ Disease Explanation
    st.subheader("🧬 Environmental Disease Explanation")
    explanation = call_openrouter(
        HEAVY_MODEL,
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
    report = call_openrouter(
        HEAVY_MODEL,
        f"Generate full scientific agricultural pathology report for: {disease}"
    )
    st.write(report)

    # 6️⃣ Treatment Plan
    st.subheader("💧 Fertilizer & Irrigation Plan")
    plan = call_openrouter(
        HEAVY_MODEL,
        f"""
        Based on this disease report:
        {report}

        Generate:
        - Fertilizer schedule
        - Water quantity per week
        - Monthly timeline
        - Preventive plan
        """
    )
    st.write(plan)

    # 7️⃣ Pest Analysis
    if include_pests:
        st.subheader("🐛 Pest Risk Analysis")
        pest = call_openrouter(
            FAST_MODEL,
            f"Analyze pest risks for this crop condition: {disease}"
        )
        st.write(pest)

    # 8️⃣ Price Search
    st.subheader("💰 Fertilizer Price Search")
    prices = call_openrouter(
        FAST_MODEL,
        f"Search fertilizer prices near {location} based on this plan: {plan}"
    )
    st.write(prices)

    # 9️⃣ Delivery Planning
    st.subheader("🚚 Delivery Planning & Cost")
    delivery = call_openrouter(
        FAST_MODEL,
        f"Plan full delivery logistics and total cost to {location} based on: {prices}"
    )
    st.write(delivery)

    # 🔟 Doctor Search
    st.subheader("👨‍⚕️ Agricultural Doctors Nearby")
    doctors = call_openrouter(
        FAST_MODEL,
        f"Find agricultural crop doctors near {location}. Include name, contact, and education."
    )
    st.write(doctors)

    st.success("Full Vision-Based Agricultural Intelligence Completed.")


