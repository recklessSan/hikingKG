# Card Parser Bot

Telegram-бот для аналитики партий карт: читает 3 рабочих чата, кладёт в БД **только агрегаты** и отдаёт отчёт по команде и по расписанию.

Номера карт, балансы по строкам и прочие PAN-данные **не сохраняются**. Перед записью текст красноруется.

## Что разбирается

### Чат 1 — поступления

Из сообщения берутся:

- банк
- количество (`N шт`)
- флаги `КЭШ`, `БЕЗ ЛК`, `❗️`
- код партии вроде `F1701092026`
- автор и дата/время сообщения
- если есть хвост: вход в ЛК, внесение, «в работу»

Строки с номерами карт игнорируются.

### Чат 2 — движение по офисам

Разбирается **только** блок `ПЕРЕДАНО В Т-ОФИС`. Остальные секции (курьер, резерв, проверка, Р-офис) пропускаются.

### Чат 3

Формат третьего чата в постановке не был задан. По умолчанию `CHAT_3_MODE=auto`: сначала пробуется парсер чата 1, затем чата 2. Можно зафиксировать `chat1` или `chat2`.

## Локальный запуск

Нужны Python 3.12 и виртуальное окружение:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

В `.env` укажи `BOT_TOKEN`, id чатов и `ADMIN_CHAT_ID`. Без webhook бот идёт через long polling:

```bash
python -m bot
```

Проверка парсеров без Telegram:

```bash
python -m bot demo
python -m bot parse --chat 1 --file message.txt
pytest
```

Локально по умолчанию SQLite (`data/bot.db`). На Heroku используется Postgres из `DATABASE_URL`.

## Команды

Доступны в админ-чате или пользователям из `ADMIN_USER_IDS`:

| Команда | Смысл |
| --- | --- |
| `/today` | отчёт за сегодня |
| `/week` | последние 7 дней |
| `/stats` | вся накопленная аналитика |
| `/toffice` | только передачи в Т-офис |
| `/report 07.09.2026` | конкретный день |
| `/report 01.09.2026 07.09.2026` | период |
| `/chatid` | id текущего чата (удобно при настройке) |

Ежедневный отчёт уходит в `ADMIN_CHAT_ID` в `REPORT_HOUR:REPORT_MINUTE` по `TIMEZONE` (по умолчанию 21:00 Europe/Moscow).

## Настройка Telegram

1. Создай бота в [@BotFather](https://t.me/BotFather).
2. Выключи privacy mode: `/setprivacy` → Disable — иначе бот не увидит сообщения в группах.
3. Добавь бота в три исходных чата и в чат для отчётов.
4. В каждом чате отправь `/chatid` и пропиши значения в env.

## Heroku

```bash
heroku create <app-name>
heroku addons:create heroku-postgresql:essential-0
heroku config:set BOT_TOKEN=...
heroku config:set CHAT_1_ID=...
heroku config:set CHAT_2_ID=...
heroku config:set CHAT_3_ID=...
heroku config:set ADMIN_CHAT_ID=...
heroku config:set ADMIN_USER_IDS=123,456
heroku config:set WEBHOOK_URL=https://<app-name>.herokuapp.com
git push heroku main
```

Если `WEBHOOK_URL` задан, процесс `web` поднимает webhook на `$PORT`. Если нет — polling плюс `/` health-check на `$PORT`, чтобы web-dyno не уснул с ошибкой boot.

`Procfile`:

```
web: python -m bot
```

## Переменные окружения

| Переменная | Назначение |
| --- | --- |
| `BOT_TOKEN` | токен BotFather |
| `DATABASE_URL` | SQLite локально, Postgres на Heroku |
| `CHAT_1_ID` / `CHAT_2_ID` / `CHAT_3_ID` | исходные чаты |
| `CHAT_3_MODE` | `auto`, `chat1` или `chat2` |
| `ADMIN_CHAT_ID` | чат для отчётов и команд |
| `ADMIN_USER_IDS` | user id через запятую |
| `TIMEZONE` | `Europe/Moscow` |
| `REPORT_HOUR` / `REPORT_MINUTE` | время ежедневного отчёта |
| `WEBHOOK_URL` | публичный URL на Heroku |

## Чего бот не делает

- не пишет в БД номера карт
- не считает балансы по конкретным картам
- не хранит исходное сообщение целиком, только короткий excerpt без PAN
