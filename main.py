import asyncio
import random
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from pymongo import MongoClient

from config import API_ID, API_HASH, BOT_TOKEN, OWNER_IDS, MONGO_URL

print("🔄 Starting controller system...")

# ---------------- DATABASE ---------------- #

mongo = MongoClient(MONGO_URL)
db = mongo["pyro_controller"]
sessions_col = db["sessions"]
texts_col = db["texts"]

# ---------------- BOT INIT ---------------- #

bot = TelegramClient("controller_bot", API_ID, API_HASH)

user_clients = []
attack_tasks = {}

# ---------------- TEXT DATABASE ---------------- #

def get_texts():
    doc = texts_col.find_one({"_id": "global"})
    return doc["texts"] if doc else []

def save_texts(texts):
    texts_col.update_one(
        {"_id": "global"},
        {"$set": {"texts": texts}},
        upsert=True
    )

# ---------------- USER SESSION ---------------- #

async def start_user_session(session_string):

    for c in user_clients:
        if c.session.save() == session_string:
            return

    client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
    await client.start()

    user_clients.append(client)
    print("✅ User session loaded")

# ---------------- ATTACK COMMAND ---------------- #

    @client.on(events.NewMessage(pattern=r"\.attack ?(.*)"))
    async def attack_handler(event):

        args = event.pattern_match.group(1).split()

        if len(args) == 1:
            target = event.chat_id
            count = int(args[0])

        elif len(args) == 2:
            target = args[0]
            count = int(args[1])

        else:
            return await event.reply(
                "Usage:\n.attack 50\n.attack @username 50"
            )

        texts = get_texts()

        if not texts:
            return await event.reply("No texts saved")

        try:
            entity = await event.client.get_entity(target)
        except:
            return await event.reply("Invalid target")

        await event.reply(f"⚡ Attack Started\nTarget: {target}\nCount: {count}")

        async def run_attack():

            sent = 0

            while sent < count:

                try:

                    msg = texts[sent % len(texts)]

                    await event.client.send_message(entity, msg)

                    sent += 1

                    await asyncio.sleep(1)

                except FloodWaitError as e:

                    await asyncio.sleep(e.seconds)

                except Exception as err:

                    print("Attack error:", err)
                    break

        task = asyncio.create_task(run_attack())

        attack_tasks[event.sender_id] = task

# ---------------- STOP COMMAND ---------------- #

    @client.on(events.NewMessage(pattern=r"\.stop$"))
    async def stop_attack(event):

        task = attack_tasks.get(event.sender_id)

        if not task:
            return await event.reply("No attack running")

        task.cancel()

        await event.reply("🛑 Attack stopped")

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
🚀 Multi Session Management  
💾 Mongo Database Connected  
🟢 Active Sessions: {len(user_clients)}

━━━━━━━━━━━━━━━━━━
"""

    buttons = [
        [
            Button.url("👨‍💻 Developer", "https://t.me/Mrmental001"),
            Button.url("📞 Support", "https://t.me/mentalchatting")
        ],
        [
            Button.inline("📊 Active Sessions", b"sessions")
        ]
    ]

    await e.reply(start_text, buttons=buttons)

# ---------------- CALLBACK ---------------- #

@bot.on(events.CallbackQuery(data=b"sessions"))
async def show_sessions(event):

    await event.answer()

    await event.edit(f"🟢 Active Sessions: {len(user_clients)}")

# ---------------- ADD SESSION ---------------- #

@bot.on(events.NewMessage(pattern=r"^/addsession$"))
async def addsession(e):

    if e.sender_id not in OWNER_IDS:

        return await e.reply("Premium Required")

    if not e.is_reply:

        return await e.reply("Reply to session string")

    session = (await e.get_reply_message()).text.strip()

    if sessions_col.find_one({"session": session}):

        return await e.reply("Session already exists")

    try:

        await start_user_session(session)

        sessions_col.insert_one({"session": session})

        await e.reply("✅ Session added successfully")

    except:

        await e.reply("❌ Invalid session")

# ---------------- TEXT SYSTEM ---------------- #

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
