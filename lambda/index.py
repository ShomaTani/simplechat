# lambda/index.py
import json
import os
import boto3
import re  # 正規表現モジュールをインポート
from botocore.exceptions import ClientError
from urllib import request, parse

# Lambda コンテキストからリージョンを抽出する関数
def extract_region_from_arn(arn):
    # ARN 形式: arn:aws:lambda:region:account-id:function:function-name
    match = re.search('arn:aws:lambda:([^:]+):', arn)
    if match:
        return match.group(1)
    return "us-east-1"  # デフォルト値

# グローバル変数としてクライアントを初期化（初期値）
bedrock_client = None

# モデルID
FAST_API = FASTAPI_URL = os.environ["https://5331-34-90-234-105.ngrok-free.app"]
def lambda_handler(event, context):
    try:
        # 1) 受信ログ
        print("Received event:", event)

        # 2) リクエストボディから message と会話履歴を取り出し
        body = json.loads(event.get("body", "{}"))
        message = body.get("message", "")
        history = body.get("conversationHistory", [])

        # 3) FastAPI に投げるためのペイロードを組み直し
        payload = {
            "message": message,
            "conversationHistory": history
        }
        raw = json.dumps(payload).encode("utf-8")

        # 4) urllib.request で POST
        req = request.Request(
            FASTAPI_URL,
            data=raw,
            headers={"Content-Type": "application/json"}
        )
        with request.urlopen(req) as resp:
            resp_body = resp.read().decode("utf-8")
            api_out = json.loads(resp_body)

        print("FastAPI response:", api_out)

        # 5) FastAPI が {"reply": "...", "conversationHistory": [...]} の形で返す想定
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": api_out.get("reply"),
                "conversationHistory": api_out.get("conversationHistory", history)
            })
        }

    except Exception as e:
        print("Error:", str(e))
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(e)
            })
        }
