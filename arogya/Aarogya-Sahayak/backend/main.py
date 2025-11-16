from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
import pdfplumber  # NEW ✔ PDF READER

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

# Logging
logging.basicConfig(level=logging.INFO)

# Load ENV variables
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")
WEATHER_KEY = os.getenv("WEATHER_API_KEY")

logging.info(f"Google Key Loaded: {GOOGLE_KEY is not None}")
logging.info(f"Weather Key Loaded: {WEATHER_KEY is not None}")

# Store uploaded report
uploaded_report_text = ""   # NEW ✔

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
# GEMINI MODEL INIT
# -------------------------
model = None

def init_model():
    global model
    try:
        model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_KEY,
            temperature=0.3,
        )
        logging.info("✅ Gemini model initialized successfully.")
    except Exception as e:
        logging.error(f"❌ Gemini initialization error: {e}")
        model = None

SYSTEM_PROMPT = SystemMessage(
    content=(
        "You are Arogya Sahayak, a safe multilingual medical assistant. "
        "Always respond in SAME language as the user. "
        "Give medically accurate, simple guidance. "
        "Ask 2–3 follow-up questions for clarity. "
        "Encourage doctor consultation for serious symptoms."
    )
)

@app.on_event("startup")
def _startup():
    init_model()

@app.get("/health")
def health():
    return {
        "status": "ok",
        "gemini_initialized": model is not None,
        "google_key": GOOGLE_KEY is not None,
        "weather_key": WEATHER_KEY is not None,
    }

# ------------------------------------------------
# 📌 NEW ENDPOINT → UPLOAD LAB REPORT (PDF)
# ------------------------------------------------
@app.post("/upload-report")
async def upload_report(file: UploadFile = File(...)):
    global uploaded_report_text

    if not file.filename.lower().endswith(".pdf"):
        return {"error": "Only PDF files allowed"}

    try:
        text = ""
        with pdfplumber.open(file.file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        uploaded_report_text = text  # store in memory

        return {
            "status": "PDF processed successfully ✔",
            "characters_extracted": len(text)
        }

    except Exception as e:
        logging.error(f"PDF Error: {e}")
        return {"error": str(e)}

# ------------------------------------------------
# 📌 MAIN CHAT ENDPOINT
# ------------------------------------------------
@app.post("/chat")
def chat(req: ChatRequest):
    if model is None:
        return {"error": "Gemini model not initialized"}

    final_alerts = ""

    # Determine if user's question is related to infectious disease / outbreaks
    def _message_is_health_related(message: str) -> bool:
        if not message:
            return False
        m = message.lower()
        keywords = [
            'fever','dengue','malaria','covid','coronavirus','influenza','flu','cholera',
            'measles','outbreak','epidemic','symptom','symptoms','infection','infectious',
            'diarrhea','diarrhoea','vomit','vomiting','rash','cough','breath','pneumonia',
            'mosquito','vector','cases','vaccine','vaccination','hospital','icu','death',
            'jaundice','typhoid','hepatitis','ebola'
        ]
        return any(k in m for k in keywords)

    user_relevant = _message_is_health_related(req.message)

    # 1. WHO + IDSP Outbreak Data (only include when relevant)
    try:
        who = get_who_outbreaks()
        idsp = get_idsp_outbreaks()

        if user_relevant and (who or idsp):
            final_alerts += "🌍 **Real-Time Health Alerts:**\n"
            for x in who[:3]:
                final_alerts += f"- {x.get('title','Unknown')} ({x.get('country','')})\n"
            for h in idsp[:3]:
                final_alerts += f"- **IDSP India:** {h}\n"
            final_alerts += "\n"

        # If not directly relevant, keep final_alerts empty so it won't appear in prompt.

    except Exception as e:
        logging.error(f"Outbreak error: {e}")

    # 2. Weather Risk
    if req.lat and req.lon and user_relevant:
        try:
            weather = get_weather(req.lat, req.lon, WEATHER_KEY)
            risks = calculate_disease_risk(weather)

            if risks:
                final_alerts += "📍 **Health Risks in Your Area:**\n"
                for r in risks:
                    final_alerts += f"- {r}\n"
                final_alerts += "\n"
        except Exception as e:
            logging.error(f"Weather Error: {e}")

    # 3. PDF Context (Very important!)
    pdf_context = ""
    if uploaded_report_text.strip():
        pdf_context = (
            "📄 **Patient Lab Report Extracted Text:**\n" +
            uploaded_report_text[:5000] +  # limit to avoid huge prompts
            "\n\n"
        )

    # 4. Build Final Prompt: include alerts only when present
    prompt_sections = [
        "Detect language and respond ONLY in that language.",
        "\n=== LAB REPORT (if uploaded) ===",
        pdf_context
    ]

    if final_alerts.strip():
        prompt_sections += ["\n=== HEALTH ALERTS ===", final_alerts]

    prompt_sections += ["\n=== USER QUESTION ===", req.message, "\nNow give medical guidance + ask follow-up questions."]

    prompt = "\n".join(prompt_sections)

    # 5. LLM Response
    try:
        reply = model.invoke([
            SYSTEM_PROMPT,
            HumanMessage(content=prompt)
        ])
        return {"reply": reply.content}

    except Exception as e:
        logging.error(f"LLM Error: {e}")
        return {"error": str(e), "alerts": final_alerts}
