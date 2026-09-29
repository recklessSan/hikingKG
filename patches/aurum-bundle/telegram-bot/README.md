# Aurum Telegram bot (aiogram)

Пошаговый бот для записи **расходов** в Aurum через HTTP API.

## Диалог

1. `/expense` → сумма  
2. описание  
3. выбор счёта (кнопки)  
4. выбор категории расходов (кнопки)  
5. подтверждение → `POST /api/transactions`

## Настройка (.env)

```env
AURUM_TELEGRAM_BOT_TOKEN=123456:ABC...   # от @BotFather
AURUM_TELEGRAM_ALLOWED_USER_IDS=123456789  # ваш id (/id в боте)
```

Если в Aurum включён basic auth:

```env
AURUM_TELEGRAM_BASIC_AUTH_USER=...
AURUM_TELEGRAM_BASIC_AUTH_PASSWORD=...
```

(в `docker-compose` они по умолчанию подтягиваются из `AURUM_BASIC_AUTH_*`)

## Запуск

```bash
cd ~/KR-DEV/Aurum
docker compose up -d --build telegram-bot
docker compose logs -f telegram-bot
```

Пока токен пустой, контейнер **не падает** — ждёт в idle. После вставки токена:

```bash
docker compose up -d telegram-bot
```

## Если бот «молчит»

1. В логах должно быть `allowed users: […]` или `NONE — set AURUM_TELEGRAM_ALLOWED_USER_IDS`.
2. Напиши боту `/id` — он ответит числом (эта команда работает всегда).
3. Впиши id в `.env`:
   ```env
   AURUM_TELEGRAM_ALLOWED_USER_IDS=123456789
   ```
4. `docker compose up -d --force-recreate telegram-bot`

Если `allowed users: NONE` и бот всё равно молчит на `/start` — пересобери образ (баг со старым middleware на Update уже исправлен в бандле).
