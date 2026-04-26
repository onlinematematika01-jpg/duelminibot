from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import random

TOKEN = "8781955789:AAHgvWcAHWxit_FxfkpVYXI18eLNJYKich8"
ADMIN_IDS = [8438490479, 1358137735]  # Admin Telegram ID'larini kiriting

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

def is_group(update: Update) -> bool:
    return update.effective_chat.type in ("group", "supergroup")

def get_mention(username: str) -> str:
    return f"@{username}"

# ─── Foydalanuvchi buyruqlari ─────────────────────────────────────────────────

def start(update: Update, context: CallbackContext):
    chat_type = "guruh" if is_group(update) else "private"
    update.message.reply_text(
        f"⚔️ *Duel Bot* — siz {chat_type} chatdasiz\n\n"
        "📌 *Buyruqlar:*\n"
        "/duel @username — duel boshlash\n"
        "/mystats — o'z statistikangiz\n"
        "/top — eng yaxshi o'yinchilar\n\n"
        "💡 Bot guruhda ham, privateda ham ishlaydi!",
        parse_mode=ParseMode.MARKDOWN
    )

def duel(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user1 = update.message.from_user.username

    if not user1:
        update.message.reply_text("❌ Username o'rnatilmagan! Telegram sozlamalaridan username qo'shing.")
        return

    if not context.args:
        update.message.reply_text("❓ Kim bilan duel?\nMisol: /duel @username")
        return

    user2 = context.args[0].replace("@", "")

    if user1 == user2:
        update.message.reply_text("❌ O'zingiz bilan duel qila olmaysiz!")
        return

    if chat_id in duels and duels[chat_id].get("active"):
        d = duels[chat_id]
        update.message.reply_text(
            f"⚠️ Bu chatda allaqachon duel bor!\n"
            f"⚔️ {get_mention(d['p1'])} vs {get_mention(d['p2'])}"
        )
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
        "active": True,
        "chat_type": update.effective_chat.type
    }

    update.message.reply_text(
        f"⚔️ *Duel boshlandi!*\n\n"
        f"🔵 {get_mention(user1)} — 100 HP\n"
        f"🔴 {get_mention(user2)} — 100 HP\n\n"
        f"📌 Faqat duel ishtirokchilari javob bera oladi!\n"
        f"Birinchi to'g'ri javob bergan raqibdan 10 HP olib qo'yadi.",
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
        + f"\n\n🔵 {get_mention(p1)}: {duel_data['hp'][p1]} HP\n"
        f"🔴 {get_mention(p2)}: {duel_data['hp'][p2]} HP"
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
            f"✅ {get_mention(user)} to'g'ri javob berdi!\n"
            f"💥 {get_mention(opponent)} -10 HP → {duel_data['hp'][opponent]} HP qoldi"
        )

        if duel_data["hp"][opponent] <= 0 or duel_data["round"] >= 5:
            end_duel(update, context, winner=user, loser=opponent)
        else:
            send_question(update, context)
    else:
        update.message.reply_text(f"❌ {get_mention(user)} noto'g'ri javob!")

def end_duel(update, context, winner, loser):
    chat_id = update.effective_chat.id
    duel_data = duels[chat_id]

    if duel_data["hp"][winner] < duel_data["hp"][loser]:
        winner, loser = loser, winner

    stats[winner]["wins"] += 1
    stats[loser]["losses"] += 1
    duel_data["active"] = False

    context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"🏆 *Duel yakunlandi!*\n\n"
            f"🥇 G'olib: {get_mention(winner)}\n"
            f"💀 Yutqazdi: {get_mention(loser)}\n\n"
            f"🔵 {get_mention(duel_data['p1'])}: {duel_data['hp'][duel_data['p1']]} HP\n"
            f"🔴 {get_mention(duel_data['p2'])}: {duel_data['hp'][duel_data['p2']]} HP\n\n"
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
    total = s["wins"] + s["losses"]
    winrate = round(s["wins"] / total * 100) if total > 0 else 0
    update.message.reply_text(
        f"📊 *{get_mention(user)} statistikasi:*\n\n"
        f"✅ G'alabalar: {s['wins']}\n"
        f"❌ Mag'lubiyatlar: {s['losses']}\n"
        f"🎯 Winrate: {winrate}%",
        parse_mode=ParseMode.MARKDOWN
    )

def top(update: Update, context: CallbackContext):
    if not stats:
        update.message.reply_text("🏅 Hali statistika yo'q.")
        return
    sorted_players = sorted(stats.items(), key=lambda x: x[1]["wins"], reverse=True)[:10]
    text = "🏅 *Top O'yinchilar:*\n\n"
    for i, (username, s) in enumerate(sorted_players, 1):
        total = s["wins"] + s["losses"]
        winrate = round(s["wins"] / total * 100) if total > 0 else 0
        text += f"{i}. {get_mention(username)} — {s['wins']}W / {s['losses']}L ({winrate}%)\n"
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
        "/reset\\_stats — barcha statistikani tozalash\n"
        "/list\\_duels — faol duellar ro'yxati",
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
        f"🔥 Faol duellar: {active_duels}\n"
        f"❓ Jami savollar: {len(questions)}",
        parse_mode=ParseMode.MARKDOWN
    )

def stop_duel(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        update.message.reply_text("🚫 Ruxsat yo'q!")
        return
    chat_id = update.effective_chat.id
    if chat_id in duels and duels[chat_id].get("active"):
        d = duels[chat_id]
        duels[chat_id]["active"] = False
        update.message.reply_text(
            f"🛑 Admin tomonidan duel to'xtatildi.\n"
            f"⚔️ {get_mention(d['p1'])} vs {get_mention(d['p2'])}"
        )
    else:
        update.message.reply_text("⚠️ Bu chatda faol duel yo'q.")

def reset_stats(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        update.message.reply_text("🚫 Ruxsat yo'q!")
        return
    stats.clear()
    update.message.reply_text("✅ Barcha statistika tozalandi.")

def list_duels(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        update.message.reply_text("🚫 Ruxsat yo'q!")
        return
    active = [(cid, d) for cid, d in duels.items() if d.get("active")]
    if not active:
        update.message.reply_text("⚠️ Faol duellar yo'q.")
        return
    text = f"🔥 *Faol duellar ({len(active)} ta):*\n\n"
    for cid, d in active:
        text += (
            f"Chat: `{cid}` ({d.get('chat_type', '?')})\n"
            f"⚔️ {get_mention(d['p1'])} ({d['hp'][d['p1']]} HP) vs "
            f"{get_mention(d['p2'])} ({d['hp'][d['p2']]} HP)\n"
            f"📌 Round: {d['round']}/5\n\n"
        )
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Foydalanuvchi buyruqlari
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("duel", duel))
    dp.add_handler(CommandHandler("mystats", my_stats))
    dp.add_handler(CommandHandler("top", top))

    # Admin buyruqlari
    dp.add_handler(CommandHandler("admin", admin_panel))
    dp.add_handler(CommandHandler("admin_stats", admin_stats))
    dp.add_handler(CommandHandler("stop_duel", stop_duel))
    dp.add_handler(CommandHandler("reset_stats", reset_stats))
    dp.add_handler(CommandHandler("list_duels", list_duels))

    # Javob handler — guruh va private ikkalasida ham ishlaydi
    dp.add_handler(MessageHandler(
        Filters.text & ~Filters.command & (Filters.chat_type.groups | Filters.chat_type.private),
        answer
    ))

    print("✅ Bot ishga tushdi...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
