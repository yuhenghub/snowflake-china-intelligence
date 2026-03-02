# LLM 模型一键部署指南

**Snowflake Container Services (SPCS) - 中国区私有化 LLM 部署**

支持多种开源大语言模型的一键部署，包括 DeepSeek、Qwen、ChatGLM、Llama 等。

---

## 快速开始

### 一键交互式部署

```bash
cd spcs_china
chmod +x deploy_model.sh
./deploy_model.sh deploy
```

脚本会引导你选择：
1. 要部署的模型（DeepSeek、Qwen、ChatGLM 等）
2. 模型下载镜像源（hf-mirror、官方源等）

---

## 支持的模型

### DeepSeek 系列

| 模型 | 大小 | 说明 | 推荐 GPU |
|-----|------|------|---------|
| deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B | ~3GB | 推理能力强，入门推荐 | GPU_NV_S |
| deepseek-ai/DeepSeek-R1-Distill-Qwen-7B | ~14GB | 更强推理能力 | GPU_NV_M |
| deepseek-ai/deepseek-coder-1.3b-instruct | ~2.5GB | 代码生成优化 | GPU_NV_S |
| deepseek-ai/deepseek-llm-7b-chat | ~14GB | 通用对话 | GPU_NV_M |

### Qwen 系列（阿里通义千问）

| 模型 | 大小 | 说明 | 推荐 GPU |
|-----|------|------|---------|
| Qwen/Qwen2.5-1.5B-Instruct | ~3GB | 最新版本，推荐 | GPU_NV_S |
| Qwen/Qwen2.5-3B-Instruct | ~6GB | 平衡性能和资源 | GPU_NV_S |
| Qwen/Qwen2.5-7B-Instruct | ~14GB | 高性能 | GPU_NV_M |
| Qwen/Qwen2.5-Coder-1.5B-Instruct | ~3GB | 代码生成 | GPU_NV_S |
| Qwen/Qwen2.5-Coder-7B-Instruct | ~14GB | 代码高性能 | GPU_NV_M |

### ChatGLM 系列（清华智谱）

| 模型 | 大小 | 说明 | 推荐 GPU |
|-----|------|------|---------|
| THUDM/chatglm3-6b | ~12GB | 通用对话 | GPU_NV_S/M |
| THUDM/glm-4-9b-chat | ~18GB | 最新版本 | GPU_NV_M |

### Llama 系列（Meta）

| 模型 | 大小 | 说明 | 推荐 GPU |
|-----|------|------|---------|
| meta-llama/Llama-3.2-1B-Instruct | ~2GB | 最小模型 | GPU_NV_S |
| meta-llama/Llama-3.2-3B-Instruct | ~6GB | 平衡选择 | GPU_NV_S |

### Yi 系列（零一万物）

| 模型 | 大小 | 说明 | 推荐 GPU |
|-----|------|------|---------|
| 01-ai/Yi-1.5-6B-Chat | ~12GB | 性能优秀 | GPU_NV_S/M |
| 01-ai/Yi-1.5-9B-Chat | ~18GB | 高性能 | GPU_NV_M |

### InternLM 系列（上海AI实验室）

| 模型 | 大小 | 说明 | 推荐 GPU |
|-----|------|------|---------|
| internlm/internlm2_5-1_8b-chat | ~3.5GB | 小巧高效 | GPU_NV_S |
| internlm/internlm2_5-7b-chat | ~14GB | 高性能 | GPU_NV_M |

### Baichuan 系列（百川智能）

| 模型 | 大小 | 说明 | 推荐 GPU |
|-----|------|------|---------|
| baichuan-inc/Baichuan2-7B-Chat | ~14GB | 中文优化 | GPU_NV_M |

---

## 模型下载镜像源

### 推荐镜像源

| 镜像源 | 地址 | 说明 |
|-------|------|------|
| **HF-Mirror** | https://hf-mirror.com | **强烈推荐**，国内访问最快 |
| HuggingFace 官方 | https://huggingface.co | 需要科学上网 |
| 上海交大镜像 | https://mirror.sjtu.edu.cn/hugging-face-models | 教育网访问快 |
| HF-Mirror CDN | https://hf-cdn.hf-mirror.com | 备用镜像 |

### HF-Mirror 使用说明

