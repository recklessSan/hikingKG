# Aurum patches (Mac: ~/KR-DEV/Aurum)

## Чтобы не настраивать заново после сна / выключения

Данные уже живут в Docker volume `aurum_pgdata` — они **не пропадают** от reboot и sleep.
Контейнеры в compose с `restart: unless-stopped` поднимаются сами, когда Docker Desktop снова online.

Сделай один раз:

1. **Docker Desktop → Settings → General → Start Docker Desktop when you sign in**
2. Установи патчи (ниже) и **больше не трогай** `~/KR-DEV/Aurum/.env`
3. После пробуждения Mac, если страница не открылась — одна команда:

```bash
~/KR-DEV/Aurum/aurum-up.sh
```

Не нужно: заново клонировать патчи, `down -v`, переписывать пароль, переустанавливать бандл.
Нельзя: `docker compose down -v` / `docker volume rm` — это удалит транзакции.

Если backend в `Restarting` с `InvalidPasswordError` (обычно после порчи `.env`) — один раз:

```bash
~/hikingKG-patches/patches/aurum-fix-db-password.sh ~/KR-DEV/Aurum
~/KR-DEV/Aurum/aurum-up.sh
```

---

## Установка патчей (копированием, не `git apply`)

```bash
cd ~
rm -rf hikingKG-patches
git clone --depth 1 -b cursor/aurum-primary-account-5ca6 \
  https://github.com/recklessSan/hikingKG.git hikingKG-patches

chmod +x ~/hikingKG-patches/patches/install-aurum-bundle.sh
chmod +x ~/hikingKG-patches/patches/aurum-fix-db-password.sh
~/hikingKG-patches/patches/install-aurum-bundle.sh ~/KR-DEV/Aurum

cd ~/KR-DEV/Aurum
chmod +x aurum-up.sh
./aurum-up.sh   # или: docker compose up -d --build  при первой установке
```

**Важно:** рабочие настройки — в файле `.env` (не `.env.example`).
Установщик не перезаписывает `.env` и существующий `.env.example`.

Проверка порта/пароля:

```bash
grep -E 'WEB_PORT|POSTGRES_PASSWORD|TELEGRAM|BIND' ~/KR-DEV/Aurum/.env
```

## Фильтр транзакций по счёту

На странице «Транзакции» — выпадающий список счетов (рядом с типом/категорией).
API уже принимал `?account_id=`; UI просто прокидывает его. Можно открыть сразу с фильтром: `/transactions?account=3`.

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
