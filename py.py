import os
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# Load credentials from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# Helper: download audio with progress
def download_audio(url, output="audio.m4a"):
    command = [
        "yt-dlp",
        "-f", "bestaudio[ext=m4a]",
        url,
        "-o", output,
        "--progress-template", "%(progress)s"
    ]
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )

    for line in process.stdout:
        print(line.strip())  # This can be sent to Telegram for progress updates

    process.wait()
    return output

# Telegram message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text(f"Downloading audio from:\n{url}")

    try:
        audio_file = download_audio(url)
        await update.message.reply_text("Download complete! Sending to Whisper for transcription...")

        with open(audio_file, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=(audio_file, f.read()),
                model="whisper-large-v3",
                response_format="verbose_json",
            )

        await update.message.reply_text(f"Transcription:\n{transcription.text}")

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a YouTube link and I will transcribe its audio!")

# Main bot runner
if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not GROQ_API_KEY:
        raise RuntimeError("Please set TELEGRAM_TOKEN and GROQ_API_KEY in environment variables.")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started...")
    app.run_polling()
