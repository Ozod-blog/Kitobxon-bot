from functools import lru_cache
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    bot_token: str = Field(alias="BOT_TOKEN")
    bot_username: str = Field(default="", alias="BOT_USERNAME")
    admin_ids_raw: str = Field(default="", alias="ADMIN_IDS")
    database_url: str = Field(default="sqlite+aiosqlite:///./kitobxon.db", alias="DATABASE_URL")
    ai_provider: str = Field(default="gemini", alias="AI_PROVIDER")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    ai_model: str = Field(default="", alias="AI_MODEL")
    coins_per_passed_quiz: int = Field(default=10, ge=0, alias="COINS_PER_PASSED_QUIZ")
    coins_per_referral_registration: int = Field(default=10, ge=0, alias="COINS_PER_REFERRAL_REGISTRATION")
    coins_per_referral_first_passed_quiz: int = Field(default=20, ge=0, alias="COINS_PER_REFERRAL_FIRST_PASSED_QUIZ")
    referral_reward_on: bool = Field(default=True, alias="REFERRAL_REWARD_ON")
    referral_reward_at: str = Field(default="registration", alias="REFERRAL_REWARD_AT")
    min_seconds_per_page: int = Field(default=30, gt=0, alias="MIN_SECONDS_PER_PAGE")
    quiz_question_count: int = Field(default=5, gt=0, alias="QUIZ_QUESTION_COUNT")
    quiz_pass_score: int = Field(default=4, ge=1, alias="QUIZ_PASS_SCORE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    run_bot: bool = Field(default=False, alias="RUN_BOT")  # True bo‘lsa, bot WebApp bilan bitta jarayonda ishlaydi (Render)

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, v):
        # Neon/Supabase/Render beradigan postgres:// manzillarini asyncpg uchun moslaydi.
        v = v.strip()
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://"):]
        if v.startswith("postgresql://"):
            v = "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v

    @field_validator("ai_provider")
    @classmethod
    def valid_provider(cls, v):
        v = v.lower().strip()
        if v not in {"gemini", "openai"}:
            raise ValueError("AI_PROVIDER faqat 'gemini' yoki 'openai' bo‘lishi mumkin.")
        return v

    @field_validator("referral_reward_at")
    @classmethod
    def valid_referral_mode(cls, v):
        if v not in {"registration", "first_passed_quiz"}:
            raise ValueError("REFERRAL_REWARD_AT: registration yoki first_passed_quiz bo‘lishi kerak.")
        return v

    @property
    def admin_ids(self) -> set[int]:
        try:
            return {int(x.strip()) for x in self.admin_ids_raw.split(",") if x.strip()}
        except ValueError as e:
            raise ValueError("ADMIN_IDS vergul bilan ajratilgan Telegram ID raqamlari bo‘lishi kerak.") from e

    @model_validator(mode="after")
    def validate_config(self):
        if not self.bot_token.strip():
            raise ValueError("BOT_TOKEN .env faylida kiritilishi shart.")
        if self.ai_provider == "gemini" and not self.gemini_api_key:
            # AI kaliti yo‘qligida bot ishlashi mumkin, test yaratish foydalanuvchiga xavfsiz xato beradi.
            pass
        if self.quiz_pass_score > self.quiz_question_count:
            raise ValueError("QUIZ_PASS_SCORE savollar sonidan katta bo‘la olmaydi.")
        return self

@lru_cache
def get_settings() -> Settings:
    return Settings()
