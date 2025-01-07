# -*- coding:utf-8 -*-
#
#   author: iflytek
#
#  本demo测试时运行的环境为：Windows + Python3.7
#  本demo测试成功运行时所安装的第三方库及其版本如下，您可自行逐一或者复制到一个新的txt文件利用pip一次性安装：
#   cffi==1.12.3
#   gevent==1.4.0
#   greenlet==0.4.15
#   pycparser==2.19
#   six==1.12.0
#   websocket==0.2.1
#   websocket-client==0.56.0
#
#  语音听写流式 WebAPI 接口调用示例 接口文档（必看）：https://doc.xfyun.cn/rest_api/语音听写（流式版）.html
#  webapi 听写服务参考帖子（必看）：http://bbs.xfyun.cn/forum.php?mod=viewthread&tid=38947&extra=
#  语音听写流式WebAPI 服务，热词使用方式：登陆开放平台https://www.xfyun.cn/后，找到控制台--我的应用---语音听写（流式）---服务管理--个性化热词，
#  设置热词
#  注意：热词只能在识别的时候会增加热词的识别权重，需要注意的是增加相应词条的识别率，但并不是绝对的，具体效果以您测试为准。
#  语音听写流式WebAPI 服务，方言试用方法：登陆开放平台https://www.xfyun.cn/后，找到控制台--我的应用---语音听写（流式）---服务管理--识别语种列表
#  可添加语种或方言，添加后会显示该方言的参数值
#  错误码链接：https://www.xfyun.cn/document/error-code （code返回错误码时必看）
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
from urllib import request
import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
from threading import Thread
import json
import base64
import hmac
import hashlib
import ssl
import time
import _thread as thread
from flask import Flask, request, jsonify
from datetime import datetime
from time import mktime
from wsgiref.handlers import format_date_time
from urllib.parse import urlencode
import websocket
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
import os
import subprocess
from jiemian import app

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识


class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, AudioFile):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.AudioFile = AudioFile

        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "vinfo": 1, "vad_eos": 10000}

    # 生成url
    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        return url


result_text = ""


# 收到websocket消息的处理
def on_message(ws, message):
    global result_text
    try:
        code = json.loads(message)["code"]
        sid = json.loads(message)["sid"]
        if code != 0:
            errMsg = json.loads(message)["message"]
            print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
        else:
            data = json.loads(message)["data"]["result"]["ws"]
            for i in data:
                for w in i["cw"]:
                    result_text += w["w"]  # 只收集拼接后的文本内容
            # 打印拼接后的文本内容
            # print("sid:%s call success!, result_text is: %s" % (sid, result_text))
    except Exception as e:
        print("receive msg, but parse exception:", e)


# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws, a, b):
    # 将结果写入文件
    with open('output_text.txt', 'w', encoding='utf-8') as f:
        f.write(result_text)
        print(f.read())


# resource_wav=r"C:\Users\31253\Desktop\lfasr_new_python_demo\audio\lfasr_涉政.wav"
resource_wav = ""


# 收到websocket连接建立的处理
def on_open(ws):
    def run(*args):
        frameSize = 8000  # 每一帧的音频大小
        intervel = 0.04  # 发送音频间隔(单位:s)
        status = STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧

        with open(wsParam.AudioFile, "rb") as fp:
            while True:
                buf = fp.read(frameSize)
                # 文件结束
                if not buf:
                    status = STATUS_LAST_FRAME
                # 第一帧处理
                # 发送第一帧音频，带business 参数
                # appid 必须带上，只需第一帧发送
                if status == STATUS_FIRST_FRAME:
                    d = {"common": wsParam.CommonArgs,
                         "business": wsParam.BusinessArgs,
                         "data": {"status": 0, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    d = json.dumps(d)
                    ws.send(d)
                    status = STATUS_CONTINUE_FRAME
                # 中间帧处理
                elif status == STATUS_CONTINUE_FRAME:
                    d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    ws.send(json.dumps(d))
                # 最后一帧处理
                elif status == STATUS_LAST_FRAME:
                    d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    ws.send(json.dumps(d))
                    time.sleep(1)
                    break
                # 模拟音频采样间隔
                time.sleep(intervel)
        ws.close()

    thread.start_new_thread(run, ())


def is_wav_file(file):
    return file.lower().endswith('.wav')


def convert_mp4_to_wav(file, wav_file):
    # 提取音频
    video = VideoFileClip(file)
    audio = video.audio
    audio.write_audiofile("temp_audio.mp3")

    # 使用pydub将MP3转换为WAV
    sound = AudioSegment.from_mp3("temp_audio.mp3")
    sound.export(wav_file, format="wav")

    # 删除临时文件
    os.remove("temp_audio.mp3")


# 改变具体的音频参数
def convert_wav(file_path, output_path):
    # 读取原始音频文件
    audio = AudioSegment.from_wav(file_path)

    # 设置采样率、比特率和声道
    audio = audio.set_frame_rate(16000)
    audio = audio.set_sample_width(2)  # 16 bit = 2 bytes
    audio = audio.set_channels(1)  # 单声道

    # 导出修改后的音频文件
    audio.export(output_path, format="wav")

def analyze_video():
    data = request.get_json()
    video_file = data.get('video_file')
    resource_wav = video_file
    wav_file = "lastest_wav.wav"
    output_wav = "output.wav"

    if not is_wav_file(resource_wav):
        convert_mp4_to_wav(resource_wav, wav_file)
        resource_wav = wav_file

    convert_wav(resource_wav, output_wav)

    global result_text
    result_text = ""
    wsParam = Ws_Param(APPID='85ba39a2', APISecret='ZTBmOWQxOTU2YTNiOGUwMzA2NmFjNDY1',
                       APIKey='b75e7701e186128d65eb861c106e868d', AudioFile=output_wav)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    # 调用 txt_to_ai.py
    result = subprocess.run(['python3', 'txt_to_ai.py', 'output_text.txt'], capture_output=True, text=True)
    print(result.stdout)

    return jsonify({"message": "Processing started", "status": "success"})


if __name__ == "__main__":
    wav_file = "lastest_wav.wav"
    output_wav = "output.wav"
    analyze_video()
    n = is_wav_file(resource_wav)
    if n == 0:
        resource_wav = wav_file
    convert_wav(resource_wav, output_wav)

    result_text = ""
    time1 = datetime.now()
    wsParam = Ws_Param(APPID='85ba39a2', APISecret='ZTBmOWQxOTU2YTNiOGUwMzA2NmFjNDY1',
                       APIKey='b75e7701e186128d65eb861c106e868d',
                       AudioFile=output_wav)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    time2 = datetime.now()
    with open('output_text.txt', 'r', encoding='utf-8') as f:
        print(f.read())
    print(result_text)
