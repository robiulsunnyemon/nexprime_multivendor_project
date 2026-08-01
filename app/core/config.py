import cloudinary
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str

    JWT_SECRET: str = "change-me-in-production"
    JWT_EXPIRE_DAYS: int = 7
    JWT_REFRESH_SECRET: str = "change-me-refresh-in-production"
    JWT_REFRESH_EXPIRE_DAYS: int = 30

    OTP_EXPIRE_MINUTES: int = 5

    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASS: str
    EMAIL_FROM: str

    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_CONNECT_RETURN_URL: str = "nexprime://stripe-callback"
    STRIPE_CONNECT_REFRESH_URL: str = "nexprime://stripe-refresh"

    LIVEKIT_URL: str = "wss://dummy.livekit.cloud"
    LIVEKIT_API_KEY: str = "dummy_key"
    LIVEKIT_API_SECRET: str = "dummy_secret"

    SENDGRID_API_KEY:str
    SENDGRID_EMAIL_FROM:str

    class Config:
        env_file = ".env"


settings = Settings()

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)