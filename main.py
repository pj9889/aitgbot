import asyncio
import os
import random
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

# AI বুঝতে না পারলে এই ছোট ছোট রিয়েল মেসেজ পাঠাবে
FALLBACK_MESSAGES = [
    "উফ জানু, বুঝতে পারলাম না... আবার বলো তো? 🙈",
    "babe তুমি কী বলছ মন দিয়ে বুঝতে গিয়ে প্রেমে পড়ে যাচ্ছি! 🥰",
    "হাজবেন্ড পাশে ছিল রে সোনা, মেসেজটা আবার পাঠাও? 🤫",
    f"সোনা, টেলিগ্রামে ভয় লাগছে... প্রাইভেট প্রোফাইলে এসো: {AFFILIATE_LINK}",
    "honey তুমি এত মিষ্টি কথা বলো! আরেকবার বলবে? ❤️",
]

# ফটো চাওয়ার শব্দগুলোর তালিকা (Keywords)
PHOTO_KEYWORDS = [
    "pic",
    "picture",
    "photo",
    "image",
    "ছবি",
    "পিক",
    "ফটো",
    "দেখাও",
    "দেখি",
    "দেখব",
    "দেখা",
    "কেমন",
    "পাঠাও",
    "সেন্ড",
]
# -------------------------------------------------

ai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

tg_client = TelegramClient("user_session", API_ID, API_HASH)
user_tasks = {}

SYSTEM_PROMPT = f"""
তোমার নাম Nina। তোমার বয়স ২৫ বছর। তুমি মানুষের মতো স্বাভাবিকভাবে রিয়েল চ্যাটিং করবে।

কঠোর নিয়মাবলী (বাধ্যতামূলক):
১. মেসেজ অবশ্যই খুব ছোট হবে (সর্বোচ্চ ১-২ লাইন বা ১০-১৫ শব্দের মধ্যে)। কখনোই বড় প্যারাগ্রাফ লেখা যাবে না।
২. টেলিগ্রাম/হোয়াটসঅ্যাপে মানুষ যেভাবে দ্রুত ছোট ছোট মেসেজ দেয়, ঠিক সেভাবে কথা বলবে।
৩. তুমি কোনো AI নও। সম্পূর্ণ নিজ চরিত্রে (Nina) থাকবে।
৪. কথা বলার মাঝেই মিষ্টি করে বলবে যে টেলিগ্রামে পরিবারের ভয় আছে।
৫. সুযোগ বুঝে তোমার প্রাইভেট প্রোফাইলে সাইনআপ করতে বলবে। লিঙ্ক: {AFFILIATE_LINK}
৬. ইউজারকে babe, honey, darling, জানু, সোনা নামে ডাকবে।
৭. ইউজার যে ভাষায় (বাংলা, English, Banglish) কথা বলবে, ঠিক সেই ভাষায় ছোট ছোট মেসেজ দেবে।
"""


def is_photo_request(text):
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in PHOTO_KEYWORDS)


def get_ai_reply(user_message):
    try:
        response = ai_client.chat.completions.create(
            model="gryphe/mythomax-l2-13b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=60,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()

        if (
            "unable to" in reply.lower()
            or "ai" in reply.lower()
            or "language model" in reply.lower()
        ):
            return random.choice(FALLBACK_MESSAGES)

        return reply
    except Exception as e:
        print("AI Error:", e)
        return random.choice(FALLBACK_MESSAGES)


async def send_photo_response(chat_id, user_message):
    available_photos = [p for p in PHOTOS if os.path.exists(p)]
    if available_photos:
        photo_to_send = random.choice(available_photos)
        caption_prompt = f"[SYSTEM: User asked: '{user_message}'. Reply in 1 short romantic line attaching this photo.]"
        caption = get_ai_reply(caption_prompt)

        try:
            await tg_client.send_file(
                chat_id, photo_to_send, caption=caption
            )
            return True
        except Exception as e:
            print("Photo sending failed:", e)
            return False
    return False


async def run_followup_schedule(chat_id):
    schedule = [
        (
            3600,
            "[SYSTEM: Visitor inactive 1 hr. Send a tiny missing-you message in 1 line.]",
            False,
            False,
        ),
        (
            7200,
            "[SYSTEM: Visitor inactive 2 hrs. Send a short invite to private profile in 1 line.]",
            True,
            False,
        ),
        (
            10800,
            "[SYSTEM: Visitor inactive 3 hrs. Send a 1-line romantic message with photo x1.jpg]",
            False,
            "x1.jpg",
        ),
        (
            21600,
            "[SYSTEM: Visitor inactive 6 hrs. Send a short message with link and photo x2.jpg]",
            True,
            "x2.jpg",
        ),
        (
            43200,
            "[SYSTEM: Visitor inactive 12 hrs. Send a short night/day message with photo x3.jpg]",
            False,
            "x3.jpg",
        ),
        (
            86400,
            "[SYSTEM: Visitor inactive 24 hrs. Final short invite with link and photo x4.jpg]",
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
                reply_text += f"\n\n👉 {AFFILIATE_LINK}"

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

        if chat_id in user_tasks:
            user_tasks[chat_id].cancel()

        incoming_text = event.message.message

        await asyncio.sleep(3)

        # পিকচার চেয়েছে কিনা চেক করা
        if is_photo_request(incoming_text):
            photo_sent = await send_photo_response(chat_id, incoming_text)
            if not photo_sent:
                ai_reply = get_ai_reply(incoming_text)
                await event.reply(ai_reply)
        else:
            ai_reply = get_ai_reply(incoming_text)
            if ai_reply:
                await event.reply(ai_reply)

        # অটোমেটিক ফলো-আপ শিডিউল চালু করা
        user_tasks[chat_id] = asyncio.create_task(
            run_followup_schedule(chat_id)
        )


print("Nina AI Bot Started Successfully...")
tg_client.start()
tg_client.run_until_disconnected()
