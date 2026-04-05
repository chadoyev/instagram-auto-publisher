<div align="center">

<h1>Instagram Auto Publisher</h1>

<p>
  <a href="#en">🇬🇧 English</a> &nbsp;|&nbsp;
  <a href="#ru">🇷🇺 Русский</a>
</p>

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0?style=flat&logo=telegram&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

</div>

---

<!-- ═══════════════════════════════════════════════════════════ -->
<!--                        ENGLISH                             -->
<!-- ═══════════════════════════════════════════════════════════ -->

<a name="en"></a>

<div align="center">

## 🇬🇧 English

</div>

A Telegram bot that covers the full content lifecycle for Instagram: **collection → moderation → publishing**.

Users send TikTok, Instagram, and YouTube links — the bot downloads the files and returns them watermark-free. This is essentially **crowdsourced content collection**: your bot's audience finds and brings the best videos to you, while you simply review the stream and approve what's worth publishing. Everything approved is automatically posted to Instagram on a configurable schedule.

### Table of Contents

- [Features](#en-features)
- [How It Works](#en-how)
- [Tech Stack](#en-stack)
- [Server Deployment](#en-deploy)
- [Publishing Setup](#en-setup)
- [Webhook Mode](#en-webhook)
- [Environment Variables](#en-env)
- [Local Development](#en-local)
- [FAQ](#en-faq)

---

<a name="en-features"></a>
### Features

#### For Users

- **Watermark-free downloads** — send a TikTok, Instagram Reels, or YouTube link and get a clean file back
- **Format support**: single videos, photos, albums (multi-file posts)
- **Multilingual**: RU / EN — language is detected automatically from Telegram settings
- **Mandatory subscription**: admin can require users to subscribe to specific Telegram channels before using the bot

#### For Admins

**Crowdsourced Moderation**

The bot acts as a content collection funnel: users find and bring videos, you pick the best ones. The review interface works like Tinder — one item at a time:

| Action | Result |
|--------|--------|
| ✅ Approve | Queued for publishing, type resolved automatically |
| 🗑 Reject | File is deleted |
| 📖 To Story | Approve and queue as an Instagram Story |
| ⏭ Skip | Show next item, revisit this one later |

- Filter by category: Story / Reels / Post / Album / IGTV
- **Inline caption editing** — type a message while reviewing and it becomes the post description

**Auto-Publishing to Instagram**

- Three time phases: **morning / day / evening** — each with its own schedule
- Configurable **start and end time** per phase
- Configurable **content type sequence** per phase (e.g. `reels, story_video, post_photo`)
- Smart **jitter** between posts — intervals vary slightly for natural-looking behaviour
- **Auto-retry on failure** — up to 3 attempts with exponential backoff (30 / 60 / 120 sec)
- Telegram notification on publish failure

**Supported publish types:**

| Key | Description |
|-----|-------------|
| `reels` | Video Reel |
| `story_video` | Video Story |
| `story_photo` | Photo Story |
| `post_video` | Video feed post |
| `post_photo` | Photo feed post |
| `album` | Carousel / Album |
| `igtv` | IGTV |

**Watermark**
- Upload your logo directly through the bot (photo or document)
- Logo is automatically applied to all files before publishing

**Broadcast**
- Send text, photo, video, or video note to all bot users
- Preview before sending + ability to revise
- Delivery report: sent / blocked count

**Subscription Management**
- Add / remove Telegram channels required for bot access
- Toggle subscription check with one button

**General Management**
- Enable / disable the bot for regular users (admin is never affected)
- Stats: users, downloads, breakdown by platform
- Detailed publish queue and daily publication stats
- External API monitoring: HikerAPI balance + TikTok API status
- Instagram session management: login, logout, delete session, challenge-flow support (SMS / email)
- WireGuard VPN config delivered via bot — for Instagram mobile authorization
- Toggle admin UI language (RU / EN)

---

<a name="en-how"></a>
### How It Works

```
User → sends a link
      ↓
  download.py — detects platform, downloads file
      ↓
  Content saved to DB (status: pending_review)
      ↓
  Moderation queue — admin approves / rejects
      ↓
  publish_queue — approved items wait for their phase
      ↓
  APScheduler — CronTrigger fires publish_phase()
      ↓
  InstagramPublisher (instagrapi) → Instagram
```

**Downloaders:**
- **TikTok** — self-hosted `evil0ctal/douyin_tiktok_download_api` container
- **Instagram** — HikerAPI cloud service (requires `HIKER_API_KEY`)
- **YouTube** — `yt-dlp`

---

<a name="en-stack"></a>
### Tech Stack

| Component | Technology |
|-----------|------------|
| Telegram bot | aiogram 3.x |
| Database | PostgreSQL 16 + SQLAlchemy 2.0 async + asyncpg |
| Cache / FSM | Redis 7 |
| Scheduler | APScheduler 3.x |
| Instagram API | instagrapi |
| Downloading | yt-dlp, aiohttp, HikerAPI |
| TikTok API | evil0ctal/douyin_tiktok_download_api |
| VPN | WireGuard (linuxserver/wireguard) |
| Media | Pillow + ffmpeg |
| Config | pydantic-settings |
| Containerisation | Docker + Docker Compose |

---

<a name="en-deploy"></a>
### Server Deployment

#### Requirements

- Ubuntu 20.04 / 22.04
- Docker Engine 24+ and Docker Compose v2
- At least 1 GB RAM (2 GB recommended)
- Port `51820/UDP` open — WireGuard VPN
- Port `8081/TCP` open — webhook mode only

#### Step 1 — Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

Verify:

```bash
docker --version && docker compose version
```

#### Step 2 — Clone the Repository

```bash
git clone https://github.com/chadoyev/instagram-auto-publisher.git
cd instagram-auto-publisher
```

#### Step 3 — Configure `.env`

```bash
cp .env.example .env
nano .env
```

Minimum required values:

```env
BOT_TOKEN=1234567890:AABBccDDeeFF...   # Token from @BotFather
ADMIN_IDS=123456789                     # Your Telegram ID (get it from @userinfobot)
IG_USERNAME=your_instagram_username     # Instagram login
IG_PASSWORD=your_instagram_password     # Instagram password
HIKER_API_KEY=your_hiker_api_key       # Key from hikerapi.com
```

> Multiple admins: `ADMIN_IDS=123456789,987654321`

#### Step 4 — Start

```bash
docker compose up -d
```

This starts 5 containers:

| Container | Purpose |
|-----------|---------|
| `ig-publisher-bot` | Telegram bot |
| `ig-publisher-db` | PostgreSQL 16 |
| `ig-publisher-redis` | Redis 7 |
| `ig-publisher-tiktok-api` | TikTok / Douyin downloader |
| `ig-publisher-vpn` | WireGuard VPN |

```bash
docker compose ps          # check status
docker compose logs -f bot # watch logs
```

#### Step 5 — Instagram Authorization

This is a required step — publishing will not work without it.

**1. Get the VPN config**

In Telegram: `/admin` → 📸 Instagram → 📥 VPN config

Or manually:
```bash
docker exec ig-publisher-vpn cat /config/peer1/peer1.conf
```

**2. Connect your phone to VPN**

Install the **WireGuard** app (iOS / Android), import `peer1.conf`, and enable the tunnel.

**3. Open Instagram on your phone**

Browse your feed for a minute — this "introduces" Instagram to your server's IP address.

**4. Log in via the bot**

`/admin` → 📸 Instagram → 🔑 Log in

If Instagram requests a verification code, the bot will prompt you for it.

**5. Done**

The session is saved to the `session_data` Docker volume. Container restarts do not require re-authentication.

> VPN is only needed for the initial login. Regular publishing works without it.

---

<a name="en-setup"></a>
### Publishing Setup

**Phase times:** `/admin` → ⏱ Autopost → ⚙️ Settings → 🕐 Phase times

Select a phase and enter a range:
```
08:00 - 11:00
```

**Content sequence:** `/admin` → ⏱ Autopost → ⚙️ Settings → 📋 Phase content

Select a phase and enter a comma-separated list of types:
```
reels, story_video, post_photo
```

The scheduler distributes posts evenly across the phase window with a small random offset.

**Enable autoposting:** `/admin` → ⏱ Autopost → toggle button

---

<a name="en-webhook"></a>
### Webhook Mode

Long-polling is the default. Switch to webhook for production deployments.

In `.env`:
```env
BOT_MODE=webhook
WEBHOOK_HOST=https://your-domain.com
WEBHOOK_PATH=/ig
WEBHOOK_PORT=8081
WEBHOOK_SECRET=any-random-string
```

Example nginx config:
```nginx
location /ig {
    proxy_pass http://127.0.0.1:8081;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

> Telegram requires HTTPS. Set up SSL with Let's Encrypt / Certbot.

---

<a name="en-env"></a>
### Environment Variables

| Variable | Req. | Description |
|----------|:----:|-------------|
| `BOT_TOKEN` | ✅ | Telegram bot token from @BotFather |
| `ADMIN_IDS` | ✅ | Comma-separated admin Telegram IDs |
| `IG_USERNAME` | ✅ | Instagram account login |
| `IG_PASSWORD` | ✅ | Instagram account password |
| `HIKER_API_KEY` | ✅ | HikerAPI key for Instagram downloads |
| `BOT_MODE` | — | `polling` (default) or `webhook` |
| `WEBHOOK_HOST` | webhook | Server URL, e.g. `https://example.com` |
| `WEBHOOK_PATH` | webhook | Webhook path, default `/ig` |
| `WEBHOOK_PORT` | webhook | Port, default `8081` |
| `WEBHOOK_SECRET` | webhook | Random string for Telegram signature verification |
| `DATABASE_URL` | — | PostgreSQL URL (Docker default already set) |
| `REDIS_URL` | — | Redis URL (Docker default already set) |
| `DB_NAME` | — | Database name (default `bot`) |
| `DB_USER` | — | Database user (default `bot`) |
| `DB_PASSWORD` | — | Database password (default `bot`) |
| `TIKTOK_API_URL` | — | TikTok API URL (default `http://tiktok-api:80`) |
| `IG_SESSION_PATH` | — | Path to Instagram session file |
| `DEFAULT_CAPTION` | — | Default caption for publications |
| `WATERMARK_PATH` | — | Path to watermark PNG logo |
| `MAX_VIDEO_DURATION` | — | Max video duration in seconds (default `240`) |
| `DAILY_RESET_TIME` | — | Time to reset daily stats (default `00:00`) |

---

<a name="en-local"></a>
### Local Development

```bash
# 1. Clone
git clone https://github.com/chadoyev/instagram-auto-publisher.git
cd instagram-auto-publisher

# 2. Start infrastructure only
docker compose up -d postgres redis tiktok-api

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure .env
cp .env.example .env
# Edit: DATABASE_URL=postgresql+asyncpg://bot:bot@localhost:5432/bot
#        REDIS_URL=redis://localhost:6379/0

# 5. Run
python -m app
```

Update a running deployment:
```bash
git pull && docker compose up -d --build
```

---

<a name="en-faq"></a>
### FAQ

**Bot doesn't download from Instagram**
→ Check HikerAPI balance: `/admin` — status is shown in the main panel.

**Publishing fails / authorization error**
→ `/admin` → 📸 Instagram → check session status. If invalid — delete it and log in again via VPN.

**How to add another admin**
→ Add the ID to `ADMIN_IDS` in `.env`, then:
```bash
docker compose restart bot
```

**WireGuard container won't start**
→ Load the kernel module manually:
```bash
sudo modprobe wireguard
```

**How to stop autoposting**
→ `/admin` → ⏱ Autopost → disable button. The current phase will finish cleanly.

---

<a name="en-ack"></a>
### Acknowledgements

This project is built on the shoulders of the following open-source tools:

- [Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) — self-hosted API for downloading TikTok / Douyin content without watermarks
- [instagrapi](https://github.com/subzeroid/instagrapi) — unofficial Python client for Instagram publishing
- [HikerAPI](https://hikerapi.com/) — cloud API for downloading Instagram media

---

<a name="en-disclaimer"></a>
### Disclaimer

This project was created **for educational purposes only** and is intended to demonstrate the principles of building Telegram bots, task queues, and third-party API integrations.

The author assumes no responsibility for any use of this project that violates the terms of service of Instagram, TikTok, YouTube, or any other platform. Automating actions on Instagram is against [Instagram's Terms of Use](https://help.instagram.com/581066165581870) and may result in account restrictions or permanent suspension.

By using this project, you accept all associated risks and take full responsibility for your own actions.

---

<br>
<div align="center">
  <a href="#en">🔝 Back to top (EN)</a> &nbsp;|&nbsp; <a href="#ru">🇷🇺 Переключить на русский</a>
</div>
<br>

---

<!-- ═══════════════════════════════════════════════════════════ -->
<!--                        РУССКИЙ                             -->
<!-- ═══════════════════════════════════════════════════════════ -->

<a name="ru"></a>

<div align="center">

## 🇷🇺 Русский

</div>

Telegram-бот, который закрывает весь цикл работы с контентом для Instagram: **сбор → модерация → публикация**.

Пользователи бота отправляют ссылки на TikTok, Instagram, YouTube — бот скачивает файлы и тут же возвращает их без водяного знака. Фактически это **краудсорс-сбор контента**: аудитория бота сама находит и приносит интересные видео, а администратор лишь просматривает поток и одобряет лучшее. Всё отобранное автоматически уходит в Instagram по расписанию.

### Содержание

- [Возможности](#ru-features)
- [Как это работает](#ru-how)
- [Стек технологий](#ru-stack)
- [Деплой на сервер](#ru-deploy)
- [Настройка публикаций](#ru-setup)
- [Webhook-режим](#ru-webhook)
- [Переменные окружения](#ru-env)
- [Локальная разработка](#ru-local)
- [FAQ](#ru-faq)

---

<a name="ru-features"></a>
### Возможности

#### Для пользователей

- **Скачивание без водяного знака** — отправь ссылку на TikTok, Instagram Reels или YouTube и получи чистый файл
- **Поддержка форматов**: одиночные видео, фото, альбомы (несколько медиафайлов)
- **Мультиязычность**: RU / EN — язык определяется автоматически по настройкам Telegram
- **Обязательная подписка**: администратор может задать список Telegram-каналов, без подписки на которые бот недоступен

#### Для администратора

**Краудсорс-модерация**

Бот работает как воронка сбора контента: пользователи сами находят и приносят видео, ты отбираешь лучшее. Интерфейс — в стиле тиндера, один контент за раз:

| Действие | Результат |
|----------|-----------|
| ✅ Одобрить | Уходит в очередь публикации, тип определяется автоматически |
| 🗑 Отклонить | Файл удаляется |
| 📖 В истории | Одобрить и поставить в очередь как Instagram Story |
| ⏭ Пропустить | Показать следующий, вернуться к этому позже |

- Фильтрация по категории: Story / Reels / Post / Album / IGTV
- **Редактирование подписи прямо в чате** — напиши текст во время просмотра, он станет описанием публикации

**Автопостинг в Instagram**

- Три временные фазы: **утро / день / вечер** — каждая со своим расписанием
- Настраиваемые **время начала и конца** каждой фазы
- Настраиваемая **последовательность типов** для каждой фазы (например: `reels, story_video, post_photo`)
- Умный **джиттер** — интервалы между постами немного варьируются для имитации живого поведения
- **Автоповтор при ошибке** — до 3 попыток с экспоненциальной задержкой (30 / 60 / 120 сек)
- Уведомление в Telegram при сбое публикации

**Поддерживаемые типы публикаций:**

| Ключ | Описание |
|------|----------|
| `reels` | Видео-рилс |
| `story_video` | Видеостория |
| `story_photo` | Фотостория |
| `post_video` | Видеопост в ленте |
| `post_photo` | Фотопост в ленте |
| `album` | Альбом (карусель) |
| `igtv` | IGTV |

**Водяной знак**
- Загрузка логотипа прямо через бота (фото или документ)
- Логотип автоматически накладывается на все публикуемые файлы

**Рассылка (Broadcast)**
- Текст, фото, видео или видеосообщение — всем пользователям бота
- Предпросмотр перед отправкой + возможность переделать
- Отчёт по итогам: доставлено / заблокировано

**Управление подписками**
- Добавление/удаление Telegram-каналов для обязательной подписки
- Включение/выключение проверки одной кнопкой

**Общее управление**
- Включение/выключение бота для пользователей (не затрагивает администратора)
- Статистика: пользователи, скачивания, по платформам
- Детальная статистика очереди и опубликованного за день
- Мониторинг внешних API: баланс HikerAPI и статус TikTok API
- Управление Instagram-сессией: логин, выход, удаление сессии, поддержка challenge-flow (SMS / email)
- VPN-конфиг WireGuard прямо из бота — для авторизации Instagram с телефона
- Переключение языка интерфейса администратора (RU / EN)

---

<a name="ru-how"></a>
### Как это работает

```
Пользователь → ссылка
      ↓
  download.py — определяет платформу, скачивает файл
      ↓
  Файл сохраняется в БД (статус: pending_review)
      ↓
  Очередь модерации — администратор одобряет / отклоняет
      ↓
  publish_queue — одобренные ждут своей фазы
      ↓
  APScheduler — CronTrigger запускает publish_phase()
      ↓
  InstagramPublisher (instagrapi) → Instagram
```

**Даунлоадеры:**
- **TikTok** — self-hosted контейнер `evil0ctal/douyin_tiktok_download_api`
- **Instagram** — HikerAPI (нужен `HIKER_API_KEY`)
- **YouTube** — `yt-dlp`

---

<a name="ru-stack"></a>
### Стек технологий

| Компонент | Технология |
|-----------|------------|
| Telegram-бот | aiogram 3.x |
| База данных | PostgreSQL 16 + SQLAlchemy 2.0 async + asyncpg |
| Кэш / FSM | Redis 7 |
| Планировщик | APScheduler 3.x |
| Instagram API | instagrapi |
| Скачивание | yt-dlp, aiohttp, HikerAPI |
| TikTok API | evil0ctal/douyin_tiktok_download_api |
| VPN | WireGuard (linuxserver/wireguard) |
| Медиа | Pillow + ffmpeg |
| Конфигурация | pydantic-settings |
| Контейнеризация | Docker + Docker Compose |

---

<a name="ru-deploy"></a>
### Деплой на сервер

#### Требования

- Ubuntu 20.04 / 22.04
- Docker Engine 24+ и Docker Compose v2
- Минимум 1 ГБ RAM (рекомендуется 2 ГБ)
- Порт `51820/UDP` открыт — WireGuard VPN
- Порт `8081/TCP` открыт — только для webhook-режима

#### Шаг 1 — Установка Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

Проверь:

```bash
docker --version && docker compose version
```

#### Шаг 2 — Клонирование

```bash
git clone https://github.com/chadoyev/instagram-auto-publisher.git
cd instagram-auto-publisher
```

#### Шаг 3 — Настройка `.env`

```bash
cp .env.example .env
nano .env
```

Минимально необходимые значения:

```env
BOT_TOKEN=1234567890:AABBccDDeeFF...   # Токен от @BotFather
ADMIN_IDS=123456789                     # Твой Telegram ID (узнать: @userinfobot)
IG_USERNAME=your_instagram_username     # Логин Instagram
IG_PASSWORD=your_instagram_password     # Пароль Instagram
HIKER_API_KEY=your_hiker_api_key       # Ключ от hikerapi.com
```

> Несколько администраторов: `ADMIN_IDS=123456789,987654321`

#### Шаг 4 — Запуск

```bash
docker compose up -d
```

Будет запущено 5 контейнеров:

| Контейнер | Назначение |
|-----------|------------|
| `ig-publisher-bot` | Telegram-бот |
| `ig-publisher-db` | PostgreSQL 16 |
| `ig-publisher-redis` | Redis 7 |
| `ig-publisher-tiktok-api` | TikTok / Douyin даунлоадер |
| `ig-publisher-vpn` | WireGuard VPN |

```bash
docker compose ps          # проверить статус
docker compose logs -f bot # следить за логами
```

#### Шаг 5 — Авторизация в Instagram

Это обязательный шаг — без него публикации работать не будут.

**1. Получи VPN-конфиг**

В Telegram: `/admin` → 📸 Instagram → 📥 VPN конфиг

Или вручную:
```bash
docker exec ig-publisher-vpn cat /config/peer1/peer1.conf
```

**2. Подключи телефон к VPN**

Установи приложение **WireGuard** (iOS / Android), импортируй `peer1.conf`, включи VPN.

**3. Зайди в Instagram на телефоне**

Открой приложение, полистай ленту — Instagram «познакомится» с IP сервера.

**4. Авторизуйся через бота**

`/admin` → 📸 Instagram → 🔑 Войти в аккаунт

Если Instagram попросит подтверждение — бот запросит код из SMS или email.

**5. Готово**

Сессия сохраняется в Docker-volume `session_data`. При перезапуске контейнера повторный логин не нужен.

> VPN нужен только для первичной авторизации. Регулярные публикации работают без него.

---

<a name="ru-setup"></a>
### Настройка публикаций

**Время фаз:** `/admin` → ⏱ Автопостинг → ⚙️ Настройки → 🕐 Время фаз

Выбери фазу и введи диапазон:
```
08:00 - 11:00
```

**Последовательность контента:** `/admin` → ⏱ Автопостинг → ⚙️ Настройки → 📋 Контент фаз

Выбери фазу и введи список типов через запятую:
```
reels, story_video, post_photo
```

Планировщик равномерно распределит публикации по диапазону с небольшим случайным отклонением.

**Включить автопостинг:** `/admin` → ⏱ Автопостинг → кнопка «Включить»

---

<a name="ru-webhook"></a>
### Webhook-режим

По умолчанию работает long-polling. Для продакшн-деплоя можно переключить на webhook.

В `.env`:
```env
BOT_MODE=webhook
WEBHOOK_HOST=https://your-domain.com
WEBHOOK_PATH=/ig
WEBHOOK_PORT=8081
WEBHOOK_SECRET=any-random-string
```

Пример конфига nginx:
```nginx
location /ig {
    proxy_pass http://127.0.0.1:8081;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

> Telegram требует HTTPS. Настрой SSL через Let's Encrypt / Certbot.

---

<a name="ru-env"></a>
### Переменные окружения

| Переменная | Обяз. | Описание |
|------------|:-----:|----------|
| `BOT_TOKEN` | ✅ | Токен Telegram-бота от @BotFather |
| `ADMIN_IDS` | ✅ | Числовые ID администраторов через запятую |
| `IG_USERNAME` | ✅ | Логин Instagram-аккаунта |
| `IG_PASSWORD` | ✅ | Пароль Instagram-аккаунта |
| `HIKER_API_KEY` | ✅ | API-ключ HikerAPI для скачивания из Instagram |
| `BOT_MODE` | — | `polling` (по умолчанию) или `webhook` |
| `WEBHOOK_HOST` | webhook | URL сервера, например `https://example.com` |
| `WEBHOOK_PATH` | webhook | Путь вебхука, по умолчанию `/ig` |
| `WEBHOOK_PORT` | webhook | Порт, по умолчанию `8081` |
| `WEBHOOK_SECRET` | webhook | Случайная строка для проверки подписи Telegram |
| `DATABASE_URL` | — | URL PostgreSQL (дефолт для Docker уже прописан) |
| `REDIS_URL` | — | URL Redis (дефолт для Docker уже прописан) |
| `DB_NAME` | — | Имя БД (по умолчанию `bot`) |
| `DB_USER` | — | Пользователь БД (по умолчанию `bot`) |
| `DB_PASSWORD` | — | Пароль БД (по умолчанию `bot`) |
| `TIKTOK_API_URL` | — | URL TikTok API (по умолчанию `http://tiktok-api:80`) |
| `IG_SESSION_PATH` | — | Путь к файлу сессии Instagram |
| `DEFAULT_CAPTION` | — | Дефолтная подпись к публикациям |
| `WATERMARK_PATH` | — | Путь к PNG-логотипу для водяного знака |
| `MAX_VIDEO_DURATION` | — | Максимальная длина видео в секундах (по умолчанию `240`) |
| `DAILY_RESET_TIME` | — | Время сброса дневной статистики (по умолчанию `00:00`) |

---

<a name="ru-local"></a>
### Локальная разработка

```bash
# 1. Клонировать
git clone https://github.com/chadoyev/instagram-auto-publisher.git
cd instagram-auto-publisher

# 2. Поднять только инфраструктуру
docker compose up -d postgres redis tiktok-api

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Настроить .env
cp .env.example .env
# Правка: DATABASE_URL=postgresql+asyncpg://bot:bot@localhost:5432/bot
#          REDIS_URL=redis://localhost:6379/0

# 5. Запустить
python -m app
```

Обновление деплоя:
```bash
git pull && docker compose up -d --build
```

---

<a name="ru-faq"></a>
### FAQ

**Бот не скачивает из Instagram**
→ Проверь баланс HikerAPI: `/admin` → баланс отображается в главной панели.

**Публикации не работают / ошибка авторизации**
→ `/admin` → 📸 Instagram → статус сессии. Если недействительна — удали и войди заново через VPN.

**Как добавить администратора**
→ Добавь ID в `ADMIN_IDS` в `.env` через запятую, затем:
```bash
docker compose restart bot
```

**Контейнер WireGuard не стартует**
→ Подгрузи модуль ядра вручную:
```bash
sudo modprobe wireguard
```

**Как остановить автопостинг**
→ `/admin` → ⏱ Автопостинг → «Выключить». Текущая фаза завершится корректно.

---

<br>
<div align="center">
  <a href="#ru">🔝 Наверх (RU)</a> &nbsp;|&nbsp; <a href="#en">🇬🇧 Switch to English</a>
</div>
<br>

---

<a name="ru-ack"></a>
### Благодарности

Проект построен на плечах следующих открытых инструментов:

- [Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) — self-hosted API для скачивания TikTok / Douyin без водяного знака
- [instagrapi](https://github.com/subzeroid/instagrapi) — неофициальный Python-клиент Instagram для публикации контента
- [HikerAPI](https://hikerapi.com/) — облачный API для скачивания медиа из Instagram

---

<a name="ru-disclaimer"></a>
### Отказ от ответственности

Данный проект создан **исключительно в образовательных целях** и предназначен для изучения принципов построения Telegram-ботов, очередей задач и интеграции с внешними API.

Автор не несёт ответственности за любое использование проекта, нарушающее правила и условия использования Instagram, TikTok, YouTube или других платформ. Автоматизация действий в Instagram противоречит [Условиям использования Instagram](https://help.instagram.com/581066165581870) и может повлечь ограничение или блокировку аккаунта.

Используя данный проект, вы принимаете на себя все связанные с этим риски и полную ответственность за свои действия.

---

<div align="center">
  MIT License · <a href="https://github.com/chadoyev/instagram-auto-publisher">github.com/chadoyev/instagram-auto-publisher</a>
</div>
