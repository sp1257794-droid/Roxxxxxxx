import os
import threading
from flask import Flask
import telebot
from openai import OpenAI

# --- Environment Variables ---
# Render will inject these from your Environment Variables settings
BOT_TOKEN = os.environ.get("bot_token")
HF_TOKEN = os.environ.get("hf_token")
PORT = int(os.environ.get("PORT", 10000))

# --- Initialize Flask App (Required for Render) ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Music Telegram Bot is running successfully!"

# --- Initialize Telegram Bot ---
bot = telebot.TeleBot(BOT_TOKEN)

# --- Initialize OpenAI Client (Hugging Face Router) ---
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# --- Bot Message Handlers ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🎵 **Welcome to the AI Music Bot!** 🎵\n\n"
        "I can recommend songs, explain lyrics, give you trivia about artists, "
        "or create custom playlists for your mood. What are you listening to today?"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_music_chat(message):
    # Show a "typing..." action in Telegram while the AI generates the response
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Call the Hugging Face Router API via OpenAI SDK
        chat_completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1:novita",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert music assistant. Help the user with song recommendations, artist trivia, playlists, and music genres. Keep responses engaging and concise."
                },
                {
                    "role": "user", 
                    "content": message.text
                }
            ],
        )
        
        # Extract the AI's response text
        reply = chat_completion.choices[0].message.content
        
        # Send the response back to the user
        bot.reply_to(message, reply)
        
    except Exception as e:
        bot.reply_to(message, f"Oops! Something went wrong while connecting to the AI: {str(e)}")

# --- Polling Thread ---
def run_bot():
    print("Starting Telegram Bot Polling...")
    # infinity_polling keeps the bot running even if Telegram servers throw an occasional error
    bot.infinity_polling()

# --- Main Execution ---
if __name__ == "__main__":
    # Start the Telegram bot in a background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start the Flask web server on the main thread (required for Render)
    print(f"Starting Flask server on port {PORT}...")
    app.run(host="0.0.0.0", port=PORT)