[HF-Mirror](https://hf-mirror.com) 是国内最稳定的 HuggingFace 镜像站：

- **网站**: https://hf-mirror.com
- **CDN**: https://cdn-lfs.hf-mirror.com
- **特点**: 免费、稳定、速度快

> 💡 **提示**: 中国大陆用户强烈建议使用 hf-mirror.com

---

## 前置条件

### 1. 本地环境要求

| 工具 | 版本要求 | 安装命令 |
|-----|---------|---------|
| Docker | 20.10+ | [Docker 官网](https://www.docker.com/) |
| Snowflake CLI | 最新版 | `pip install snowflake-cli-labs` |
| Python | 3.9+ | - |

### 2. Snowflake 账户要求

- Snowflake 中国区账户
- ACCOUNTADMIN 角色（或具有创建计算池权限的角色）
- SPCS 功能已启用
- GPU 配额已分配

### 3. Snowflake 连接配置

确保 `~/.snowflake/connections.toml` 中已配置 `china_dev` 连接：

```toml
[china_dev]
host = "YOUR_ACCOUNT.snowflakecomputing.cn"
account = "YOUR_ACCOUNT"
user = "YOUR_USER"
role = "YOUR_ROLE"
authenticator = "PROGRAMMATIC_ACCESS_TOKEN"
token_file_path = "/path/to/your-token.txt"
```

---

## 部署命令参考

```bash
# 交互式完整部署（推荐）
./deploy_model.sh deploy

# 快速部署（跳过镜像构建，使用已有镜像）
./deploy_model.sh quick

# 仅构建镜像
./deploy_model.sh build

# 构建并推送镜像
./deploy_model.sh push

# 仅创建服务（镜像已存在）
./deploy_model.sh service

# 查看服务状态
./deploy_model.sh status

# 查看服务日志
./deploy_model.sh logs

# 测试服务
./deploy_model.sh test

# 列出所有已部署的服务
./deploy_model.sh list

# 清理资源
./deploy_model.sh cleanup

# 显示可用模型列表
./deploy_model.sh models

# 显示可用镜像源列表
./deploy_model.sh mirrors

# 显示帮助
./deploy_model.sh help
```

---

## 环境变量配置

| 变量 | 默认值 | 说明 |
|-----|--------|------|
| SNOWFLAKE_CONNECTION | china_dev | Snowflake 连接名称 |
| MODEL_NAME | - | 预设模型名称（跳过交互选择） |
| HF_ENDPOINT | - | 预设镜像源（跳过交互选择） |
| IMAGE_TAG | latest | Docker 镜像标签 |

### 使用环境变量快速部署

```bash
# 预设模型和镜像源，跳过交互选择
MODEL_NAME="Qwen/Qwen2.5-1.5B-Instruct" \
HF_ENDPOINT="https://hf-mirror.com" \
./deploy_model.sh deploy

# 使用不同的连接
SNOWFLAKE_CONNECTION=china_prod ./deploy_model.sh deploy
```

---

## 使用示例

### SQL 调用

部署完成后，会自动创建对应的 UDF 函数。函数名格式为 `LLM_COMPLETE_<模型后缀>`。

```sql
-- DeepSeek 1.5B 模型
SELECT SPCS_CHINA.MODEL_SERVICE.LLM_COMPLETE_DEEPSEEK_1_5B(
    '{"model":"deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B","messages":[{"role":"user","content":"什么是机器学习？"}]}'
);

-- Qwen 1.5B 模型
SELECT SPCS_CHINA.MODEL_SERVICE.LLM_COMPLETE_QWEN_1_5B(
    '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[{"role":"user","content":"请介绍一下你自己"}]}'
);

-- 带系统提示词
SELECT SPCS_CHINA.MODEL_SERVICE.LLM_COMPLETE_QWEN_1_5B(
    '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[
        {"role":"system","content":"你是一个专业的数据分析师"},
        {"role":"user","content":"如何优化 SQL 查询性能？"}
    ]}'
);

-- 批量处理
SELECT 
    id,
    question,
    SPCS_CHINA.MODEL_SERVICE.LLM_COMPLETE_QWEN_1_5B(
        '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[{"role":"user","content":"' || question || '"}]}'
    ) AS answer
FROM my_questions
LIMIT 10;
```

### Streamlit 应用

```python
import streamlit as st
import json
from snowflake.snowpark.context import get_active_session

session = get_active_session()

# 选择已部署的模型
MODEL_OPTIONS = {
    "DeepSeek R1 1.5B": ("LLM_COMPLETE_DEEPSEEK_1_5B", "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"),
    "Qwen 2.5 1.5B": ("LLM_COMPLETE_QWEN_1_5B", "Qwen/Qwen2.5-1.5B-Instruct"),
    "ChatGLM3 6B": ("LLM_COMPLETE_CHATGLM3", "THUDM/chatglm3-6b"),
}

def call_llm(udf_name: str, model_name: str, prompt: str) -> str:
    payload = json.dumps({
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}]
    }, ensure_ascii=False).replace("'", "''")
    
    result = session.sql(f"SELECT SPCS_CHINA.MODEL_SERVICE.{udf_name}('{payload}')").collect()
    return result[0][0] if result else ""

st.title("LLM 助手")
selected_model = st.selectbox("选择模型", list(MODEL_OPTIONS.keys()))
udf_name, model_name = MODEL_OPTIONS[selected_model]

user_input = st.chat_input("请输入您的问题...")
if user_input:
    with st.spinner("思考中..."):
        response = call_llm(udf_name, model_name, user_input)
        st.write(response)
```

---

## 服务管理

### 暂停服务（节省成本）

```sql
ALTER SERVICE SPCS_CHINA.MODEL_SERVICE.LLM_SERVICE_QWEN_1_5B SUSPEND;
```

### 恢复服务

```sql
ALTER SERVICE SPCS_CHINA.MODEL_SERVICE.LLM_SERVICE_QWEN_1_5B RESUME;
```

### 重启服务

```sql
ALTER SERVICE SPCS_CHINA.MODEL_SERVICE.LLM_SERVICE_QWEN_1_5B RESTART;
```

### 查看服务日志

```sql
SELECT SYSTEM$GET_SERVICE_LOGS('SPCS_CHINA.MODEL_SERVICE.LLM_SERVICE_QWEN_1_5B', 0, 'model-service', 100);
```

### 列出所有服务

```sql
SHOW SERVICES LIKE 'LLM_SERVICE_%' IN SCHEMA SPCS_CHINA.MODEL_SERVICE;
```

---

## GPU 配额说明

| 实例类型 | GPU | 显存 | 推荐模型大小 | 每小时成本 |
|---------|-----|------|------------|----------|
| GPU_NV_S | NVIDIA T4 | 16GB | ≤7B | ~$2-3 |
| GPU_NV_M | NVIDIA A10 | 24GB | ≤13B | ~$4-5 |
| GPU_NV_L | NVIDIA A100 | 40GB | ≤30B | ~$8-10 |

> 💡 **建议**: 
> - 小模型（1-3B）使用 GPU_NV_S
> - 中等模型（6-7B）使用 GPU_NV_S 或 GPU_NV_M
> - 大模型（9B+）必须使用 GPU_NV_M 或更高

---

## 故障排除

### 常见问题

| 问题 | 可能原因 | 解决方案 |
|-----|---------|---------|
| Docker 登录失败 | PAT Token 过期 | 在 Snowflake 中重新创建 PAT Token |
| 镜像推送失败 | 网络问题 | 检查网络连接，重试 |
| 服务启动超时 | 模型下载慢 | 检查镜像源是否可访问 |
| GPU 不可用 | 配额不足 | 联系 Snowflake 支持 |
| OOM 错误 | 模型太大 | 选择更小的模型或更大的 GPU |
| 下载失败 | 镜像源不通 | 尝试其他镜像源 |

### 检查网络连通性

```sql
-- 检查外部访问配置
SHOW NETWORK RULES IN SCHEMA SPCS_CHINA.MODEL_SERVICE;
SHOW EXTERNAL ACCESS INTEGRATIONS;
```

### 网络规则支持的域名

部署脚本自动配置以下域名的网络访问：

| 域名 | 用途 |
|-----|------|
| hf-mirror.com | HuggingFace 国内镜像 |
| cdn-lfs.hf-mirror.com | HF-Mirror LFS CDN |
| cas-bridge.xethub.hf.co | HuggingFace XetHub CDN |
| xethub.hf.co | HuggingFace XetHub |
| huggingface.co | HuggingFace 官方 |
| modelscope.cn | ModelScope 魔搭 |
| mirror.sjtu.edu.cn | 上海交大镜像 |

### 查看详细日志

```bash
# 查看完整服务日志
./deploy_model.sh logs
```

### 重新部署

如果部署失败，可以清理后重试：

```bash
./deploy_model.sh cleanup
./deploy_model.sh deploy
```

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Snowflake China Region                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              LLM_COMPLETE_xxx() UDF                  │    │
│  │         Service Function → SPCS Endpoint            │    │
│  └───────────────────────┬─────────────────────────────┘    │
│                          │                                   │
│  ┌───────────────────────▼─────────────────────────────┐    │
│  │              SPCS Container Service                  │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │        GPU Compute Pool (GPU_NV_S/M)        │    │    │
│  │  │  ┌───────────────┐  ┌───────────────────┐  │    │    │
│  │  │  │ Proxy (:8001) │─▶│ vLLM (:8000)      │  │    │    │
│  │  │  │ - 格式转换     │  │ - LLM Model       │  │    │    │
│  │  │  │ - 健康检查     │  │ - GPU 推理        │  │    │    │
│  │  │  └───────────────┘  └───────────────────┘  │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Model Download Mirror                   │    │
│  │   hf-mirror.com / huggingface.co / modelscope.cn   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 参考资料

- [Snowflake Container Services 文档](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)
- [HF-Mirror 国内镜像](https://hf-mirror.com/)
- [DeepSeek 模型](https://github.com/deepseek-ai/DeepSeek-LLM)
- [Qwen 模型](https://github.com/QwenLM/Qwen2.5)
- [ChatGLM 模型](https://github.com/THUDM/ChatGLM3)
- [vLLM 高性能推理框架](https://github.com/vllm-project/vllm)

---

*如有问题，请联系 Snowflake 中国技术支持。*
