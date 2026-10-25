import pytest
from app.database.models import User
from app.services.referral_service import attach_referral
@pytest.mark.asyncio
async def test_self_referral_blocked(session):
    u=User(telegram_id=123,first_name="Ali",last_name="Valiyev",phone="+998901234567",region="Farg‘ona",district="Farg‘ona")
    session.add(u); await session.flush()
    assert await attach_referral(session,u,123) is None
