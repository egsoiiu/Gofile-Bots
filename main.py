import os
import requests
from dotenv import load_dotenv
from gofile import uploadFile
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from flask import Flask
import threading
import logging
import math
import time
import asyncio

# Suppress Flask development server warning
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

load_dotenv()

# Create a simple Flask app for health checks and port binding
app = Flask(__name__)

# Disable Flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def home():
    return "🤖 GoFile Bot is running!"

@app.route('/health')
def health():
    return "✅ Bot is healthy!"

@app.route('/ping')
def ping():
    return "pong"

def run_flask_simple():
    port = int(os.environ.get("PORT", 10000))
    # Run with suppressed output
    import flask.cli
    flask.cli.show_server_banner = lambda *args: None
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Start Flask in a separate thread
flask_thread = threading.Thread(target=run_flask_simple)
flask_thread.daemon = True
flask_thread.start()

Bot = Client(
    "GoFile-Bot",
    bot_token=os.environ.get("BOT_TOKEN"),
    api_id=int(os.environ.get("API_ID")),
    api_hash=os.environ.get("API_HASH"),
)

def format_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def format_time(seconds):
    """Convert seconds to human readable time"""
    if seconds < 60:
        return f"{int(seconds)} sec"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes} min {secs} sec"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours} hr {minutes} min"

def create_progress_bar(percentage, bar_length=10):
    """Create a visual progress bar with 10 boxes"""
    filled = int(bar_length * percentage / 100)
    empty = bar_length - filled
    return '▣' * filled + '□' * empty

class DownloadProgress:
    def __init__(self, message, filename, total_size):
        self.message = message
        self.filename = filename
        self.total_size = total_size
        self.start_time = time.time()
        self.downloaded = 0
        self.last_update = 0

    async def update(self, chunk_size):
        self.downloaded += chunk_size
        current_time = time.time()
        
        # Update every 2 seconds to avoid spam
        if current_time - self.last_update >= 2:
            self.last_update = current_time
            await self._update_message()

    async def _update_message(self):
        percentage = (self.downloaded / self.total_size) * 100
        progress_bar = create_progress_bar(percentage)
        
        elapsed_time = time.time() - self.start_time
        if self.downloaded > 0 and elapsed_time > 0:
            speed = self.downloaded / elapsed_time
            remaining_size = self.total_size - self.downloaded
            if speed > 0:
                time_left = remaining_size / speed
            else:
                time_left = 0
        else:
            speed = 0
            time_left = 0

        text = f"<b>Downloading...</b> 📥\n\n"
        text += f"ㅤ\n"
        text += f"  <b>File Name:</b> <code>{self.filename}</code>\n\n"
        text += f"ㅤㅤ<b>Size:</b> <code>{format_size(self.total_size)}</code>\n\n"
        text += f"<b>[ {progress_bar} ]</b> <code>{percentage:.2f}%</code>\n\n"
        text += f"<b>➩</b> <code>{format_size(self.downloaded)}</code> of <code>{format_size(self.total_size)}</code>\n\n"
        text += f"<b>➩ Speed:</b> <code>{format_size(speed)}/s</code>\n\n"
        text += f"<b>➩ Time Left:</b> <code>{format_time(time_left)}</code>"

        try:
            await self.message.edit_text(text, parse_mode=ParseMode.HTML)
        except:
            pass

    async def complete(self):
        text = f"<b>Download Completed</b> ✓\n\n"
        text += f"ㅤ\n"
        text += f"  <b>File Name:</b> <code>{self.filename}</code>\n\n"
        text += f"ㅤㅤ<b>Size:</b> <code>{format_size(self.total_size)}</code>\n\n"
        text += f"<b>Download Completed</b> ✓"
        
        try:
            await self.message.edit_text(text, parse_mode=ParseMode.HTML)
        except:
            pass

