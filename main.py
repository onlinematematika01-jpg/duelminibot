from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import random

TOKEN = "YOUR_BOT_TOKEN"
ADMIN_IDS = [123456789]  # O'z Telegram ID'ingizni kiriting

duels = {}
stats = {}  # {username: {"wins": 0, "losses": 0}}

questions = [
    {
        "q": "Avengers lideri kim?",
        "options": ["A) Iron Man", "B) Captain America", "C) Thor", "D) Hulk"],
        "answer": "B"
    },
    {
        "q": "Thor qayerdan?",
        "options": ["A) Earth", "B) Asgard", "C) Titan", "D) Mars"],
        "answer": "B"
    },
    {
        "q": "Iron Man haqiqiy ismi nima?",
        "options": ["A) Steve Rogers", "B) Bruce Banner", "C) Tony Stark", "D) Clint Barton"],
        "answer": "C"
    },
    {
        "q": "Spider-Man kimdan kuch oldi?",
        "options": ["A) Radioaktiv o'rgimchak", "B) Laboratoriya", "C) Ilon", "D) Meteor"],
        "answer": "A"
    },
    {
        "q": "Black Widow qaysi davlatdan?",
        "options": ["A) AQSh", "B) Germaniya", "C) Rossiya", "D) Xitoy"],
        "answer": "C"
    },
]

# ─── Yordamchi funksiyalar ────────────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def init_stats(username: str):
    if username not in stats:
        stats[username] = {"wins": 0, "losses": 0}

# ─── Foydalanuvchi buyruqlari ─────────────────────────────────────────────────

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "⚔️ *Duel Bot*\n\n"
        "/duel @username — duel boshlash\n"
        "/mystats — o'z statistikangiz\n"
        "/top — eng yaxshi o'yinchilar",
        parse_mode=ParseMode.MARKDOWN
    )

def duel(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user1 = update.message.from_user.username

    if not user1:
        update.message.reply_text("❌ Username o'rnatilmagan!")
        return

    if not context.args:
        update.message.reply_text("❓ Kim bilan duel? /duel @username")
        return

    user2 = context.args[0].replace("@", "")

    if user1 == user2:
        update.message.reply_text("❌ O'zingiz bilan duel qila olmaysiz!")
        return

    if chat_id in duels and duels[chat_id].get("active"):
        update.message.reply_text("⚠️ Bu chatda allaqachon duel bor!")
        return

    init_stats(user1)
    init_stats(user2)

    duels[chat_id] = {
        "p1": user1,
        "p2": user2,
        "hp": {user1: 100, user2: 100},
        "round": 0,
        "current_answer": None,
        "answered": False,
        "active": True
    }

    update.message.reply_text(
        f"⚔️ *Duel boshlandi!*\n\n"
        f"🔵 @{user1} (100 HP)\n"
        f"🔴 @{user2} (100 HP)\n\n"
        f"Birinchi to'g'ri javob bergan 10 HP olib qo'yadi!",
        parse_mode=ParseMode.MARKDOWN
    )
    send_question(update, context)

def send_question(update, context):
    chat_id = update.effective_chat.id
    duel_data = duels[chat_id]

    q = random.choice(questions)
    duel_data["current_answer"] = q["answer"]
    duel_data["round"] += 1
    duel_data["answered"] = False

    p1, p2 = duel_data["p1"], duel_data["p2"]
    text = (
        f"❓ *{duel_data['round']}-savol:*\n{q['q']}\n\n"
        + "\n".join(q["options"])
        + f"\n\n💙 @{p1}: {duel_data['hp'][p1]} HP\n"
        f"❤️ @{p2}: {duel_data['hp'][p2]} HP"
    )
    context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)

