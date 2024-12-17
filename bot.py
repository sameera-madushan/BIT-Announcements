from fastapi import FastAPI
from fastapi.responses import JSONResponse
from bs4 import BeautifulSoup
from telegram import Bot
from dotenv import load_dotenv
import requests
import os
import asyncio

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
URL = os.getenv("URL")
LAST_ANNOUNCEMENT_FILE = os.getenv("LAST_ANNOUNCEMENT_FILE")

bot = Bot(token=BOT_TOKEN)

app = FastAPI()

task_running = False


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


async def announcement_checker():
    """Periodic check for new announcements."""
    global task_running
    while task_running:
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
        await asyncio.sleep(1800) 


@app.on_event("startup")
async def startup_event():
    """Start the background task when the app starts."""
    global task_running
    if not task_running:
        task_running = True
        asyncio.create_task(announcement_checker())


@app.on_event("shutdown")
async def shutdown_event():
    """Stop the background task when the app stops."""
    global task_running
    task_running = False


@app.get("/")
async def home():
    """Health check endpoint."""
    return JSONResponse({"status": "ok", "message": "Announcement bot is running"})


@app.get("/latest")
async def get_latest():
    """Fetch the latest announcement from the website."""
    try:
        title, link = get_latest_announcement()
        return JSONResponse({"status": "success", "title": title, "link": link})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})
