import base64
import io
import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path

import requests
from flask import Flask, redirect, render_template, request, session, url_for
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "leaf-detect-basic-secret"

# User requested API key in-code
OPENROUTER_API_KEY = "YOUR_OPENROUTER_API_KEY"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
VISION_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"
REASONING_MODEL = "deepseek/deepseek-r1-0528:free"

USER_DB = "users.json"
SESSION_DB = "last_session.json"
EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)

TASK_LOCK = threading.Lock()
TASKS: dict[str, dict] = {}
REPORTS: dict[str, list] = {}

translations = {
    "English": {
        "login": "Login",
        "username": "Username",
        "password": "Password",
        "login_button": "Login / Register",
        "invalid_password": "Invalid password",
        "app_title": "Agricultural Intelligence",
        "agent": "Agent Status",
        "home": "Home",
        "chat": "Chat",
        "shops": "Shops",
        "doctors": "Doctors",
        "contact": "Contact Us",
        "analysis": "Analysis",
        "price_prediction": "Price Prediction",
        "export_chat": "Export Chat PDF",
        "show_all": "Show All",
        "crop_name": "Crop Name",
        "specific_requirement": "Specific Requirement",
        "search_products": "Search",
        "analyze_crop": "Analyze Crop",
        "farm_location": "Farm Location",
        "upload": "Upload Leaf Image",
        "send": "Send",
        "settings": "Settings",
        "theme": "Theme",
        "logout": "Logout",
        "more": "More",
    },
    "Hindi": {
        "login": "लॉगिन",
        "username": "उपयोगकर्ता नाम",
        "password": "पासवर्ड",
        "login_button": "लॉगिन / रजिस्टर",
        "invalid_password": "गलत पासवर्ड",
        "app_title": "कृषि बुद्धिमत्ता",
        "agent": "एजेंट स्थिति",
        "home": "होम",
        "chat": "चैट",
        "shops": "दुकान",
        "doctors": "डॉक्टर्स",
        "contact": "संपर्क",
        "analysis": "विश्लेषण",
        "price_prediction": "मूल्य पूर्वानुमान",
        "export_chat": "चैट PDF निर्यात",
        "show_all": "सभी दिखाएं",
        "crop_name": "फसल का नाम",
        "specific_requirement": "विशिष्ट आवश्यकता",
        "search_products": "खोजें",
        "analyze_crop": "फसल विश्लेषण",
        "farm_location": "फार्म स्थान",
        "upload": "पत्ता अपलोड",
        "send": "भेजें",
        "settings": "सेटिंग्स",
        "theme": "थीम",
        "logout": "लॉगआउट",
        "more": "अधिक",
    },
    "Marathi": {
        "login": "लॉगिन",
        "username": "वापरकर्ता नाव",
        "password": "पासवर्ड",
        "login_button": "लॉगिन / नोंदणी",
        "invalid_password": "चुकीचा पासवर्ड",
        "app_title": "कृषी बुद्धिमत्ता",
        "agent": "एजंट स्थिती",
        "home": "होम",
        "chat": "चॅट",
        "shops": "दुकान",
        "doctors": "डॉक्टर्स",
        "contact": "संपर्क",
        "analysis": "विश्लेषण",
        "price_prediction": "किंमत अंदाज",
        "export_chat": "चॅट PDF निर्यात",
        "show_all": "सर्व दाखवा",
        "crop_name": "पिकाचे नाव",
        "specific_requirement": "विशिष्ट गरज",
        "search_products": "शोधा",
        "analyze_crop": "पीक विश्लेषण",
        "farm_location": "शेती स्थान",
        "upload": "पान अपलोड",
        "send": "पाठवा",
        "settings": "सेटिंग्ज",
        "theme": "थीम",
        "logout": "लॉगआउट",
        "more": "अधिक",
    },
}

ALL_FERTILIZERS = [
    "Urea (46-0-0)",
    "DAP (18-46-0)",
    "NPK 10-26-26",
    "MOP (0-0-60)",
    "Compost + Bio-fertilizer",
]


CAPABILITY_BLOCKS = {
    "Water Layer": [
        "Soil moisture modeling",
        "Water requirement prediction",
        "AI-driven irrigation schedule",
        "Drought early warning",
        "Water waste optimization %",
    ],
    "Soil Layer": [
        "Nitrogen, phosphorus, potassium prediction",
        "pH imbalance detection",
        "Nutrient deficiency via leaf + soil fusion model",
        "Fertilizer recommendation engine",
        "Long-term soil health score",
    ],
    "Vision Layer": [
        "Insect classification",
        "Pest density estimation",
        "Swarm detection",
        "Migration pattern prediction",
        "Smart pesticide timing",
    ],
    "Climate Layer": [
        "7–30 day disease risk prediction",
        "Frost risk alerts",
        "Heat stress prediction",
        "Wind-based pest migration modeling",
        "Crop growth stage mapping",
    ],
    "Market Layer": [
        "Satellite imagery integration",
        "Growth stage tracking",
        "Production estimate per acre",
        "Profit forecast",
        "Market price integration",
    ],
    "Execution Layer": [
        "Camera → analyze → recommend → auto-execute",
        "Irrigation valve control",
        "Sprayer control",
        "Drone-based spraying",
        "Automated farm reporting",
    ],
}