def answer(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id not in duels:
        return

    duel_data = duels[chat_id]
    if not duel_data["active"] or duel_data.get("answered"):
        return

    user = update.message.from_user.username
    if not user:
        return

    if user not in (duel_data["p1"], duel_data["p2"]):
        return

    msg = update.message.text.strip().upper()
    if msg not in ("A", "B", "C", "D"):
        return

    if msg == duel_data["current_answer"]:
        duel_data["answered"] = True
        opponent = duel_data["p1"] if user == duel_data["p2"] else duel_data["p2"]
        duel_data["hp"][opponent] -= 10

        update.message.reply_text(
            f"✅ @{user} to'g'ri javob berdi!\n"
            f"💥 @{opponent} -10 HP → {duel_data['hp'][opponent]} HP qoldi"
        )

        if duel_data["hp"][opponent] <= 0 or duel_data["round"] >= 5:
            end_duel(update, context, winner=user, loser=opponent)
        else:
            send_question(update, context)
    else:
        update.message.reply_text(f"❌ @{user} noto'g'ri!")

def end_duel(update, context, winner, loser):
    chat_id = update.effective_chat.id
    duel_data = duels[chat_id]

    # Agar round tugasa, HP ga qarab g'olibni aniqlash
    if duel_data["hp"][winner] <= 0:
        winner, loser = loser, winner

    stats[winner]["wins"] += 1
    stats[loser]["losses"] += 1

    duel_data["active"] = False

    context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"🏆 *Duel yakunlandi!*\n\n"
            f"🥇 G'olib: @{winner}\n"
            f"💀 Yutqazdi: @{loser}\n\n"
            f"Yangi duel: /duel @username"
        ),
        parse_mode=ParseMode.MARKDOWN
    )

def my_stats(update: Update, context: CallbackContext):
    user = update.message.from_user.username
    if not user or user not in stats:
        update.message.reply_text("📊 Siz hali birorta duelda qatnashmadingiz.")
        return
    s = stats[user]
    update.message.reply_text(
        f"📊 *@{user} statistikasi:*\n\n"
        f"✅ G'alabalar: {s['wins']}\n"
        f"❌ Mag'lubiyatlar: {s['losses']}",
        parse_mode=ParseMode.MARKDOWN
    )

def top(update: Update, context: CallbackContext):
    if not stats:
        update.message.reply_text("🏅 Hali statistika yo'q.")
        return
    sorted_players = sorted(stats.items(), key=lambda x: x[1]["wins"], reverse=True)[:10]
    text = "🏅 *Top O'yinchilar:*\n\n"
    for i, (username, s) in enumerate(sorted_players, 1):
        text += f"{i}. @{username} — {s['wins']}W / {s['losses']}L\n"
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ─── Admin buyruqlari ─────────────────────────────────────────────────────────

def admin_panel(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        update.message.reply_text("🚫 Ruxsat yo'q!")
        return
    update.message.reply_text(
        "🛠 *Admin Panel:*\n\n"
        "/admin\\_stats — umumiy statistika\n"
        "/stop\\_duel — joriy dualni to'xtatish\n"
        "/add\\_question — savol qo'shish (tez orada)\n"
        "/broadcast — xabar yuborish (tez orada)",
        parse_mode=ParseMode.MARKDOWN
    )

def admin_stats(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        update.message.reply_text("🚫 Ruxsat yo'q!")
        return
    total_players = len(stats)
    total_duels_ended = sum(s["wins"] for s in stats.values())
    active_duels = sum(1 for d in duels.values() if d.get("active"))
    update.message.reply_text(
        f"📈 *Umumiy statistika:*\n\n"
        f"👥 Jami o'yinchilar: {total_players}\n"
        f"⚔️ Tugagan duellar: {total_duels_ended}\n"
        f"🔥 Faol duellar: {active_duels}",
        parse_mode=ParseMode.MARKDOWN
    )

def stop_duel(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        update.message.reply_text("🚫 Ruxsat yo'q!")
        return
    chat_id = update.effective_chat.id
    if chat_id in duels and duels[chat_id].get("active"):
        duels[chat_id]["active"] = False
        update.message.reply_text("🛑 Admin tomonidan duel to'xtatildi.")
    else:
        update.message.reply_text("⚠️ Bu chatda faol duel yo'q.")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Foydalanuvchi
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("duel", duel))
    dp.add_handler(CommandHandler("mystats", my_stats))
    dp.add_handler(CommandHandler("top", top))

    # Admin
    dp.add_handler(CommandHandler("admin", admin_panel))
    dp.add_handler(CommandHandler("admin_stats", admin_stats))
    dp.add_handler(CommandHandler("stop_duel", stop_duel))

    # Javob handler
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, answer))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
