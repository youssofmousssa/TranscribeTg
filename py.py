import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# Telegram token
TELEGRAM_TOKEN = "8456668310:AAGQJYVwKrmWTRIKIieNX_b63Oo0_YeUCHk"

# Groq client with API key directly
client = Groq(api_key="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")

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
        print(line.strip())  # Can be sent to Telegram as progress updates

    process.wait()
    return output

# Handler for messages
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

# Main function
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started...")
    app.run_polling()
