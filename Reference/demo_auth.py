import requests

# ===================== 官方配置 =====================
HOST = "fcs.botzooo.com"
PORT = 30080
USERNAME = "fcs002"
PASSWORD = "fcs002fcs002"

def get_token():
    url = f"http://{HOST}:{PORT}/api/auth/token"
    headers = {"Content-Type": "application/json"}
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    resp = requests.post(url, json=data, headers=headers)
    result = resp.json()
    if result.get("code") == "1":
        return result["data"]["token"]
    else:
        raise Exception("获取Token失败：" + result.get("msg"))

if __name__ == "__main__":
    token = get_token()
    print("比赛官方演示：获取Token成功")
    print("Token:", token)