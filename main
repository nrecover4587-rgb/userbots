import asyncio, time, random
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID, OWNER_USERNAME, MONGO_URL

mongo = MongoClient(MONGO_URL)
db = mongo["premium_bot"]
users_col = db["users"]
sessions_col = db["sessions"]
texts_col = db["texts"]

bot = Client("premium_controller", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
active_clients = {}

def now():
    return int(time.time())

def is_premium(uid):
    if uid == OWNER_ID:
        return True
    user = users_col.find_one({"user_id": uid})
    if not user:
        return False
    return user["expiry"] == 0 or user["expiry"] > now()

def premium_message():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Contact Owner for Premium", url=f"https://t.me/{OWNER_USERNAME}")]]
    )

async def start_user_session(uid, string):
    client = TelegramClient(StringSession(string), API_ID, API_HASH)
    await client.start()
    active_clients[uid] = client

@bot.on_message(filters.command("start"))
async def start_cmd(_, m):
    if is_premium(m.from_user.id):
        await m.reply(
            "Premium access is active.\n\nUse /help to see available commands."
        )
    else:
        await m.reply(
            "Premium access is required to use this bot.",
            reply_markup=premium_message()
        )

@bot.on_message(filters.command("help"))
async def help_cmd(_, m):
    if not is_premium(m.from_user.id):
        await m.reply(
            "Premium access is required to use this bot.",
            reply_markup=premium_message()
        )
        return
    await m.reply(
        "/addsession – Add your account session\n"
        "/add – Save a text (reply)\n"
        "/texts – View saved texts\n"
        "/remove <number> – Remove a text\n"
        "/clear – Clear all texts\n"
        "/blast <user> <count> – Send random texts\n"
        "/spam <user> <count> – Send repeated text\n"
        "/random <user> <count> – Shuffle texts\n"
        "/profile – View your premium status"
    )

@bot.on_message(filters.command("profile"))
async def profile_cmd(_, m):
    uid = m.from_user.id
    if not is_premium(uid):
        await m.reply(
            "Premium access is required.",
            reply_markup=premium_message()
        )
        return
    user = users_col.find_one({"user_id": uid})
    if uid == OWNER_ID:
        await m.reply("Account Type: Owner\nPremium: Lifetime")
    else:
        expiry = "Lifetime" if user["expiry"] == 0 else time.strftime("%d %b %Y", time.localtime(user["expiry"]))
        await m.reply(f"Premium Status: Active\nExpires: {expiry}")

@bot.on_message(filters.command("givepremium") & filters.user(OWNER_ID))
async def givepremium_cmd(_, m):
    args = m.text.split()
    if len(args) != 3:
        return
    uid = int(args[1])
    duration = args[2]
    if duration.lower() == "lifetime":
        expiry = 0
    else:
        expiry = now() + int(duration) * 86400
    users_col.update_one(
        {"user_id": uid},
        {"$set": {"premium": True, "expiry": expiry}},
        upsert=True
    )
    await m.reply("Premium granted successfully.")

@bot.on_message(filters.command("addsession"))
async def addsession_cmd(_, m):
    if not is_premium(m.from_user.id):
        await m.reply(
            "Premium access is required.",
            reply_markup=premium_message()
        )
        return
    if not m.reply_to_message:
        return
    string = m.reply_to_message.text.strip()
    await start_user_session(m.from_user.id, string)
    sessions_col.update_one(
        {"user_id": m.from_user.id},
        {"$set": {"string": string}},
        upsert=True
    )
    await m.reply("Session added successfully.")

@bot.on_message(filters.command("add"))
async def add_text(_, m):
    if not is_premium(m.from_user.id):
        await m.reply("Premium access is required.", reply_markup=premium_message())
        return
    if not m.reply_to_message:
        return
    texts_col.update_one(
        {"user_id": m.from_user.id},
        {"$push": {"texts": m.reply_to_message.text}},
        upsert=True
    )
    await m.reply("Text saved.")

@bot.on_message(filters.command("texts"))
async def list_texts(_, m):
    doc = texts_col.find_one({"user_id": m.from_user.id})
    if not doc or not doc.get("texts"):
        await m.reply("No texts found.")
        return
    msg = "\n".join(f"{i+1}. {t[:40]}" for i, t in enumerate(doc["texts"]))
    await m.reply(msg)

@bot.on_message(filters.command("remove"))
async def remove_text(_, m):
    args = m.text.split()
    if len(args) != 2:
        return
    idx = int(args[1]) - 1
    doc = texts_col.find_one({"user_id": m.from_user.id})
    if not doc or idx >= len(doc["texts"]):
        return
    doc["texts"].pop(idx)
    texts_col.update_one({"user_id": m.from_user.id}, {"$set": {"texts": doc["texts"]}})
    await m.reply("Text removed.")

@bot.on_message(filters.command("clear"))
async def clear_texts(_, m):
    texts_col.delete_one({"user_id": m.from_user.id})
    await m.reply("All texts cleared.")

async def send_loop(client, entity, texts, count, delay):
    for i in range(count):
        try:
            await client.send_message(entity, texts[i % len(texts)])
            await asyncio.sleep(delay)
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)

@bot.on_message(filters.command(["blast", "spam", "random"]))
async def send_cmd(_, m):
    uid = m.from_user.id
    if not is_premium(uid) or uid not in active_clients:
        await m.reply("Premium access is required.", reply_markup=premium_message())
        return
    args = m.text.split()
    target = args[1]
    count = int(args[2])
    client = active_clients[uid]
    entity = await client.get_entity(target)
    doc = texts_col.find_one({"user_id": uid})
    texts = doc["texts"]
    if m.command[0] == "spam":
        texts = [texts[0]]
    elif m.command[0] == "random":
        random.shuffle(texts)
    await send_loop(client, entity, texts, count, 1)

async def main():
    for s in sessions_col.find():
        await start_user_session(s["user_id"], s["string"])
    await bot.start()
    await asyncio.Event().wait()

asyncio.run(main())