class UploadProgress:
    def __init__(self, message, filename, total_size):
        self.message = message
        self.filename = filename
        self.total_size = total_size
        self.start_time = time.time()
        self.uploaded = 0
        self.last_update = 0

    async def update(self, chunk_size):
        self.uploaded += chunk_size
        current_time = time.time()
        
        # Update every 1 second to avoid spam
        if current_time - self.last_update >= 1:
            self.last_update = current_time
            await self._update_message()

    async def _update_message(self):
        percentage = (self.uploaded / self.total_size) * 100
        progress_bar = create_progress_bar(percentage)
        
        # Fixed speed of 5 MB/s for dummy progress
        speed = 5 * 1024 * 1024  # 5 MB/s in bytes
        remaining_size = self.total_size - self.uploaded
        
        if speed > 0:
            time_left = remaining_size / speed
        else:
            time_left = 0

        text = f"<b>Uploading...</b> 📤\n\n"
        text += f"<b>[ {progress_bar} ]</b> <code>{percentage:.2f}%</code>\n\n"
        text += f"<b>➩</b> <code>{format_size(self.uploaded)}</code> of <code>{format_size(self.total_size)}</code>\n\n"
        text += f"<b>➩ Speed:</b> <code>5.0 MB/s</code>\n\n"
        text += f"<b>➩ Time Left:</b> <code>{format_time(time_left)}</code>"

        try:
            await self.message.edit_text(text, parse_mode=ParseMode.HTML)
        except:
            pass

    async def complete(self):
        try:
            await self.message.edit_text("<b>Upload Completed</b> ✓", parse_mode=ParseMode.HTML)
        except:
            pass

WELCOME_MESSAGE = """
🤖 <b>Welcome to GoFile Uploader Bot!</b>

I can help you upload files to gofile.io easily. Just send me a file or a direct download link and I'll handle the rest!

<b>What I can do:</b>
• Upload files to GoFile
• Support direct download links
• Custom folder uploads
• And much more!

Use the buttons below to explore features or get help.
"""

HELP_MESSAGE = """
📖 <b>Help Guide</b>

<b>How to use this bot:</b>

<b>With Media Files:</b>
1. Send me any file (document, photo, video, etc.)
2. Reply to the file with <code>/upload</code>
3. Optional: Add token and folder ID
   - <code>/upload token</code>
   - <code>/upload token folderid</code>

<b>With Download Links:</b>
1. Send <code>/upload</code> followed by your URL
   - <code>/upload https://example.com/file.zip</code>
   - <code>/upload https://example.com/file.zip token</code>
   - <code>/upload https://example.com/file.zip token folderid</code>

<b>Need more help?</b> Feel free to explore the features!
"""

FEATURES_MESSAGE = """
⭐ <b>Bot Features</b>

🔹 <b>File Upload</b>: Upload any type of file to GoFile
🔹 <b>Link Support</b>: Upload from direct download links
🔹 <b>Custom Folders</b>: Specify custom folder IDs
🔹 <b>Token Support</b>: Use your own GoFile tokens
🔹 <b>Fast Processing</b>: Quick upload and download speeds
🔹 <b>User-Friendly</b>: Simple commands and intuitive interface

<b>Supported File Types:</b>
• Documents (PDF, ZIP, RAR, etc.)
• Images (JPG, PNG, GIF, etc.)
• Videos (MP4, AVI, MKV, etc.)
• Audio files (MP3, WAV, etc.)
• And many more!

Start by sending me a file or use the /upload command!
"""

# Home keyboard (shown with start message)
HOME_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("❓ Help", callback_data="help"),
     InlineKeyboardButton("⭐ Features", callback_data="features")],
    [InlineKeyboardButton("❌ Close", callback_data="close")]
])

# Help keyboard (shown with help message)
HELP_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("⬅️ Back", callback_data="back_home"),
     InlineKeyboardButton("⭐ Features", callback_data="features")],
    [InlineKeyboardButton("❌ Close", callback_data="close")]
])

# Features keyboard (shown with features message)
FEATURES_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("⬅️ Back", callback_data="back_home"),
     InlineKeyboardButton("❓ Help", callback_data="help")],
    [InlineKeyboardButton("❌ Close", callback_data="close")]
])


@Bot.on_message(filters.private & filters.command("start"))
async def start(bot, update):
    await update.reply_text(
        text=WELCOME_MESSAGE,
        reply_markup=HOME_KEYBOARD,
        disable_web_page_preview=True,
        quote=True,
        parse_mode=ParseMode.HTML
    )


@Bot.on_callback_query()
async def handle_callbacks(bot, update):
    callback_data = update.data
    message = update.message
    
    if callback_data == "help":
        await message.edit_text(
            text=HELP_MESSAGE,
            reply_markup=HELP_KEYBOARD,
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML
        )
    
    elif callback_data == "features":
        await message.edit_text(
            text=FEATURES_MESSAGE,
            reply_markup=FEATURES_KEYBOARD,
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML
        )
    
    elif callback_data == "back_home":
        await message.edit_text(
            text=WELCOME_MESSAGE,
            reply_markup=HOME_KEYBOARD,
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML
        )
    
    elif callback_data == "close":
        await message.delete()
        # Also try to delete the /start command message if possible
        try:
            await update.message.reply_to_message.delete()
        except:
            pass
    
    await update.answer()


