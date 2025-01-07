from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage

# 星火认知大模型Spark Max的URL值，其他版本大模型URL值请前往文档（https://www.xfyun.cn/doc/spark/Web.html）查看
import app

SPARKAI_URL = 'wss://spark-api.xf-yun.com/v3.5/chat'
# 星火认知大模型调用秘钥信息，请前往讯飞开放平台控制台（https://console.xfyun.cn/services/bm35）查看
SPARKAI_APP_ID = '85ba39a2'
SPARKAI_API_SECRET = 'ZTBmOWQxOTU2YTNiOGUwMzA2NmFjNDY1'
SPARKAI_API_KEY = 'b75e7701e186128d65eb861c106e868d'
# 星火认知大模型Spark Max的domain值，其他版本大模型domain值请前往文档（https://www.xfyun.cn/doc/spark/Web.html）查看
SPARKAI_DOMAIN = 'generalv3.5'


if __name__ == '__main__':

    spark = ChatSparkLLM(
        spark_api_url=SPARKAI_URL,
        spark_app_id=SPARKAI_APP_ID,
        spark_api_key=SPARKAI_API_KEY,
        spark_api_secret=SPARKAI_API_SECRET,
        spark_llm_domain=SPARKAI_DOMAIN,
        streaming=False,
    )

    with open('output_text.txt', 'r', encoding='utf-8') as file:
        # 读取文件内容
        content = file.read()

        Input = ("请你总结下面这些内容，如有必要可以适当解释和扩展" + content)
    messages = [ChatMessage(
        role="user",
        content=Input
    )]
    handler = ChunkPrintHandler()
    a = spark.generate([messages], callbacks=[handler])
    print(a)
    text_content = a.generations[0][0].text
    with open('ai.txt', 'w', encoding='utf-8') as ai_file:
        ai_file.write(text_content)
