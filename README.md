# Card Parser Bot

Telegram-бот для аналитики партий и проверки телефонов из чата 1 по справочнику. Отчёт — по команде и по расписанию. Подходит для локального запуска и Heroku.

16-значные PAN-подобные последовательности **не сохраняются**. В чате 1 в список попадают только телефоны (10–11 цифр, `+7` / `8` / `9…`).

## Что разбирается

### Чат 1 — поступления и телефоны

Из сообщения берутся:

- банк, количество (`N шт`), флаги `КЭШ` / `БЕЗ ЛК` / `❗️`, код партии
- автор и дата/время сообщения
- список телефонов
- каждый телефон сверяется со справочником: есть / нет в базе
- если есть хвост: вход в ЛК, внесение, «в работу»

### Чат 2 — движение по офисам

Разбирается **только** блок `ПЕРЕДАНО В Т-ОФИС`.

### Чат 3

`CHAT_3_MODE=auto`: сначала парсер чата 1, затем чата 2.

## Справочник телефонов

CSV со столбцами `phone,label` (см. `phones.example.csv`). Нормализация: `8 900 111-22-33` и `+7 900 111-22-33` → `79001112233`.

Как наполнить базу:

1. Файл `PHONES_FILE` (по умолчанию `phones.csv`) — подхватывается при старте и командой `/phones_reload`
2. `/phones_add +7 900 123-45-67 метка`
3. Прислать `.csv` в админ-чат

## Локальный запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cp phones.example.csv phones.csv
python -m bot demo
python -m bot
pytest
```

## Команды

| Команда | Смысл |
| --- | --- |
| `/today` | отчёт за сегодня |
| `/week` | последние 7 дней |
| `/stats` | вся аналитика |
| `/toffice` | только Т-офис |
| `/phones` | проверка телефонов за сегодня |
| `/check 79001234567` | найти номер в справочнике |
| `/phones_add 79001234567 метка` | добавить в справочник |
| `/phones_reload` | загрузить CSV |
| `/report 07.09.2026` | день или период |
| `/chatid` | id текущего чата |

Ежедневный отчёт — в `ADMIN_CHAT_ID` в 21:00 Europe/Moscow.

## Heroku

```bash
heroku create <app-name>
heroku addons:create heroku-postgresql:essential-0
heroku config:set BOT_TOKEN=... CHAT_1_ID=... CHAT_2_ID=... ADMIN_CHAT_ID=...
heroku config:set WEBHOOK_URL=https://<app-name>.herokuapp.com
git push heroku main
```

На Heroku файловая система эфемерна: справочник лучше держать в Postgres через `/phones_add` или загрузку CSV в админ-чат.

В BotFather выключи privacy mode (`/setprivacy` → Disable).
