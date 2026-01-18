"""
後方互換性のためのエイリアスモジュール

新規コードでは以下を使用してください:
- from src.llm.cloud_client import QwenCloudClient
- from src.llm.factory import LLMClientFactory
"""

from .cloud_client import QwenCloudClient

# 後方互換性のためのエイリアス
QwenClient = QwenCloudClient
