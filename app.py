import base64
import io
import json
import os

import requests
import streamlit as st
from PIL import Image

# ================= CONFIG ================= #

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

VISION_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"
REASONING_MODEL = "deepseek/deepseek-r1-0528:free"

USER_DB = "users.json"
SESSION_DB = "last_session.json"

# ================= API ================= #


def call_openrouter(messages, model):
    if not OPENROUTER_API_KEY:
        return "OpenRouter API key not configured. Set OPENROUTER_API_KEY in environment."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {"model": model, "messages": messages}
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        return f"API request failed: {error}"

    if "choices" in data:
        return data["choices"][0]["message"]["content"]

    return str(data)


# ================= TRANSLATIONS ================= #

translations = {
    "English": {
        "select_language": "🌍 Select Language",
        "language": "Language",
        "continue": "Continue",
        "login": "Login",
        "username": "Username",
        "password": "Password",
        "login_button": "Login / Register",
        "logout": "Logout",
        "login_success": "Login successful.",
        "account_created": "Account created and logged in.",
        "home": "Home",
        "chat": "Chat",
        "shops": "Shops",
        "contact": "Contact Us",
        "app_title": "🌾 Agricultural Intelligence",
        "farm_location": "Farm Location",
        "upload": "Upload Leaf Image",
        "analyze": "Analyze Crop",
        "upload_error": "Please upload an image first.",
        "result": "## Result",
        "chat_title": "💬 AI Chat",
        "chat_placeholder": "Ask anything about agriculture",
        "send": "Send",
        "shops_title": "🛒 Fertilizer Shop Search",
        "crop_name": "Crop Name",
        "specific_requirement": "Specific Requirement",
        "search_products": "Search Products",
        "contact_title": "📞 Contact Us",
        "contact_details": """**Name:** Rutuj Dhodapkar  
**Email:** rutujdhodapkar@gmail.com  
**Username:** rutujdhodapkar  
**Portfolio:** https://rutujdhodapkar.vercel.app/  
**Specialization:** Advanced AI, Deep Learning, Machine Learning, Big Data  
**Location:** Los Angeles  
""",
    },
    "Hindi": {
        "select_language": "🌍 भाषा चुनें",
        "language": "भाषा",
        "continue": "आगे बढ़ें",
        "login": "लॉगिन",
        "username": "उपयोगकर्ता नाम",
        "password": "पासवर्ड",
        "login_button": "लॉगिन / रजिस्टर",
        "logout": "लॉगआउट",
        "login_success": "लॉगिन सफल रहा।",
        "account_created": "खाता बन गया और लॉगिन हो गया।",
        "home": "होम",
        "chat": "चैट",
        "shops": "दुकान",
        "contact": "संपर्क करें",
        "app_title": "🌾 कृषि बुद्धिमत्ता",
        "farm_location": "फार्म स्थान",
        "upload": "पत्ता अपलोड करें",
        "analyze": "फसल विश्लेषण करें",
        "upload_error": "कृपया पहले छवि अपलोड करें।",
        "result": "## परिणाम",
        "chat_title": "💬 AI चैट",
        "chat_placeholder": "कृषि के बारे में कुछ भी पूछें",
        "send": "भेजें",
        "shops_title": "🛒 उर्वरक खोज",
        "crop_name": "फसल का नाम",
        "specific_requirement": "विशिष्ट आवश्यकता",
        "search_products": "उत्पाद खोजें",
        "contact_title": "📞 संपर्क करें",
        "contact_details": """**नाम:** Rutuj Dhodapkar  
**ईमेल:** rutujdhodapkar@gmail.com  
**यूज़रनेम:** rutujdhodapkar  
**पोर्टफोलियो:** https://rutujdhodapkar.vercel.app/  
**विशेषज्ञता:** Advanced AI, Deep Learning, Machine Learning, Big Data  
**स्थान:** Los Angeles  
""",
    },
    "Marathi": {
        "select_language": "🌍 भाषा निवडा",
        "language": "भाषा",
        "continue": "पुढे जा",
        "login": "लॉगिन",
        "username": "वापरकर्ता नाव",
        "password": "पासवर्ड",
        "login_button": "लॉगिन / नोंदणी",
        "logout": "लॉगआउट",
        "login_success": "लॉगिन यशस्वी.",
        "account_created": "खाते तयार झाले आणि लॉगिन झाले.",
        "home": "होम",
        "chat": "चॅट",
        "shops": "दुकान",
        "contact": "संपर्क",
        "app_title": "🌾 कृषी बुद्धिमत्ता",
        "farm_location": "शेतीचे ठिकाण",
        "upload": "पान अपलोड करा",
        "analyze": "पीक विश्लेषण करा",
        "upload_error": "कृपया आधी प्रतिमा अपलोड करा.",
        "result": "## निकाल",
        "chat_title": "💬 AI चॅट",
        "chat_placeholder": "कृषीबद्दल काहीही विचारा",
        "send": "पाठवा",
        "shops_title": "🛒 खत शोध",
        "crop_name": "पिकाचे नाव",
        "specific_requirement": "विशिष्ट गरज",
        "search_products": "उत्पादने शोधा",
        "contact_title": "📞 संपर्क",
        "contact_details": """**नाव:** Rutuj Dhodapkar  
**ईमेल:** rutujdhodapkar@gmail.com  
**यूजरनेम:** rutujdhodapkar  
**पोर्टफोलियो:** https://rutujdhodapkar.vercel.app/  
**तज्ज्ञता:** Advanced AI, Deep Learning, Machine Learning, Big Data  
**स्थान:** Los Angeles  
""",
    },
}


