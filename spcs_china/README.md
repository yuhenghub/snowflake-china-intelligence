# SPCS 私有化 LLM 服务

**Snowflake China Intelligence** 的核心组件之一

[English Version](./README_EN.md) | 中文版

> 基于 Snowflake Container Services (SPCS) 的私有化 LLM 解决方案。在 Snowflake 平台内部署和运行开源大语言模型，确保数据不出数据平台，满足企业数据合规要求。

---

## 📁 项目结构

```
spcs_china/
├── README.md                    # 项目文档 (中文)
├── README_EN.md                 # 项目文档 (English)
├── deploy.sh                    # 一键部署脚本
├── check_status.sh              # 服务状态检查脚本
├── streamlit_example.py         # Streamlit 示例应用
│
├── model_service/               # 模型服务核心代码
│   ├── Dockerfile               # Docker 镜像构建文件 (基于 vLLM)
│   ├── entrypoint.sh            # 容器启动脚本 (下载模型 + 启动服务)
│   ├── proxy.py                 # Snowflake Service Function 代理
│   ├── app.py                   # 备用 Transformers 推理服务
│   ├── download_model.py        # 模型下载脚本
│   ├── requirements.txt         # Python 依赖
│   └── spec.yaml                # SPCS 服务规格模板
│
└── setup_sql/                   # SQL 设置脚本 (按顺序执行)
    ├── 01_create_compute_pool.sql   # 创建 GPU 计算池
    ├── 02_create_external_access.sql # 配置外部网络访问
    ├── 03_create_image_repo.sql     # 创建镜像仓库
    ├── 04_create_service.sql        # 创建 SPCS 服务
    └── 05_create_udf.sql            # 创建 UDF 函数
```

---

## 📌 背景

### 方案价值

本方案基于 **Snowflake Container Services (SPCS)** 为中国区客户提供强大的 AI 能力：

- ✅ **数据合规**：模型完全运行在 Snowflake 平台内，数据不出数据平台，满足合规要求
- ✅ **开箱即用**：通过 UDF 提供与 Cortex LLM 类似的调用体验，无需改变现有工作流
- ✅ **灵活定制**：可自由选择和部署开源模型，满足不同业务场景需求
- ✅ **成本可控**：GPU 按需使用，支持自动暂停，有效控制成本

### 解决思路

我们设计了一个基于 **Snowflake Container Services (SPCS)** 的自托管 LLM 方案：

1. **使用开源模型**：部署阿里通义千问 (Qwen) 系列模型
2. **本地化部署**：模型完全运行在 Snowflake 平台内，数据不出数据平台
3. **无缝集成**：通过 UDF 提供与 Cortex LLM 类似的调用体验
4. **GPU 加速**：利用 SPCS 的 GPU 计算池实现高效推理

---

## 🏗️ 架构设计

### 架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Snowflake China Region                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        User Applications                             │    │
│  │  ┌─────────────┐  ┌─────────────────┐  ┌──────────────────────────┐ │    │
│  │  │ Streamlit   │  │  SQL Worksheet  │  │  BI Tools (Tableau etc.) │ │    │
│  │  └──────┬──────┘  └────────┬────────┘  └────────────┬─────────────┘ │    │
│  └─────────┼──────────────────┼────────────────────────┼───────────────┘    │
│            │                  │                        │                     │
│            ▼                  ▼                        ▼                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     QWEN_COMPLETE() UDF                              │    │
│  │          Service Function → SPCS Service Endpoint                    │    │
│  └─────────────────────────────────┬───────────────────────────────────┘    │
│                                    │                                         │
│  ┌─────────────────────────────────▼───────────────────────────────────┐    │
│  │              Snowflake Container Services (SPCS)                     │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │                   GPU Compute Pool (GPU_NV_S)                  │  │    │
│  │  │                    NVIDIA T4 / A10 GPU                         │  │    │
│  │  │  ┌─────────────────────────────────────────────────────────┐  │  │    │
│  │  │  │              QWEN_MODEL_SERVICE Container                │  │  │    │
│  │  │  │  ┌─────────────────┐    ┌─────────────────────────────┐ │  │  │    │
│  │  │  │  │  Snowflake      │    │    vLLM / Transformers      │ │  │  │    │
│  │  │  │  │  Proxy (:8001)  │───▶│    Inference (:8000)        │ │  │  │    │
│  │  │  │  │                 │    │                             │ │  │  │    │
│  │  │  │  │  - 格式转换      │    │  - Qwen2.5-1.5B-Instruct   │ │  │  │    │
│  │  │  │  │  - 健康检查      │    │  - GPU 推理                 │ │  │  │    │
│  │  │  │  └─────────────────┘    └─────────────────────────────┘ │  │  │    │
│  │  │  └─────────────────────────────────────────────────────────┘  │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  │                                    │                                 │    │
│  │                                    │ External Access Integration     │    │
│  │                                    ▼                                 │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │              Model Download (首次启动)                         │  │    │
│  │  │    ┌─────────────────┐    ┌────────────────────────────────┐  │  │    │
│  │  │    │  HF-Mirror      │    │   ModelScope                   │  │  │    │
│  │  │    │  (hf-mirror.com)│    │   (modelscope.cn)              │  │  │    │
│  │  │    │  ✓ 推荐          │    │   ✓ 备用                        │  │  │    │
│  │  │    └─────────────────┘    └────────────────────────────────┘  │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 架构说明

