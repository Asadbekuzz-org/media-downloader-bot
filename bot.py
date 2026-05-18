import os
import sqlite3
import logging
import yt_dlp
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

# Уланиш созламалари
ADMIN_ID = 7705020569  
TOKEN = "8872513669:AAH8sY6wuL0YDS-eQpn6kCi3uZpDUjMTD8k"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- МАЪЛУМОТЛАР БАЗАСИ (Лотинча) ---
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

# --- СТАРТ ВА АДМИН БУЙРУҚЛАРИ ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    add_user(message.from_user.id, message.from_user.username)
    await message.answer(
        f"👋 Assalomu alaykum, {message.from_user.full_name}!\n\n"
        "📹 Instagram/Facebook linkini yuboring — video yoki MP3 qilib beraman.\n"
        "✍️ Shunchaki matn yozing — qo'shiq qidiramiz yoki AI yordamchisidan maslahat olamiz!"
    )

@dp.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        count = get_stats()
        await message.answer(f"👑 **Admin Panel**\n\n📊 Botdagi jami a'zolar: **{count}** ta")

# --- МEДИА ВА ҚИДИРУВ ФУНКЦИЯЛАРИ ---
def download_media(url, mode, filename):
    if mode == "video":
        ydl_opts = {'outtmpl': filename, 'format': 'best', 'merge_output_format': 'mp4', 'quiet': True}
    else:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': filename.replace('.mp4', '.mp3'),
            'postprocs': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'quiet': True
        }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def search_music_5(text):
    ydl_opts = {'format': 'bestaudio', 'default_search': 'ytsearch5', 'quiet': True, 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(text, download=False)
        return info.get('entries', [])

# --- AI ФУНКЦИЯСИ (Минималистик ва тезкор кутубхонасиз тизим) ---
async def ask_media_ai(prompt):
    # Бот мавзусини AI га уқтириш (Промпт)
    system_instruction = (
        "Siz Media Downloader botining aqlli AI yordamchisiz. Vazifangiz foydalanuvchilarga "
        "faqat va faqat musiqa, qo'shiqlar, Instagram/Facebook trendlari, kreativ video g'oyalar, "
        "reels ssenariylari va video ostiga yoziladigan chiroyli opisaniyalar (caption) bo'yicha "
        "lotin alifbosida, qisqa va qiziqarli maslahatlar berish. Boshqa mavzularga javob bermang."
    )
    try:
        # Тезкор бепул API орқали GPT-4 дан жавоб олиш
        import aiohttp
        url = "https://chb.su/api/chat" # Муқобил очиқ AI тармоғи
        payload = {"messages": [{"role": "system", "content": system_instruction}, {"role": "user", "content": prompt}]}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=15) as resp:
                if resp.status == 200:
                    res_json = await resp.json()
                    return res_json['choices'][0]['message']['content']
    except Exception:
        pass
    return "🤖 Hozirda AI tizimi band. Birozdan so'ng qayta urinib ko'ring yoki musiqa qidirib turing!"

# --- ХАБАРЛАРНИ СAРАЛАШ ҚИСМИ ---
@dp.message()
async def handle_message(message: types.Message):
    if not message.text:
        await message.answer("⚠️ Iltimos, menga faqat link yoki matn yuboring!")
        return

    text = message.text.strip()

    # Линк келса (Instagram / Facebook)
    if any(x in text for x in ["instagram.com", "facebook.com", "fb.watch", "fb.gg"]):
        builder = InlineKeyboardBuilder()
        builder.button(text="📹 Videoni yuklash", callback_data=f"vid|{text[:40]}")
        builder.button(text="🎵 MP3 (Musiqasini olish)", callback_data=f"aud|{text[:40]}")
        builder.adjust(1)
        await message.reply("⚙️ Formatni tanlang:", reply_markup=builder.as_markup())

    # Текст келса — Танлов тугмалари чиқади (Минимализм)
    else:
        builder = InlineKeyboardBuilder()
        # Текстни тугма ичида хавфсиз олиб юриш учун вақтинчалик яширамиз
        builder.button(text="🔍 Musiqa qidirish", callback_data=f"search|{text[:40]}")
        builder.button(text="🤖 AI dan so'rash", callback_data=f"ai|{text[:40]}")
        builder.adjust(2)
        await message.reply("💡 Bu matn bilan nima qilamiz?", reply_markup=builder.as_markup())

# --- ТУГМАЛАР ИШЛАШИ (Callback) ---
@dp.callback_query()
async def handle_callbacks(callback: types.CallbackQuery):
    data = callback.data.split("|")
    action = data[0]
    
    # Тўлиқ асл матнни олиш (агар линк ёки текст узун бўлса хабардан ўқийди)
    original_text = callback.message.reply_to_message.text if callback.message.reply_to_message else callback.message.text

    await callback.answer("⏳ Jarayon boshlandi...")

    if action in ["vid", "aud"]:
        filename = "media.mp4"
        msg = await callback.message.edit_text("📥 Yuklanmoqda...")
        try:
            if action == "vid":
                await asyncio.to_thread(download_media, original_text, "video", filename)
                await callback.message.answer_video(video=types.FSInputFile(filename), caption="📹 Video tayyor!")
                if os.path.exists(filename): os.remove(filename)
            else:
                mp3_file = "media.mp3"
                await asyncio.to_thread(download_media, original_text, "audio", filename)
                await callback.message.answer_audio(audio=types.FSInputFile(mp3_file), caption="🎵 Musiqa tayyor!")
                if os.path.exists(mp3_file): os.remove(mp3_file)
            await msg.delete()
        except Exception:
            await msg.edit_text("❌ Yuklashda xatolik bo'ldi.")

    elif action == "search":
        msg = await callback.message.edit_text("🔍 Musiqalar qidirilmoqda...")
        try:
            tracks = await asyncio.to_thread(search_music_5, original_text)
            if not tracks:
                await msg.edit_text("❌ Hech narsa topilmadi.")
                return

            res_text = f"🔍 **'{original_text}' bo'yicha topildi:**\n\n"
            builder = InlineKeyboardBuilder()
            for i, track in enumerate(tracks[:5]):
                res_text += f"{i+1}. 🎵 {track.get('title', 'Nomalum')}\n"
                builder.button(text=f"{i+1}", callback_data=f"dl|{track['id']}")
            
            builder.adjust(5)
            await msg.edit_text(res_text, reply_markup=builder.as_markup())
        except Exception:
            await msg.edit_text("❌ Qidiruvda xatolik bo'ldi.")

    elif action == "dl":
        msg = await callback.message.answer("📥 Musiqa yuklanmoqda...")
        try:
            url = f"https://www.youtube.com/watch?v={data[1]}"
            await asyncio.to_thread(download_media, url, "audio", "track.mp4")
            await callback.message.answer_audio(audio=types.FSInputFile("track.mp3"), caption="🎵 Musiqangiz tayyor!")
            if os.path.exists("track.mp3"): os.remove("track.mp3")
            await msg.delete()
        except Exception:
            await msg.edit_text("❌ Yuklashda xatolik.")

    elif action == "ai":
        msg = await callback.message.edit_text("🤖 AI o'ylanmoqda...")
        ai_response = await ask_media_ai(original_text)
        await msg.edit_text(f"🤖 **AI Ekspert:**\n\n{ai_response}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
