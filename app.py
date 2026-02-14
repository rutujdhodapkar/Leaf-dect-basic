import streamlit as st
import requests
import base64
import json
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

# ================= CONFIG =================

OPENROUTER_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

PRIMARY_MODEL = "openai/gpt-oss-120b:free"
VISION_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"

st.set_page_config(layout="wide")

# ================= MODEL CALL =================

def call_model(model, messages):
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
        r = requests.post(OPENROUTER_URL, headers=headers, json=payload)
        data = r.json()
        return data["choices"][0]["message"]["content"]
    except:
        return None


# ================= UI =================

st.title("🌾 Smart Farming AI Agent")

mode = st.sidebar.radio(
    "Select Mode",
    ["🌿 Leaf Disease Detection", "🌱 Farming Intelligence"]
)

location_input = st.sidebar.text_input("Enter Location (village/city/district)")


# =========================================================
# 🌿 LEAF DISEASE DETECTION
# =========================================================

if mode == "🌿 Leaf Disease Detection":

    uploaded_file = st.file_uploader("Upload Leaf Image", type=["jpg","png","jpeg"])

    if uploaded_file:

        image = Image.open(uploaded_file)
        st.image(image, width=300)

        if st.button("Analyze Leaf"):

            img_b64 = base64.b64encode(uploaded_file.getvalue()).decode()

            vision_messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """
                            Analyze this plant leaf.
                            Return ONLY JSON:
                            {
                              "leaf_name": "",
                              "disease": "",
                              "description": "",
                              "solutions": []
                            }
                            """
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                        }
                    ]
                }
            ]

            result = call_model(VISION_MODEL, vision_messages)

            if result:
                parsed = json.loads(result)

                st.title(parsed["leaf_name"])
                st.subheader(parsed["disease"])
                st.write(parsed["description"])

                st.markdown("### 🌿 Solutions")
                for s in parsed["solutions"]:
                    st.write("•", s)

                # ================= DOCTOR SEARCH =================

                if location_input:

                    doctor_prompt = [
                        {
                            "role": "user",
                            "content": f"""
                            Location: {location_input}
                            Disease: {parsed['disease']}

                            Find nearby agriculture/plant doctors.
                            Return JSON list:
                            [
                              {{
                                "name":"",
                                "education":"",
                                "contact":"",
                                "profile_pic":"https://randomuser.me/api/portraits/men/1.jpg"
                              }}
                            ]
                            """
                        }
                    ]

                    doctors_raw = call_model(PRIMARY_MODEL, doctor_prompt)

                    if doctors_raw:
                        doctors = json.loads(doctors_raw)

                        st.markdown("## 👨‍⚕️ Nearby Experts")

                        cols = st.columns(3)

                        for i, doc in enumerate(doctors):
                            with cols[i % 3]:
                                st.image(doc["profile_pic"], width=120)
                                st.subheader(doc["name"])
                                st.write(doc["education"])
                                st.write("📞", doc["contact"])


# =========================================================
# 🌱 FARMING INTELLIGENCE AGENT
# =========================================================

if mode == "🌱 Farming Intelligence":

    if location_input and st.button("Generate Farming Report"):

        farming_prompt = [
            {
                "role": "user",
                "content": f"""
                Location: {location_input}

                Analyze this location for agriculture.

                Return STRICT JSON:
                {{
                  "weather":[
                    {{"month":"Jan","temp":25,"rain":20}}
                  ],
                  "crop_recommendation":[
                    {{"month":"June","crop":"Rice","score":85}}
                  ],
                  "soil":[
                    {{"chemical":"Nitrogen","level":70}}
                  ],
                  "description":"Detailed farming explanation"
                }}
                """
            }
        ]

        response = call_model(PRIMARY_MODEL, farming_prompt)

        if response:

            parsed = json.loads(response)

            # ================= WEATHER TABLE =================

            st.markdown("## 🌦 Weather Overview")
            weather_df = pd.DataFrame(parsed["weather"])
            st.table(weather_df)

            # ================= CROP GRAPH =================

            st.markdown("## 🌱 Best Crop Months")

            crop_df = pd.DataFrame(parsed["crop_recommendation"])

            plt.figure()
            plt.bar(crop_df["month"], crop_df["score"])
            plt.xticks(rotation=45)
            st.pyplot(plt)

            # ================= SOIL GRAPH =================

            st.markdown("## 🧪 Soil Composition")

            soil_df = pd.DataFrame(parsed["soil"])

            plt.figure()
            plt.bar(soil_df["chemical"], soil_df["level"])
            st.pyplot(plt)

            # ================= DESCRIPTION =================

            st.markdown("## 📘 Detailed Farming Advice")
            st.write(parsed["description"])

            # ================= CHAT WITH AI =================

            if "chat_memory" not in st.session_state:
                st.session_state.chat_memory = []

            st.markdown("## 💬 Talk With AI Advisor")

            user_question = st.text_input("Ask about your farm")

            if user_question:

                context = json.dumps(parsed)

                chat_prompt = [
                    {
                        "role": "user",
                        "content": f"""
                        You are an agricultural expert.
                        Context Data: {context}
                        Farmer Question: {user_question}
                        Provide precise, practical advice.
                        """
                    }
                ]

                chat_response = call_model(PRIMARY_MODEL, chat_prompt)

                st.session_state.chat_memory.append(("Farmer", user_question))
                st.session_state.chat_memory.append(("AI", chat_response))

            for role, msg in st.session_state.chat_memory:
                st.write(f"**{role}:** {msg}")
