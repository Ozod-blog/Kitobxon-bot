import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Quiz, QuizQuestion, QuizAttempt, QuizAnswer, ReadingSession, User, Referral
from app.services.ai_service import generate_quiz
from app.services.reading_service import remaining_seconds, source_for_session
from app.services.coin_service import change_coins
from app.config import get_settings

async def _quiz_questions(session: AsyncSession, quiz_id: int):
    return list((await session.scalars(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id)
                                       .order_by(QuizQuestion.position))).all())

async def create_quiz(session: AsyncSession, reading_id: int, user_id: int):
    reading = await session.get(ReadingSession, reading_id)
    if not reading or reading.user_id != user_id: raise ValueError("O‘qish sessiyasi topilmadi.")
    if reading.status != "active": raise ValueError("Bu sessiya faol emas.")
    if await remaining_seconds(reading) > 0: raise ValueError("Minimal o‘qish vaqti hali tugamadi.")
    existing = await session.scalar(select(Quiz).where(Quiz.reading_session_id == reading_id))
    if existing:
        # Test yaratilgan, lekin foydalanuvchi uni topshirmagan bo‘lishi mumkin (oyna yopilgan,
        # internet uzilgan va h.k.). Yangi test yaratmasdan, o‘sha testni qaytaramiz.
        if await session.scalar(select(QuizAttempt).where(QuizAttempt.quiz_id == existing.id)):
            raise ValueError("Bu sessiya uchun test allaqachon topshirilgan.")
        rows = await _quiz_questions(session, existing.id)
        if rows: return existing, rows
        raise ValueError("Bu sessiya uchun test allaqachon yaratilgan.")
    source = await source_for_session(session, reading)
    if not source: raise ValueError("Tanlangan sahifalarning to‘liq matnini administrator biriktirishi kerak.")
    generated = await generate_quiz(source)
    quiz = Quiz(user_id=user_id, reading_session_id=reading_id, book_id=reading.book_id)
    session.add(quiz); await session.flush()
    for i, q in enumerate(generated.questions):
        session.add(QuizQuestion(quiz_id=quiz.id, position=i, question=q.question,
            options_json=json.dumps(q.options, ensure_ascii=False), correct_index=q.correct_index))
    await session.flush()
    # Saqlangan savollar (id va options_json bilan) qaytariladi: web va bot shularni ishlatadi.
    return quiz, await _quiz_questions(session, quiz.id)

async def submit_answers(session: AsyncSession, quiz_id: int, user_id: int, selected: dict[int,int]):
    quiz = await session.get(Quiz, quiz_id)
    if not quiz or quiz.user_id != user_id: raise ValueError("Test topilmadi.")
    old = await session.scalar(select(QuizAttempt).where(QuizAttempt.quiz_id == quiz_id))
    if old: raise ValueError("Bu test javoblari allaqachon yuborilgan.")
    questions = list((await session.scalars(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id).order_by(QuizQuestion.position))).all())
    if len(questions) != 5 or set(selected) != {q.id for q in questions}: raise ValueError("Barcha 5 savolga javob bering.")
    correct = sum(1 for q in questions if selected[q.id] == q.correct_index)
    settings = get_settings()
    passed = correct >= settings.quiz_pass_score
    attempt = QuizAttempt(quiz_id=quiz_id, user_id=user_id, correct_count=correct, passed=passed,
                          coins_awarded=0)
    session.add(attempt); await session.flush()
    for q in questions:
        session.add(QuizAnswer(attempt_id=attempt.id, question_id=q.id, selected_index=selected[q.id],
                               is_correct=(selected[q.id] == q.correct_index)))
    reading = await session.get(ReadingSession, quiz.reading_session_id)
    reading.status = "completed"
    reading.completed_at = reading.completed_at or __import__("app.database.models", fromlist=["utcnow"]).utcnow()
    user = await session.get(User, user_id)
    user.total_pages += reading.page_count
    if passed:
        await change_coins(session, user_id, settings.coins_per_passed_quiz, "quiz_reward",
                           "Testdan muvaffaqiyatli o‘tish", f"quiz:{quiz_id}", "quiz", quiz_id)
        attempt.coins_awarded = settings.coins_per_passed_quiz
        ref = await session.scalar(select(Referral).where(Referral.invitee_id == user_id))
        if ref and not ref.quiz_rewarded and settings.referral_reward_on:
            await change_coins(session, ref.inviter_id, settings.coins_per_referral_first_passed_quiz,
                "referral_quiz_reward", "Taklif qilingan do‘st birinchi testdan o‘tdi",
                f"referral-quiz:{ref.id}", "referral", ref.id)
            ref.quiz_rewarded = True
    quiz.status = "completed"
    await session.flush()
    return correct, passed, settings.coins_per_passed_quiz if passed else 0
