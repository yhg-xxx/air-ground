import os
from loguru import logger
import requests
from datetime import datetime

from demo_auth import get_token

HOST = "fcs.botzooo.com"
PORT = 30080
logger.add(
    "api_demo.log",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    rotation="10MB"
)
def capture_image(token):
    url = f"http://{HOST}:{PORT}/api/gimbal/capture"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    # 官方说明：本接口无需传入请求体参数
    resp = requests.post(url, headers=headers)

    if "image" in resp.headers.get("Content-Type", ""):
        # 保存图片
        os.makedirs("capture", exist_ok=True)
        filename = f"capture/{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        with open(filename, "wb") as f:
            f.write(resp.content)
        logger.info("图片抓取成功，已保存至：", filename)
    else:
        error = resp.json()
        print("抓拍失败：", error)

if __name__ == "__main__":
    token = get_token()
    logger.info("开始")
    capture_image(token)