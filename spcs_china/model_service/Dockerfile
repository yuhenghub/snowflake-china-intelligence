# SPCS Model Service Dockerfile for Snowflake China Region
# 使用 vLLM 运行 Qwen2.5-1.5B-Instruct 模型
# 使用国内镜像解决网络问题

# 使用 DaoCloud 镜像源
FROM docker.m.daocloud.io/vllm/vllm-openai:v0.7.0

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct \
    VLLM_USE_MODELSCOPE=True

# 使用清华镜像源安装依赖
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip && \
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple modelscope httpx

# 复制应用文件
COPY entrypoint.sh /app/entrypoint.sh
COPY proxy.py /app/proxy.py
RUN chmod +x /app/entrypoint.sh

# vLLM 端口: 8000, Proxy 端口: 8001
EXPOSE 8000 8001

ENTRYPOINT ["/app/entrypoint.sh"]
