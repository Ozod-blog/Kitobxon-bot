from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import User, Referral
from app.services.coin_service import change_coins
from app.config import get_settings

async def attach_referral(session: AsyncSession, new_user: User, inviter_telegram_id: int | None):
    if not inviter_telegram_id or inviter_telegram_id == new_user.telegram_id: return None
    inviter = await session.scalar(select(User).where(User.telegram_id == inviter_telegram_id))
    if not inviter or inviter.id == new_user.id: return None
    ref = Referral(inviter_id=inviter.id, invitee_id=new_user.id)
    session.add(ref); await session.flush()
    s = get_settings()
    if s.referral_reward_on and s.referral_reward_at == "registration":
        await change_coins(session, inviter.id, s.coins_per_referral_registration, "referral_registration",
            "Do‘st ro‘yxatdan o‘tdi", f"referral-reg:{ref.id}", "referral", ref.id)
        ref.registration_rewarded = True
    return ref

async def referral_stats(session: AsyncSession, user_id: int):
    count = await session.scalar(select(func.count(Referral.id)).where(Referral.inviter_id == user_id)) or 0
    total = await session.scalar(select(func.coalesce(func.sum(ReferralRegistration.amount), 0))) if False else 0
    return count, total
