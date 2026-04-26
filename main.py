from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import random

TOKEN = "8781955789:AAHgvWcAHWxit_FxfkpVYXI18eLNJYKich8"
ADMIN_IDS = [1358137735, 8438490479]

duels = {}
stats = {}

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

# ─── Yordamchi ───────────────────────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def init_stats(username: str):
    if username not in stats:
        stats[username] = {"wins": 0, "losses": 0}

def is_group(update: Update) -> bool:
    return update.effective_chat.type in ("group", "supergroup")

def mention(username: str) -> str:
    return f"@{username}"

# ─── Foydalanuvchi buyruqlari ─────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = "guruh" if is_group(update) else "private"
    await update.message.reply_text(
        f"⚔️ *Duel Bot* — siz {chat_type} chatdasiz\n\n"
        "📌 *Buyruqlar:*\n"
        "/duel @username — duel boshlash\n"
        "/mystats — o'z statistikangiz\n"
        "/top — eng yaxshi o'yinchilar\n\n"
        "💡 Bot guruhda ham, privateda ham ishlaydi!",
        parse_mode="Markdown"
    )

async def duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user1 = update.message.from_user.username

    if not user1:
        await update.message.reply_text("❌ Username o'rnatilmagan!")
        return

    if not context.args:
        await update.message.reply_text("❓ Kim bilan duel?\nMisol: /duel @username")
        return

    user2 = context.args[0].replace("@", "")

    if user1 == user2:
        await update.message.reply_text("❌ O'zingiz bilan duel qila olmaysiz!")
        return

    if chat_id in duels and duels[chat_id].get("active"):
        d = duels[chat_id]
        await update.message.reply_text(
            f"⚠️ Bu chatda allaqachon duel bor!\n"
            f"⚔️ {mention(d['p1'])} vs {mention(d['p2'])}"
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

    await update.message.reply_text(
        f"⚔️ *Duel boshlandi!*\n\n"
        f"🔵 {mention(user1)} — 100 HP\n"
        f"🔴 {mention(user2)} — 100 HP\n\n"
        f"📌 Faqat duel ishtirokchilari javob bera oladi!\n"
        f"Birinchi to'g'ri javob bergan raqibdan 10 HP olib qo'yadi.",
        parse_mode="Markdown"
    )
    await send_question(update, context)

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        + f"\n\n🔵 {mention(p1)}: {duel_data['hp'][p1]} HP\n"
        f"🔴 {mention(p2)}: {duel_data['hp'][p2]} HP"
    )
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")

async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in duels:
        return

    duel_data = duels[chat_id]
    if not duel_data["active"] or duel_data.get("answered"):
        return

    user = update.message.from_user.username
    if not user or user not in (duel_data["p1"], duel_data["p2"]):
        return

    msg = update.message.text.strip().upper()
    if msg not in ("A", "B", "C", "D"):
        return

    if msg == duel_data["current_answer"]:
        duel_data["answered"] = True
        opponent = duel_data["p1"] if user == duel_data["p2"] else duel_data["p2"]
        duel_data["hp"][opponent] -= 10

        await update.message.reply_text(
            f"✅ {mention(user)} to'g'ri javob berdi!\n"
            f"💥 {mention(opponent)} -10 HP → {duel_data['hp'][opponent]} HP qoldi"
        )

        if duel_data["hp"][opponent] <= 0 or duel_data["round"] >= 5:
            await end_duel(update, context, winner=user, loser=opponent)
        else:
            await send_question(update, context)
    else:
        await update.message.reply_text(f"❌ {mention(user)} noto'g'ri javob!")

async def end_duel(update: Update, context: ContextTypes.DEFAULT_TYPE, winner: str, loser: str):
    chat_id = update.effective_chat.id
    duel_data = duels[chat_id]

    if duel_data["hp"][winner] < duel_data["hp"][loser]:
        winner, loser = loser, winner

    stats[winner]["wins"] += 1
    stats[loser]["losses"] += 1
    duel_data["active"] = False

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"🏆 *Duel yakunlandi!*\n\n"
            f"🥇 G'olib: {mention(winner)}\n"
            f"💀 Yutqazdi: {mention(loser)}\n\n"
            f"🔵 {mention(duel_data['p1'])}: {duel_data['hp'][duel_data['p1']]} HP\n"
            f"🔴 {mention(duel_data['p2'])}: {duel_data['hp'][duel_data['p2']]} HP\n\n"
            f"Yangi duel: /duel @username"
        ),
        parse_mode="Markdown"
    )

