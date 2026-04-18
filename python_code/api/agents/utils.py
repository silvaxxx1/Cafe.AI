import time
import structlog
from contextvars import ContextVar
from openai import AsyncOpenAI

log = structlog.get_logger()

# Accumulates token usage across all LLM calls within a single request.
_token_counter: ContextVar[dict | None] = ContextVar("token_counter", default=None)


def reset_token_counter() -> None:
    _token_counter.set({"input": 0, "output": 0})


def get_token_counts() -> dict:
    return _token_counter.get() or {"input": 0, "output": 0}


async def get_chatbot_response(
    client: AsyncOpenAI,
    model_name: str,
    messages: list,
    temperature: float = 0,
    json_mode: bool = False,
) -> str:
    input_messages = [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    start = time.perf_counter()
    response = await client.chat.completions.create(
        model=model_name,
        messages=input_messages,
        temperature=temperature,
        top_p=0.8,
        max_tokens=2000,
        **kwargs,
    )
    latency_ms = round((time.perf_counter() - start) * 1000)

    usage = response.usage
    input_tokens = usage.prompt_tokens if usage else 0
    output_tokens = usage.completion_tokens if usage else 0

    counter = _token_counter.get()
    if counter is not None:
        counter["input"] += input_tokens
        counter["output"] += output_tokens

    log.info(
        "llm_call",
        model=model_name,
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    return response.choices[0].message.content


async def double_check_json_output(client: AsyncOpenAI, model_name: str, json_string: str) -> str:
    prompt = f""" You will check this json string and correct any mistakes that will make it invalid. Then you will return the corrected json string. Nothing else.
    If the Json is correct just return it.

    Do NOT return a single letter outside of the json string.

    {json_string}
    """
    messages = [{"role": "user", "content": prompt}]
    return await get_chatbot_response(client, model_name, messages)