#### 1. 用户层 (User Applications)

- **Streamlit in Snowflake**: 构建交互式 AI 应用
- **SQL Worksheet**: 直接在 SQL 中调用 LLM
- **BI Tools**: 与 Tableau、Power BI 等工具集成

#### 2. 服务接口层 (UDF)

```sql
-- 用户调用方式
SELECT SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE(
  '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[{"role":"user","content":"你好"}]}'
);
```

- 使用 **Service Function** 将 UDF 请求路由到 SPCS 服务
- 自动处理 Snowflake 的批量请求格式 (`{"data": [[row_id, payload], ...]}`)

#### 3. SPCS 服务层 (Container Services)

**GPU 计算池**：
- 实例类型：`GPU_NV_S` (NVIDIA T4 16GB / A10 24GB)
- 自动扩缩：MIN_NODES=1, MAX_NODES=2
- 自动暂停：600 秒无请求后自动暂停

**容器架构**：
- **Snowflake Proxy (Port 8001)**: 处理 Snowflake Service Function 的特殊请求格式
- **vLLM / Transformers (Port 8000)**: 高性能 LLM 推理引擎

#### 4. 模型下载层 (External Access)

由于网络限制，我们配置了两个模型下载源：

| 下载源 | 域名 | 优先级 | 说明 |
|-------|------|--------|------|
| HF-Mirror | hf-mirror.com | ✅ 推荐 | HuggingFace 国内镜像，速度快 |
| ModelScope | modelscope.cn | 备用 | 阿里云模型库 |

---

## 📋 实施先决条件

### Snowflake 环境要求

| 要求 | 说明 |
|-----|------|
| **Snowflake 账户** | Snowflake 中国区账户 |
| **角色权限** | ACCOUNTADMIN（创建计算池和外部访问集成）|
| **SPCS 功能** | 账户已启用 Snowflake Container Services |
| **GPU 配额** | 账户有 GPU 计算池配额 |

### 本地开发环境

| 工具 | 版本要求 | 用途 |
|-----|---------|------|
| **Docker** | 20.10+ | 构建容器镜像 |
| **SnowSQL** | 最新版 | 执行 SQL 脚本 |
| **Python** | 3.9+ | （可选）本地测试 |

### 网络要求

确保 SPCS 服务可以访问以下域名：

```
# HF-Mirror (推荐)
hf-mirror.com:443
cdn-lfs.hf-mirror.com:443

# ModelScope (备用)
modelscope.cn:443
www.modelscope.cn:443
cdn-lfs-cn-1.modelscope.cn:443
cdn-lfs-cn-2.modelscope.cn:443
```

---

## 🚀 快速开始

### 一键部署

```bash
# 设置环境变量
export SNOWFLAKE_ACCOUNT="your_account"
export SNOWFLAKE_USER="your_user"

# 运行一键部署
./deploy.sh deploy

# 或者分步执行
./deploy.sh build    # 仅构建镜像
./deploy.sh push     # 构建并推送
./deploy.sh sql      # 仅执行 SQL
```

### 手动部署步骤

