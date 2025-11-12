# Instagram-auto-publisher
An automated Instagram publishing system controlled via a Telegram bot. It collects media from Instagram, TikTok, and YouTube, adds watermarks, sorts by category, and posts photos, stories, reels, and albums on schedule. Built with Python, Instagrapi, MoviePy, Telegram Bot API, and SQLite.
# 🤖 Instagram Auto Publisher

An automated Instagram content management system fully controlled through a Telegram bot.  
The system downloads media from various social platforms (TikTok, Instagram, YouTube), adds watermarks, organizes them, and posts automatically according to a schedule.

---

## 🧠 Key Features

- 📲 **Telegram Bot Control** — manage uploads and schedules directly through Telegram  
- 🕓 **Automated Posting** — publish posts, stories, reels, and albums at specific times (morning, noon, evening)  
- 💧 **Automatic Watermarking** — apply a logo watermark to all video content using MoviePy  
- ⚙️ **Social Media Integration** — supports TikTok, YouTube, and Instagram APIs  
- 🧩 **Smart Content Management** — auto-cleanup and queue-based publishing  
- 🗃️ **Local Database** — store metadata and settings in SQLite  
- 💬 **Real-time Notifications** — get posting updates or errors directly in Telegram

---

## 🧰 Technologies Used

- **Python 3.10+**  
- [instagrapi](https://github.com/adw0rd/instagrapi)  
- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI)  
- [moviepy](https://zulko.github.io/moviepy/)  
- [pytubefix](https://github.com/pytubefix/pytubefix)  
- [Pillow](https://python-pillow.org)  
- **SQLite3**, **schedule**, **requests**

---

## 📂 Project Structure
```
instagram-auto-publisher/
│
├── main.py # Telegram bot logic: content management, downloading
├── loopbot.py # Scheduled posting logic
├── get_json.py # Instagram login helper (creates postit.json)
├── db.db # Local SQLite database
├── postit.json # Instagram session file (auto-generated)
├── logo.png # Watermark image
├── /photo_posts # Photo posts
├── /video_posts # Video posts (including reels, IGTV)
├── /storys # Instagram stories
└── /albums_posts # Multi-image posts
```
---

## 🚀 Setup & Usage

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Generate the Instagram session file:**
   ```python
   python get_json.py
   ```
   Enter your Instagram login credentials when prompted.
   A file called postit.json will be created automatically.

3. **Run the Telegram bot:**
   ```python
   python main.py
   ```

4. **Configure posting schedule and content type via Telegram commands.**

---

## 📸 Example Workflow
1. **You send a TikTok or Instagram link to the Telegram bot.**
2. **The bot downloads the media, applies a watermark, and queues it for posting.**
3. **At the scheduled time, it publishes the content automatically.**
4. **Old files are removed after successful posting.**

---

## 👤 Author

**Iskander Chadoyev**\
Python developer & automation enthusiast\
📍 Kazakhstan\
🐙 GitHub: [chadoyev](https://github.com/chadoyev)\
💬 Telegram: [chadoyev](https://t.me/chadoyev)
