import streamlit as st
import requests
import json
from datetime import datetime
from PIL import Image

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

PLANTNET_API_KEY = "2b10HBK5Qcj0zSVelLDZHgIG"
PLANTNET_URL = "https://my-api.plantnet.org/v2/identify/all"

OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "openai/gpt-oss-120b:free"

# --------------------------------------------------
# STREAMLIT CONFIG
# --------------------------------------------------

st.set_page_config(page_title="AI Plant Scanner Pro", layout="centered")
st.title("🌿 AI Plant & Leaf Detection System")

uploaded_file = st.file_uploader("Upload a plant/leaf image", type=["jpg", "jpeg", "png"])

# --------------------------------------------------
# PLANT IDENTIFICATION
# --------------------------------------------------

def identify_plant(image_bytes):
    files = {
        "images": image_bytes
    }

    data = {
        "organs": ["leaf"]
    }

    response = requests.post(
        f"{PLANTNET_URL}?api-key={PLANTNET_API_KEY}",
        files=files,
        data=data
    )

    return response.json()


# --------------------------------------------------
# GENERATE BACKGROUND JSON
# --------------------------------------------------

def generate_background_json(species_info):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    background_json = {
        "species_common_name": species_info.get("common_name"),
        "species_scientific_name": species_info.get("scientific_name"),
        "confidence_score": species_info.get("confidence"),
        "timestamp": timestamp,
        "weather": "Not Integrated Yet",
        "location": "Not Integrated Yet"
    }

    return background_json


# --------------------------------------------------
# REASONING MODEL VIA OPENROUTER
# --------------------------------------------------

def run_reasoning_model(background_json):

    prompt = f"""
    You are a botanical AI reasoning system.
    Analyze this plant scan JSON and return structured output.

    Input JSON:
    {json.dumps(background_json, indent=2)}

    Return ONLY valid JSON in this structure:
    {{
        "plant_health_assessment": "",
        "care_recommendations": "",
        "disease_risk": "",
        "confidence_level": ""
    }}
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are an advanced plant reasoning model."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=payload)

    result = response.json()

    try:
        output_text = result["choices"][0]["message"]["content"]
        return json.loads(output_text)
    except:
        return {"error": "Reasoning model failed", "raw_response": result}


# --------------------------------------------------
# MAIN EXECUTION
# --------------------------------------------------

if uploaded_file:

    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    image_bytes = uploaded_file.read()

    with st.spinner("Detecting plant species..."):

        result = identify_plant(image_bytes)

        if "results" in result and len(result["results"]) > 0:

            top = result["results"][0]

            species_info = {
                "common_name": top["species"]["commonNames"][0]
                               if top["species"].get("commonNames")
                               else "Unknown",
                "scientific_name": top["species"]["scientificNameWithoutAuthor"],
                "confidence": round(top["score"] * 100, 2)
            }

            background_json = generate_background_json(species_info)

            st.success("Plant Identified")

            st.subheader("🌱 Detection Result")
            st.write(f"Common Name: {species_info['common_name']}")
            st.write(f"Scientific Name: {species_info['scientific_name']}")
            st.write(f"Confidence: {species_info['confidence']}%")

            st.subheader("📦 Background JSON")
            st.json(background_json)

            # -------------------------
            # REASONING STAGE
            # -------------------------

            with st.spinner("Running botanical reasoning model..."):

                reasoning_output = run_reasoning_model(background_json)

                st.subheader("🧠 AI Reasoning Output")
                st.json(reasoning_output)

        else:
            st.error("No plant detected. Try clearer leaf image.")
