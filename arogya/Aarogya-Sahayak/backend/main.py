from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
import os
import logging

# Gemini LLM
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Real-time health modules
from realtime_health import (
    get_who_outbreaks,
    get_idsp_outbreaks,
    get_weather,
    calculate_disease_risk
)

# Logging setup
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")
WEATHER_KEY = os.getenv("WEATHER_API_KEY")

logging.info(f"Google Key Loaded: {GOOGLE_KEY is not None}")
logging.info(f"Weather Key Loaded: {WEATHER_KEY is not None}")

# FastAPI App
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    lat: float | None = None
    lon: float | None = None


# -------------------------
# Gemini MODEL Init
# -------------------------
model = None

def init_model():
    global model
    if not GOOGLE_KEY:
        logging.error("❌ GOOGLE_API_KEY missing")
        return

    try:
        model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_KEY,
            temperature=0.3,
        )
        logging.info("✅ Gemini model initialized successfully.")
    except Exception as e:
        model = None
        logging.error(f"❌ Gemini Init Error: {e}")


# -------------------------
# SYSTEM PROMPTS
# -------------------------
SYSTEM_PROMPT = SystemMessage(
    content=(
        "You are Arogya Sahayak, a reliable medical assistant. "
        "Give safe, simple, medically accurate guidance. "
        "Include health alerts and weather risk if provided. "
        "Encourage doctor consultation for serious symptoms."
    )
)

FOLLOWUP_PROMPT = SystemMessage(
    content=(
        "You are a medical assistant. Based on the user's symptoms, "
        "generate 2 to 4 short follow-up questions to understand their condition better. "
        "Ask ONLY questions, no advice. Keep them short and relevant."
    )
)


# -------------------------
# STARTUP EVENT
# -------------------------
@app.on_event("startup")
def _startup():
    init_model()


# -------------------------
# HEALTH CHECK ROUTE
# -------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "gemini_initialized": model is not None,
        "google_key": GOOGLE_KEY is not None,
        "weather_key": WEATHER_KEY is not None,
    }


# -------------------------
# MAIN CHAT ROUTE
# -------------------------
@app.post("/chat")
def chat(req: ChatRequest):

    if model is None:
        return {"error": "Gemini model not initialized"}

    final_alert_data = ""

    # 1️⃣ WHO + IDSP outbreak data
    try:
        who = get_who_outbreaks()
        idsp = get_idsp_outbreaks()

        if who or idsp:
            final_alert_data += "🌍 **Real-Time Health Alerts:**\n"
            for x in who[:3]:
                final_alert_data += f"- {x['title']} ({x['country']})\n"
            for h in idsp[:3]:
                final_alert_data += f"- **IDSP India:** {h}\n"
            final_alert_data += "\n"

    except Exception as e:
        logging.error(f"Outbreak Error: {e}")

    # 2️⃣ Weather-based risk
    if req.lat and req.lon:
        try:
            weather = get_weather(req.lat, req.lon, WEATHER_KEY)
            risks = calculate_disease_risk(weather)

            if risks:
                final_alert_data += "📍 **Health Risks in Your Area:**\n"
                for r in risks:
                    final_alert_data += f"- {r}\n"
                final_alert_data += "\n"

        except Exception as e:
            logging.error(f"Weather Risk Error: {e}")

    # 3️⃣ FOLLOW-UP QUESTION GENERATION
    try:
        followup_questions = model.invoke([
            FOLLOWUP_PROMPT,
            HumanMessage(content=req.message)
        ]).content

    except Exception as e:
        logging.error(f"Follow-up Error: {e}")
        followup_questions = ""

    # 4️⃣ FINAL MEDICAL ANSWER
    try:
        full_prompt = (
            final_alert_data +
            "\n📝 Follow-up questions to understand better:\n" +
            followup_questions +
            "\n\n---\nUser Query: " + req.message
        )

        reply = model.invoke([
            SYSTEM_PROMPT,
            HumanMessage(content=full_prompt)
        ])

        final_response = (
            "🤖 **Before I give full advice, please answer these questions:**\n"
            + followup_questions +
            "\n---\n" +
            reply.content
        )

    except Exception as e:
        logging.error(f"LLM Error: {e}")
        return {"error": str(e), "alerts_collected": final_alert_data}

    return {"reply": final_response}
