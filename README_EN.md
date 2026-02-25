# Snowflake China Intelligence

[中文版](./README.md) | English Version

> **Snowflake China Intelligence** is a comprehensive AI-powered analytics solution designed for Snowflake China Region. It provides enterprise-grade data intelligence capabilities as a transitional solution before Cortex AI services become available in the region.

---

## 📁 Project Structure

```
snowflake-china-intelligence/
├── README.md                      # Documentation (Chinese)
├── README_EN.md                   # Documentation (English)
│
├── semantic_model_generator/      # 📊 Semantic Model Generator (Core Engine)
│   ├── data_processing/           # Data processing and transformation
│   ├── protos/                    # Protocol Buffers definitions
│   ├── snowflake_utils/           # Snowflake connection & LLM utilities
│   └── validate/                  # Model validation logic
│
├── agent_intelligence/            # 🤖 Agent Intelligence (Analytics Assistant)
│   ├── cortex_agent_sis_v2.py     # Main application (Streamlit in Snowflake)
│   ├── environment.yml            # SiS dependencies
│   ├── setup_qwen_udf.sql         # External API UDF deployment script
│   └── README.md                  # Module documentation
│
├── spcs_china/                    # 🔒 Private LLM Service (SPCS)
│   ├── model_service/             # Container service code
│   │   ├── Dockerfile             # Image build file
│   │   ├── proxy.py               # Service Function proxy
│   │   └── spec.yaml              # SPCS service specification
│   ├── setup_sql/                 # SQL setup scripts
│   ├── deploy.sh                  # One-click deployment script
│   └── README.md                  # Detailed documentation
│
├── app.py                         # Semantic Model Generator Streamlit app
├── sis_setup/                     # Streamlit in Snowflake deployment scripts
├── journeys/                      # User workflow modules
├── partner/                       # Partner integrations (dbt, Looker)
└── app_utils/                     # Shared utilities
```

---

## 🏗️ Architecture

### System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                      │
│                        ╔═══════════════════════════════════════╗                     │
│                        ║     SNOWFLAKE CHINA INTELLIGENCE      ║                     │
│                        ║     AI-Powered Analytics Platform      ║                     │
│                        ╚═══════════════════════════════════════╝                     │
│                                          │                                           │
│              ┌───────────────────────────┼───────────────────────────┐              │
│              │                           │                           │              │
│              ▼                           ▼                           ▼              │
│   ┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐      │
│   │  📊 Semantic Model   │   │  🤖 Agent            │   │  🔒 Private LLM     │      │
│   │     Generator        │   │     Intelligence     │   │     Service (SPCS)  │      │
│   ├─────────────────────┤   ├─────────────────────┤   ├─────────────────────┤      │
│   │ • Auto-generate     │   │ • Natural language  │   │ • Data stays in     │      │
│   │   semantic models   │   │   to SQL            │   │   platform          │      │
│   │ • dbt/Looker import │   │ • Smart insights    │   │ • GPU-accelerated   │      │
│   │ • AI descriptions   │   │ • Multi-turn chat   │   │ • Open-source models│      │
│   │ • Model validation  │   │ • Visualizations    │   │ • Cost-effective    │      │
│   └─────────┬───────────┘   └──────────┬──────────┘   └──────────┬──────────┘      │
│             │                          │                          │                 │
│             └──────────────────────────┼──────────────────────────┘                 │
│                                        │                                            │
│                                        ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │                              LLM Service Layer                               │  │
│   │  ┌─────────────────────────────┐    ┌─────────────────────────────────────┐ │  │
│   │  │    Option A: External API   │    │      Option B: SPCS Private         │ │  │
│   │  │  ┌─────────────────────────┐│    │  ┌───────────────────────────────┐  │ │  │
│   │  │  │   QWEN_COMPLETE UDF     ││    │  │    QWEN_COMPLETE UDF          │  │ │  │
│   │  │  │   (External Access)     ││    │  │    (Service Function)         │  │ │  │
│   │  │  └────────────┬────────────┘│    │  └───────────────┬───────────────┘  │ │  │
│   │  │               │             │    │                  │                  │ │  │
│   │  │               ▼             │    │                  ▼                  │ │  │
│   │  │  ┌─────────────────────────┐│    │  ┌───────────────────────────────┐  │ │  │
│   │  │  │    External LLM APIs    ││    │  │      SPCS Container           │  │ │  │
│   │  │  │  • DashScope (Qwen)     ││    │  │  ┌─────────┐  ┌─────────────┐ │  │ │  │
│   │  │  │  • DeepSeek             ││    │  │  │ Proxy   │─▶│ Qwen Model  │ │  │ │  │
│   │  │  │  • Moonshot (Kimi)      ││    │  │  │ :8001   │  │ vLLM :8000  │ │  │ │  │
│   │  │  └─────────────────────────┘│    │  │  └─────────┘  └─────────────┘ │  │ │  │
│   │  │                             │    │  │         GPU Compute Pool       │  │ │  │
│   │  │  ✓ Quick integration       │    │  │                               │  │ │  │
│   │  │  ✓ No GPU required         │    │  │  ✓ Data compliance           │  │ │  │
│   │  │  ✓ Pay-per-call            │    │  │  ✓ Fully private             │  │ │  │
│   │  └─────────────────────────────┘    │  └───────────────────────────────┘  │ │  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│                                  Snowflake China Region                              │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              User Interaction Layer                                  │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────────────┐   │
│  │ 🖥️ Streamlit App   │  │ 📝 SQL Worksheet  │  │ 📊 BI Tools (Tableau, etc.)   │   │
│  └─────────┬─────────┘  └─────────┬─────────┘  └───────────────┬───────────────┘   │
└────────────┼──────────────────────┼────────────────────────────┼────────────────────┘
             │                      │                            │
             ▼                      ▼                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Semantic Model Layer                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                        Semantic Model (YAML)                                 │   │
