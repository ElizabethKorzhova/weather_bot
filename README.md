# Weather Telegram Bot

Telegram bot that provides current weather forecast for any
city using the OpenWeather API.

## Features
- **Real-time Weather:** Get temperature, feels like, description and humidity.
- **Caching:** Uses Redis to store weather data for 10 minutes, reducing API calls and increasing speed.
- **Logging:** Tracks successful/failed requests and errors in `app.log`.

## Requirements
  - **Python** 3.14
  - **Redis server** 8.6
  - **Packages:**
    - `python-telegram-bot` — for Telegram interaction
    - `redis` — for caching data
    - `requests` — for API calls
    - `python-dotenv` — for environment variables management

## API and Services
Before starting, you need to obtain the following keys:

- **OpenWeather API**: [Get API Key](https://openweathermap.org)

- **BotFather** (Telegram): [@BotFather](https://t.me/BotFather). Create a new bot to get your TELEGRAM_BOT_TOKEN.

## Installation

### 1. Clone project

``` bash
git clone git@github.com:ElizabethKorzhova/weather_bot.git
cd weather_bot
```

### 2. Setup Redis
Ensure Redis is installed and running on your system.

macOS:

``` bash
brew services start redis
```

Linux:
``` bash
sudo systemctl start redis
```

### 3. Create virtual environment

``` bash
python -m venv venv
```

### 4. Activate virtual environment

Windows:

``` bash
venv\Scripts\activate
```

macOS/Linux:

``` bash
source venv/bin/activate
```

### 4. Install dependencies

``` bash
pip install -r requirements.txt
```

### 5. Create `.env` file and fill in your credentials

``` env
API_KEY=
TELEGRAM_BOT_TOKEN=
REDIS_HOST=
REDIS_PORT=
REDIS_DB=
```

### 5. Run the bot

``` bash
python main.py
```

## Available commands

-   `/start` - welcome message
-   `/help` - list of commands
-   `/weather` - check the weather in the city


> Note: Logs are automatically saved in app.log for monitoring and debugging.
