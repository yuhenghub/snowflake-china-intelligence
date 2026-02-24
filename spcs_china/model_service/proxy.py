"""
Snowflake Service Function 代理
处理 Snowflake Service Function 的 {"data": [[row_id, payload]]} 格式
转换为 vLLM 的 OpenAI API 格式
"""

import os
import json
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="Snowflake SPCS Proxy")

VLLM_URL = os.environ.get("VLLM_URL", "http://localhost:8000")
MODEL_NAME = os.environ.get("MODEL_NAME", "Qwen/Qwen2.5-1.5B-Instruct")


@app.get("/health")
async def health():
    """Health check - 转发到 vLLM"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{VLLM_URL}/health", timeout=5)
            return JSONResponse(content={"status": "healthy"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"status": "unhealthy", "error": str(e)}, status_code=503)


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    处理 Snowflake Service Function 格式
    输入: {"data": [[0, '{"model": "...", "messages": [...]}']]}
    """
    body = await request.json()
    
    # Snowflake Service Function 格式
    if "data" in body:
        results = []
        for row in body["data"]:
            row_id = row[0]
            payload_str = row[1]
            
            try:
                # 解析 JSON 字符串
                payload = json.loads(payload_str)
                
                # 确保有 model 字段
                if "model" not in payload:
                    payload["model"] = MODEL_NAME
                
                # 调用 vLLM
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        f"{VLLM_URL}/v1/chat/completions",
                        json=payload,
                        timeout=120
                    )
                    result = resp.json()
                    
                    # 提取响应内容
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]
                    else:
                        content = json.dumps(result)
                    
                    results.append([row_id, content])
                    
            except json.JSONDecodeError as e:
                results.append([row_id, f"Error: Invalid JSON - {str(e)}"])
            except Exception as e:
                results.append([row_id, f"Error: {str(e)}"])
        
        return {"data": results}
    
    # 直接 OpenAI 格式 - 转发到 vLLM
    else:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{VLLM_URL}/v1/chat/completions",
                json=body,
                timeout=120
            )
            return resp.json()


@app.post("/complete")
async def simple_complete(request: Request):
    """
    简单的完成接口 - 处理 Snowflake Service Function 格式
    输入: {"data": [[0, "prompt text"]]}
    """
    body = await request.json()
    
    if "data" in body:
        results = []
        for row in body["data"]:
            row_id = row[0]
            prompt = row[1]
            
            try:
                # 构建 OpenAI 格式请求
                payload = {
                    "model": MODEL_NAME,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2048,
                    "temperature": 0.7
                }
                
                # 调用 vLLM
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        f"{VLLM_URL}/v1/chat/completions",
                        json=payload,
                        timeout=120
                    )
                    result = resp.json()
                    
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]
                    else:
                        content = json.dumps(result)
                    
                    results.append([row_id, content])
                    
            except Exception as e:
                results.append([row_id, f"Error: {str(e)}"])
        
        return {"data": results}
    
    return {"error": "Invalid format. Expected {'data': [[row_id, prompt], ...]}"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PROXY_PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)




