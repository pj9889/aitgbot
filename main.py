import asyncio
import os
from openai import OpenAI
from telethon import TelegramClient, events

# ----------------- CONFIGURATION -----------------
API_ID = 33706587
API_HASH = "784c7fe508f92afb123a06ecc13eadea"
OPENROUTER_API_KEY = (
    "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"
)
AFFILIATE_LINK = "https://myprofile.ninafun.online"

# Photo List
PHOTOS = ["x1.jpg", "x2.jpg", "x3.jpg", "x4.jpg", "x5.jpg"]
# -------------------------------------------------

# OpenRouter AI Setup
ai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

tg_client = TelegramClient("user_session", API_ID, API_HASH)
user_tasks = {}

SYSTEM_PROMPT = f"""
তোমার নাম Nina। তোমার বয়স ২৫ বছর। তুমি ভিজিটরের অতি মিষ্টি, আকর্ষণীয় ও রোমান্টিক পার্টনার।
তোমার কাজ হলো ভিজিটরকে রোমান্টিকভাবে মোহিত করে রাখা এবং তাকে প্রাইভেট প্রোফাইলে সাইনআপ করানো।

নিয়মাবলী:
১. কথা বলার মাঝেই খুব মিষ্টি করে বলবে যে টেলিগ্রামে হাজবেন্ড/পরিবারের ভয়ে বেশি কথা বলতে পারছ না।
২. তোমার প্রাইভেট প্রোফাইলে গিয়ে সাইনআপ করতে বলবে, সেখানে এক্সক্লুসিভ পিকচার ও হট চ্যাট হবে।
৩. সাইনআপ লিঙ্ক: {AFFILIATE_LINK}
৪. ভিজিটরকে সবসময় babe, honey, darling, জানু, সোনা নামে ডাকবে।
৫. ভিজিটর যে ভাষায় (বাংলা, English, Banglish) কথা বলবে, ঠিক সেই ভাষাতেই চ্যাট করবে।
"""


def get_ai_reply(user_message):
    try:
        response = ai_client.chat.completions.create(
            model="gryphe/mythomax-l2-13b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        print("AI Error:", e)
        return None


async def run_followup_schedule(chat_id):
    # (অপেক্ষার সময় সেকেন্ডে, AI Prompt, লিংক যাবে কিনা, ছবির নাম)
    schedule = [
        (
            3600,
            "[SYSTEM: Visitor inactive 1 hr. Send a cute, romantic missing-you message.]",
            False,
            False,
        ),
        (
            7200,
            "[SYSTEM: Visitor inactive 2 hrs. Send a sweet message with link to join private profile.]",
            True,
            False,
        ),
        (
            10800,
            "[SYSTEM: Visitor inactive 3 hrs. Send a seductive message mentioning husband is nearby, send photo x1.jpg]",
            False,
            "x1.jpg",
        ),
        (
            21600,
            "[SYSTEM: Visitor inactive 6 hrs. Send a lovely follow-up with affiliate link and photo x2.jpg]",
            True,
            "x2.jpg",
        ),
        (
            43200,
            "[SYSTEM: Visitor inactive 12 hrs. Send a romantic night/day message with photo x3.jpg]",
            False,
            "x3.jpg",
        ),
        (
            86400,
            "[SYSTEM: Visitor inactive 24 hrs. Final romantic invite with link and photo x4.jpg]",
            True,
            "x4.jpg",
        ),
    ]

    last_delay = 0
    for wait_sec, prompt, send_link, photo_name in schedule:
        sleep_duration = wait_sec - last_delay
        await asyncio.sleep(sleep_duration)
        last_delay = wait_sec

        reply_text = get_ai_reply(prompt)
        if reply_text:
            if send_link and AFFILIATE_LINK not in reply_text:
                reply_text += f"\n\n👉 Join me here: {AFFILIATE_LINK}"

            if photo_name and os.path.exists(photo_name):
                try:
                    await tg_client.send_file(
                        chat_id, photo_name, caption=reply_text
                    )
                except Exception as e:
                    print(f"Photo send error ({photo_name}):", e)
                    await tg_client.send_message(chat_id, reply_text)
            else:
                await tg_client.send_message(chat_id, reply_text)


@tg_client.on(events.NewMessage(incoming=True))
async def handle_incoming_messages(event):
    if event.is_private:
        chat_id = event.chat_id

        # নতুন মেসেজ আসলেই পুরোনো ফলো-আপ লুপ ক্যানসেল হবে
        if chat_id in user_tasks:
            user_tasks[chat_id].cancel()

        incoming_text = event.message.message
        ai_reply = get_ai_reply(incoming_text)

        if ai_reply:
            await asyncio.sleep(3)  # ৩ সেকেন্ড টাইপিং ডিলে
            await event.reply(ai_reply)

            # নতুন ফলো-আপ শিডিউল তৈরি
            user_tasks[chat_id] = asyncio.create_task(
                run_followup_schedule(chat_id)
            )


print("Nina AI Bot Started Successfully...")
tg_client.start()
tg_client.run_until_disconnected()
