from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
from PIL import Image
import pytesseract
import requests
import os
import io
import re
import traceback

app = Flask(__name__)

# Channel Access Token and Secret from environment variables
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# Configure Tesseract path if necessary
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_id = event.source.user_id
    msg = event.message.text

    # 查找消息中是否包含以66开头且长度为19位的数字
    match = re.search(r'66\d{17}', msg)
    if match:
        try:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('order'))
        except:
            print(traceback.format_exc())
            line_bot_api.reply_message(event.reply_token, TextSendMessage('发生错误，请稍后再试。'))
    elif msg.lower() == 'id':
        try:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(user_id))
        except:
            print(traceback.format_exc())
            line_bot_api.reply_message(event.reply_token, TextSendMessage('发生错误，请稍后再试。'))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    user_id = event.source.user_id
    message_content = line_bot_api.get_message_content(event.message.id)
    image = Image.open(io.BytesIO(message_content.content))

    # 使用Tesseract OCR识别图片中的文本
    text = pytesseract.image_to_string(image)
    app.logger.info(f"Detected text: {text}")

    # 查找文本中是否包含以66开头且长度为19位的数字
    match = re.search(r'66\d{17}', text)
    if match:
        try:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('order_image'))
        except:
            print(traceback.format_exc())
            line_bot_api.reply_message(event.reply_token, TextSendMessage('发生错误，请稍后再试。'))

@handler.add(PostbackEvent)
def handle_postback(event):
    print(event.postback.data)

@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}，欢迎加入cbody')
    line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
