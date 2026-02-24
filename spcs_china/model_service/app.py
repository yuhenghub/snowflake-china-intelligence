"""
SPCS Model Service for Snowflake China Region
本地运行 Qwen2.5-1.5B-Instruct 模型
模型从 ModelScope 下载，使用 Transformers 推理
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========================================
# 配置
# ========================================
MODEL_NAME = os.environ.get("MODEL_NAME", "Qwen/Qwen2.5-1.5B-Instruct")
CACHE_DIR = os.environ.get("MODELSCOPE_CACHE", "/app/models")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MAX_NEW_TOKENS = int(os.environ.get("MAX_NEW_TOKENS", "2048"))

# 全局模型和 tokenizer
model = None
tokenizer = None

# ========================================
# 请求/响应模型
# ========================================
class ChatMessage(BaseModel):
    role: str
    content: str

class CompletionRequest(BaseModel):
    model: str = "qwen2.5-1.5b-instruct"
    prompt: Optional[str] = None
    messages: Optional[List[ChatMessage]] = None
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.95

class CompletionResponse(BaseModel):
    id: str
    model: str
    content: str
    usage: Dict[str, int]
    finish_reason: str

class HealthResponse(BaseModel):
    status: str
    model: str
    device: str
    model_loaded: bool


# ========================================
# 模型加载
# ========================================
def download_model_from_modelscope():
    """从 ModelScope 下载模型"""
    logger.info(f"从 ModelScope 下载模型: {MODEL_NAME}")
    
    try:
        from modelscope import snapshot_download
        
        model_dir = snapshot_download(
            MODEL_NAME,
            cache_dir=CACHE_DIR,
            revision='master'
        )
        logger.info(f"模型下载完成: {model_dir}")
        return model_dir
    except Exception as e:
        logger.error(f"ModelScope 下载失败: {e}")
        # 如果 ModelScope 失败，尝试直接使用 transformers
        return MODEL_NAME


def load_model():
    """加载模型和 tokenizer"""
    global model, tokenizer
    
    logger.info(f"开始加载模型，设备: {DEVICE}")
    
    # 下载模型
    model_path = download_model_from_modelscope()
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        logger.info(f"加载 tokenizer: {model_path}")
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True,
            cache_dir=CACHE_DIR
        )
        
        logger.info(f"加载模型: {model_path}")
        
        # 根据设备选择加载方式
        if DEVICE == "cuda":
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True,
                cache_dir=CACHE_DIR
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float32,
                trust_remote_code=True,
                cache_dir=CACHE_DIR
            )
            model = model.to(DEVICE)
        
        model.eval()
        logger.info("模型加载完成!")
        
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        raise


# ========================================
# 推理函数
# ========================================
def generate_response(
    messages: List[Dict[str, str]],
    max_tokens: int = 2048,
    temperature: float = 0.7,
    top_p: float = 0.95
) -> str:
    """生成响应"""
    global model, tokenizer
    
    if model is None or tokenizer is None:
        raise RuntimeError("模型未加载")
    
    # 使用 chat template 构建输入
    try:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
    except Exception:
        # 如果没有 chat template，手动构建
        text = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                text += f"<|im_start|>system\n{content}<|im_end|>\n"
            elif role == "user":
                text += f"<|im_start|>user\n{content}<|im_end|>\n"
            elif role == "assistant":
                text += f"<|im_start|>assistant\n{content}<|im_end|>\n"
        text += "<|im_start|>assistant\n"
    
    # Tokenize
    inputs = tokenizer(text, return_tensors="pt").to(DEVICE)
    
    # 生成
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=min(max_tokens, MAX_NEW_TOKENS),
            temperature=temperature if temperature > 0 else 1.0,
            top_p=top_p,
            do_sample=temperature > 0,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    
    # 解码输出
    generated_ids = outputs[0][inputs['input_ids'].shape[1]:]
    response = tokenizer.decode(generated_ids, skip_special_tokens=True)
    
    return response.strip()


# ========================================
# FastAPI 应用
# ========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时加载模型
    logger.info("应用启动，开始加载模型...")
    try:
        load_model()
        logger.info("模型加载成功，服务就绪")
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        # 不阻止启动，允许健康检查返回未加载状态
    
    yield
    
    # 关闭时清理
    logger.info("应用关闭")


app = FastAPI(
    title="SPCS Qwen Model Service",
    description="本地运行 Qwen2.5-1.5B-Instruct 模型",
    version="1.0.0",
    lifespan=lifespan
)


# ========================================
# API 端点
# ========================================
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    return HealthResponse(
        status="healthy" if model is not None else "loading",
        model=MODEL_NAME,
        device=DEVICE,
        model_loaded=model is not None
    )


@app.get("/v1/models")
async def list_models():
    """列出可用模型"""
    return {
        "models": [
            {
                "id": "qwen2.5-1.5b-instruct",
                "name": MODEL_NAME,
                "device": DEVICE,
                "loaded": model is not None
            }
        ]
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: CompletionRequest):
    """Chat Completions API - 兼容 OpenAI 格式"""
    if model is None:
        raise HTTPException(status_code=503, detail="模型正在加载中，请稍候...")
    
    # 构建消息
    messages = []
    if request.messages:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
    elif request.prompt:
        messages = [{"role": "user", "content": request.prompt}]
    else:
        raise HTTPException(status_code=400, detail="需要 'messages' 或 'prompt'")
    
    try:
        # 在线程池中运行推理（避免阻塞事件循环）
        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(
            None,
            generate_response,
            messages,
            request.max_tokens,
            request.temperature,
            request.top_p
        )
        
        return {
            "id": f"chatcmpl-{os.urandom(4).hex()}",
            "object": "chat.completion",
            "model": MODEL_NAME,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 0,  # 简化，不计算
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
    except Exception as e:
        logger.error(f"推理错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/completions")
async def completions(request: CompletionRequest):
    """Completions API"""
    if not request.prompt:
        raise HTTPException(status_code=400, detail="需要 'prompt'")
    
    messages = [{"role": "user", "content": request.prompt}]
    
    if model is None:
        raise HTTPException(status_code=503, detail="模型正在加载中")
    
    try:
        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(
            None,
            generate_response,
            messages,
            request.max_tokens,
            request.temperature,
            request.top_p
        )
        
        return CompletionResponse(
            id=f"cmpl-{os.urandom(4).hex()}",
            model=MODEL_NAME,
            content=content,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            finish_reason="stop"
        )
    except Exception as e:
        logger.error(f"推理错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/complete")
async def simple_complete(model: str = "qwen", prompt: str = ""):
    """
    简单的完成接口 - 直接返回文本
    专门为 Snowflake UDF 设计
    """
    if not prompt:
        return {"content": ""}
    
    if globals()['model'] is None:
        return {"content": "Error: 模型正在加载中，请稍候..."}
    
    messages = [{"role": "user", "content": prompt}]
    
    try:
        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(
            None,
            generate_response,
            messages,
            2048,
            0.7,
            0.95
        )
        return {"content": content}
    except Exception as e:
        logger.error(f"推理错误: {e}")
        return {"content": f"Error: {str(e)}"}


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "SPCS Qwen Model Service",
        "model": MODEL_NAME,
        "status": "ready" if model is not None else "loading",
        "endpoints": [
            "/health",
            "/v1/models",
            "/v1/chat/completions",
            "/v1/completions",
            "/complete"
        ]
    }


# ========================================
# 主函数
# ========================================
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", "8000"))
    workers = int(os.environ.get("WORKERS", "1"))  # GPU 推理通常用单 worker
    
    logger.info(f"启动服务: port={port}, workers={workers}")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info"
    )
