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
👨‍💻 Developer: @Mrmental001
📞 Support: @mentalchatting
📢 Updates: @codexempire

━━━━━━━━━━━━━━━━━━
💎 Premium Automation • Fast • Secure
"""

    buttons = [
        [
            Button.url("👨‍💻 Developer", "https://t.me/mrmental001"),
            Button.url("📞 Support", "https://t.me/mentalchatting")
        ],
        [
            Button.url("📢 Updates", "https://t.me/codexempire")
        ],
        [
            Button.inline("📊 Active Sessions", b"sessions")
        ]
    ]

    await e.reply(start_text, buttons=buttons)
