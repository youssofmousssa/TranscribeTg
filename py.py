import os
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# Load API keys from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq client
client = Groq(api_key=GROQ_API_KEY)

# Helper: download audio with absolute path
def download_audio(url, output="audio.m4a"):
    output_path = os.path.join(os.getcwd(), output)  # absolute path
    command = [
        "yt-dlp",
        "-f", "bestaudio[ext=m4a]",
        url,
        "-o", output_path,
        "--progress-template", "%(progress)s"
    ]
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )

    for line in process.stdout:
        print(line.strip())  # You could also send this to Telegram

    process.wait()
    if not os.path.isfile(output_path):
        raise FileNotFoundError(f"Audio file not found at {output_path}")
    return output_path

# Handler for incoming messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    await update.message.reply_text(f"Downloading audio from:\n{url}")

    try:
        audio_file = download_audio(url)

        await update.message.reply_text("Download complete! Sending to Whisper for transcription...")

        with open(audio_file, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_file), f.read()),
                model="whisper-large-v3",
                response_format="verbose_json",
            )

        await update.message.reply_text(f"Transcription:\n{transcription.text}")

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a YouTube link and I will transcribe its audio!")

# Main bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started...")
    app.run_polling()
