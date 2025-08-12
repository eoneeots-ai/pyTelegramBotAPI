import telebot
import sqlite3

TOKEN = "8407580759:AAG1HBTRfE-MxpmmXwGuwODLJ4LX82Gl0Po"
bot = telebot.TeleBot(TOKEN)

conn = sqlite3.connect("ads.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS ads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    photo_id TEXT,
    description TEXT
)
""")
conn.commit()

user_states = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привіт! 👋\n\n/add — додати оголошення\n/search — пошук оголошення")

@bot.message_handler(commands=['add'])
def add_ad(message):
    bot.send_message(message.chat.id, "Відправ фото товару 📸")
    user_states[message.chat.id] = {'step': 'photo'}

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.chat.id in user_states and user_states[message.chat.id]['step'] == 'photo':
        user_states[message.chat.id]['photo_id'] = message.photo[-1].file_id
        user_states[message.chat.id]['step'] = 'description'
        bot.send_message(message.chat.id, "Відправ опис товару 📝")
    else:
        bot.send_message(message.chat.id, "Щоб додати оголошення, напиши /add")

@bot.message_handler(func=lambda m: m.chat.id in user_states and user_states[m.chat.id]['step'] == 'description')
def handle_description(message):
    user_states[message.chat.id]['description'] = message.text
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "Немає username"
    photo_id = user_states[message.chat.id]['photo_id']
    description = user_states[message.chat.id]['description']

    cursor.execute("INSERT INTO ads (user_id, username, photo_id, description) VALUES (?, ?, ?, ?)",
                   (user_id, username, photo_id, description))
    conn.commit()

    bot.send_message(message.chat.id, "✅ Оголошення додано!")
    user_states.pop(message.chat.id, None)

@bot.message_handler(commands=['search'])
def search_ads(message):
    bot.send_message(message.chat.id, "Введи ключове слово для пошуку 🔍")
    user_states[message.chat.id] = {'step': 'search'}

@bot.message_handler(func=lambda m: m.chat.id in user_states and user_states[m.chat.id]['step'] == 'search')
def handle_search(message):
    keyword = message.text.lower()
    cursor.execute("SELECT username, photo_id, description FROM ads WHERE lower(description) LIKE ?", (f"%{keyword}%",))
    results = cursor.fetchall()

    if results:
        for username, photo_id, description in results:
            bot.send_photo(message.chat.id, photo_id, caption=f"{description}\nПродавець: {username}")
    else:
        bot.send_message(message.chat.id, "❌ Нічого не знайдено.")

    user_states.pop(message.chat.id, None)

print("Бот запущено...")
bot.infinity_polling()
