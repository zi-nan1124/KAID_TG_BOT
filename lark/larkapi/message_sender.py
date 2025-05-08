import requests
import json

def message(webhook_url: str, content: str) -> dict:
    """
    向飞书自定义机器人发送文本消息。
    返回结构体结果字典，用于判断状态和错误原因。
    """
    full_text = f"Kaid小助手：\n{content}"
    payload = {
        "msg_type": "text",
        "content": {
            "text": full_text
        }
    }

    headers = {"Content-Type": "application/json"}
    result = {
        "success": False,
        "http_status": None,
        "error_msg": "",
        "feishu_code": None,
        "feishu_msg": ""
    }

    try:
        response = requests.post(webhook_url, headers=headers, data=json.dumps(payload))
        result["http_status"] = response.status_code

        if response.status_code == 200:
            resp_json = response.json()
            result["feishu_code"] = resp_json.get("StatusCode")
            result["feishu_msg"] = resp_json.get("StatusMessage")

            if resp_json.get("StatusCode") == 0:
                result["success"] = True
        else:
            result["error_msg"] = response.text

    except Exception as e:
        result["error_msg"] = str(e)

    return result


if __name__ == "__main__":
    webhook = "https://open.larksuite.com/open-apis/bot/v2/hook/6ef1a3db-2a07-480c-9d76-79e7466618ab"
    res = message(webhook, "系统启动成功，进入监控状态。")

    if res["success"]:
        print("✅ 消息发送成功")
    else:
        print("❌ 消息发送失败")
        print(f"HTTP 状态码: {res['http_status']}")
        print(f"飞书错误: {res['feishu_code']} - {res['feishu_msg']}")
        print(f"详细信息: {res['error_msg']}")
