from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage

# 星火认知大模型Spark Max的URL值
SPARKAI_URL = 'wss://spark-api.xf-yun.com/v3.5/chat'
# 星火认知大模型调用秘钥信息
SPARKAI_APP_ID = '85ba39a2'
SPARKAI_API_SECRET = 'ZTBmOWQxOTU2YTNiOGUwMzA2NmFjNDY1'
SPARKAI_API_KEY = 'b75e7701e186128d65eb861c106e868d'
# 星火认知大模型Spark Max的domain值
SPARKAI_DOMAIN = 'generalv3.5'


def ask_spark(question):
    spark = ChatSparkLLM(
        spark_api_url=SPARKAI_URL,
        spark_app_id=SPARKAI_APP_ID,
        spark_api_key=SPARKAI_API_KEY,
        spark_api_secret=SPARKAI_API_SECRET,
        spark_llm_domain=SPARKAI_DOMAIN,
        streaming=False,
    )
    messages = [ChatMessage(
        role="user",
        content=question
    )]
    handler = ChunkPrintHandler()
    response = spark.generate([messages], callbacks=[handler])

    # 输出 response 对象以查看其结构
    print("Response object:", response)

    # 从 response 中提取回答文本
    if response.generations and len(response.generations) > 0 and len(response.generations[0]) > 0:
        answer_text = response.generations[0][0].text
    else:
        answer_text = "No response"

    return answer_text


