import os
import sqlite3
from flask import Flask, request
import telebot
from telebot import types

# --- কনফিগারেশন ---
# এখানে আপনার আসল বটের টোকেনটি বসাবেন
BOT_TOKEN = "8606592862:AAF4R5u6jaM78RzWeduWqpWF6OZDml2SZ-k" 

# আপনার চ্যানেলের ইউজারনেম (@ সহ)
CHANNEL_USERNAME = "@ai_income_bdt" 

# আপনার সঠিক অ্যাডমিন আইডি (শুধুমাত্র সংখ্যা)
ADMIN_ID = 8658873921 

AD_LINK = "https://t.me/ai_income_bdt"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- ডাটাবেজ সেটআপ ---
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, referred_by INTEGER, broadcast_state INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

def is_sub(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ['member', 'administrator', 'creator']
    except Exception:
        return False

# --- মেইন মেনু ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("🧮 অংক করুন"),
        types.KeyboardButton("📊 প্রোফাইল"),
        types.KeyboardButton("👥 রেফার করুন"),
        types.KeyboardButton("💳 টাকা তুলুন"),
        types.KeyboardButton("🏆 লিডারবোর্ড"),
        types.KeyboardButton("📞 সাপোর্ট"),
        types.KeyboardButton("👑 অ্যাডমিন প্যানেল")
    )
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        # রেফারেল চেক
        args = message.text.split()
        referred_by = None
        if len(args) > 1 and args[1].isdigit():
            ref_id = int(args[1])
            if ref_id != user_id:
                referred_by = ref_id
        
        cursor.execute("INSERT INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, referred_by))
        conn.commit()
    
    # ব্রডকাস্ট স্টেট রিসেট (যাতে বট জ্যাম না লাগে)
    cursor.execute("UPDATE users SET broadcast_state = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    if not is_sub(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 জয়েন করুন", url=AD_LINK))
        bot.send_message(user_id, f"❌ আমাদের বটের কাজ করতে হলে আপনাকে অবশ্যই আমাদের চ্যানেলে জয়েন থাকতে হবে।\n\nচ্যানেল লিংক: {CHANNEL_USERNAME}\n\nজয়েন করার পর আবার /start চাপুন।", reply_markup=markup)
        return

    bot.send_message(user_id, "👋 স্বাগতম! নিচে থেকে যেকোনো একটি বাটন সিলেক্ট করুন:", reply_markup=main_menu())

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    text = message.text
    
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT broadcast_state FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    state = res[0] if res else 0

    # অ্যাডমিন যদি বিজ্ঞাপন মোডে থাকে
    if user_id == ADMIN_ID and state == 1:
        cursor.execute("UPDATE users SET broadcast_state = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        
        cursor.execute("SELECT user_id FROM users")
        all_users = cursor.fetchall()
        conn.close()
        
        bot.send_message(user_id, "📢 বিজ্ঞাপন পাঠানো শুরু হচ্ছে...")
        success = 0
        for u in all_users:
            try:
                bot.send_message(u[0], text)
                success += 1
            except Exception:
                continue
        bot.send_message(user_id, f"✅ সফলভাবে {success} জন ইউজারের কাছে বিজ্ঞাপন পাঠানো হয়েছে।", reply_markup=main_menu())
        return

    if not is_sub(user_id):
        conn.close()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 জয়েন করুন", url=AD_LINK))
        bot.send_message(user_id, f"❌ আপনি চ্যানেল থেকে লিভ নিয়েছেন! দয়া করে আবার জয়েন করুন।", reply_markup=markup)
        return

    if text == "🧮 অংক করুন":
        bot.send_message(user_id, "🔢 অংক করার ফিচারটি খুব দ্রুত চালু করা হচ্ছে।")
    elif text == "📊 প্রোফাইল":
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        bal = cursor.fetchone()[0]
        bot.send_message(user_id, f"👤 **আপনার প্রোফাইল**\n\n🆔 আইডি: `{user_id}`\n💰 ব্যালেন্স: {bal:.2f} টাকা")
    elif text == "👥 রেফার করুন":
        bot.send_message(user_id, f"🔗 **আপনার রেফারেল লিংক:**\nhttps://t.me/{bot.get_me().username}?start={user_id}")
    elif text == "💳 টাকা তুলুন":
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        bal = cursor.fetchone()[0]
        if bal < 20:
            bot.send_message(user_id, f"❌ সর্বনিম্ন ২০ টাকা লাগবে। আপনার ব্যালেন্স: {bal:.2f} টাকা।")
        else:
            bot.send_message(user_id, "💸 উইথড্র করার সিস্টেমটি প্রক্রিয়াধীন রয়েছে।")
    elif text == "🏆 লিডারবোর্ড":
        bot.send_message(user_id, "🏆 শীর্ষ ১০ জন ইউজারের তালিকা শীঘ্রই আসবে।")
    elif text == "📞 সাপোর্ট":
        bot.send_message(user_id, f"👨‍💻 যেকোনো সমস্যায় যোগাযোগ করুন: {CHANNEL_USERNAME}")
    elif text == "👑 অ্যাডমিন প্যানেল":
        if user_id == ADMIN_ID:
            cursor.execute("SELECT COUNT(*) FROM users")
            total = cursor.fetchone()[0]
            
            markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            markup.add(types.KeyboardButton("📊 মোট ইউজার"), types.KeyboardButton("📢 বিজ্ঞাপন পাঠান"), types.KeyboardButton("🔙 মেইন মেনু"))
            bot.send_message(user_id, f"👑 **অ্যাডমিন প্যানেল:**\n\n👥 মোট ইউজার: {total} জন", reply_markup=markup)
        else:
            bot.send_message(user_id, "❌ আপনি এই বটের অ্যাডমিন নন!")
    elif text == "📊 মোট ইউজার" and user_id == ADMIN_ID:
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        bot.send_message(user_id, f"📊 বটের মোট রেজিস্টার্ড ইউজার: {total} জন")
    elif text == "📢 বিজ্ঞাপন পাঠান" and user_id == ADMIN_ID:
        cursor.execute("UPDATE users SET broadcast_state = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        bot.send_message(user_id, "📝 বিজ্ঞাপনের মেসেজটি লিখুন এবং সেন্ড করুন (এটি সবার কাছে চলে যাবে):")
    elif text == "🔙 মেইন মেনু":
        bot.send_message(user_id, "🔙 মেইন মেনুতে ফিরে আসা হয়েছে।", reply_markup=main_menu())
    
    conn.close()

# --- WEBHOOK SERVER ---
@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://' + request.host + '/' + BOT_TOKEN)
    return "Bot is running live!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
