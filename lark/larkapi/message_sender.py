import json
import logging
import lark_oapi as lark
from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody

# Configure logger
logger = logging.getLogger(__name__)

class LarkMessageSender:
    def __init__(self, app_id: str, app_secret: str):
        self.client = lark.Client.builder() \
            .app_id(app_id) \
            .app_secret(app_secret) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()

    def send_message(self, user_id: str, content: str, uuid: str = None) -> bool:
        if uuid is None:
            import uuid as uuid_lib
            uuid = str(uuid_lib.uuid4())

        request = CreateMessageRequest.builder() \
            .receive_id_type("email") \
            .request_body(CreateMessageRequestBody.builder()
                .receive_id(user_id)
                .msg_type("text")
                .content(json.dumps({"text": content}))
                .uuid(uuid)
                .build()) \
            .build()

        response = self.client.im.v1.message.create(request)

        if not response.success():
            logger.error(
                f"Failed to send message to {user_id}, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \\n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
            )
            return False

        logger.info(f"Message sent to {user_id}: {content}")
        return True


if __name__ == "__main__":
    # 替换为你的实际 app_id 和 app_secret
    app_id = "cli_a880bef271f89009"
    app_secret = "Iq7KNfcVNQbp8AHn1VV7HgN61oAGhL5N"
    user_id = "kaid.y@mexc.com"  # 替换为有效的 user_id
    content = "你好"

    sender = LarkMessageSender(app_id, app_secret)
    success = sender.send_message(user_id, content)

    if success:
        print("消息发送成功")
    else:
        print("消息发送失败")
