import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from infrastructure.cache.redis_queue import dequeue_job
from infrastructure.mail.reset_email import send_reset_email


async def run():
    while True:
        job = dequeue_job("email_queue", timeout=5)
        if not job:
            await asyncio.sleep(0.2)
            continue
        if job.get("type") == "reset_password":
            email = job.get("email")
            token = job.get("token")
            if email and token:
                await send_reset_email(email, token)


if __name__ == "__main__":
    asyncio.run(run())