│  │  • Tables                    • Dimensions                                    │   │
│  │  • Measures                  • Time Dimensions                               │   │
│  │  • Joins                     • Synonyms                                      │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Intelligence Layer                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  Agent Intelligence: Natural Language → Semantic Understanding → SQL        │   │
│  │                      Generation → Result Analysis → Insight Output          │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Data Storage Layer                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │                     Snowflake Tables / Views / Stages                         │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Core Components

### 1. 📊 Semantic Model Generator

| Feature | Description |
|---------|-------------|
| **Auto-Generation** | Automatically generate Cortex Analyst semantic models from Snowflake tables/views |
| **Partner Import** | Import existing models from dbt Semantic Model or Looker Explore |
| **AI-Enhanced Descriptions** | Use LLM to auto-generate field descriptions and synonyms |
| **Model Validation** | Validate semantic models against Cortex Analyst specifications |
| **API Support** | Automate batch generation via stored procedures |

### 2. 🤖 Agent Intelligence

| Feature | Description |
|---------|-------------|
| **Natural Language Queries** | Describe data requirements in natural language (Chinese/English) |
| **Smart SQL Generation** | Automatically generate accurate SQL based on semantic models |
| **Data Insights** | Automatically analyze query results and provide insights |
| **Visualizations** | Generate appropriate data visualizations automatically |
| **Multi-turn Conversations** | Support contextual multi-turn data analysis conversations |

### 3. 🔒 Private LLM Service (SPCS)

| Advantage | Description |
|-----------|-------------|
| **Data Compliance** | Model runs within Snowflake platform, data never leaves the platform |
| **Full Control** | Choose and deploy open-source models (Qwen, ChatGLM, etc.) |
| **GPU Acceleration** | Leverage SPCS GPU compute pools for efficient inference |
| **Cost Optimization** | Support auto-suspend for on-demand usage |

---

## 📌 Solution Comparison

| Feature | External API | SPCS Private |
|---------|-------------|--------------|
| **Data Compliance** | ⚠️ Data sent to external API | ✅ Data stays in platform |
| **Cost Model** | Pay-per-call | GPU hourly billing |
| **Network Dependency** | Requires external access | No external dependency |
| **Model Selection** | Limited to API provider | Deploy any open-source model |
| **Use Cases** | Quick integration, prototyping | Production, high compliance |

### Supported LLM Providers (External API)