def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def call_openrouter(messages, model):
    if OPENROUTER_API_KEY in ("", "YOUR_OPENROUTER_API_KEY"):
        return "Demo mode: Add valid API key in app.py to get live model responses."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "messages": messages}

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as error:
        return f"Model request failed: {error}"


def current_lang():
    return session.get("language", "English")


def t(key):
    return translations[current_lang()].get(key, key)


def ensure_auth():
    if not session.get("logged_in"):
        return False
    return True


def start_task(username, task_type, payload):
    task_id = f"{username}-{int(time.time() * 1000)}"
    with TASK_LOCK:
        TASKS[task_id] = {
            "id": task_id,
            "username": username,
            "type": task_type,
            "status": "running",
            "message": "Agent is processing...",
            "result": None,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    thread = threading.Thread(target=run_task, args=(task_id, payload), daemon=True)
    thread.start()
    return task_id


def run_task(task_id, payload):
    username = TASKS[task_id]["username"]
    task_type = TASKS[task_id]["type"]
    result = ""

    if task_type == "leaf_analysis":
        prompt = payload["prompt"]
        result = call_openrouter(
            [
                {"role": "system", "content": "You are a farm AI agent pipeline."},
                {"role": "user", "content": prompt},
            ],
            REASONING_MODEL,
        )
    elif task_type in {"shop_search", "doctor_search"}:
        prompt = payload["prompt"]
        result = call_openrouter(
            [
                {"role": "system", "content": "Provide concise actionable recommendations."},
                {"role": "user", "content": prompt},
            ],
            REASONING_MODEL,
        )

    report = {
        "title": f"{task_type.replace('_', ' ').title()} Report",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "content": result,
        "task_id": task_id,
    }
    with TASK_LOCK:
        TASKS[task_id]["status"] = "done"
        TASKS[task_id]["message"] = "Completed"
        TASKS[task_id]["result"] = result
        REPORTS.setdefault(username, []).insert(0, report)


def get_user_reports(username):
    return REPORTS.get(username, [])


def get_agent_status(username):
    with TASK_LOCK:
        running = [x for x in TASKS.values() if x["username"] == username and x["status"] == "running"]
    if running:
        return "Agent is running background tasks: " + ", ".join([r["type"] for r in running])
    return "Agent is idle"


@app.context_processor
def inject_common():
    username = session.get("username", "Guest")
    reports = get_user_reports(username) if username != "Guest" else []
    return {
        "txt": translations[current_lang()],
        "language": current_lang(),
        "languages": list(translations.keys()),
        "agent_status": get_agent_status(username),
        "reports": reports,
        "username": username,
        "profile_photo": "https://ui-avatars.com/api/?name=" + username,
    }


@app.route("/set-language", methods=["POST"])
def set_language():
    session["language"] = request.form.get("language", "English")
    return redirect(request.referrer or url_for("home"))


@app.route("/", methods=["GET", "POST"])
def login():
    users = load_json(USER_DB, {})

    saved = load_json(SESSION_DB, {})
    if saved.get("username") in users and not session.get("logged_in"):
        session["logged_in"] = True
        session["username"] = saved["username"]
        session.setdefault("language", "English")
        session.setdefault("theme", "light")
        session.setdefault("chat_history", [])
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username in users and users[username] != password:
            return render_template("login.html", error=t("invalid_password"))
        if username not in users:
            users[username] = password
            save_json(USER_DB, users)
        session["logged_in"] = True
        session["username"] = username
        session.setdefault("language", "English")
        session.setdefault("theme", "light")
        session.setdefault("chat_history", [])
        save_json(SESSION_DB, {"username": username})
        return redirect(url_for("home"))

    return render_template("login.html", error=None)


@app.route("/logout")
def logout():
    session.clear()
    if os.path.exists(SESSION_DB):
        os.remove(SESSION_DB)
    return redirect(url_for("login"))


@app.route("/home", methods=["GET", "POST"])
def home():
    if not ensure_auth():
        return redirect(url_for("login"))

    if request.method == "POST":
        location = request.form.get("location", "")
        image_file = request.files.get("leaf_image")
        image_desc = "No image uploaded"

        if image_file and image_file.filename:
            image = Image.open(image_file)
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            image_desc = call_openrouter(
                [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this leaf."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                        ],
                    }
                ],
                VISION_MODEL,
            )

        prompt = f"""
Location: {location}
Leaf description: {image_desc}
Build one actionable report with:
- Multi-modal fusion model (Vision + Weather + Soil + Time)
- disease diagnosis + remedy
- irrigation and nutrient action plan
- auto-execute suggestions.
"""
        start_task(session["username"], "leaf_analysis", {"prompt": prompt})
        return redirect(url_for("analysis"))

    return render_template("home.html")


