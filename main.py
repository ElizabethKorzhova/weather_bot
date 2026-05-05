"""This script implements the weather telegram bot"""
import os
import logging
import time
import json

from redis.asyncio import Redis
import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from utils import format_weather_message

load_dotenv()
API_KEY = os.getenv("API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

redis_client = Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=int(os.getenv("REDIS_DB", "0")),
    decode_responses=True,
)

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command `/start` is invoked."""
    user = update.effective_user.first_name
    logging.info(f"/start command used by {user}")
    await update.message.reply_text(f"Hello {user}! I'm the weather bot 🌤\n"
                                    f"Type /help to see the available commands.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command `/help` is invoked."""
    user = update.effective_user.first_name
    logging.info(f"/help command used by {user}")
    await update.message.reply_text(
        "Available commands:\n"
        "/start — welcome message\n"
        "/help — list of commands\n"
        "/weather — check the weather in the city\n\n"
        "Or just type a city anytime."
    )


async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command `/weather` is invoked."""
    user = update.effective_user.first_name
    logging.info(f"/weather command used by {user}")
    await update.message.reply_text("Please enter the city name:")


async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get weather forecast from API and send it to the user."""
    city = update.message.text.strip()
    user = update.effective_user.first_name
    start_time = time.perf_counter()

    cached_message = await redis_client.get(city.lower())

    if cached_message:
        data = json.loads(cached_message)
        message = format_weather_message(city, data)
        await update.message.reply_text(message)
        return

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}"
        f"&appid={API_KEY}"
        "&units=metric"
        "&lang=en"
    )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            execution_time = time.perf_counter() - start_time

            if response.status_code == 200:
                data = response.json()
                message = format_weather_message(city, data)
                logging.info(
                    f"SUCCESS request | user={user} | city={city} | "
                    f"time={execution_time:.2f}s"
                )
                await redis_client.setex(city.lower(), 600, json.dumps(data), )
                await update.message.reply_text(message)

            else:
                logging.warning(
                    f"FAILED request | user={user} | city={city} | "
                    f"status={response.status_code} | time={execution_time:.2f}s"
                )
                await update.message.reply_text("Could not find weather for this city.")

        except httpx.RequestError as ex:
            execution_time = time.perf_counter() - start_time
            logging.error(
                f"ERROR request | user={user} | city={city} | "
                f"error={ex} | time={execution_time:.2f}s"
            )
            await update.message.reply_text("Service temporarily unavailable.")


app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("weather", weather))

app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_city))

app.run_polling(drop_pending_updates=True)
