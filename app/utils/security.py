from app.config import get_settings
def is_admin(telegram_id: int | None) -> bool:
    return telegram_id is not None and telegram_id in get_settings().admin_ids
