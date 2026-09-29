# Aurum patches (Mac: ~/KR-DEV/Aurum)

Установка **копированием файлов** (не `git apply`):

```bash
cd ~
rm -rf hikingKG-patches
git clone --depth 1 -b cursor/aurum-primary-account-5ca6 \
  https://github.com/recklessSan/hikingKG.git hikingKG-patches

chmod +x ~/hikingKG-patches/patches/install-aurum-bundle.sh
~/hikingKG-patches/patches/install-aurum-bundle.sh ~/KR-DEV/Aurum

cd ~/KR-DEV/Aurum
docker compose up -d --build
```

## Telegram-бот (aiogram)

После установки бандла в `.env`:

```env
AURUM_TELEGRAM_BOT_TOKEN=           # от @BotFather
AURUM_TELEGRAM_ALLOWED_USER_IDS=    # узнайте через /id у бота
```

```bash
cd ~/KR-DEV/Aurum
docker compose up -d --build telegram-bot
```

Пока токен пустой — контейнер в idle. Диалог: `/expense` → сумма → описание → счёт → категория → сохранить.

Подробнее: `telegram-bot/README.md` в дереве Aurum.
