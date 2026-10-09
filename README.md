# NeoTowerGameBot

Telegram RPG game inside chat.

## Features
- Heroes
- Tower floors
- Battles
- Player database

## Launch
Install requirements and set BOT_TOKEN.

## Render deployment

- Set `BOT_TOKEN` to the Telegram bot token.
- For persistent player progress, attach a Render persistent disk and set `DATABASE_PATH=/var/data/neotower.db` (the mount path must match the disk's mount path).
- The health endpoint listens on Render's `PORT`; the worker starts with `python main.py`.

## Local checks

Run `python -m unittest discover -s tests -v` and `python -m compileall -q .`.
