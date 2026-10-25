from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import User, CoinTransaction

class CoinError(ValueError): pass

async def change_coins(session: AsyncSession, user_id: int, amount: int, operation_type: str,
                       reason: str, idempotency_key: str | None = None,
                       reference_type: str | None = None, reference_id: int | None = None) -> bool:
    """Centralized balance mutation. Returns False if idempotency key was already processed."""
    if amount == 0: return True
    if idempotency_key:
        old = await session.scalar(select(CoinTransaction).where(CoinTransaction.idempotency_key == idempotency_key))
        if old: return False
    user = await session.scalar(select(User).where(User.id == user_id).with_for_update())
    if user is None: raise CoinError("Foydalanuvchi topilmadi.")
    if user.coins + amount < 0: raise CoinError("Tanga yetarli emas.")
    user.coins += amount
    session.add(CoinTransaction(user_id=user_id, amount=amount, operation_type=operation_type,
        reason=reason, idempotency_key=idempotency_key, reference_type=reference_type, reference_id=reference_id))
    await session.flush()
    return True
