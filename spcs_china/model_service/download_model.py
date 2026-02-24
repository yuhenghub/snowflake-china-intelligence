"""
模型下载脚本
从 ModelScope 下载 Qwen 模型到本地缓存
"""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_NAME = os.environ.get("MODEL_NAME", "Qwen/Qwen2.5-1.5B-Instruct")
CACHE_DIR = os.environ.get("MODELSCOPE_CACHE", "/app/models")


def download_model():
    """从 ModelScope 下载模型"""
    logger.info(f"开始下载模型: {MODEL_NAME}")
    logger.info(f"缓存目录: {CACHE_DIR}")
    
    try:
        from modelscope import snapshot_download
        
        # 下载模型
        model_dir = snapshot_download(
            MODEL_NAME,
            cache_dir=CACHE_DIR,
            revision='master'
        )
        
        logger.info(f"模型下载完成: {model_dir}")
        return model_dir
        
    except Exception as e:
        logger.error(f"模型下载失败: {e}")
        raise


if __name__ == "__main__":
    download_model()