async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.username
    if not user or user not in stats:
        await update.message.reply_text("📊 Siz hali birorta duelda qatnashmadingiz.")
        return
    s = stats[user]
    total = s["wins"] + s["losses"]
    winrate = round(s["wins"] / total * 100) if total > 0 else 0
    await update.message.reply_text(
        f"📊 *{mention(user)} statistikasi:*\n\n"
        f"✅ G'alabalar: {s['wins']}\n"
        f"❌ Mag'lubiyatlar: {s['losses']}\n"
        f"🎯 Winrate: {winrate}%",
        parse_mode="Markdown"
    )

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not stats:
        await update.message.reply_text("🏅 Hali statistika yo'q.")
        return
    sorted_players = sorted(stats.items(), key=lambda x: x[1]["wins"], reverse=True)[:10]
    text = "🏅 *Top O'yinchilar:*\n\n"
    for i, (username, s) in enumerate(sorted_players, 1):
        total = s["wins"] + s["losses"]
        winrate = round(s["wins"] / total * 100) if total > 0 else 0
        text += f"{i}. {mention(username)} — {s['wins']}W / {s['losses']}L ({winrate}%)\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ─── Admin buyruqlari ─────────────────────────────────────────────────────────

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Ruxsat yo'q!")
        return
    await update.message.reply_text(
        "🛠 *Admin Panel:*\n\n"
        "/admin\\_stats — umumiy statistika\n"
        "/stop\\_duel — joriy dualni to'xtatish\n"
        "/reset\\_stats — barcha statistikani tozalash\n"
        "/list\\_duels — faol duellar ro'yxati",
        parse_mode="Markdown"
    )

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Ruxsat yo'q!")
        return
    active_duels = sum(1 for d in duels.values() if d.get("active"))
    await update.message.reply_text(
        f"📈 *Umumiy statistika:*\n\n"
        f"👥 Jami o'yinchilar: {len(stats)}\n"
        f"⚔️ Tugagan duellar: {sum(s['wins'] for s in stats.values())}\n"
        f"🔥 Faol duellar: {active_duels}\n"
        f"❓ Jami savollar: {len(questions)}",
        parse_mode="Markdown"
    )

async def stop_duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Ruxsat yo'q!")
        return
    chat_id = update.effective_chat.id
    if chat_id in duels and duels[chat_id].get("active"):
        d = duels[chat_id]
        duels[chat_id]["active"] = False
        await update.message.reply_text(
            f"🛑 Admin tomonidan duel to'xtatildi.\n"
            f"⚔️ {mention(d['p1'])} vs {mention(d['p2'])}"
        )
    else:
        await update.message.reply_text("⚠️ Bu chatda faol duel yo'q.")

async def reset_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Ruxsat yo'q!")
        return
    stats.clear()
    await update.message.reply_text("✅ Barcha statistika tozalandi.")

async def list_duels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Ruxsat yo'q!")
        return
    active = [(cid, d) for cid, d in duels.items() if d.get("active")]
    if not active:
        await update.message.reply_text("⚠️ Faol duellar yo'q.")
        return
    text = f"🔥 *Faol duellar ({len(active)} ta):*\n\n"
    for cid, d in active:
        text += (
            f"Chat: `{cid}` ({d.get('chat_type', '?')})\n"
            f"⚔️ {mention(d['p1'])} ({d['hp'][d['p1']]} HP) vs "
            f"{mention(d['p2'])} ({d['hp'][d['p2']]} HP)\n"
            f"📌 Round: {d['round']}/5\n\n"
        )
    await update.message.reply_text(text, parse_mode="Markdown")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TOKEN).build()

    # Foydalanuvchi
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("duel", duel))
    app.add_handler(CommandHandler("mystats", my_stats))
    app.add_handler(CommandHandler("top", top))

    # Admin
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("admin_stats", admin_stats))
    app.add_handler(CommandHandler("stop_duel", stop_duel))
    app.add_handler(CommandHandler("reset_stats", reset_stats))
    app.add_handler(CommandHandler("list_duels", list_duels))

    # Javob handler
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & (filters.ChatType.GROUPS | filters.ChatType.PRIVATE),
        answer
    ))

    print("✅ Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
