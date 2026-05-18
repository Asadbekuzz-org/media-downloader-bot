import os
import sqlite3
import logging
import yt_dlp
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command

logging.basicConfig(level=logging.INFO)

# 🔔 Ўз Телеграм ID рақамингизни шу ерга ёзинг!
ADMIN_ID = 7705020569  

TOKEN = "8872513669:AAH8sY6wuL0YDS-eQpn6kCi3uZpDUjMTD8k"
bot = Bot(token=TOKEN)
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT)")
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

init_db()

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    add_user(message.from_user.id, message.from_user.username)
    await message.answer(
        f"👋 Ассалому алайкум, {message.from_user.full_name}!\n\n"
        "📹 Инстаграм ёки Фейсбук линкини юборинг (видео юклаб бераман).\n"
        "🎵 Ёки қўшиқ номини ёзинг (мусиқа топиб бераман)!"
    )

@dp.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        count = get_stats()
        await message.answer(f"👑 **Админ Панель**\n\n📊 Ботдаги аъзолар: **{count}** та")
    else:
        await message.answer("⚠️ Бу буйруқ фақат бот админи учун.")

# Юклаш жараёни қотиб қолмаслиги учун алоҳида функция
def download_media(url, is_video=True):
    if is_video:
        ydl_opts = {
            'outtmpl': 'video.mp4', 
            'format': 'best',
            'merge_output_format': 'mp4',
            'no_warnings': True,
            'quiet': True
        }
    else:
        ydl_opts = {
            'format': 'bestaudio/best',
            'default_search': 'scsearch1',
            'outtmpl': 'music.mp3',
            'noplaylist': True,
            'no_warnings': True,
            'quiet': True
        }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@dp.message()
async def handle_message(message: types.Message):
    text = message.text.strip()
    
    if "instagram.com" in text or "facebook.com" in text or "fb.watch" in text or "fb.gg" in text:
        msg = await message.answer("⏳ Видео юкланмоқда, илтимос кутинг...")
        try:
            # Бот қотиб қолмаслиги учун юклашни алоҳида оқимга оламиз (Async)
            await asyncio.to_thread(download_media, text, True)
            
            if os.path.exists("video.mp4"):
                video = types.FSInputFile("video.mp4")
                await message.reply_video(video=video, caption="📹 Видео тайёр!")
                os.remove("video.mp4")
                await bot.delete_message(message.chat.id, msg.message_id)
            else:
                await msg.edit_text("❌ Видеони юклаб бўлмади (муаллиф ёпиқ қўйган бўлиши мумкин).")
        except Exception as e:
            await msg.edit_text("❌ Юклашда хатолик содир бўлди.")
            if os.path.exists("video.mp4"): os.remove("video.mp4")
            
    else:
        msg = await message.answer("🔍 Мусиқа қидирилмоқда...")
        try:
            await asyncio.to_thread(download_media, text, False)
            
            if os.path.exists("music.mp3"):
                audio = types.FSInputFile("music.mp3")
                await message.reply_audio(audio=audio, caption=f"🎵 {text} — топилди!")
                os.remove("music.mp3")
                await bot.delete_message(message.chat.id, msg.message_id)
            else:
                await msg.edit_text("❌ Мусиқа топилмади.")
        except Exception as e:
            await msg.edit_text("❌ Мусиқа қидиришда хатолик бўлди.")
            if os.path.exists("music.mp3"): os.remove("music.mp3")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
