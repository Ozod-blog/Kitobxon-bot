import pytest
from app.database.models import User, Gift
from app.services.gift_service import create_order, update_order_status
@pytest.mark.asyncio
async def test_gift_rejection_refunds(session):
    u=User(telegram_id=123,first_name="Ali",last_name="Valiyev",phone="+998901234567",region="Farg‘ona",district="Farg‘ona",coins=50)
    g=Gift(name="Daftar",description="",price=20,stock=1)
    session.add_all([u,g]); await session.flush()
    o=await create_order(session,u.id,g.id)
    assert u.coins==30 and g.stock==0
    await update_order_status(session,o.id,"rejected")
    assert u.coins==50 and g.stock==1
