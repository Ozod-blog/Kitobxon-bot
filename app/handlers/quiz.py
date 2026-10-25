import json, logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from app.database.models import User, Quiz, QuizQuestion, QuizAttempt
from app.services.quiz_service import create_quiz, submit_answers
from app.keyboards.inline import quiz_option_keyboard

logger = logging.getLogger(__name__)
router = Router()

async def launch_quiz(message, session, user, reading, state: FSMContext | None = None):
    try:
        quiz, questions = await create_quiz(session, reading.id, user.id)
    except Exception as e:
        logger.warning("Quiz creation failed user_id=%s error_type=%s", user.id, type(e).__name__)
        await message.answer("Test yaratilmadi. Tanlangan sahifalar matni va AI sozlamalarini tekshiring. Keyin /test orqali qayta urinib ko‘ring.")
        return
    if state is None:
        await message.answer("Test yaratildi, ammo savollarni davom ettirish uchun /test buyrug‘ini yuboring.")
        return
    await state.set_data({
        "active_quiz_id": quiz.id,
        "quiz_question_ids": [q.id for q in questions],
        "quiz_answers": {},
        "quiz_position": 0,
    })
    await message.answer(f"📝 Test #{quiz.id} boshlandi. Har savolga javob bering.")
    await _send_current_question(message, session, quiz.id, questions[0].id)

async def _send_current_question(target, session, quiz_id: int, question_id: int):
    q = await session.get(QuizQuestion, question_id)
    if not q:
        await target.answer("Savol topilmadi. /test orqali qayta urinib ko‘ring.")
        return
    await target.answer(
        f"Savol {q.position + 1}/5:\n{q.question}",
        reply_markup=quiz_option_keyboard(quiz_id, q.id, json.loads(q.options_json))
    )

@router.callback_query(F.data.startswith("ans:"))
async def answer_question(callback: CallbackQuery, session, state: FSMContext):
    try:
        _, quiz_raw, question_raw, option_raw = callback.data.split(":")
        quiz_id, question_id, option = int(quiz_raw), int(question_raw), int(option_raw)
    except (ValueError, AttributeError):
        await callback.answer("Noto‘g‘ri so‘rov.", show_alert=True)
        return
    user = await session.scalar(select(User).where(User.telegram_id == callback.from_user.id))
    if not user or user.is_banned:
        await callback.answer("Akkauntdan foydalanish mumkin emas.", show_alert=True)
        return
    quiz = await session.get(Quiz, quiz_id)
    question = await session.get(QuizQuestion, question_id)
    data = await state.get_data()
    if (not quiz or quiz.user_id != user.id or not question or question.quiz_id != quiz.id
        or data.get("active_quiz_id") != quiz_id):
        await callback.answer("Bu test sizga tegishli emas yoki faol emas.", show_alert=True)
        return
    old_attempt = await session.scalar(select(QuizAttempt).where(QuizAttempt.quiz_id == quiz_id))
    if old_attempt:
        await callback.answer("Test yakunlangan.", show_alert=True)
        return
    question_ids = data.get("quiz_question_ids", [])
    position = data.get("quiz_position", 0)
    if position >= len(question_ids) or question_ids[position] != question_id:
        await callback.answer("Bu savolga allaqachon javob berilgan yoki navbat emas.", show_alert=True)
        return
    options = json.loads(question.options_json)
    if not 0 <= option < len(options):
        await callback.answer("Variant noto‘g‘ri.", show_alert=True)
        return
    answers = data.get("quiz_answers", {})
    answers[str(question_id)] = option
    position += 1
    await state.update_data(quiz_answers=answers, quiz_position=position)
    await callback.answer("Javob qabul qilindi.")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    if position < len(question_ids):
        await _send_current_question(callback.message, session, quiz_id, question_ids[position])
        return
    try:
        selected = {int(k): int(v) for k, v in answers.items()}
        correct, passed, coins = await submit_answers(session, quiz_id, user.id, selected)
        await state.clear()
        await callback.message.answer(
            f"📊 Test yakunlandi!\nTo‘g‘ri javoblar: {correct}/5\n"
            f"Noto‘g‘ri javoblar: {5-correct}/5\n"
            f"Natija: {'✅ Muvaffaqiyatli' if passed else '❌ O‘tilmadi'}"
            + (f"\n🪙 Mukofot: {coins} tanga" if passed else "")
        )
    except Exception as e:
        logger.warning("Quiz submission failed quiz_id=%s error_type=%s", quiz_id, type(e).__name__)
        await callback.message.answer("Natijani saqlashda xatolik yuz berdi. Administratorga murojaat qiling.")

@router.message(F.text.startswith("/javoblar"))
async def answer_help(message: Message):
    await message.answer("Test savollariga inline tugmalar orqali ketma-ket javob bering. Test yakunida natija avtomatik hisoblanadi.")
