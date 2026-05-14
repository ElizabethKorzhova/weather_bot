"""This script implements the weather telegram bot"""
import os
import logging
import time
import json
from typing import List

from redis.asyncio import Redis
import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from utils import format_weather_message

load_dotenv()

API_KEY = os.getenv("API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "baidu/cobuddy:free")

openrouter_client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

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
        "Or just type a city anytime.\n\n"
        "/ai — ask AI assistant\n"
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


async def send_ai_response(update: Update, user_message: str) -> None:
    """Generates AI response using OpenRouter model."""
    messages: List[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": (
                "You are a sarcastic cyberpunk weather assistant "
                "from the future. "
                "Answer shortly, humorously, and helpfully."
            ),
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

    try:
        response = await openrouter_client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=messages,
            temperature=0.8,
            max_tokens=300,
        )

        ai_message: str | None = response.choices[0].message.content
        logging.info(
            f"OpenRouter model used | model={response.model} | "
            f"finish_reason={response.choices[0].finish_reason}"
        )

        if not ai_message:
            await update.message.reply_text("AI returned an empty response.")
            return

        await update.message.reply_text(ai_message)

    except Exception as ex:
        logging.error(f"OpenRouter AI error | error={ex}")

        await update.message.reply_text("AI assistant is temporarily unavailable.")


async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enables AI mode or process AI command."""
    user_message: str = " ".join(context.args)

    if not user_message:
        context.user_data["ai_mode"] = True

        await update.message.reply_text(
            "🤖 AI assistant is listening.\n"
            "Write your message.\n"
            "For example:\nTell me a joke about rain"
        )
        return

    await send_ai_response(update, user_message)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles text messages for AI mode or weather."""
    text: str = update.message.text.strip()

    if context.user_data.get("ai_mode"):
        context.user_data["ai_mode"] = False
        await send_ai_response(update, text)
        return

    await handle_city(update, context)


app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("weather", weather))
app.add_handler(CommandHandler("ai", ai_chat))

app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

app.run_polling(drop_pending_updates=True)