详细步骤请参考下方的 [实施过程](#-实施过程) 章节。

---

## 🔧 实施过程

### 步骤概览

```
┌────────────────────────────────────────────────────────────────────┐
│                         部署流程                                    │
│                                                                     │
│   Step 1          Step 2          Step 3          Step 4           │
│  ┌─────────┐    ┌─────────────┐  ┌───────────┐  ┌─────────────┐   │
│  │ 创建     │    │ 配置        │  │ 构建并    │  │ 创建服务    │   │
│  │ 计算池   │───▶│ 网络访问    │─▶│ 推送镜像  │─▶│ 和 UDF     │   │
│  └─────────┘    └─────────────┘  └───────────┘  └─────────────┘   │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

### Step 1: 创建数据库和计算池

```sql
-- 使用 ACCOUNTADMIN 角色
USE ROLE ACCOUNTADMIN;

-- 创建数据库和 Schema
CREATE DATABASE IF NOT EXISTS SPCS_CHINA;
CREATE SCHEMA IF NOT EXISTS SPCS_CHINA.MODEL_SERVICE;

-- 创建 GPU 计算池
CREATE COMPUTE POOL IF NOT EXISTS GPU_NV_S_POOL
    MIN_NODES = 1
    MAX_NODES = 2
    INSTANCE_FAMILY = GPU_NV_S
    AUTO_RESUME = TRUE
    AUTO_SUSPEND_SECS = 600
    COMMENT = 'GPU compute pool for LLM inference service (China Region)';

-- 验证计算池创建成功
SHOW COMPUTE POOLS;
DESC COMPUTE POOL GPU_NV_S_POOL;
```

### Step 2: 配置外部网络访问

```sql
USE DATABASE SPCS_CHINA;
USE SCHEMA MODEL_SERVICE;

-- 创建网络规则：允许访问模型下载源
CREATE OR REPLACE NETWORK RULE modelscope_network_rule
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = (
        -- HF-Mirror (推荐)
        'hf-mirror.com:443',
        'cdn-lfs.hf-mirror.com:443',
        -- ModelScope (备用)
        'www.modelscope.cn:443',
        'modelscope.cn:443',
        'cdn-lfs-cn-1.modelscope.cn:443',
        'cdn-lfs-cn-2.modelscope.cn:443'
    )
    COMMENT = 'Network rule for model download';

-- 创建外部访问集成
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION modelscope_access_integration
    ALLOWED_NETWORK_RULES = (modelscope_network_rule)
    ENABLED = TRUE
    COMMENT = 'External access for model download';
```

### Step 3: 创建镜像仓库并推送 Docker 镜像

```sql
-- 创建镜像仓库
CREATE IMAGE REPOSITORY IF NOT EXISTS MODEL_SERVICE_REPO
    COMMENT = 'Image repository for SPCS model service';

-- 获取仓库 URL
SHOW IMAGE REPOSITORIES LIKE 'MODEL_SERVICE_REPO';
-- 从结果中的 repository_url 列复制完整 URL
-- 示例输出: <org>-<account>.registry.snowflakecomputing.cn/spcs_china/model_service/model_service_repo
```

#### 登录镜像仓库（使用 PAT Token）

由于很多企业账户禁用了用户名/密码登录，推荐使用 **Programmatic Access Token (PAT)** 登录镜像仓库。

**Step 1: 创建 PAT Token**

在 Snowflake 中执行以下 SQL 创建 PAT：

```sql
-- 创建一个有效期 30 天的 PAT Token
ALTER USER <your_username> ADD PROGRAMMATIC ACCESS TOKEN
    TOKEN_NAME = 'docker_registry_token'
    TOKEN_VALIDITY_IN_DAYS = 30
    COMMENT = 'Token for Docker registry login';

-- 查看已创建的 Token（注意：Token 值只在创建时显示一次，请妥善保存）
SHOW PROGRAMMATIC ACCESS TOKENS FOR USER <your_username>;
```

> **重要提示：**
> - PAT Token 只在创建时显示一次，请立即复制并安全保存
> - 如果忘记 Token，需要删除后重新创建：`ALTER USER <your_username> REMOVE PROGRAMMATIC ACCESS TOKEN TOKEN_NAME = 'docker_registry_token';`
> - 更多信息请参考 [Snowflake PAT 文档](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens)

**Step 2: 查询 Image Repository URL**

```bash
# 使用 Snowflake CLI 查询
snow sql -c <your_connection> -q "SHOW IMAGE REPOSITORIES;"

# 或在 Snowflake Worksheet 中执行
# SHOW IMAGE REPOSITORIES LIKE 'MODEL_SERVICE_REPO';
```

从结果中复制 `repository_url` 列的值，例如：`xxx-xxx.registry.snowflakecomputing.cn/spcs_china/model_service/model_service_repo`

**Step 3: 使用 PAT Token 登录 Docker Registry**

```bash
# 将 <PAT_TOKEN> 替换为 Step 1 中获取的 Token
# 将 <REGISTRY_HOST> 替换为 repository_url 的域名部分
# 将 <YOUR_USERNAME> 替换为您的 Snowflake 用户名

echo "<PAT_TOKEN>" | docker login <REGISTRY_HOST> -u <YOUR_USERNAME> --password-stdin
```

**示例：**

```bash
echo "eyJraWQiOiIz..." | docker login xxx-xxx.registry.snowflakecomputing.cn -u MY_USER --password-stdin
```

> **说明：**
> - 用户名是您的 **Snowflake 用户名**（创建 PAT 的用户）
> - 密码是 **PAT Token**（不是 Snowflake 登录密码）
> - 该用户/角色需要对仓库有 `READ, WRITE ON IMAGE REPOSITORY` 权限

#### 构建与推送镜像

完成 `docker login` 后，执行以下步骤：

```bash
# 设置环境变量（从 SHOW IMAGE REPOSITORIES 结果中复制 repository_url）
export REGISTRY_URL="<org>-<account>.registry.snowflakecomputing.cn/spcs_china/model_service/model_service_repo"

# 1. 构建 Docker 镜像
cd spcs_china/model_service
docker build -t qwen-service:latest .

# 2. 标记并推送镜像
docker tag qwen-service:latest ${REGISTRY_URL}/qwen-service:latest
docker push ${REGISTRY_URL}/qwen-service:latest

# 3. 验证上传
snow sql -c <your_connection> -q "SHOW IMAGES IN IMAGE REPOSITORY SPCS_CHINA.MODEL_SERVICE.MODEL_SERVICE_REPO;"
```

### Step 4: 创建 SPCS 服务

```sql
USE DATABASE SPCS_CHINA;
USE SCHEMA MODEL_SERVICE;

-- 创建服务
CREATE SERVICE IF NOT EXISTS QWEN_MODEL_SERVICE
    IN COMPUTE POOL GPU_NV_S_POOL
    MIN_INSTANCES = 1
    MAX_INSTANCES = 1
    EXTERNAL_ACCESS_INTEGRATIONS = (modelscope_access_integration)
    FROM SPECIFICATION $$
spec:
  containers:
    - name: qwen-service
      image: /spcs_china/model_service/model_service_repo/qwen-service:latest
      env:
        MODEL_NAME: "Qwen/Qwen2.5-1.5B-Instruct"
        HF_ENDPOINT: "https://hf-mirror.com"
      resources:
        requests:
          memory: 8Gi
          cpu: 2
          nvidia.com/gpu: 1
        limits:
          memory: 14Gi
          cpu: 4
          nvidia.com/gpu: 1
      readinessProbe:
        httpGet:
          path: /health
          port: 8001
        initialDelaySeconds: 120
        periodSeconds: 30
  endpoints:
    - name: qwen-api
      port: 8001
      public: false
$$;

-- 查看服务状态
SELECT SYSTEM$GET_SERVICE_STATUS('QWEN_MODEL_SERVICE');

-- 查看服务日志（监控模型下载进度）
SELECT SYSTEM$GET_SERVICE_LOGS('QWEN_MODEL_SERVICE', 0, 'qwen-service', 50);
```

### Step 5: 创建 UDF 并测试

```sql
-- 创建 Service Function UDF
CREATE OR REPLACE FUNCTION QWEN_COMPLETE(prompt VARCHAR)
RETURNS VARCHAR
SERVICE = QWEN_MODEL_SERVICE
ENDPOINT = 'qwen-api'
MAX_BATCH_ROWS = 1
AS '/v1/chat/completions';

-- 授权给其他角色
GRANT USAGE ON FUNCTION QWEN_COMPLETE(VARCHAR) TO ROLE PUBLIC;

-- 测试调用
SELECT SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE(
  '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[{"role":"user","content":"介绍一下 Snowflake 数据云"}]}'
) AS response;
```

---

## 📊 使用示例

### 基础调用

```sql
-- 简单问答
SELECT QWEN_COMPLETE(
  '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[{"role":"user","content":"什么是数据仓库？"}]}'
);

-- 带系统提示词
SELECT QWEN_COMPLETE(
  '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[
    {"role":"system","content":"你是一个数据分析专家"},
    {"role":"user","content":"如何优化 SQL 查询性能？"}
  ]}'
);
```

### 批量处理

```sql
-- 批量生成产品描述
SELECT 
    product_id,
    product_name,
    QWEN_COMPLETE(
      '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[
        {"role":"system","content":"为以下产品生成简短的营销描述"},
        {"role":"user","content":"' || product_name || '"}
      ]}'
    ) AS ai_description
