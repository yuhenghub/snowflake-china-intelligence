#!/bin/bash
set -e

# 模型名称
MODEL=${MODEL_NAME:-"Qwen/Qwen2.5-1.5B-Instruct"}

echo "======================================"
echo "Starting SPCS Qwen Model Service"
echo "Model: $MODEL"
echo "======================================"

# 使用 HF-Mirror 加速下载 (hf-mirror.com)
export HF_ENDPOINT=https://hf-mirror.com
echo "Using HF-Mirror for faster download: $HF_ENDPOINT"

# 安装依赖
pip install -q huggingface_hub httpx

# 从 HuggingFace (通过镜像) 下载模型
echo "Downloading model from HuggingFace via hf-mirror.com..."
huggingface-cli download --resume-download $MODEL --local-dir /models/

echo "Model downloaded successfully!"
echo "$(ls -ltr /models)"

# vLLM 启动参数
optional_args=()

# GPU 内存配置 (gpu_nv_s T4 16GB / A10 24GB)
optional_args+=("--gpu-memory-utilization" "0.9")

# 最大模型长度
optional_args+=("--max-model-len" "4096")

# 启动 vLLM 服务 (后台运行)
echo "Starting vLLM server on port 8000..."
python3 -m vllm.entrypoints.openai.api_server \
  --model /models \
  --served-model-name $MODEL \
  --trust-remote-code \
  --enforce-eager \
  --host 0.0.0.0 \
  --port 8000 \
  "${optional_args[@]}" &

VLLM_PID=$!
echo "vLLM started with PID: $VLLM_PID"

# 等待 vLLM 启动
echo "Waiting for vLLM to be ready..."
for i in {1..60}; do
  if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "vLLM is ready!"
    break
  fi
  echo "Waiting... ($i/60)"
  sleep 5
done

# 启动 Snowflake 代理 (前台运行，作为主进程)
echo "Starting Snowflake proxy on port 8001..."
export VLLM_URL=http://localhost:8000
export PROXY_PORT=8001
python3 /app/proxy.py
