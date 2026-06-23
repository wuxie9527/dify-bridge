"""
阿里云 OCR 测试脚本

使用方法:
1. 配置 .env 文件中的阿里云 AccessKey
2. 运行：python test_ocr.py
"""
import os
import sys
import json
import logging

logging.basicConfig(level=logging.INFO)
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

# 配置
ACCESS_KEY_ID = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID", "")
ACCESS_KEY_SECRET = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "")
ENDPOINT = os.getenv("ALIYUN_OCR_ENDPOINT", "ocr-api.cn-hangzhou.aliyuncs.com")

# 测试图片
TEST_IMAGE_URL = "https://img.alicdn.com/tfs/TB1q5IeXAvoK1RjSZFNXXcxMVXa-483-307.jpg"


def main():
    print("\n" + "=" * 60)
    print("阿里云 OCR 测试")
    print("=" * 60)

    if not ACCESS_KEY_ID or not ACCESS_KEY_SECRET:
        print("\n[ERROR] 未配置 AccessKey!")
        print("请在 .env 文件中配置:")
        print("  ALIBABA_CLOUD_ACCESS_KEY_ID=...")
        print("  ALIBABA_CLOUD_ACCESS_KEY_SECRET=...")
        return

    print(f"\n[OK] AccessKey 已配置")
    print(f"   Endpoint: {ENDPOINT}")

    from app.clients.aliyun_ocr import AliyunOCRClient
    client = AliyunOCRClient(ACCESS_KEY_ID, ACCESS_KEY_SECRET, ENDPOINT)
    print(f"[OK] 客户端初始化成功\n")

    # 测试通用文字识别
    print("测试：通用文字识别")
    print(f"图片 URL: {TEST_IMAGE_URL}")
    print("-" * 60)

    result = client.recognize_general(image_url=TEST_IMAGE_URL)

    if result["success"]:
        print("\n[OK] 识别成功!\n")
        print(f"识别文本：{result['data']['text']}\n")
        print(f"行数：{len(result['data']['lines'])}")
        for i, line in enumerate(result['data']['lines'][:10], 1):
            print(f"  {i}. {line['text']} (置信度：{line['confidence']:.2f})")
    else:
        print(f"\n[FAIL] 识别失败：{result['error']}")


if __name__ == "__main__":
    main()
