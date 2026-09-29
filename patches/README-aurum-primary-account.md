# Aurum: основной счёт + валюты счетов

## Если `git apply` падает

Не используйте патч. Скопируйте готовые файлы скриптом.

### На Mac

```bash
# 1) скачать папку patches из ветки hikingKG
cd ~
git clone --depth 1 -b cursor/aurum-primary-account-5ca6 \
  https://github.com/recklessSan/hikingKG.git hikingKG-patches

# 2) установить файлы в Aurum
chmod +x ~/hikingKG-patches/patches/install-aurum-bundle.sh
~/hikingKG-patches/patches/install-aurum-bundle.sh ~/KR-DEV/Aurum

# 3) пересобрать
cd ~/KR-DEV/Aurum
docker compose up -d --build
```

Путь Aurum на Mac: `~/KR-DEV/Aurum`.

### Что делать, если прошлый `git apply` частично прошёл

```bash
cd ~/KR-DEV/Aurum
git status

# откатиться к чистому состоянию репозитория, потом поставить бандл:
git restore .
git clean -fd
# (осторожно: удалит незакоммиченные файлы)
~/hikingKG-patches/patches/install-aurum-bundle.sh ~/KR-DEV/Aurum
docker compose up -d --build
```

## Возможности после установки

1. Галочка **Основной счёт**
2. Валюта на счетах и в транзакциях
3. Для KGS — знак сома **сом** (U+20C0 ⃀)
4. Поле валюты в форме счёта
