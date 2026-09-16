#!/bin/bash

# Start the FastAPI web server in the background
uvicorn web:app --host 0.0.0.0 --port $PORT &

# Start the Discord bot
python bot.py
