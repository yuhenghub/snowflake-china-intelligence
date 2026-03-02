# SPCS Self-Hosted LLM Service

**A core component of Snowflake China Intelligence**

[中文版](./README.md) | English Version

> A private LLM solution based on Snowflake Container Services (SPCS). Deploy and run open-source large language models within the Snowflake platform, ensuring data stays within the platform and meets enterprise compliance requirements.

---

## 🎯 Supported Models

| Model | Size | Description | Deploy Script |
|-------|------|-------------|---------------|
| **Qwen/Qwen2.5-1.5B-Instruct** | ~3GB | Alibaba Qwen, Chinese & English | `deploy.sh` |
| **deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B** | ~3GB | DeepSeek-R1 distilled, with reasoning chain | `deploy_deepseek.sh` |
| deepseek-ai/deepseek-coder-1.3b-instruct | ~2.5GB | DeepSeek code generation optimized | `deploy_deepseek.sh` |

---

## 📁 Project Structure

```
spcs_china/
├── README.md                    # Documentation (Chinese)
├── README_EN.md                 # Documentation (English)
├── deploy.sh                    # Qwen one-click deployment script
├── deploy_deepseek.sh           # DeepSeek one-click deployment script
├── check_status.sh              # Qwen service status check
├── check_deepseek_status.sh     # DeepSeek service status check
├── DEPLOY_DEEPSEEK.md           # DeepSeek deployment guide
├── streamlit_example.py         # Streamlit example app (multi-model management)
│
├── model_service/               # Model service core code
│   ├── Dockerfile               # Docker image build file (based on vLLM)
│   ├── entrypoint.sh            # Container startup script
│   ├── proxy.py                 # Snowflake Service Function proxy
│   ├── app.py                   # Backup Transformers inference service
│   ├── download_model.py        # Model download script
│   ├── requirements.txt         # Python dependencies
│   └── spec.yaml                # SPCS service spec template
│
└── setup_sql/                   # SQL setup scripts (execute in order)
    ├── 01_create_compute_pool.sql   # Create GPU compute pool
    ├── 02_create_external_access.sql # Configure external network access
    ├── 03_create_image_repo.sql     # Create image repository
    ├── 04_create_service.sql        # Create SPCS service
    └── 05_create_udf.sql            # Create UDF function
```

---

## 📌 Background

### Solution Value

This solution provides powerful AI capabilities for China region customers based on **Snowflake Container Services (SPCS)**:

- ✅ **Data Compliance**: Models run entirely within the Snowflake platform, data stays within the platform, meeting compliance requirements
- ✅ **Ready to Use**: Provides Cortex LLM-like experience via UDF, no need to change existing workflows
- ✅ **Flexible Customization**: Freedom to choose and deploy open-source models for different business scenarios
- ✅ **Cost Effective**: GPU on-demand usage with auto-suspend support for effective cost control

### Solution Approach

We designed a self-hosted LLM solution based on **Snowflake Container Services (SPCS)**:

1. **Use Open-Source Models**: Support multiple models including Qwen and DeepSeek
2. **Local Deployment**: Models run entirely within the Snowflake platform, data stays within the platform
3. **Seamless Integration**: Provide a Cortex LLM-like experience via UDF
4. **GPU Acceleration**: Leverage SPCS GPU compute pools for efficient inference
5. **Service Management**: Manage services (start/stop) via Streamlit app

---

## 🏗️ Architecture Design

### Architecture Diagram

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
│  │  │  │  │  - Format conv. │    │  - Qwen2.5-1.5B-Instruct   │ │  │  │    │
│  │  │  │  │  - Health check │    │  - GPU inference            │ │  │  │    │
│  │  │  │  └─────────────────┘    └─────────────────────────────┘ │  │  │    │
│  │  │  └─────────────────────────────────────────────────────────┘  │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  │                                    │                                 │    │
│  │                                    │ External Access Integration     │    │
│  │                                    ▼                                 │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │              Model Download (First startup)                    │  │    │
│  │  │    ┌─────────────────┐    ┌────────────────────────────────┐  │  │    │
│  │  │    │  HF-Mirror      │    │   ModelScope                   │  │  │    │
│  │  │    │  (hf-mirror.com)│    │   (modelscope.cn)              │  │  │    │
│  │  │    │  ✓ Recommended  │    │   ✓ Backup                     │  │  │    │
│  │  │    └─────────────────┘    └────────────────────────────────┘  │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Architecture Components