# ================= HELPERS ================= #


def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return default



def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


# ================= SESSION INIT ================= #

if "language" not in st.session_state:
    st.session_state.language = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "menu" not in st.session_state:
    st.session_state.menu = "Home"

# Auto-login from saved session
users = load_json(USER_DB, {})
saved_session = load_json(SESSION_DB, {})
saved_user = saved_session.get("username")
if saved_user and saved_user in users and not st.session_state.logged_in:
    st.session_state.logged_in = True
    st.session_state.username = saved_user

# ================= LANGUAGE SELECT ================= #

if not st.session_state.language:
    st.title("🌍 Select Language")
    selected_language = st.selectbox("Language", ["English", "Hindi", "Marathi"])
    if st.button("Continue"):
        st.session_state.language = selected_language
        st.rerun()
    st.stop()

lang_text = translations[st.session_state.language]

# ================= LOGIN SYSTEM ================= #

if not st.session_state.logged_in:
    st.title(lang_text["login"])
    username = st.text_input(lang_text["username"])
    password = st.text_input(lang_text["password"], type="password")

    if st.button(lang_text["login_button"]):
        if username in users and users[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            save_json(SESSION_DB, {"username": username})
            st.success(lang_text["login_success"])
            st.rerun()

        elif username in users and users[username] != password:
            st.error("Invalid password")

        else:
            users[username] = password
            save_json(USER_DB, users)
            save_json(SESSION_DB, {"username": username})
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(lang_text["account_created"])
            st.rerun()

    st.stop()

# ================= NAVIGATION ================= #

col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
if col1.button(lang_text["home"], use_container_width=True):
    st.session_state.menu = lang_text["home"]
if col2.button(lang_text["chat"], use_container_width=True):
    st.session_state.menu = lang_text["chat"]
if col3.button(lang_text["shops"], use_container_width=True):
    st.session_state.menu = lang_text["shops"]
if col4.button(lang_text["contact"], use_container_width=True):
    st.session_state.menu = lang_text["contact"]
if col5.button(lang_text["logout"], use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.username = ""
    if os.path.exists(SESSION_DB):
        os.remove(SESSION_DB)
    st.rerun()

if st.session_state.menu not in [
    lang_text["home"],
    lang_text["chat"],
    lang_text["shops"],
    lang_text["contact"],
]:
    st.session_state.menu = lang_text["home"]

menu = st.session_state.menu

# ================= HOME ================= #

if menu == lang_text["home"]:
    st.title(lang_text["app_title"])
    st.caption(f"{lang_text['username']}: {st.session_state.username}")

    st.text_input(lang_text["farm_location"])
    uploaded_image = st.file_uploader(lang_text["upload"], type=["jpg", "png", "jpeg"])

    if st.button(lang_text["analyze"]):
        if not uploaded_image:
            st.error(lang_text["upload_error"])
            st.stop()

        image = Image.open(uploaded_image)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode()

        desc = call_openrouter(
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this leaf in detail."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                        },
                    ],
                }
            ],
            VISION_MODEL,
        )

        diagnosis = call_openrouter(
            [
                {"role": "system", "content": "You are a plant pathologist."},
                {
                    "role": "user",
                    "content": f"Based on this description: {desc}. Identify crop and disease with remedy.",
                },
            ],
            REASONING_MODEL,
        )

        st.markdown(lang_text["result"])
        st.write(diagnosis)

# ================= CHAT ================= #

elif menu == lang_text["chat"]:
    st.title(lang_text["chat_title"])
    user_query = st.text_input(lang_text["chat_placeholder"])

    if st.button(lang_text["send"]):
        response = call_openrouter(
            [
                {"role": "system", "content": "You are an agricultural assistant."},
                {"role": "user", "content": user_query},
            ],
            REASONING_MODEL,
        )
        st.write(response)

# ================= SHOPS ================= #

elif menu == lang_text["shops"]:
    st.title(lang_text["shops_title"])

    crop = st.text_input(lang_text["crop_name"])
    req = st.text_input(lang_text["specific_requirement"])

    if st.button(lang_text["search_products"]):
        result = call_openrouter(
            [
                {
                    "role": "system",
                    "content": "You are a fertilizer market analyst. Use reasoning and provide practical recommendations.",
                },
                {
                    "role": "user",
                    "content": f"""
Find best fertilizers online for crop: {crop}
Requirement: {req}
Provide:
- Product Name
- NPK Ratio
- Approx Price
- Usage Reason
- Online availability
- Why this matches user requirement
""",
                },
            ],
            REASONING_MODEL,
        )
        st.write(result)

# ================= CONTACT ================= #

elif menu == lang_text["contact"]:
    st.title(lang_text["contact_title"])
    st.markdown(lang_text["contact_details"])
