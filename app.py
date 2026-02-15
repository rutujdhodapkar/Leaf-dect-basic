import streamlit as st
import requests
import base64
from PIL import Image
import io

# ================= CONFIG ================= #

OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

LOCAL_LLM_URL = "https://4ce5-2401-4900-7c88-d450-445d-cf33-80bb-fa11.ngrok-free.app"
LOCAL_VISION_MODEL = "qwen/qwen2.5-vl-7b"

MAIN_BRAIN = "qwen/qwen3-next-80b-a3b-instruct:free"
HEAVY_MODEL = "openai/gpt-oss-120b:free"
FAST_MODEL = "nvidia/nemotron-3-nano-30b-a3b:free"

# ================= CORE CALLERS ================= #

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

    r = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=300)
    return r.json()["choices"][0]["message"]["content"]


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

    r = requests.post(LOCAL_LLM_URL, json=payload, timeout=300)
    return r.json()["choices"][0]["message"]["content"]

# ================= STREAMLIT UI ================= #

st.set_page_config(layout="wide")
st.title("🌾 Vision-Based Farm Intelligence System")

location = st.text_input("Farm Location")
image_file = st.file_uploader("Upload Plant Image", type=["jpg", "jpeg", "png"])
include_pests = st.checkbox("Include Pest Analysis")

if st.button("Run Full Vision Pipeline"):

    if image_file is None:
        st.error("Upload image first.")
    else:

        st.image(image_file, caption="Uploaded Crop Image", use_column_width=True)

        st.subheader("🪴 Plant & Disease Detection (Local Vision Model)")

        image_base64 = encode_image(image_file)

        disease = call_local_vision_model(
            image_base64,
            "Identify plant type and any disease. Be specific."
        )

        st.write(disease)

        st.subheader("🌦 Weather Intelligence")
        weather = call_openrouter(
            FAST_MODEL,
            f"Provide 1 year weather analysis for {location}"
        )
        st.write(weather)

        st.subheader("🌱 Soil & Water Intelligence")
        soil = call_openrouter(
            FAST_MODEL,
            f"Provide soil and groundwater report for {location}"
        )
        st.write(soil)

        st.subheader("🧬 Disease Explanation with Environmental Context")
        explanation = call_openrouter(
            HEAVY_MODEL,
            f"""
            Disease: {disease}
            Weather: {weather}
            Soil: {soil}
            Explain full biological cause and why environment contributed.
            """
        )
        st.write(explanation)

        st.subheader("📄 Full Scientific Disease Report")
        report = call_openrouter(
            HEAVY_MODEL,
            f"Generate complete crop pathology report for {disease}"
        )
        st.write(report)

        st.subheader("💧 Treatment & Irrigation Plan")
        plan = call_openrouter(
            HEAVY_MODEL,
            f"Create fertilizer, irrigation schedule, water quantity, and monthly calendar plan based on {report}"
        )
        st.write(plan)

        if include_pests:
            st.subheader("🐛 Pest Analysis")
            pest = call_openrouter(
                FAST_MODEL,
                f"Analyze pest risks based on this crop condition: {disease}"
            )
            st.write(pest)

        st.subheader("💰 Fertilizer Price Search")
        prices = call_openrouter(
            FAST_MODEL,
            f"Search online fertilizer prices near {location} from this plan: {plan}"
        )
        st.write(prices)

        st.subheader("🚚 Delivery Planning")
        delivery = call_openrouter(
            FAST_MODEL,
            f"Plan full logistics and total cost delivery to {location} based on {prices}"
        )
        st.write(delivery)

        st.subheader("👨‍⚕️ Local Crop Doctors")
        doctors = call_openrouter(
            FAST_MODEL,
            f"Find agricultural crop doctors near {location} with name, contact and education."
        )
        st.write(doctors)

        st.success("Vision Agricultural Intelligence Pipeline Completed.")

