from anthropic import AsyncAnthropic
from dotenv import load_dotenv
import asyncio

load_dotenv()

client = AsyncAnthropic(timeout=100)


async def model_call(
    messages: list | str,
    encoded_image: str = None,
    model="claude-3-5-haiku-20241022",
    max_tokens=8000,
    stream=False,
    tools=None,
):
    retries = 3
    sleep_time = 2

    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]
    api_parameters = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": stream,
    }
    for attempt in range(retries):
        try:
            response = await client.messages.create(**api_parameters)
            return response

        except Exception as e:
            print(f"\n[model_call]: {e}")
            if attempt < retries - 1:
                sleep_time = sleep_time * (2**attempt)
                print(f"\n[model_call]: Retrying in {sleep_time} seconds...")
                await asyncio.sleep(sleep_time)
            else:
                print(f"\n[model_call]: Failed after {retries} attempts")
                break

    return None


############################################################################################################