FROM products
LIMIT 10;
```

### 在 Streamlit 中使用

我们提供了完整的 Streamlit 示例应用 `streamlit_example.py`，包含：

- 💬 交互式对话界面
- 📝 批量文本处理功能
- 🔧 SQL 调用示例和测试工具
- ⚙️ 可配置的参数（Temperature、Max Tokens 等）

**快速示例代码：**

```python
import streamlit as st
import json
from snowflake.snowpark.context import get_active_session

# UDF 路径
QWEN_UDF_PATH = "SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE"

def call_qwen_complete(session, prompt: str, system_prompt: str = None) -> str:
    """调用 QWEN_COMPLETE UDF"""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = json.dumps({
        "model": "Qwen/Qwen2.5-1.5B-Instruct",
        "messages": messages
    }, ensure_ascii=False).replace("'", "''")
    
    query = f"SELECT {QWEN_UDF_PATH}('{payload}')"
    result = session.sql(query).collect()
    return result[0][0] if result else ""

# Streamlit 应用
session = get_active_session()
st.title("🤖 Qwen AI Assistant (China Region)")

user_input = st.chat_input("请输入您的问题...")
if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            response = call_qwen_complete(session, user_input)
            st.markdown(response)
```

---

## 💰 成本与性能

### 成本估算

| 组件 | 规格 | 估算成本 (参考) |
|-----|------|---------------|
| GPU 计算池 | GPU_NV_S (T4 16GB) | ~$2-3/小时 |
| 存储 | 镜像 + Stage | < $1/月 |
| 网络 | 内部通信 | 包含 |

**成本优化建议**：
- 设置 `AUTO_SUSPEND_SECS = 600` 自动暂停
- 非工作时间手动暂停服务：`ALTER SERVICE QWEN_MODEL_SERVICE SUSPEND;`

### 性能参考

| 指标 | Qwen2.5-1.5B | 说明 |
|-----|--------------|------|
| 首次启动 | 3-5 分钟 | 包含模型下载 |
| 冷启动 | 60-90 秒 | 模型已缓存 |
| 推理延迟 | 1-3 秒 | 100 tokens 输出 |
| 吞吐量 | ~50 tokens/s | 单请求 |

---

## 🔧 运维管理

### 服务监控

```sql
-- 查看服务状态
SELECT SYSTEM$GET_SERVICE_STATUS('QWEN_MODEL_SERVICE');

