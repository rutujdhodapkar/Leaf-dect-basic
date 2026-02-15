import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd

# ================= CONFIG ================= #

OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

LOCAL_LLM_URL = " https://e5dc-2401-4900-7c88-d450-445d-cf33-80bb-fa11.ngrok-free.app"
LOCAL_MODEL = "deepseek/deepseek-r1-0528-qwen3-8b"

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


def call_local_model(prompt):
    data = {
        "model": LOCAL_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }

    r = requests.post(LOCAL_LLM_URL, json=data, timeout=300)
    return r.json()["choices"][0]["message"]["content"]


# ================= DECISION ENGINE ================= #

def brain_decision(user_query):
    prompt = f"""
    Analyze this farm query:
    {user_query}

    Decide:
    - Weather duration needed (1 day, 3 months, 1 year, 5 years)
    - Whether soil report needed
    - Whether disease analysis needed
    - Whether pest analysis needed
    - Whether fertilizer pricing needed
    - Whether doctor search needed

    Output STRICT JSON.
    """
    return call_openrouter(MAIN_BRAIN, prompt)


# ================= MODULES ================= #

def weather_module(location, duration):
    prompt = f"Provide detailed weather analysis for {location} for {duration}"
    return call_openrouter(FAST_MODEL, prompt)


def soil_water_module(location):
    prompt = f"Provide soil chemistry and groundwater analysis for {location}"
    return call_openrouter(FAST_MODEL, prompt)


def plant_disease_detection(description):
    prompt = f"Identify plant and disease from this description: {description}"
    return call_local_model(prompt)


def disease_explanation(disease, weather, soil):
    prompt = f"""
    Disease: {disease}
    Weather context: {weather}
    Soil context: {soil}
    Explain biological cause and how weather and soil influenced it.
    """
    return call_openrouter(HEAVY_MODEL, prompt)


def full_disease_report(disease):
    return call_openrouter(
        HEAVY_MODEL,
        f"Generate full scientific crop pathology report for {disease}"
    )


def treatment_plan(report):
    return call_openrouter(
        HEAVY_MODEL,
        f"Generate irrigation schedule, fertilizer plan, water quantity, and monthly calendar plan based on: {report}"
    )


def pest_analysis(description):
    return call_openrouter(
        FAST_MODEL,
        f"Analyze pest or insect risk from this context: {description}"
    )


def fertilizer_price_search(plan, location):
    return call_openrouter(
        FAST_MODEL,
        f"Search fertilizer names in this plan: {plan}. Give online prices near {location}"
    )


def delivery_planner(price_report, location):
    return call_openrouter(
        FAST_MODEL,
        f"Plan full delivery logistics including total cost breakdown to {location}. Based on: {price_report}"
    )


def doctor_search(crop, location):
    return call_openrouter(
        FAST_MODEL,
        f"Search online agricultural doctors for {crop} near {location}. Include name, contact, education."
    )


# ================= STREAMLIT UI ================= #

st.set_page_config(layout="wide")
st.title("🌾 Autonomous Farm Intelligence System")

location = st.text_input("Farm Location")
query = st.text_area("Describe crop / issue / symptoms")
include_pests = st.checkbox("Include Pest Analysis")

if st.button("Execute Full Pipeline"):

    st.subheader("🧠 Brain Decision")
    decision = brain_decision(query)
    st.code(decision)

    st.subheader("🌦 Weather Intelligence")
    weather = weather_module(location, "1 year")
    st.write(weather)

    st.subheader("🌱 Soil & Water Intelligence")
    soil = soil_water_module(location)
    st.write(soil)

    st.subheader("🪴 Plant & Disease Detection (Local Model)")
    disease = plant_disease_detection(query)
    st.write(disease)

    st.subheader("🧬 Disease Explanation")
    explanation = disease_explanation(disease, weather, soil)
    st.write(explanation)

    st.subheader("📄 Full Scientific Disease Report")
    report = full_disease_report(disease)
    st.write(report)

    st.subheader("💧 Treatment & Irrigation Planning")
    plan = treatment_plan(report)
    st.write(plan)

    if include_pests:
        st.subheader("🐛 Pest Analysis")
        pest = pest_analysis(query)
        st.write(pest)

    st.subheader("💰 Fertilizer Price Search")
    prices = fertilizer_price_search(plan, location)
    st.write(prices)

    st.subheader("🚚 Delivery Planning")
    delivery = delivery_planner(prices, location)
    st.write(delivery)

    st.subheader("👨‍⚕️ Local Crop Doctors")
    doctors = doctor_search("crop", location)
    st.write(doctors)

    st.success("Full Autonomous Agricultural Intelligence Completed.")