@app.route("/chat", methods=["GET", "POST"])
def chat():
    if not ensure_auth():
        return redirect(url_for("login"))
    history = session.get("chat_history", [])
    if request.method == "POST":
        q = request.form.get("query", "")
        if q:
            ans = call_openrouter(
                [
                    {"role": "system", "content": "You are a practical agriculture assistant."},
                    {"role": "user", "content": q},
                ],
                REASONING_MODEL,
            )
            history.append({"q": q, "a": ans})
            session["chat_history"] = history
    return render_template("chat.html", history=history)


@app.route("/shops", methods=["GET", "POST"])
def shops():
    if not ensure_auth():
        return redirect(url_for("login"))
    if request.method == "POST":
        if request.form.get("action") == "show_all":
            return render_template("shops.html", all_items=ALL_FERTILIZERS)

        crop = request.form.get("crop", "")
        req = request.form.get("requirement", "")
        prompt = f"Find fertilizers for crop={crop}, requirement={req}, include reason and estimated price."
        start_task(session["username"], "shop_search", {"prompt": prompt})
        return redirect(url_for("analysis"))
    return render_template("shops.html", all_items=None)


@app.route("/doctors", methods=["GET", "POST"])
def doctors():
    if not ensure_auth():
        return redirect(url_for("login"))
    if request.method == "POST":
        if request.form.get("action") == "show_all":
            doctors_list = ["Crop doctor teleconsult", "Pest specialist", "Soil specialist"]
            return render_template("doctors.html", all_items=doctors_list)
        crop = request.form.get("crop", "")
        req = request.form.get("requirement", "")
        prompt = f"Suggest agriculture doctors/experts for crop={crop}, need={req} with reason."
        start_task(session["username"], "doctor_search", {"prompt": prompt})
        return redirect(url_for("analysis"))
    return render_template("doctors.html", all_items=None)


@app.route("/analysis")
def analysis():
    if not ensure_auth():
        return redirect(url_for("login"))
    return render_template("analysis.html", capability_blocks=CAPABILITY_BLOCKS)


@app.route("/contact")
def contact():
    if not ensure_auth():
        return redirect(url_for("login"))
    return render_template("contact.html")


@app.route("/price-prediction", methods=["GET", "POST"])
def price_prediction():
    if not ensure_auth():
        return redirect(url_for("login"))
    result = None
    if request.method == "POST":
        seed = float(request.form.get("seed_cost", 0))
        fertilizer = float(request.form.get("fertilizer_cost", 0))
        labor = float(request.form.get("labor_cost", 0))
        irrigation = float(request.form.get("irrigation_cost", 0))
        misc = float(request.form.get("misc_cost", 0))
        expected_yield = float(request.form.get("yield_quintal", 0))
        market_price = float(request.form.get("market_price", 0))

        total_cost = seed + fertilizer + labor + irrigation + misc
        expected_revenue = expected_yield * market_price
        gain = expected_revenue - total_cost
        result = {
            "total_cost": round(total_cost, 2),
            "expected_revenue": round(expected_revenue, 2),
            "gain": round(gain, 2),
        }
    return render_template("price_prediction.html", result=result)


@app.route("/export-chat")
def export_chat():
    if not ensure_auth():
        return redirect(url_for("login"))

    history = session.get("chat_history", [])
    if not history:
        return redirect(url_for("chat"))

    filename = EXPORT_DIR / f"chat_{session['username']}_{int(time.time())}.pdf"
    c = canvas.Canvas(str(filename), pagesize=A4)
    y = 800
    c.drawString(40, y, f"Chat Export - {session['username']}")
    y -= 30
    for item in history:
        for line in [f"Q: {item['q']}", f"A: {item['a']}"]:
            wrapped = [line[i : i + 100] for i in range(0, len(line), 100)]
            for wline in wrapped:
                c.drawString(40, y, wline)
                y -= 18
                if y < 60:
                    c.showPage()
                    y = 800
        y -= 8
    c.save()
    return redirect(url_for("chat"))


@app.route("/theme/<theme_name>")
def set_theme(theme_name):
    session["theme"] = "dark" if theme_name == "dark" else "light"
    return redirect(request.referrer or url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
