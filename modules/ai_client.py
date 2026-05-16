"""AI API 调用模块"""

import json
import urllib.request
import ssl

from .config import API_KEY, API_URL, MODEL


def call_ai_api(messages):
    """调用 AI API，传入完整的消息历史"""
    body = json.dumps(
        {"model": MODEL, "messages": messages, "temperature": 0.3}
    ).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )

    ctx = ssl.create_default_context()

    try:
        with urllib.request.urlopen(req, timeout=120, context=ctx) as response:
            response_data = response.read().decode("utf-8")
    except Exception as e:
        raise Exception(f"API请求失败: {str(e)}")

    result = json.loads(response_data)
    ai_reply = result["choices"][0]["message"]["content"]

    # 清理 markdown 包裹
    ai_reply = ai_reply.strip()
    if ai_reply.startswith("```"):
        lines = ai_reply.split("\n")
        ai_reply = "\n".join(lines[1:-1])
    if ai_reply.endswith("```"):
        ai_reply = ai_reply[:-3]

    return ai_reply.strip()
