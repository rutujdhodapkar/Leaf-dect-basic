import streamlit as st
import requests
import base64
import json
import re
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

# ================= CONFIG =================

OPENROUTER_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

PRIMARY_MODEL = "openai/gpt-oss-120b:free"
VISION_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"

st.set_page_config(layout="wide")

# ================= SAFE JSON =================

def safe_json_loads(raw_text):
    if not raw_text or not isinstance(raw_text, str):
        return None

    try:
        return json.loads(raw_text)
    except:
        match = re.search(r'\{.*\}|\[.*\]', raw_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                return None
        return None


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

        if r.status_code != 200:
            st.error(f"API Error: {r.status_code}")
            st.code(r.text)
            return None

        data = r.json()

        if "choices" not in data:
            st.error("Model response malformed")
            st.code(data)
            return None

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        st.error("Connection error")
        st.code(str(e))
        return None

# ================= UI =================

st.title("🌾 Smart Farming AI Research Agent")

mode = st.sidebar.radio(
    "Select Mode",
    ["🌿 Leaf Disease Detection", "🌱 Farming Intelligence"]
)

location_input = st.sidebar.text_input("Enter Location")

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
            parsed = safe_json_loads(result)

            if parsed:

                st.title(parsed["leaf_name"])
                st.subheader(parsed["disease"])
                st.write(parsed["description"])

                st.markdown("### 🌿 Solutions")
                for s in parsed["solutions"]:
                    st.write("•", s)

                # DOCTOR SEARCH

                if location_input:

                    doctor_prompt = [
                        {
                            "role": "user",
                            "content": f"""
                            Location: {location_input}
                            Disease: {parsed['disease']}

                            Return JSON list of nearby agriculture doctors:
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
                    doctors = safe_json_loads(doctors_raw)

                    if doctors:

                        st.markdown("## 👨‍⚕️ Nearby Experts")
                        cols = st.columns(3)

                        for i, doc in enumerate(doctors):
                            with cols[i % 3]:
                                st.image(doc["profile_pic"], width=120)
                                st.subheader(doc["name"])
                                st.write(doc["education"])
                                st.write("📞", doc["contact"])

# =========================================================
# 🌱 FARMING INTELLIGENCE
# =========================================================

if mode == "🌱 Farming Intelligence":

    if location_input and st.button("Generate Farming Research Report"):

        farming_prompt = [
            {
                "role": "user",
                "content": f"""
                Location: {location_input}

                Perform deep agricultural analysis.

                Return STRICT JSON:

                {{
                  "best_crop":"",

                  "weather":[
                    {{
                      "month":"Jan",
                      "temp":0,
                      "rain":0,
                      "humidity":0
                    }}
                  ],

                  "crop_scores":[
                    {{
                      "crop":"",
                      "score":0
                    }}
                  ],

                  "soil_macro":[
                    {{"element":"Nitrogen","level":0}},
                    {{"element":"Phosphorus","level":0}},
                    {{"element":"Potassium","level":0}}
                  ],

                  "soil_micro":[
                    {{"element":"Zinc","level":0}},
                    {{"element":"Iron","level":0}}
                  ],

                  "risks":[
                    "risk 1"
                  ],

                  "yield_estimate":"",

                  "conclusion":""
                }}
                """
            }
        ]

        response = call_model(PRIMARY_MODEL, farming_prompt)
        parsed = safe_json_loads(response)

        if parsed:

            # TITLE
            st.title(f"🌱 Recommended Crop: {parsed['best_crop']}")

            # WEATHER TABLE
            weather_df = pd.DataFrame(parsed["weather"])
            st.subheader("🌦 Weather Data")
            st.dataframe(weather_df)

            # TEMP GRAPH
            fig1, ax1 = plt.subplots()
            ax1.plot(weather_df["month"], weather_df["temp"])
            ax1.set_title("Temperature Trend")
            st.pyplot(fig1)

            # RAIN GRAPH
            fig2, ax2 = plt.subplots()
            ax2.plot(weather_df["month"], weather_df["rain"])
            ax2.set_title("Rainfall Trend")
            st.pyplot(fig2)

            # CROP SCORE GRAPH
            crop_df = pd.DataFrame(parsed["crop_scores"])
            fig3, ax3 = plt.subplots()
            ax3.bar(crop_df["crop"], crop_df["score"])
            ax3.set_title("Crop Suitability Score")
            st.pyplot(fig3)

            # SOIL MACRO
            macro_df = pd.DataFrame(parsed["soil_macro"])
            fig4, ax4 = plt.subplots()
            ax4.bar(macro_df["element"], macro_df["level"])
            ax4.set_title("Soil Macro Nutrients")
            st.pyplot(fig4)

            # SOIL MICRO
            micro_df = pd.DataFrame(parsed["soil_micro"])
            fig5, ax5 = plt.subplots()
            ax5.bar(micro_df["element"], micro_df["level"])
            ax5.set_title("Soil Micro Nutrients")
            st.pyplot(fig5)

            # RISKS
            st.subheader("⚠️ Farming Risks")
            for r in parsed["risks"]:
                st.write("•", r)

            # YIELD
            st.subheader("📈 Estimated Yield")
            st.info(parsed["yield_estimate"])

            # CONCLUSION
            st.subheader("🧠 Final Agricultural Conclusion")
            st.write(parsed["conclusion"])

            # CHAT WITH AI

            if "chat_memory" not in st.session_state:
                st.session_state.chat_memory = []

            st.subheader("💬 Talk With AI Advisor")

            user_question = st.text_input("Ask about your farm")

            if user_question:

                context = json.dumps(parsed)

                chat_prompt = [
                    {
                        "role": "user",
                        "content": f"""
                        You are agricultural advisor.
                        Context Data: {context}
                        Farmer Question: {user_question}
                        Provide practical advice.
                        """
                    }
                ]

                chat_response = call_model(PRIMARY_MODEL, chat_prompt)

                st.session_state.chat_memory.append(("Farmer", user_question))
                st.session_state.chat_memory.append(("AI", chat_response))

            for role, msg in st.session_state.chat_memory:
                st.write(f"**{role}:** {msg}")