#### 1. User Layer (User Applications)

- **Streamlit in Snowflake**: Build interactive AI applications
- **SQL Worksheet**: Call LLM directly from SQL
- **BI Tools**: Integrate with Tableau, Power BI, etc.

#### 2. Service Interface Layer (UDF)

```sql
-- User calling method
SELECT SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE(
  '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[{"role":"user","content":"Hello"}]}'
);
```

- Uses **Service Function** to route UDF requests to SPCS service
- Automatically handles Snowflake's batch request format (`{"data": [[row_id, payload], ...]}`)

#### 3. SPCS Service Layer (Container Services)

**GPU Compute Pool**:
- Instance type: `GPU_NV_S` (NVIDIA T4 16GB / A10 24GB)
- Auto-scaling: MIN_NODES=1, MAX_NODES=2
- Auto-suspend: Suspends after 600 seconds of inactivity

**Container Architecture**:
- **Snowflake Proxy (Port 8001)**: Handles Snowflake Service Function's special request format
- **vLLM / Transformers (Port 8000)**: High-performance LLM inference engine

#### 4. Model Download Layer (External Access)

Due to network restrictions, we configured two model download sources:

| Source | Domain | Priority | Description |
|--------|--------|----------|-------------|
| HF-Mirror | hf-mirror.com | ✅ Recommended | HuggingFace China mirror, fast |
| ModelScope | modelscope.cn | Backup | Alibaba Cloud model repository |

---

## 📋 Prerequisites

### Snowflake Environment Requirements

| Requirement | Description |
|-------------|-------------|
| **Snowflake Account** | Snowflake China region account |
| **Role Permissions** | ACCOUNTADMIN (to create compute pools and external access integrations) |
| **SPCS Feature** | Snowflake Container Services enabled on account |
| **GPU Quota** | Account has GPU compute pool quota |

### Local Development Environment

| Tool | Version | Purpose |
|------|---------|---------|
| **Docker** | 20.10+ | Build container images |
| **SnowSQL** | Latest | Execute SQL scripts |
| **Python** | 3.9+ | (Optional) Local testing |

### Network Requirements

Ensure SPCS service can access these domains:

```
# HF-Mirror (Recommended)
hf-mirror.com:443
cdn-lfs.hf-mirror.com:443

# ModelScope (Backup)
modelscope.cn:443
www.modelscope.cn:443
cdn-lfs-cn-1.modelscope.cn:443
cdn-lfs-cn-2.modelscope.cn:443
```

---

## 🚀 Quick Start

### One-Click Deploy Qwen Model

```bash
# Set environment variables
export SNOWFLAKE_ACCOUNT="your_account"
export SNOWFLAKE_USER="your_user"

# Run one-click deployment
./deploy.sh deploy

# Or execute step by step
./deploy.sh build    # Build image only
./deploy.sh push     # Build and push
./deploy.sh sql      # Execute SQL only
```

### One-Click Deploy DeepSeek Model

```bash
# Deploy DeepSeek using china_dev connection
./deploy_deepseek.sh deploy

# Other commands
./deploy_deepseek.sh status   # Check status
./deploy_deepseek.sh logs     # View logs
./deploy_deepseek.sh test     # Test service
./deploy_deepseek.sh cleanup  # Cleanup resources
```

> For detailed DeepSeek deployment instructions, see [DEPLOY_DEEPSEEK.md](./DEPLOY_DEEPSEEK.md)

### Manual Deployment Steps

