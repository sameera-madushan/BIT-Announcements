import requests
from bs4 import BeautifulSoup
from telegram import Bot
import time
import os
import asyncio
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
URL = os.getenv("URL")
LAST_ANNOUNCEMENT_FILE = os.getenv("LAST_ANNOUNCEMENT_FILE")

# Initialize Telegram Bot
bot = Bot(token=BOT_TOKEN)

def get_latest_announcement():
    """Fetch the latest announcement from the website."""
    response = requests.get(URL)
    if response.status_code != 200:
        raise Exception("Failed to fetch the webpage.")
    
    soup = BeautifulSoup(response.content, "html.parser")
    
    main_content = soup.find("div", {"id": "primary"})
    if not main_content:
        raise Exception("Could not find the main announcements container.")
    
    latest_announcement = main_content.find("h4").find("a")
    if not latest_announcement:
        raise Exception("No announcements found.")
    
    title = latest_announcement.text.strip()
    link = latest_announcement["href"]
    
    return title, link

async def send_telegram_message(title, link):
    """Send the announcement to the Telegram chat."""
    message = f"🆕 New Announcement:\n\n{title}\n🔗 {link}"
    await bot.send_message(chat_id=CHAT_ID, text=message)

def get_last_announcement():
    """Read the last announcement title from a file."""
    if os.path.exists(LAST_ANNOUNCEMENT_FILE):
        with open(LAST_ANNOUNCEMENT_FILE, "r") as file:
            return file.read().strip()
    return ""

def save_last_announcement(title):
    """Save the latest announcement title to a file."""
    with open(LAST_ANNOUNCEMENT_FILE, "w") as file:
        file.write(title)

async def main():
    print("🔄 Starting the Announcement Bot...")
    while True:
        try:

            title, link = get_latest_announcement()
            last_title = get_last_announcement()

            if title != last_title:
                print(f"✅ New announcement found: {title}")
                await send_telegram_message(title, link)
                save_last_announcement(title)
            else:
                print("ℹ️ No new announcement found.")

        except Exception as e:
            print(f"❌ Error: {e}")

        time.sleep(1800)

if __name__ == "__main__":
    asyncio.run(main())
