from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Gift, GiftOrder, User
from app.services.coin_service import change_coins, CoinError

async def create_order(session: AsyncSession, user_id: int, gift_id: int):
    gift = await session.scalar(select(Gift).where(Gift.id == gift_id, Gift.is_active.is_(True)).with_for_update())
    if not gift or gift.stock < 1: raise ValueError("Bu sovg‘a hozir mavjud emas.")
    user = await session.get(User, user_id)
    if not user or user.coins < gift.price: raise CoinError("Tanga balansingiz yetarli emas.")
    # Reserve stock and coins at creation; reject restores both.
    gift.stock -= 1
    order = GiftOrder(user_id=user_id, gift_id=gift.id, price_each=gift.price, status="pending")
    session.add(order); await session.flush()
    await change_coins(session, user_id, -gift.price, "gift_reservation", "Sovg‘a buyurtmasi uchun rezerv",
                       f"gift-order:{order.id}:reserve", "gift_order", order.id)
    return order

async def update_order_status(session: AsyncSession, order_id: int, status: str):
    if status not in {"approved", "rejected", "fulfilled"}: raise ValueError("Buyurtma holati noto‘g‘ri.")
    order = await session.scalar(select(GiftOrder).where(GiftOrder.id == order_id).with_for_update())
    if not order: raise ValueError("Buyurtma topilmadi.")
    if order.status == status: return order
    if order.status != "pending": raise ValueError("Faqat pending buyurtmani o‘zgartirish mumkin.")
    if status == "rejected":
        gift = await session.get(Gift, order.gift_id)
        gift.stock += order.quantity
        await change_coins(session, order.user_id, order.price_each * order.quantity, "gift_refund",
                           "Sovg‘a buyurtmasi rad etildi", f"gift-order:{order.id}:refund", "gift_order", order.id)
    order.status = status
    await session.flush()
    return order
