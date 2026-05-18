import os
import sqlite3
import logging
import yt_dlp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command

logging.basicConfig(level=logging.INFO)

# 🔔 МУҲИМ: Бу ерга ўз Телеграм ID рақамингизни ёзинг!
ADMIN_ID = 7705020569  # Ўзингизникига алмаштиринг!

TOKEN = os.getenv("8872513669:AAHwZhYKwxxBnfHvNSOLn5rK7jENTaD1SgY")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- МАЪЛУМОТЛАР БАЗАСИ ---
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

# --- БУЙРУҚЛАР ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    add_user(message.from_user.id, message.from_user.username)
    await message.answer(
        f"👋 Ассалому алайкум, {message.from_user.full_name}!\n\n"
        "📹 Менга Инстаграм ёки Фейсбук линкини юборинг (видео юклаб бераман).\n"
        "🎵 Ёки шунчаки қўшиқ номини ёзинг (мусиқа топиб бераман)!"
    )

@dp.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        count = get_stats()
        await message.answer(f"👑 **Ҳурматли Админ, хуш келибсиз!**\n\n📊 Ботдаги жами аъзолар: **{count}** та")
    else:
        await message.answer("⚠️ Бу буйруқ фақат бот adminи учун.")

# --- ХАБАРЛАРНИ УШЛАШ ВА ЮКЛАШ ҚИСМИ ---
@dp.message()
async def handle_message(message: types.Message):
    text = message.text.strip()
    
    # Инстаграм ёки Фейсбук линки бўлса
    if "instagram.com" in text or "facebook.com" in text or "fb.watch" in text:
        msg = await message.answer("⏳ Видео юкланмоқда, илтимос кутинг...")
        try:
            ydl_opts = {
                'outtmpl': 'video.mp4', 
                'format': 'best',
                'merge_output_format': 'mp4'
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([text])
            
            video = types.FSInputFile("video.mp4")
            await message.reply_video(video=video, caption="📹 Сиз сўраган видео тайёр!")
            
            # Файлни тозалаймиз
            if os.path.exists("video.mp4"):
                os.remove("video.mp4")
            await bot.delete_message(message.chat.id, msg.message_id)
            
        except Exception as e:
            await msg.edit_text(f"❌ Видео юклашда хатолик бўлди. Линк нотўғри ёки видео ёпиқ профилда бўлиши мумкин.")
            if os.path.exists("video.mp4"):
                os.remove("video.mp4")
            
    # Оддий текст бўлса — Мусиқа қидиради
    else:
        msg = await message.answer("🔍 Мусиқа қидирилмоқда...")
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'default_search': 'scsearch1',
                'outtmpl': 'music.mp3',
                'noplaylist': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([text])
                
            audio = types.FSInputFile("music.mp3")
            await message.reply_audio(audio=audio, caption=f"🎵 {text} — топилди!")
            
            if os.path.exists("music.mp3"):
                os.remove("music.mp3")
            await bot.delete_message(message.chat.id, msg.message_id)
            
        except Exception as e:
            await msg.edit_text("❌ Афсуски, бундай мусиқа топилмади.")
            if os.path.exists("music.mp3"):
                os.remove("music.mp3")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
