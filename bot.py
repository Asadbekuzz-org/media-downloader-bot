import os
import sqlite3
import logging
import yt_dlp
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiohttp import web

logging.basicConfig(level=logging.INFO)

# --- БОТ СОЗЛАМАЛАРИ (МАЪЛУМОТЛАРИНГИЗ ТЎЛИҚ ЖОЙЛАНДИ) ---
ADMIN_ID = 7705020569  
TOKEN = "8872513669:AAFyCT8DRYsNDAdG-UNOG-T8juES-B97_gE"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- FSM (РАССИЛКА УЧУН ҲОЛАТЛАР) ---
class BroadcastState(StatesGroup):
    waiting_for_message = State()

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

def get_all_users():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

init_db()

# --- START VA ADMIN PANEL ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    add_user(message.from_user.id, message.from_user.username)
    await message.answer(
        f"👋 Assalomu alaykum, {message.from_user.full_name}!\n\n"
        "📹 Instagram/Facebook linkini yuboring — video yoki MP3 qilib beraman.\n"
        "✍️ Shunchaki matn yozing — qo'shiq qidiramiz yoki 100% barqaror AI yordamchisidan maslahat olamiz!"
    )

@dp.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        count = get_stats()
        builder = InlineKeyboardBuilder()
        builder.button(text="📢 Reklama / Elon yuborish", callback_data="send_broadcast")
        
        await message.answer(
            f"👑 **Admin Panel**\n\n📊 Botdagi jami a'zolar: **{count}** ta",
            reply_markup=builder.as_markup()
        )

# --- РАССИЛКА ФУНКЦИЯСИ (ҲАММАГА ХАБАР ЮБОРИШ) ---
@dp.callback_query(lambda c: c.data == "send_broadcast")
async def start_broadcast(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    
    await callback.message.answer("✍️ **Hamma foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yozing.**\n"
                                  "Bu matn, rasm, video yoki audio bo'lishi mumkin. Bekor qilish uchun /cancel deb yozing.")
    await state.set_state(BroadcastState.waiting_for_message)
    await callback.answer()

@dp.message(Command("cancel"))
async def cancel_broadcast(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Reklama yuborish bekor qilindi.")

@dp.message(BroadcastState.waiting_for_message)
async def process_broadcast_message(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    await state.clear()
    user_ids = get_all_users()
    
    status_msg = await message.answer(f"⏳ **Yuborish boshlandi...**\nJami foydalanuvchilar: {len(user_ids)} ta.")
    
    success = 0
    failed = 0
    
    for user_id in user_ids:
        try:
            await message.copy_to(chat_id=user_id)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
            
    await status_msg.edit_text(f"📢 **Xabar hamma foydalanuvchilarga yuborildi!**\n\n✅ Muvaqqiyatli: {success} ta\n❌ Yetkazilmadi (botni o'chirgan): {failed} ta")

# --- MEDIA FUNKSIYALARI ---
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

# --- 100% СТАБИЛ ГEМИНИ АИ ТИЗИМИ ---
async def ask_gemini_ai(prompt):
    # Сизнинг шахсий Gemini API калитингиз муваффақиятли қўшилди!
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=AIzaSyDZ-iztnXyKsoCK6VHD2COk-P5Y7BMiKvw"
    
    system_instruction = (
        "Siz Media Downloader botining aqlli AI yordamchisiz. Vazifangiz foydalanuvchilarga "
        "faqat musiqa, qo'shiqlar, Instagram/Facebook trendlari, kreativ video g'oyalar, "
        "reels ssenariylari va caption yozish bo'yicha lotin alifbosida, juda qisqa "
        "va qiziqarli (3-4 ta gapda) javob berish. Boshqa mavzularga qisqa qilib rad javobini bering."
    )
    
    payload = {
        "contents": [{"parts": [{"text": f"{system_instruction}\n\nFoydalanuvchi savoli: {prompt}"}]}]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=10) as resp:
                if resp.status == 200:
                    res_json = await resp.json()
                    return res_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        logging.error(f"AI Error: {e}")
    
    return "🤖 Hozirda AI tizimida yuklama yuqori. Iltimos, birozdan so'ng qayta urinib ko'ring."

# --- XABARLARNI SARALASH ---
@dp.message()
async def handle_message(message: types.Message):
    if not message.text:
        return

    text = message.text.strip()

    if any(x in text for x in ["instagram.com", "facebook.com", "fb.watch", "fb.gg"]):
        builder = InlineKeyboardBuilder()
        builder.button(text="📹 Videoni yuklash", callback_data=f"vid|{text[:40]}")
        builder.button(text="🎵 MP3 (Musiqasini olish)", callback_data=f"aud|{text[:40]}")
        builder.adjust(1)
        await message.reply("⚙️ Formatni tanlang:", reply_markup=builder.as_markup())
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔍 Musiqa qidirish", callback_data=f"search|{text[:40]}")
        builder.button(text="🤖 AI dan so'rash", callback_data=f"ai|{text[:40]}")
        builder.adjust(2)
        await message.reply("💡 Bu matn bilan nima qilamiz?", reply_markup=builder.as_markup())

# --- ТУГМАЛАР ИШЛАШИ ---
@dp.callback_query()
async def handle_callbacks(callback: types.CallbackQuery):
    data = callback.data.split("|")
    action = data[0]
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
        ai_response = await ask_gemini_ai(original_text)
        await msg.edit_text(f"🤖 **AI Ekspert:**\n\n{ai_response}")

# --- RENDER PORT ТИЗИМИ ---
async def start_web_server():
    async def handle(request):
        return web.Response(text="Bot is running completely live with custom Gemini API!")

    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get('PORT', 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