See detailed steps in the [Implementation Process](#-implementation-process) section below.

---

## 🔧 Implementation Process

### Step Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                      Deployment Process                             │
│                                                                     │
│   Step 1          Step 2          Step 3          Step 4           │
│  ┌─────────┐    ┌─────────────┐  ┌───────────┐  ┌─────────────┐   │
│  │ Create  │    │ Configure   │  │ Build &   │  │ Create      │   │
│  │ Pool    │───▶│ Network     │─▶│ Push Image│─▶│ Service+UDF │   │
│  └─────────┘    └─────────────┘  └───────────┘  └─────────────┘   │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

### Step 1: Create Database and Compute Pool

```sql
-- Use ACCOUNTADMIN role
USE ROLE ACCOUNTADMIN;

-- Create database and schema
CREATE DATABASE IF NOT EXISTS SPCS_CHINA;
CREATE SCHEMA IF NOT EXISTS SPCS_CHINA.MODEL_SERVICE;

-- Create GPU compute pool
CREATE COMPUTE POOL IF NOT EXISTS GPU_NV_S_POOL
    MIN_NODES = 1
    MAX_NODES = 2
    INSTANCE_FAMILY = GPU_NV_S
    AUTO_RESUME = TRUE
    AUTO_SUSPEND_SECS = 600
    COMMENT = 'GPU compute pool for LLM inference service (China Region)';

-- Verify compute pool creation
SHOW COMPUTE POOLS;
DESC COMPUTE POOL GPU_NV_S_POOL;
```

### Step 2: Configure External Network Access

```sql
USE DATABASE SPCS_CHINA;
USE SCHEMA MODEL_SERVICE;

-- Create network rule: Allow access to model download sources
CREATE OR REPLACE NETWORK RULE modelscope_network_rule
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = (
        -- HF-Mirror (Recommended)
        'hf-mirror.com:443',
        'cdn-lfs.hf-mirror.com:443',
        -- ModelScope (Backup)
        'www.modelscope.cn:443',
        'modelscope.cn:443',
        'cdn-lfs-cn-1.modelscope.cn:443',
        'cdn-lfs-cn-2.modelscope.cn:443'
    )
    COMMENT = 'Network rule for model download';

-- Create external access integration
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION modelscope_access_integration
    ALLOWED_NETWORK_RULES = (modelscope_network_rule)
    ENABLED = TRUE
    COMMENT = 'External access for model download';
```

### Step 3: Create Image Repository and Push Docker Image

```sql
-- Create image repository
CREATE IMAGE REPOSITORY IF NOT EXISTS MODEL_SERVICE_REPO
    COMMENT = 'Image repository for SPCS model service';

-- Get repository URL
SHOW IMAGE REPOSITORIES LIKE 'MODEL_SERVICE_REPO';
-- Copy the full URL from the repository_url column
-- Example output: <org>-<account>.registry.snowflakecomputing.cn/spcs_china/model_service/model_service_repo
```

#### Login to Image Repository (Using PAT Token)

Since many enterprise accounts disable username/password login, we recommend using **Programmatic Access Token (PAT)** to login to the image repository.

**Step 1: Create PAT Token**

Execute the following SQL in Snowflake to create a PAT:

```sql
-- Create a PAT Token with 7-day validity (adjust days as needed)
ALTER USER ADD PROGRAMMATIC ACCESS TOKEN docker_registry_token
    DAYS_TO_EXPIRY = 7
    COMMENT = 'Token for Docker registry login';
```

After successful execution, the result will show `token_name` and `token_secret` columns. **Copy the Token value directly from the `token_secret` column**.

> **Important:**
> - `token_secret` is only displayed once at creation time - copy and save it immediately
> - To delete a Token: `ALTER USER REMOVE PROGRAMMATIC ACCESS TOKEN docker_registry_token;`
> - For more information, see [Snowflake PAT Documentation](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens)

**Step 2: Query Image Repository URL**

```bash
# Query using Snowflake CLI
snow sql -c <your_connection> -q "SHOW IMAGE REPOSITORIES;"

# Or execute in Snowflake Worksheet
# SHOW IMAGE REPOSITORIES LIKE 'MODEL_SERVICE_REPO';
```

Copy the `repository_url` column value from the result, e.g., `xxx-xxx.registry.snowflakecomputing.cn/spcs_china/model_service/model_service_repo`

**Step 3: Login to Docker Registry with PAT Token**

```bash
# Replace <PAT_TOKEN> with the Token from Step 1
# Replace <REGISTRY_HOST> with the domain part of repository_url
# Replace <YOUR_USERNAME> with your Snowflake username

echo "<PAT_TOKEN>" | docker login <REGISTRY_HOST> -u <YOUR_USERNAME> --password-stdin
```

**Example:**

```bash
echo "eyJraWQiOiIz..." | docker login xxx-xxx.registry.snowflakecomputing.cn -u MY_USER --password-stdin
```

> **Notes:**
> - Username is your **Snowflake username** (the user who created the PAT)
> - Password is the **PAT Token** (not your Snowflake login password)
> - The user/role must have `READ, WRITE ON IMAGE REPOSITORY` privileges

#### Build and Push Image

After completing `docker login`, execute the following steps:

```bash
# Set environment variable (copy repository_url from SHOW IMAGE REPOSITORIES result)
export REGISTRY_URL="<org>-<account>.registry.snowflakecomputing.cn/spcs_china/model_service/model_service_repo"

# 1. Build Docker image
cd spcs_china/model_service
docker build -t qwen-service:latest .

# 2. Tag and push image
docker tag qwen-service:latest ${REGISTRY_URL}/qwen-service:latest
docker push ${REGISTRY_URL}/qwen-service:latest

# 3. Verify upload
snow sql -c <your_connection> -q "SHOW IMAGES IN IMAGE REPOSITORY SPCS_CHINA.MODEL_SERVICE.MODEL_SERVICE_REPO;"
```

### Step 4: Create SPCS Service

```sql
USE DATABASE SPCS_CHINA;
USE SCHEMA MODEL_SERVICE;

-- Create service
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
        port: 8001
        path: /health
  endpoints:
    - name: qwen-api
      port: 8001
      public: false
$$;

-- Check service status
SELECT SYSTEM$GET_SERVICE_STATUS('QWEN_MODEL_SERVICE');

-- View service logs (monitor model download progress)
SELECT SYSTEM$GET_SERVICE_LOGS('QWEN_MODEL_SERVICE', 0, 'qwen-service', 50);
```

### Step 5: Create UDF and Test

```sql
-- Create Service Function UDF
CREATE OR REPLACE FUNCTION QWEN_COMPLETE(prompt VARCHAR)
RETURNS VARCHAR
SERVICE = QWEN_MODEL_SERVICE
ENDPOINT = 'qwen-api'
MAX_BATCH_ROWS = 1
AS '/v1/chat/completions';

-- Grant to other roles
GRANT USAGE ON FUNCTION QWEN_COMPLETE(VARCHAR) TO ROLE PUBLIC;

-- Test call
SELECT SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE(
  '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[{"role":"user","content":"Introduce Snowflake Data Cloud"}]}'
) AS response;
```

---

## 📊 Usage Examples

### Qwen Model Usage

```sql
-- Simple Q&A
SELECT SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE(
  '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[{"role":"user","content":"What is a data warehouse?"}]}'
);

-- With system prompt
SELECT SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE(
  '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[
    {"role":"system","content":"You are a data analytics expert"},
    {"role":"user","content":"How to optimize SQL query performance?"}
  ]}'
);
```

### DeepSeek Model Usage

```sql
-- DeepSeek-R1 Q&A (with reasoning chain)
SELECT SPCS_CHINA.MODEL_SERVICE.DEEPSEEK_COMPLETE(
  '{"model":"deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B","messages":[{"role":"user","content":"Explain what is machine learning"}]}'
);

-- DeepSeek code generation
SELECT SPCS_CHINA.MODEL_SERVICE.DEEPSEEK_COMPLETE(
  '{"model":"deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B","messages":[
    {"role":"system","content":"You are a programming expert"},
    {"role":"user","content":"Write a quick sort algorithm in Python"}
  ]}'
);
```

### Batch Processing

```sql
-- Batch generate product descriptions
SELECT 
    product_id,
    product_name,
    QWEN_COMPLETE(
      '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[
        {"role":"system","content":"Generate a short marketing description for the following product"},
        {"role":"user","content":"' || product_name || '"}
      ]}'
    ) AS ai_description
FROM products
LIMIT 10;
```

### Using in Streamlit

We provide a complete Streamlit example application `streamlit_example.py`, including:

- 💬 Interactive chat interface (supports Qwen and DeepSeek model switching)
- 📝 Batch text processing
- 🔧 SQL call examples and testing tools
- ⚙️ Configurable parameters (Temperature, Max Tokens, etc.)
- 🎛️ **Service Management Panel**: Start/Stop/View status
- 💰 Cost Control: One-click pause GPU services to save costs

**Quick Example Code:**

```python
import streamlit as st
import json
from snowflake.snowpark.context import get_active_session

# UDF path
QWEN_UDF_PATH = "SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE"

def call_qwen_complete(session, prompt: str, system_prompt: str = None) -> str:
    """Call QWEN_COMPLETE UDF"""
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

# Streamlit app
session = get_active_session()
st.title("🤖 Qwen AI Assistant (China Region)")

user_input = st.chat_input("Enter your question...")
if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = call_qwen_complete(session, user_input)
            st.markdown(response)
```

---

## 💰 Cost & Performance

### Cost Estimation

| Component | Spec | Estimated Cost (Reference) |
|-----------|------|---------------------------|
| GPU Compute Pool | GPU_NV_S (T4 16GB) | ~$2-3/hour |
| Storage | Image + Stage | < $1/month |
| Network | Internal | Included |

**Cost Optimization Tips**:
- Set `AUTO_SUSPEND_SECS = 600` for auto-suspend
- Manually suspend during non-working hours: `ALTER SERVICE QWEN_MODEL_SERVICE SUSPEND;`

### Performance Reference

| Metric | Qwen2.5-1.5B | Notes |
|--------|--------------|-------|
| First startup | 3-5 minutes | Including model download |
| Cold start | 60-90 seconds | Model cached |
| Inference latency | 1-3 seconds | 100 tokens output |
| Throughput | ~50 tokens/s | Single request |

---

## 🔧 Operations & Management

### Service Monitoring

```sql
-- Check service status
SELECT SYSTEM$GET_SERVICE_STATUS('QWEN_MODEL_SERVICE');

-- View service logs
SELECT SYSTEM$GET_SERVICE_LOGS('QWEN_MODEL_SERVICE', 0, 'qwen-service', 100);

-- Check compute pool status
DESC COMPUTE POOL GPU_NV_S_POOL;
```

### Common Management Commands

```sql
-- Suspend service (save cost)
ALTER SERVICE QWEN_MODEL_SERVICE SUSPEND;

-- Resume service
ALTER SERVICE QWEN_MODEL_SERVICE RESUME;

-- Restart service
ALTER SERVICE QWEN_MODEL_SERVICE RESTART;

-- Redeploy after image update
ALTER SERVICE QWEN_MODEL_SERVICE 
    FROM SPECIFICATION $$ ... $$;
```

### Troubleshooting

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| Service startup timeout | Slow model download | Check network rules, verify HF-Mirror accessibility |
| GPU unavailable | Insufficient compute pool quota | Contact Snowflake support for quota increase |
| Inference error | Out of memory | Increase container memory limit or use smaller model |

---

## 📝 Summary

### Solution Advantages

✅ **Data Stays In-Region**: Model runs entirely within Snowflake China region, meeting compliance requirements

✅ **Seamless Integration**: Provides Cortex LLM-like experience via UDF

✅ **Flexible Extension**: Can switch to other open-source models (Qwen-7B, ChatGLM, etc.)

✅ **Cost Control**: Supports auto-suspend, pay-as-you-go

✅ **One-Click Deployment**: Automated scripts simplify implementation

### Use Cases

- China region customers need AI capabilities within Snowflake
- Strict data security requirements, data must stay within the platform
- Need integration with existing Snowflake workflows (SQL, Streamlit)
- Transitional solution while waiting for Cortex LLM China region launch

### Future Evolution

When Snowflake Cortex LLM officially launches in China region, users can:
1. Gradually migrate to official Cortex LLM service
2. Keep SPCS solution for specific scenarios (custom models, private deployment)
3. Use both solutions in hybrid mode to meet different needs

---

## 📚 References

- [Snowflake Container Services Documentation](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)
- [Qwen2.5 Model Introduction](https://github.com/QwenLM/Qwen2.5)
- [vLLM High-Performance Inference Framework](https://github.com/vllm-project/vllm)
- [HF-Mirror China Mirror](https://hf-mirror.com/)

---

## 📄 License

MIT License

---

*This project is maintained by Snowflake China team. Please contact technical support for any questions.*
