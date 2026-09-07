from bot.config import Settings


def test_postgres_url_is_converted_to_asyncpg():
    settings = Settings(database_url="postgres://user:pass@host:5432/db")
    assert settings.sqlalchemy_url() == "postgresql+asyncpg://user:pass@host:5432/db"


def test_admin_ids_from_csv():
    settings = Settings(admin_user_ids="1, 2, 3")
    assert settings.admin_user_ids == [1, 2, 3]


def test_chat_ids_mapping():
    settings = Settings(chat_1_id=-1001, chat_2_id=-1002, chat_3_id=-1003)
    assert settings.chat_ids() == {"chat1": -1001, "chat2": -1002, "chat3": -1003}
