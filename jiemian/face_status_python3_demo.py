#
# 眼睛状态检测 WebAPI 接口调用示例
# 运行前：请先填写Appid、APIKey、APISecret以及图片路径
# 运行方法：直接运行 main 即可 
# 结果： 控制台输出结果信息
# 
# 接口文档（必看）：https://www.xfyun.cn/doc/face/face_status/API.html
#

from datetime import datetime
from wsgiref.handlers import format_date_time
from time import mktime
import hashlib
import base64
import hmac
from urllib.parse import urlencode
import os
import traceback
import json
import requests
import cv2
import time


class AssembleHeaderException(Exception):
    def __init__(self, msg):
        self.message = msg


class Url:
    def __init__(this, host, path, schema):
        this.host = host
        this.path = path
        this.schema = schema
        pass


# 进行sha256加密和base64编码
def sha256base64(data):
    sha256 = hashlib.sha256()
    sha256.update(data)
    digest = base64.b64encode(sha256.digest()).decode(encoding='utf-8')
    return digest


def parse_url(requset_url):
    stidx = requset_url.index("://")
    host = requset_url[stidx + 3:]
    schema = requset_url[:stidx + 3]
    edidx = host.index("/")
    if edidx <= 0:
        raise AssembleHeaderException("invalid request url:" + requset_url)
    path = host[edidx:]
    host = host[:edidx]
    u = Url(host, path, schema)
    return u


def assemble_ws_auth_url(requset_url, method="GET", api_key="", api_secret=""):
    u = parse_url(requset_url)
    host = u.host
    path = u.path
    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))
    # print(date)
    # date = "Thu, 12 Dec 2019 01:57:27 GMT"
    signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)
    # print(signature_origin)
    signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                             digestmod=hashlib.sha256).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
    authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
        api_key, "hmac-sha256", "host date request-line", signature_sha)
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    # print(authorization_origin)
    values = {
        "host": host,
        "date": date,
        "authorization": authorization
    }

    return requset_url + "?" + urlencode(values)


def gen_body(appid, img_path, server_id):
    with open(img_path, 'rb') as f:
        img_data = f.read()
    body = {
        "header": {
            "app_id": appid,
            "status": 3
        },
        "parameter": {
            server_id: {
                "service_kind": "face_status",
                "face_status_result": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "json"
                }
            }
        },
        "payload": {
            "input1": {
                "encoding": "jpg",
                "status": 3,
                "image": str(base64.b64encode(img_data), 'utf-8')
            }
        }
    }
    return json.dumps(body)


def run(appid, apikey, apisecret, img_path, server_id='s67c9c78c'):
    url = 'http://api.xf-yun.com/v1/private/{}'.format(server_id)
    request_url = assemble_ws_auth_url(url, "POST", apikey, apisecret)
    headers = {'content-type': "application/json", 'host': 'api.xf-yun.com', 'app_id': appid}
    response = requests.post(request_url, data=gen_body(appid, img_path, server_id), headers=headers)
    resp_data = json.loads(response.content.decode('utf-8'))
    # print(base64.b64decode(resp_data['payload']['face_status_result']['text']).decode())
    text = base64.b64decode(resp_data['payload']['face_status_result']['text']).decode()
    return text


# 请填写控制台获取的APPID、APISecret、APIKey以及要检测的图片路径

def capture_image(save_path, interval=15):
    # 打开摄像头
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("无法打开摄像头")
        return

    try:

        # 读取摄像头的帧
        ret, frame = cap.read()
        if not ret:
            print("无法获取帧")

        # 保存照片
        cv2.imwrite(save_path, frame)
        print(f"照片保存为 {save_path}")

        # 等待指定时间间隔
        # time.sleep(interval)
    except KeyboardInterrupt:
        print("程序被手动终止")

    # 释放摄像头
    cap.release()


def caution():
    while True:
        save_path = "captured_image.jpg"
        capture_image(save_path, interval=15)
        text = run(
            appid='85ba39a2',
            apisecret='ZTBmOWQxOTU2YTNiOGUwMzA2NmFjNDY1',
            apikey='b75e7701e186128d65eb861c106e868d',
            img_path=r'C:\Users\OpticGazelley\Desktop\jiemian\captured_image.jpg',
        )
        # 假设text是一个包含所需参数的字符串，例如："width:100,left_x:200,left_y:300"
        params = text.split(',')
        width_str = (params[8].split(':')[1])
        faceleft_x_str = (params[9].split(':')[1])
        faceleft_y_str = (params[10].split(':')[1]).strip().strip('}')
        time.sleep(30)

        if not ('135' < width_str < '153' and '210' < faceleft_x_str < '240' and '142' < faceleft_y_str < '160'):
            return True
