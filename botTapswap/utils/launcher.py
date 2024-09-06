import asyncio
import argparse
from itertools import cycle
from pyrogram import Client, compose

from botTapswap.config import settings
from botTapswap.utils import logger
from botTapswap.core.tapper import run_tapper
from botTapswap.core.registrator import register_sessions
from botTapswap.utils.scripts import get_session_names, get_proxies

banner = """

▀▀█▀▀ █▀▀█ █▀▀█ ░█▀▀▀█ █   █ █▀▀█ █▀▀█ ░█▀▀█ █▀▀█ ▀▀█▀▀
 ░█   █▄▄█ █  █  ▀▀▀▄▄ █▄█▄█ █▄▄█ █  █ ░█▀▀▄ █  █   █
 ░█   ▀  ▀ █▀▀▀ ░█▄▄▄█  ▀ ▀  ▀  ▀ █▀▀▀ ░█▄▄█ ▀▀▀▀   ▀

"""

options = """
Select an action:

    1. Create session
    2. Run clicker
    3. Run via Telegram (Beta)
"""


global tg_clients


async def get_tg_clients(username) -> list[Client]:
    global tg_clients

    session_names = get_session_names(username)

    if not session_names:
        raise FileNotFoundError("Not found session files")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    tg_clients = [
        Client(
            name=session_name,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            workdir="sessions/",
            plugins=dict(root="bot/plugins"),
        )
        for session_name in session_names
    ]

    return tg_clients


async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action", type=int, help="Action to perform")
    parser.add_argument('-u', '--user')
    username = parser.parse_args().user
    logger.info(f"username== {username}")
    logger.info(f"Detected {len(get_session_names(username))} sessions | {len(get_proxies())} proxies")

    action = parser.parse_args().action

    if not action:
        print(options)

        while True:
            action = input("> ")

            if not action.isdigit():
                logger.warning("Action must be number")
            elif action not in ["1", "2", "3"]:
                logger.warning("Action must be 1, 2 or 3")
            else:
                action = int(action)
                break

    if action == 1:
        await register_sessions()
    elif action == 2:
        tg_clients = await get_tg_clients(username)

        await run_tasks(tg_clients=tg_clients)
    elif action == 3:
        tg_clients = await get_tg_clients(username)

        logger.info("Send /help command in Saved Messages\n")

        await compose(tg_clients)


async def run_tasks(tg_clients: list[Client]):
    proxies = get_proxies()
    proxies_cycle = cycle(proxies) if proxies else None
    lock = asyncio.Lock()

    tasks = [
        asyncio.create_task(
            run_tapper(
                tg_client=tg_client,
                proxy=next(proxies_cycle) if proxies_cycle else None,
                lock=lock,
            )
        )
        for tg_client in tg_clients
    ]

    await asyncio.gather(*tasks)