@Bot.on_message(filters.private & filters.command("upload"))
async def filter(_, update):
    message = await update.reply_text(
        text="<code>Processing...</code>", 
        quote=True, 
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )

    text = update.text.replace("\n", " ")
    url = None
    token = None
    folderId = None

    if " " in text:
        text = text.split(" ", 1)[1]
        if update.reply_to_message:
            if " " in text:
                token, folderId = text.split(" ", 1)
            else:
                token = text
        else:
            if " " in text:
                if len(text.split()) > 2:
                    url, token, folderId = text.split(" ", 2)
                else:
                    url, token = text.split()
            else:
                url = text
            if not (url.startswith("http://") or url.startswith("https://")):
                await message.edit_text("Error :- <code>url is wrong</code>", parse_mode=ParseMode.HTML)
                return
    elif not update.reply_to_message:
        await message.edit_text("Error :- <code>downloadable media or url not found</code>", parse_mode=ParseMode.HTML)
        return

    try:
        # Download process
        if url:
            await message.edit_text("<code>Getting file information...</code>", parse_mode=ParseMode.HTML)
            response = requests.head(url, allow_redirects=True)
            total_size = int(response.headers.get('content-length', 0))
            filename = url.split("/")[-1] or "download_file"
            
            download_progress = DownloadProgress(message, filename, total_size)
            
            await message.edit_text("<code>Starting download...</code>", parse_mode=ParseMode.HTML)
            response = requests.get(url, stream=True)
            media = filename
            
            with open(media, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        await download_progress.update(len(chunk))
            
            await download_progress.complete()
        else:
            # For Telegram files
            if update.reply_to_message.document:
                filename = update.reply_to_message.document.file_name
                total_size = update.reply_to_message.document.file_size
            elif update.reply_to_message.video:
                filename = update.reply_to_message.video.file_name or "video.mp4"
                total_size = update.reply_to_message.video.file_size
            elif update.reply_to_message.audio:
                filename = update.reply_to_message.audio.file_name or "audio.mp3"
                total_size = update.reply_to_message.audio.file_size
            elif update.reply_to_message.photo:
                filename = "photo.jpg"
                total_size = update.reply_to_message.photo.file_size
            else:
                filename = "file"
                total_size = 0
            
            download_progress = DownloadProgress(message, filename, total_size)
            
            async def progress_callback(current, total):
                await download_progress.update(current - download_progress.downloaded)
            
            media = await update.reply_to_message.download(progress=progress_callback)
            await download_progress.complete()

        # Upload process with dummy progress - START IMMEDIATELY
        file_size = os.path.getsize(media)
        upload_progress = UploadProgress(message, filename, file_size)
        
        # Start upload progress immediately
        await upload_progress._update_message()
        
        # Simulate upload progress with 5 MB/s speed
        steps = 10  # Number of progress updates
        chunk_size = file_size // steps
        
        for i in range(steps):
            if i < steps - 1:
                await upload_progress.update(chunk_size)
            else:
                # Last step - complete the upload
                await upload_progress.update(file_size - upload_progress.uploaded)
            await asyncio.sleep(0.5)  # Update every 0.5 seconds
        
        # Actual upload (this happens quickly after the progress simulation)
        response = uploadFile(file_path=media, token=token, folderId=folderId)
        await upload_progress.complete()

      
        try:
            os.remove(media)
        except:
            pass

    except Exception as error:
        await message.edit_text(f"Error :- `{error}`")
        return

    text = f"**File Name:** `{response['name']}`" + "\n"
    text += f"**File ID:** `{response['id']}`" + "\n"
    text += f"**Parent Folder Code:** `{response['parentFolderCode']}`" + "\n"
    text += f"**Guest Token:** `{response['guestToken']}`" + "\n"
    text += f"**md5:** `{response['md5']}`" + "\n"
    text += f"**Download Page:** `{response['downloadPage']}`"
    link = response["downloadPage"]
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="Open Link", url=link),
                InlineKeyboardButton(
                    text="Share Link", url=f"https://telegram.me/share/url?url={link}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Feedback", url="https://telegram.me/FayasNoushad"
                )
            ],
        ]
    )
    await message.edit_text(
        text=text, reply_markup=reply_markup, disable_web_page_preview=True
    )


if __name__ == "__main__":
    print("🤖 Bot is starting with port binding...")
    print("✅ Server is running and ready for health checks")
    Bot.run()
