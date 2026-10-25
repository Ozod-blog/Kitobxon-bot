import pytest
from app.database.models import User
from app.services.coin_service import change_coins, CoinError
@pytest.mark.asyncio
async def test_coin_change_and_idempotency(session):
    u=User(telegram_id=123,first_name="Ali",last_name="Valiyev",phone="+998901234567",region="Farg‘ona",district="Farg‘ona")
    session.add(u); await session.flush()
    assert await change_coins(session,u.id,10,"test","test","once")
    assert not await change_coins(session,u.id,10,"test","test","once")
    assert u.coins==10
    with pytest.raises(CoinError): await change_coins(session,u.id,-20,"test","test")