-- 查看服务日志
SELECT SYSTEM$GET_SERVICE_LOGS('QWEN_MODEL_SERVICE', 0, 'qwen-service', 100);

-- 查看计算池状态
DESC COMPUTE POOL GPU_NV_S_POOL;
```

### 常用管理命令

```sql
-- 暂停服务（节省成本）
ALTER SERVICE QWEN_MODEL_SERVICE SUSPEND;

-- 恢复服务
ALTER SERVICE QWEN_MODEL_SERVICE RESUME;

-- 重启服务
ALTER SERVICE QWEN_MODEL_SERVICE RESTART;

-- 更新镜像后重新部署
ALTER SERVICE QWEN_MODEL_SERVICE 
    FROM SPECIFICATION $$ ... $$;
```

### 故障排除

| 问题 | 可能原因 | 解决方案 |
|-----|---------|---------|
| 服务启动超时 | 模型下载慢 | 检查网络规则，确认 HF-Mirror 可访问 |
| GPU 不可用 | 计算池配额不足 | 联系 Snowflake 支持增加配额 |
| 推理错误 | 内存不足 | 增加容器内存限制或使用更小模型 |

---

## 📝 总结

### 方案优势

✅ **数据不出平台**：模型完全运行在 Snowflake 平台内，满足合规要求

✅ **无缝集成**：通过 UDF 提供类似 Cortex LLM 的调用体验

✅ **灵活扩展**：可更换为其他开源模型（Qwen-7B、ChatGLM 等）

✅ **成本可控**：支持自动暂停，按需付费

✅ **一键部署**：提供自动化脚本，简化实施过程

### 适用场景

- 中国区客户需要在 Snowflake 中使用 AI 能力
- 对数据安全有严格要求，不允许数据出境
- 需要与现有 Snowflake 工作流（SQL、Streamlit）集成
- 等待 Cortex LLM 中国区上线前的过渡方案

### 后续演进

当 Snowflake Cortex LLM 在中国区正式上线后，用户可以：
1. 逐步迁移到官方 Cortex LLM 服务
2. 保留 SPCS 方案用于特定场景（定制模型、私有部署）
3. 混合使用两种方案以满足不同需求

---

## 📚 参考资料

- [Snowflake Container Services 文档](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)
- [Qwen2.5 模型介绍](https://github.com/QwenLM/Qwen2.5)
- [vLLM 高性能推理框架](https://github.com/vllm-project/vllm)
- [HF-Mirror 国内镜像](https://hf-mirror.com/)

---

## 📄 License

MIT License

---

*本项目由 Snowflake 中国团队整理，如有问题请联系技术支持。*
