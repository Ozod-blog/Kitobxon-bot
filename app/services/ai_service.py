import asyncio
import json
import logging
from pydantic import BaseModel, Field, ValidationError
from app.config import get_settings

class GeneratedQuestion(BaseModel):
    question: str = Field(min_length=8, max_length=1000)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3)

class GeneratedQuiz(BaseModel):
    questions: list[GeneratedQuestion] = Field(min_length=5, max_length=5)

logger = logging.getLogger(__name__)

class AIError(RuntimeError):
    """Foydalanuvchiga ko‘rsatish xavfsiz bo‘lgan AI xatosi."""

def explain_ai_error(e: Exception) -> str:
    t = str(e)
    if "429" in t or "RESOURCE_EXHAUSTED" in t or "quota" in t.lower():
        return "AI kunlik limiti tugadi. Birozdan keyin yoki ertaga qayta urinib ko‘ring."
    if "API key" in t or "API_KEY" in t or "PERMISSION_DENIED" in t or "UNAUTHENTICATED" in t or "403" in t:
        return "AI kaliti noto‘g‘ri yoki ruxsati yo‘q. Administrator GEMINI_API_KEY ni tekshirsin."
    if "NOT_FOUND" in t or "404" in t:
        return "AI modeli topilmadi. Administrator AI_MODEL sozlamasini tekshirsin."
    if "503" in t or "UNAVAILABLE" in t or "overloaded" in t.lower():
        return "AI hozir band. Birozdan keyin qayta urinib ko‘ring."
    return "AI test yarata olmadi. Birozdan keyin qayta urinib ko‘ring."
# Google eski modellarni o‘chirib turadi, shuning uchun zaxira ro‘yxat bor.
# Aniq model kerak bo‘lsa .env faylida AI_MODEL=... deb yozing.
GEMINI_MODELS = ["gemini-3.8-flash", "gemini-flash-latest", "gemini-2.5-flash"]

PROMPT = """Quyidagi manba matnigagina asoslanib, aynan 5 ta o‘zaro farqli test savoli tuz.
Har savolda aynan 4 variant va bitta to‘g‘ri variant bo‘lsin. Manbada yo‘q faktlarni to‘qima.
Faqat JSON qaytar: {"questions":[{"question":"...","options":["...","...","...","..."],"correct_index":0}]}
MANBA:
"""
async def generate_quiz(source_text: str) -> GeneratedQuiz:
    if not source_text.strip():
        raise ValueError("Tanlangan sahifalar uchun kitob matni biriktirilmagan.")
    settings = get_settings()
    raw = ""
    if settings.ai_provider == "openai":
        if not settings.openai_api_key: raise AIError("OpenAI API kaliti sozlanmagan.")
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model=settings.ai_model or "gpt-4o-mini",
            messages=[{"role":"system","content":"Siz manbaga sodiq test yaratuvchisiz. Faqat JSON qaytaring."},
                      {"role":"user","content":PROMPT + source_text[:30000]}],
            response_format={"type":"json_object"}, temperature=0.3)
        raw = response.choices[0].message.content or ""
    else:
        if not settings.gemini_api_key: raise AIError("Gemini API kaliti sozlanmagan.")
        from google import genai
        client = genai.Client(api_key=settings.gemini_api_key)
        models = [settings.ai_model] if settings.ai_model else GEMINI_MODELS
        last_error = None
        for model in models:
            for attempt in range(3):
                try:
                    response = await client.aio.models.generate_content(
                        model=model,
                        contents=PROMPT + source_text[:30000],
                        config={"response_mime_type":"application/json"})
                    raw = response.text or ""
                    break
                except Exception as e:
                    last_error = e
                    logger.warning("Gemini model %s ishlamadi (urinish %s/3): %s", model, attempt + 1, e)
                    busy = any(k in str(e) for k in ("503", "UNAVAILABLE", "overloaded"))
                    if busy and attempt < 2:
                        await asyncio.sleep(2 * (attempt + 1))  # band bo‘lsa, shu modelni biroz kutib qayta sinaymiz
                        continue
                    break
            if raw:
                break
            # Model topilmasa, limiti tugasa yoki band bo‘lsa — keyingi modelni sinaymiz.
            # Kalit xatosi (400/403) bo‘lsa to‘xtaymiz.
            if not any(k in str(last_error) for k in ("NOT_FOUND", "404", "429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE")):
                break
        if not raw:
            raise AIError(explain_ai_error(last_error or RuntimeError(""))) from last_error
    try:
        parsed = GeneratedQuiz.model_validate(json.loads(raw))
        if any(len(set(x.strip() for x in q.options)) != 4 for q in parsed.questions):
            raise AIError("AI noto‘g‘ri test yaratdi. Qayta urinib ko‘ring.")
        return parsed
    except (json.JSONDecodeError, ValidationError) as e:
        raise AIError("AI testni to‘g‘ri formatda yarata olmadi. Qayta urinib ko‘ring.") from e
