from openai import AsyncOpenAI


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

    response = await client.chat.completions.create(
        model=model_name,
        messages=input_messages,
        temperature=temperature,
        top_p=0.8,
        max_tokens=2000,
        **kwargs,
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
