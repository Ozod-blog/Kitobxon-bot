import pytest
from app.services.user_service import register_user
@pytest.mark.asyncio
async def test_registration_and_unique_telegram(session):
    data=dict(telegram_id=123,first_name="Ali",last_name="Valiyev",phone="+998901234567",region="Farg‘ona",district="Farg‘ona")
    user=await register_user(session,**data)
    assert user.id is not None
    with pytest.raises(ValueError): await register_user(session,**data)
