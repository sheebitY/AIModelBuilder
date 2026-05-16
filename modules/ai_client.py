"""AI API 调用模块"""

import json
import urllib.request
import ssl
import traceback

from modules.config import API_KEY, API_URL, MODEL


def call_ai_api(messages):
    """调用 AI API，传入完整的消息历史"""
    print("[AI Client] 开始调用API...")
    print("[AI Client] API地址: {}".format(API_URL))
    print("[AI Client] 模型: {}".format(MODEL))

    body = json.dumps(
        {"model": MODEL, "messages": messages, "temperature": 0.3}
    ).encode("utf-8")

    print("[AI Client] 请求体大小: {} bytes".format(len(body)))

    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Authorization": "Bearer {}".format(API_KEY),
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )

    ctx = ssl.create_default_context()

    try:
        print("[AI Client] 发送请求...")
        with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
            print("[AI Client] 收到响应，状态码: {}".format(response.status))
            response_data = response.read().decode("utf-8")
            print("[AI Client] 响应数据大小: {} bytes".format(len(response_data)))
    except urllib.error.URLError as e:
        error_msg = "网络错误: {}".format(str(e))
        print("[AI Client] {}".format(error_msg))
        raise Exception(error_msg)
    except urllib.error.HTTPError as e:
        error_msg = "HTTP错误 {}: {}".format(e.code, e.reason)
        print("[AI Client] {}".format(error_msg))
        raise Exception(error_msg)
    except TimeoutError:
        error_msg = "请求超时（30秒）"
        print("[AI Client] {}".format(error_msg))
        raise Exception(error_msg)
    except Exception as e:
        error_msg = "API请求失败: {}".format(str(e))
        print("[AI Client] {}".format(error_msg))
        print("[AI Client] 详细错误: {}".format(traceback.format_exc()))
        raise Exception(error_msg)

    try:
        result = json.loads(response_data)
        print("[AI Client] JSON解析成功")
    except json.JSONDecodeError as e:
        error_msg = "JSON解析失败: {}".format(str(e))
        print("[AI Client] {}".format(error_msg))
        print("[AI Client] 响应内容: {}".format(response_data[:500]))
        raise Exception(error_msg)

    if "choices" not in result:
        error_msg = "API响应格式错误，缺少choices字段"
        print("[AI Client] {}".format(error_msg))
        print("[AI Client] 响应内容: {}".format(json.dumps(result, ensure_ascii=False)[:500]))
        raise Exception(error_msg)

    ai_reply = result["choices"][0]["message"]["content"]
    print("[AI Client] AI回复长度: {} 字符".format(len(ai_reply)))

    # 清理 markdown 包裹
    ai_reply = ai_reply.strip()
    if ai_reply.startswith("```"):
        lines = ai_reply.split("\n")
        ai_reply = "\n".join(lines[1:-1])
    if ai_reply.endswith("```"):
        ai_reply = ai_reply[:-3]

    print("[AI Client] API调用完成")
    return ai_reply.strip()