| Provider | Models | Features |
|----------|--------|----------|
| **DashScope (Qwen)** | qwen-max, qwen-plus, qwen-turbo | Alibaba Cloud official, stable & reliable |
| **DeepSeek** | deepseek-chat, deepseek-reasoner | Cost-effective, strong reasoning |
| **Moonshot (Kimi)** | moonshot-v1-8k/32k/128k | Excellent long-context handling |

---

## 📋 Prerequisites

### Snowflake Environment

| Requirement | Description |
|-------------|-------------|
| **Snowflake Account** | Snowflake China region account |
| **Role Permissions** | ACCOUNTADMIN (for creating external access integrations, compute pools) |
| **SPCS Feature** | (Optional) Enable SPCS for private deployment |
| **GPU Quota** | (Optional) GPU quota for private deployment |

### External API Keys

| Provider | How to Obtain |
|----------|---------------|
| DashScope | [Alibaba Cloud DashScope Console](https://dashscope.console.aliyun.com/) |
| DeepSeek | [DeepSeek Platform](https://platform.deepseek.com/) |
| Moonshot | [Moonshot Platform](https://platform.moonshot.cn/) |

### Local Development Environment

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.9 - 3.11 | Local development and testing |
| **Snow CLI** | Latest | Deploy applications |
| **Docker** | 20.10+ | (Optional) SPCS image building |

---

## 🚀 Quick Start

### Option 1: Deploy Semantic Model Generator

```bash
# 1. Clone the repository
git clone https://github.com/yuhenghub/snowflake-china-intelligence.git
cd snowflake-china-intelligence

# 2. Deploy to Streamlit in Snowflake
snow sql -f sis_setup/app_setup.sql --connection your_connection

# 3. Open the application
snow streamlit get-url SEMANTIC_MODEL_GENERATOR --open \
    --database cortex_analyst_semantics \
    --schema semantic_model_generator \
    --connection your_connection
```

### Option 2: Deploy Agent Intelligence (External API)

```sql
-- 1. Configure API Key (edit agent_intelligence/setup_qwen_udf.sql)
-- 2. Execute UDF deployment script

-- 3. Create Stage and upload application
CREATE STAGE YOUR_DB.YOUR_SCHEMA.AGENT_STAGE DIRECTORY = (ENABLE = true);

PUT file://agent_intelligence/cortex_agent_sis_v2.py @YOUR_DB.YOUR_SCHEMA.AGENT_STAGE/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;
PUT file://agent_intelligence/environment.yml @YOUR_DB.YOUR_SCHEMA.AGENT_STAGE/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;

-- 4. Create Streamlit application
CREATE STREAMLIT YOUR_DB.YOUR_SCHEMA.CHINA_INTELLIGENCE
    ROOT_LOCATION = '@YOUR_DB.YOUR_SCHEMA.AGENT_STAGE'
    MAIN_FILE = 'cortex_agent_sis_v2.py'
    TITLE = "Snowflake China Intelligence"
    QUERY_WAREHOUSE = YOUR_WAREHOUSE
    EXTERNAL_ACCESS_INTEGRATIONS = (qwen_api_integration);
```

### Option 3: Deploy Private LLM (SPCS)

For detailed instructions, see [spcs_china/README_EN.md](./spcs_china/README_EN.md)

```bash
cd spcs_china
./deploy.sh deploy
```

---

## 📊 Usage Examples

### Basic LLM Calls

```sql
-- Simple Q&A
SELECT QWEN_COMPLETE('qwen-turbo', 'What is a data warehouse?');

-- With system prompt
SELECT QWEN_COMPLETE('qwen-max', 
  'You are a data analytics expert. Analyze this trend: ' || 
  (SELECT LISTAGG(category || ': ' || total_sales, ', ') FROM sales_summary)
);
```

### Batch Processing

```sql
-- Batch generate product descriptions
SELECT 
    product_id,
    product_name,
    QWEN_COMPLETE('qwen-turbo', 
      'Generate a one-line marketing copy for: ' || product_name
    ) AS ai_description
FROM products
LIMIT 10;
```

### Semantic Model Example

```yaml
name: Sales Analytics
description: Enterprise sales semantic model for trend and regional analysis

tables:
  - name: sales_data
    description: Daily sales transaction data
    base_table:
      database: ANALYTICS
      schema: SALES
      table: DAILY_SALES

    dimensions:
      - name: product_category
        synonyms: ["category", "product type"]
        description: Category of the sold product
        expr: CATEGORY
        data_type: TEXT

      - name: region
        synonyms: ["area", "sales region"]
        description: Geographic region where sale occurred
        expr: REGION
        data_type: TEXT

    time_dimensions:
      - name: sale_date
        synonyms: ["date", "transaction date"]
        description: Date of the sale
        expr: SALE_DATE
        data_type: DATE

    measures:
      - name: sales_amount
        synonyms: ["revenue", "sales total"]
        description: Total sales amount
        expr: AMOUNT
        data_type: NUMBER
        default_aggregation: sum

      - name: order_count
        synonyms: ["orders", "transaction count"]
        description: Total number of orders
        expr: ORDER_ID
        data_type: NUMBER
        default_aggregation: count_distinct
```

---

## 💰 Cost Reference

### External API Pricing

| Provider | Model | Price (Reference) |
|----------|-------|-------------------|
| DashScope | qwen-turbo | ¥0.008/1K tokens |
| DashScope | qwen-max | ¥0.04/1K tokens |
| DeepSeek | deepseek-chat | ¥0.001/1K tokens |

### SPCS Private Deployment

| Component | Specification | Estimated Cost |
|-----------|---------------|----------------|
| GPU Compute Pool | GPU_NV_S (T4 16GB) | ~$2-3/hour |
| Storage | Image + Stage | < $1/month |

**Cost Optimization Tips:**
- Set `AUTO_SUSPEND_SECS = 600` for auto-suspend
- Manually suspend during off-hours: `ALTER SERVICE QWEN_MODEL_SERVICE SUSPEND;`

---

## 🔧 Operations & Management

### Common Commands

```sql
-- Check UDF status
SHOW FUNCTIONS LIKE 'QWEN_COMPLETE';

-- Test UDF
SELECT QWEN_COMPLETE('qwen-turbo', 'Hello');

-- SPCS service status
SELECT SYSTEM$GET_SERVICE_STATUS('QWEN_MODEL_SERVICE');

-- Suspend/Resume SPCS service
ALTER SERVICE QWEN_MODEL_SERVICE SUSPEND;
ALTER SERVICE QWEN_MODEL_SERVICE RESUME;
```

### Troubleshooting

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| UDF call fails | Invalid API Key | Check Secret configuration |
| External access fails | Network rule not configured | Check External Access Integration |
| SPCS startup timeout | Slow model download | Check network rules, verify HF-Mirror accessibility |
| GPU unavailable | Insufficient quota | Contact Snowflake support for quota increase |

---

## 📝 Summary

### Solution Advantages

✅ **Cortex AI Alternative** - Complete transitional solution before Cortex AI launches in China region

✅ **Flexible Deployment** - Choose between external APIs or SPCS private deployment

✅ **Data Compliance** - SPCS ensures data never leaves the platform

✅ **Seamless Integration** - Perfect integration with Snowflake SQL and Streamlit

✅ **Multi-Model Support** - Support for multiple mainstream LLM providers and open-source models

### Use Cases

- China region customers needing AI analytics capabilities within Snowflake
- Natural language data querying and analysis based on semantic models
- Strict data security requirements where data must stay within the platform
- Transitional solution while waiting for Cortex AI China region launch

### Future Evolution

When Snowflake Cortex AI officially launches in China region:
1. Gradually migrate to official Cortex AI services
2. Retain SPCS solution for specific scenarios (custom models, private deployment)
3. Semantic models can be directly reused with Cortex Analyst

---

## 📚 References

- [Snowflake Cortex Analyst Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Snowflake Container Services Documentation](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)
- [DashScope API Documentation](https://help.aliyun.com/zh/dashscope/)
- [Qwen2.5 Model](https://github.com/QwenLM/Qwen2.5)
- [vLLM Inference Framework](https://github.com/vllm-project/vllm)

---

## 📄 License

Apache 2.0 License

---

## 🤝 Contributing

Contributions and suggestions are welcome! This project is adapted from [Snowflake-Labs/semantic-model-generator](https://github.com/Snowflake-Labs/semantic-model-generator) for China region.
