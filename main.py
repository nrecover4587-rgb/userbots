import asyncio
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from pymongo import MongoClient

from config import API_ID, API_HASH, BOT_TOKEN, OWNER_IDS, MONGO_URL

print("🔄 Starting controller system...")

mongo = MongoClient(MONGO_URL)
db = mongo["pyro_controller"]
sessions_col = db["sessions"]
texts_col = db["texts"]

bot = TelegramClient("controller_bot", API_ID, API_HASH)
user_clients = []

# ---------------- TEXT DATABASE ---------------- #

def get_texts():
    doc = texts_col.find_one({"_id": "global"})
    return doc["texts"] if doc and "texts" in doc else []

def save_texts(texts):
    texts_col.update_one(
        {"_id": "global"},
        {"$set": {"texts": texts}},
        upsert=True
    )

# ---------------- USER SESSION SYSTEM ---------------- #

async def start_user_session(session_string):
    for c in user_clients:
        if c.session.save() == session_string:
            return

    client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
    await client.start()
    user_clients.append(client)
    print("✅ User session loaded")

    @client.on(events.NewMessage(pattern=r"^\.attack (\d+)$"))
    async def attack(event):
        count = int(event.pattern_match.group(1))
        texts = get_texts()
        if not texts or count <= 0:
            return

        sent = 0
        while sent < count:
            try:
                await client.send_message(
                    event.chat_id,
                    texts[sent % len(texts)]
                )
                sent += 1
                await asyncio.sleep(1)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except Exception:
                break

# ---------------- STARTUP ---------------- #

async def startup():
    for s in sessions_col.find():
        try:
            await start_user_session(s["session"])
        except Exception:
            pass
    print(f"🚀 Loaded {len(user_clients)} sessions")

# ---------------- START MESSAGE ---------------- #

@bot.on(events.NewMessage(pattern=r"^/start$"))
async def start_cmd(e):
    start_text = f"""
🤖 **PYRO CONTROLLER SYSTEM**

━━━━━━━━━━━━━━━━━━
⚡ Advanced Userbot Controller  
🚀 Multi Session Support  
💾 Mongo Database Connected  
🟢 Active Sessions: {len(user_clients)}

━━━━━━━━━━━━━━━━━━
💎 Premium Automation • Fast • Secure
"""

    buttons = [
        [Button.inline("📊 Active Sessions", b"sessions")]
    ]

    await e.reply(start_text, buttons=buttons)

# ---------------- CALLBACK BUTTON ---------------- #

@bot.on(events.CallbackQuery(data=b"sessions"))
async def show_sessions(event):
    await event.answer()
    await event.edit(f"🟢 Active Sessions: {len(user_clients)}")

# ---------------- ADD SESSION (PREMIUM PROTECTED) ---------------- #

@bot.on(events.NewMessage(pattern=r"^/addsession$"))
async def addsession(e):

    # 🚫 Non Owner = Premium Required
    if e.sender_id not in OWNER_IDS:
        return await e.reply(
            "💎 **Premium Required!**\n\n"
            "This feature is available for premium users only.\n"
            "Contact Developer to purchase access."
        )

    # ✅ Owner Logic
    if not e.is_reply:
        return await e.reply("Reply to session string")

    session = (await e.get_reply_message()).text.strip()

    if sessions_col.find_one({"session": session}):
        return await e.reply("Session already exists")

    try:
        await start_user_session(session)
        sessions_col.insert_one({"session": session})
        await e.reply("✅ Session added successfully")
    except Exception:
        await e.reply("❌ Invalid session string")

# ---------------- OWNER COMMANDS ---------------- #

@bot.on(events.NewMessage(from_users=OWNER_IDS, pattern=r"^/listsessions$"))
async def listsessions(e):
    await e.reply(f"Active sessions: {len(user_clients)}")

@bot.on(events.NewMessage(from_users=OWNER_IDS, pattern=r"^/removesession (\d+)$"))
async def removesession(e):
    idx = int(e.pattern_match.group(1)) - 1
    if idx not in range(len(user_clients)):
        return await e.reply("Invalid index")

    client = user_clients.pop(idx)
    sessions_col.delete_one({"session": client.session.save()})
    await client.disconnect()
    await e.reply("🗑 Session removed")

@bot.on(events.NewMessage(from_users=OWNER_IDS, pattern=r"^/add$"))
async def add_text(e):
    if not e.is_reply:
        return
    t = (await e.get_reply_message()).text
    texts = get_texts()
    texts.append(t)
    save_texts(texts)
    await e.reply("➕ Text added")

@bot.on(events.NewMessage(from_users=OWNER_IDS, pattern=r"^/texts$"))
async def list_texts(e):
    texts = get_texts()
    if not texts:
        return await e.reply("No texts saved")
    msg = "\n".join(f"{i+1}. {t[:40]}" for i, t in enumerate(texts))
    await e.reply(msg)

@bot.on(events.NewMessage(from_users=OWNER_IDS, pattern=r"^/remove (\d+)$"))
async def remove_text(e):
    idx = int(e.pattern_match.group(1)) - 1
    texts = get_texts()
    if idx not in range(len(texts)):
        return await e.reply("Invalid index")
    texts.pop(idx)
    save_texts(texts)
    await e.reply("🗑 Text removed")

@bot.on(events.NewMessage(from_users=OWNER_IDS, pattern=r"^/clear$"))
async def clear_texts(e):
    save_texts([])
    await e.reply("🧹 All texts cleared")

# ---------------- MAIN ---------------- #

async def main():
    await bot.start(bot_token=BOT_TOKEN)
    await startup()
    print("🟢 System running")
    await bot.run_until_disconnected()

asyncio.run(main())
