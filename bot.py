import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart
from yt_dlp import YoutubeDL

# Логлар
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8872513669:AAHwZhYKwxxBnfHvNSOLn5rK7jENTaD1SgY"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# 🚀 ТЕЛЕГРАМ КЭШ ТИЗИМИ (Видео ва Мусиқаларни эслаб қолиш учун оддий база)
# Бу бот ўчиб ёқилгунча ишлайди. Тўлиқ база учун кейинроқ SQLite қўшамиз.
video_cache = {}
audio_cache = {}

COMMON_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'socket_timeout': 10,
    'prefer_insecure': True,
    'external_downloader': 'aria2c', # Агар компьютерингизда aria2 бўлса, жуда тез юклайди
}

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"<b>Ассалому алайкум, {message.from_user.full_name}!</b>\n\n"
        "⚡ <b>Мукаммаллаштирилган Ракета Бот!</b>\n"
        "Бот энди кэш тизимида ишлайди ва юкланган файлларни сонияларда қайтаради.",
        parse_mode="HTML"
    )

# МУСИҚА ЮКЛАШ
async def fast_download_audio(search_query, message):
    # Агар бу қўшиқ олдин изланган бўлса, КЭШДАН ОЛИШ
    if search_query in audio_cache:
        await message.reply_audio(audio=audio_cache[search_query], caption="🎵 Кэшдан тезкор топилди!")
        return

    audio_opts = {
        **COMMON_OPTS,
        'format': 'bestaudio/best',
        'outtmpl': f'{DOWNLOAD_DIR}/a_%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'default_search': 'ytsearch1',
    }
    try:
        loop = asyncio.get_event_loop()
        audio_info = await loop.run_in_executor(None, lambda: YoutubeDL(audio_opts).extract_info(search_query, download=True))
        video_entry = audio_info['entries'][0]
        audio_file = f"{DOWNLOAD_DIR}/a_{video_entry['id']}.mp3"
        
        audio_title = video_entry.get('title', 'Оригинал Мусиқа')
        performer = video_entry.get('uploader', 'Мусиқа боти')

        # Файлни юбориш ва ТEЛEГРAМ ID сини кэшга сақлаш
        sent_audio = await message.reply_audio(audio=FSInputFile(audio_file), title=audio_title, performer=performer, caption="🎵 Тўлиқ оригинал варианти!")
        audio_cache[search_query] = sent_audio.audio.file_id # Кичик сир мана шу ерда!
        
        os.remove(audio_file)
    except Exception as e:
        logging.error(f"Мусиқада хато: {e}")

# ВИДЕО ЮКЛАШ
@dp.message(F.text.contains("instagram") | F.text.contains("instagr") | 
            F.text.contains("facebook") | F.text.contains("fb.watch"))
async def handle_link(message: Message):
    url = message.text.strip()

    # 🚀 СИРЛИ ЖОЙИ: Агар бу линк олдин юкланган бўлса, 0 сонияда юбориш
    if url in video_cache:
        await message.reply_video(video=video_cache[url], caption="🎥 Олдин юкланган тайёр видео (Тезкор режим)!")
        return

    status_msg = await message.answer("⚡ Юклаш бошланди...")

    video_opts = {
        **COMMON_OPTS,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'{DOWNLOAD_DIR}/v_%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
    }

    try:
        if "ddinstagram.com" in url:
            url = url.replace("ddinstagram.com", "instagram.com")

        loop = asyncio.get_event_loop()
        video_info = await loop.run_in_executor(None, lambda: YoutubeDL(video_opts).extract_info(url, download=True))
        
        video_file = YoutubeDL(video_opts).prepare_filename(video_info)
        if not video_file.endswith('.mp4'):
            video_file = os.path.splitext(video_file)[0] + '.mp4'

        # Видеони юбориш ва унинг Telegram ID сини кэшга ёзиб қўйиш
        sent_video = await message.reply_video(video=FSInputFile(video_file), caption="🎥 Видео тайёр!")
        video_cache[url] = sent_video.video.file_id # Линкни базага файл_ид билан боғладик
        
        # Орқа фонда оригинал мусиқа қидируви
        desc = video_info.get('title', '') or video_info.get('description', 'Популярная музыка')
        search_query = ' '.join(desc.split()[:5])
        asyncio.create_task(fast_download_audio(search_query, message))

        os.remove(video_file)
        await status_msg.delete()

    except Exception as e:
        # Прокси усули
        if "instagram.com" in url:
            proxy_url = url.replace("instagram.com", "ddinstagram.com")
            try:
                loop = asyncio.get_event_loop()
                video_info = await loop.run_in_executor(None, lambda: YoutubeDL(video_opts).extract_info(proxy_url, download=True))
                video_file = YoutubeDL(video_opts).prepare_filename(video_info)
                if not video_file.endswith('.mp4'):
                    video_file = os.path.splitext(video_file)[0] + '.mp4'

                sent_video = await message.reply_video(video=FSInputFile(video_file), caption="🎥 Видео тайёр!")
                video_cache[url] = sent_video.video.file_id
                
                desc = video_info.get('description', 'Популярная музыка')
                search_query = ' '.join(desc.split()[:5])
                asyncio.create_task(fast_download_audio(search_query, message))
                
                os.remove(video_file)
                await status_msg.delete()
                return
            except Exception:
                pass
        await status_msg.edit_text("❌ Юклашда хатолик бўлди.")

@dp.message(F.text)
async def search_music(message: Message):
    query = message.text.strip()
    if query.startswith("http"): return
    status_msg = await message.answer(f"🔍 '{query}' изланмоқда...")
    await fast_download_audio(query, message)
    try: await status_msg.delete()
    except: pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())