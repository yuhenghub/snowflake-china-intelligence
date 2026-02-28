# Snowflake China Intelligence

[English Version](./README_EN.md) | 中文版

> **Snowflake China Intelligence** 是一套为 Snowflake 中国区打造的完整 AI 智能分析解决方案，在 Cortex AI 服务上线前，为企业提供数据驱动的智能分析能力。

---

## 📁 项目结构

```
snowflake-china-intelligence/
├── README.md                      # 项目总览文档
│
├── semantic_model_generator/      # 📊 语义模型生成器 (核心引擎)
│   ├── data_processing/           # 数据处理与转换
│   ├── protos/                    # Protocol Buffers 定义
│   ├── snowflake_utils/           # Snowflake 连接与 LLM 工具
│   └── validate/                  # 模型验证逻辑
│
├── agent_intelligence/            # 🤖 智能分析助手
│   ├── cortex_agent_sis_v2.py     # 主应用 (Streamlit in Snowflake)
│   ├── environment.yml            # SiS 依赖配置
│   ├── setup_qwen_udf.sql         # 外部 API UDF 部署脚本
│   └── README.md                  # 模块说明
│
├── spcs_china/                    # 🔒 私有化 LLM 服务 (SPCS)
│   ├── model_service/             # 容器服务代码
│   │   ├── Dockerfile             # 镜像构建文件
│   │   ├── proxy.py               # Service Function 代理
│   │   └── spec.yaml              # SPCS 服务规格
│   ├── setup_sql/                 # SQL 设置脚本
│   ├── deploy.sh                  # 一键部署脚本
│   └── README.md                  # 详细文档
│
├── app.py                         # 语义模型生成器 Streamlit 主应用
├── sis_setup/                     # Streamlit in Snowflake 部署脚本
├── journeys/                      # 用户工作流模块
├── partner/                       # 合作伙伴集成 (dbt, Looker)
└── app_utils/                     # 共享工具库
```

---

## 🏗️ 整体架构

### Snowflake China Intelligence 架构图

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                      │
│                        ╔═══════════════════════════════════════╗                     │
│                        ║   SNOWFLAKE CHINA INTELLIGENCE        ║                     │
│                        ║   Snowflake 中国区 AI 智能分析平台       ║                     │
│                        ╚═══════════════════════════════════════╝                     │
│                                          │                                           │
│              ┌───────────────────────────┼───────────────────────────┐              │
│              │                           │                           │              │
│              ▼                           ▼                           ▼              │
│   ┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐      │
│   │  📊 语义模型生成器     │   │  🤖 智能分析助手       │   │  🔒 私有化 LLM 服务   │      │
│   │  Semantic Model     │   │  Agent Intelligence  │   │  SPCS Self-Hosted   │      │
│   │  Generator          │   │                      │   │  LLM                │      │
│   ├─────────────────────┤   ├─────────────────────┤   ├─────────────────────┤      │
│   │ • 自动生成语义模型    │   │ • 自然语言转 SQL      │   │ • 数据不出平台        │      │
│   │ • dbt/Looker 导入   │   │ • 智能数据洞察        │   │ • GPU 加速推理       │      │
│   │ • AI 增强描述       │   │ • 多轮对话分析        │   │ • 开源模型部署       │      │
│   │ • 模型验证          │   │ • 可视化图表         │   │ • 成本可控          │      │
│   └─────────┬───────────┘   └──────────┬──────────┘   └──────────┬──────────┘      │
│             │                          │                          │                 │
│             └──────────────────────────┼──────────────────────────┘                 │
│                                        │                                            │
│                                        ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │                              LLM 服务层                                       │  │
│   │  ┌─────────────────────────────┐    ┌─────────────────────────────────────┐ │  │
│   │  │      方案 A: 外部 API        │    │        方案 B: SPCS 私有化           │ │  │
│   │  │  ┌─────────────────────────┐│    │  ┌───────────────────────────────┐  │ │  │
│   │  │  │   QWEN_COMPLETE UDF     ││    │  │    QWEN_COMPLETE UDF          │  │ │  │
│   │  │  │   (External Access)     ││    │  │    (Service Function)         │  │ │  │
│   │  │  └────────────┬────────────┘│    │  └───────────────┬───────────────┘  │ │  │
│   │  │               │             │    │                  │                  │ │  │
│   │  │               ▼             │    │                  ▼                  │ │  │
│   │  │  ┌─────────────────────────┐│    │  ┌───────────────────────────────┐  │ │  │
│   │  │  │    外部 LLM API          ││    │  │      SPCS Container           │  │ │  │
│   │  │  │  • DashScope (Qwen)     ││    │  │  ┌─────────┐  ┌─────────────┐ │  │ │  │
│   │  │  │  • DeepSeek             ││    │  │  │ Proxy   │─▶│ Qwen Model  │ │  │ │  │
│   │  │  │  • Moonshot (Kimi)      ││    │  │  │ :8001   │  │ vLLM :8000  │ │  │ │  │
│   │  │  └─────────────────────────┘│    │  │  └─────────┘  └─────────────┘ │  │ │  │
│   │  │                             │    │  │         GPU Compute Pool       │  │ │  │
│   │  │  ✓ 快速集成                  │    │  │                               │  │ │  │
│   │  │  ✓ 无需 GPU                 │    │  │  ✓ 数据合规                    │  │ │  │
│   │  │  ✓ 按调用付费               │    │  │  ✓ 完全私有                    │  │ │  │
│   │  └─────────────────────────────┘    │  └───────────────────────────────┘  │ │  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│                                  Snowflake China Region                              │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### 数据流架构

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              用户交互层                                               │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────────────┐   │
│  │ 🖥️ Streamlit App   │  │ 📝 SQL Worksheet  │  │ 📊 BI Tools (Tableau, etc.)   │   │
│  └─────────┬─────────┘  └─────────┬─────────┘  └───────────────┬───────────────┘   │
└────────────┼──────────────────────┼────────────────────────────┼────────────────────┘
             │                      │                            │
             ▼                      ▼                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              语义模型层                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                        Semantic Model (YAML)                                 │   │
│  │  • 表定义 (Tables)           • 维度 (Dimensions)                              │   │
│  │  • 度量 (Measures)           • 时间维度 (Time Dimensions)                     │   │
│  │  • 关系 (Joins)              • 同义词 (Synonyms)                              │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              智能分析层                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  Agent Intelligence: 自然语言 → 语义理解 → SQL 生成 → 结果分析 → 洞察输出       │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              数据存储层                                               │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │                     Snowflake Tables / Views / Stages                         │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ 核心功能

### 1. 📊 语义模型生成器 (Semantic Model Generator)

| 功能 | 说明 |
|-----|------|
| **自动生成** | 从 Snowflake 表/视图自动生成 Cortex Analyst 语义模型 |
| **合作伙伴导入** | 从 dbt Semantic Model 或 Looker Explore 导入已有模型 |
| **AI 增强描述** | 使用 LLM 自动生成字段描述和同义词 |
| **模型验证** | 验证语义模型是否符合 Cortex Analyst 规范 |
| **API 调用** | 通过存储过程支持自动化批量生成 |

### 2. 🤖 智能分析助手 (Agent Intelligence)

| 功能 | 说明 |
|-----|------|
| **自然语言查询** | 用中文/英文自然语言描述数据需求 |
| **智能 SQL 生成** | 基于语义模型自动生成准确的 SQL |
| **数据洞察** | 自动分析查询结果，提供数据洞察 |
| **可视化图表** | 自动生成适合的数据可视化图表 |
| **多轮对话** | 支持上下文关联的多轮数据分析对话 |

### 3. 🔒 私有化 LLM 服务 (SPCS Self-Hosted)

| 优势 | 说明 |
|-----|------|
| **数据合规** | 模型运行在 Snowflake 平台内，数据不出数据平台 |
| **完全可控** | 自主选择和部署开源模型 (Qwen, ChatGLM 等) |
| **GPU 加速** | 利用 SPCS GPU 计算池实现高效推理 |
| **成本优化** | 支持自动暂停，按需使用 |

---

## 📌 方案对比

| 特性 | 外部 API 方案 | SPCS 私有化方案 |
|-----|-------------|----------------|
| **数据合规** | ⚠️ 数据传输到外部 API | ✅ 数据不出数据平台 |
| **成本模式** | 按调用付费 | GPU 按时计费 |
| **网络依赖** | 需要外部网络访问 | 无外部依赖 |
| **模型选择** | 取决于 API 提供商 | 可部署任意开源模型 |
| **适用场景** | 快速集成、原型验证 | 生产环境、合规要求高 |

### 支持的 LLM 提供商 (外部 API)

| 提供商 | 模型 | 特点 |
|-------|------|------|
| **DashScope (通义千问)** | qwen-max, qwen-plus, qwen-turbo | 阿里云官方，稳定可靠 |
| **DeepSeek** | deepseek-chat, deepseek-reasoner | 性价比高，推理能力强 |
| **Moonshot (Kimi)** | moonshot-v1-8k/32k/128k | 长文本处理能力强 |

---

## 📋 先决条件

### Snowflake 环境

| 要求 | 说明 |
|-----|------|
| **Snowflake 账户** | Snowflake 中国区账户 |
| **角色权限** | ACCOUNTADMIN（创建外部访问集成、计算池）|
| **SPCS 功能** | (可选) 私有化部署需启用 SPCS |
| **GPU 配额** | (可选) 私有化部署需有 GPU 配额 |

### 外部 API 密钥

| 提供商 | 获取方式 |
|-------|---------|
| DashScope | [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/) |
| DeepSeek | [DeepSeek 开放平台](https://platform.deepseek.com/) |
| Moonshot | [Moonshot 开放平台](https://platform.moonshot.cn/) |

### 本地开发环境

| 工具 | 版本要求 | 用途 |
|-----|---------|------|
| **Python** | 3.9 - 3.11 | 本地开发测试 |
| **Snow CLI** | 最新版 | 部署应用 |
| **Docker** | 20.10+ | (可选) SPCS 镜像构建 |

---

## 🚀 快速开始

### 方案一: 部署语义模型生成器

```bash
# 1. 克隆项目
git clone https://github.com/your-org/snowflake-china-intelligence.git
cd snowflake-china-intelligence

# 2. 部署到 Streamlit in Snowflake
snow sql -f sis_setup/app_setup.sql --connection your_connection

# 3. 打开应用
snow streamlit get-url SEMANTIC_MODEL_GENERATOR --open \
    --database cortex_analyst_semantics \
    --schema semantic_model_generator \
    --connection your_connection
```

### 方案二: 部署智能分析助手 (外部 API)

```sql
-- 1. 配置 API Key (修改 agent_intelligence/setup_qwen_udf.sql)
-- 2. 执行 UDF 部署脚本

-- 3. 创建 Stage 并上传应用
CREATE STAGE YOUR_DB.YOUR_SCHEMA.AGENT_STAGE DIRECTORY = (ENABLE = true);

PUT file://agent_intelligence/cortex_agent_sis_v2.py @YOUR_DB.YOUR_SCHEMA.AGENT_STAGE/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;
PUT file://agent_intelligence/environment.yml @YOUR_DB.YOUR_SCHEMA.AGENT_STAGE/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;

-- 4. 创建 Streamlit 应用
CREATE STREAMLIT YOUR_DB.YOUR_SCHEMA.CHINA_INTELLIGENCE
    ROOT_LOCATION = '@YOUR_DB.YOUR_SCHEMA.AGENT_STAGE'
    MAIN_FILE = 'cortex_agent_sis_v2.py'
    TITLE = "Snowflake China Intelligence"
    QUERY_WAREHOUSE = YOUR_WAREHOUSE
    EXTERNAL_ACCESS_INTEGRATIONS = (qwen_api_integration);
```

### 方案三: 部署私有化 LLM (SPCS)

详细说明请参考 [spcs_china/README.md](./spcs_china/README.md)

```bash
cd spcs_china
./deploy.sh deploy
```

---

## 📊 使用示例

### 基础 LLM 调用

```sql
-- 简单问答
SELECT QWEN_COMPLETE('qwen-turbo', '什么是数据仓库？');

-- 带系统提示
SELECT QWEN_COMPLETE('qwen-max', 
  '你是一个数据分析专家。请分析以下数据趋势: ' || 
  (SELECT LISTAGG(category || ': ' || total_sales, ', ') FROM sales_summary)
);
```

### 批量智能处理

```sql
-- 批量生成产品描述
SELECT 
    product_id,
    product_name,
    QWEN_COMPLETE('qwen-turbo', 
      '为以下产品生成一句营销文案: ' || product_name
    ) AS ai_description
FROM products
LIMIT 10;
```

### 语义模型示例

```yaml
name: 销售数据分析
description: 企业销售数据语义模型，支持销售趋势、区域分析等场景

tables:
  - name: sales_data
    description: 每日销售明细数据
    base_table:
      database: ANALYTICS
      schema: SALES
      table: DAILY_SALES

    dimensions:
      - name: product_category
        synonyms: ["产品类别", "商品分类", "品类"]
        description: 销售产品的类别
        expr: CATEGORY
        data_type: TEXT

      - name: region
        synonyms: ["区域", "地区", "销售区域"]
        description: 销售发生的地理区域
        expr: REGION
        data_type: TEXT

    time_dimensions:
      - name: sale_date
        synonyms: ["销售日期", "日期"]
        description: 销售发生的日期
        expr: SALE_DATE
        data_type: DATE

    measures:
      - name: sales_amount
        synonyms: ["销售额", "营收", "销售金额"]
        description: 总销售金额
        expr: AMOUNT
        data_type: NUMBER
        default_aggregation: sum

      - name: order_count
        synonyms: ["订单数", "订单量"]
        description: 订单总数
        expr: ORDER_ID
        data_type: NUMBER
        default_aggregation: count_distinct
```

---

## 💰 成本参考

### 外部 API 方案

| 提供商 | 模型 | 价格 (参考) |
|-------|------|-----------|
| DashScope | qwen-turbo | ¥0.008/1K tokens |
| DashScope | qwen-max | ¥0.04/1K tokens |
| DeepSeek | deepseek-chat | ¥0.001/1K tokens |

### SPCS 私有化方案

| 组件 | 规格 | 估算成本 |
|-----|------|---------|
| GPU 计算池 | GPU_NV_S (T4 16GB) | ~$2-3/小时 |
| 存储 | 镜像 + Stage | < $1/月 |

**成本优化建议:**
- 设置 `AUTO_SUSPEND_SECS = 600` 自动暂停
- 非工作时间手动暂停: `ALTER SERVICE QWEN_MODEL_SERVICE SUSPEND;`

---

## 🔧 运维管理

### 常用命令

```sql
-- 查看 UDF 状态
SHOW FUNCTIONS LIKE 'QWEN_COMPLETE';

-- 测试 UDF
SELECT QWEN_COMPLETE('qwen-turbo', '你好');

-- SPCS 服务状态
SELECT SYSTEM$GET_SERVICE_STATUS('QWEN_MODEL_SERVICE');

-- 暂停/恢复 SPCS 服务
ALTER SERVICE QWEN_MODEL_SERVICE SUSPEND;
ALTER SERVICE QWEN_MODEL_SERVICE RESUME;
```

### 故障排除

| 问题 | 可能原因 | 解决方案 |
|-----|---------|---------|
| UDF 调用失败 | API Key 无效 | 检查 Secret 配置 |
| 外部访问失败 | 网络规则未配置 | 检查 External Access Integration |
| SPCS 启动超时 | 模型下载慢 | 检查网络规则，确认 HF-Mirror 可访问 |
| GPU 不可用 | 配额不足 | 联系 Snowflake 支持增加配额 |

---

## 📝 总结

### 方案优势

✅ **Cortex AI 替代** - 中国区 Cortex AI 上线前的完整过渡方案

✅ **灵活部署** - 外部 API 或 SPCS 私有化，满足不同需求

✅ **数据合规** - SPCS 方案确保数据不出数据平台，满足合规要求

✅ **无缝集成** - 与 Snowflake SQL、Streamlit 完美集成

✅ **多模型支持** - 支持多个主流 LLM 提供商和开源模型

### 适用场景

- 中国区客户需要在 Snowflake 中使用 AI 智能分析能力
- 需要基于语义模型进行自然语言数据查询和分析
- 对数据安全有严格要求，需要数据不出数据平台
- 等待 Cortex AI 中国区上线前的过渡方案

### 未来演进

当 Snowflake Cortex AI 在中国区正式上线后：
1. 可逐步迁移到官方 Cortex AI 服务
2. 保留 SPCS 方案用于特定场景（定制模型、私有部署）
3. 语义模型可直接复用于 Cortex Analyst

---

## 🗂️ Snowflake China 资源清单

本项目在 Snowflake 中国区环境中创建以下资源。根据部署方案的不同，创建的资源也有所区别。

### 方案一：外部 API 方案（语义模型生成器 + 智能分析助手）

> 部署脚本：`sis_setup/china_setup.sql` 和 `agent_intelligence/setup_qwen_udf.sql`

| 资源类型 | 资源名称 | 用途说明 |
|---------|---------|---------|
| **Database** | `CORTEX_ANALYST_SEMANTICS` | 存储语义模型生成器相关对象 |
| **Schema** | `SEMANTIC_MODEL_GENERATOR` | 语义模型生成器的 Schema |
| **Network Rule** | `qwen_api_network_rule` | 出站网络规则，允许访问 DashScope/DeepSeek/Moonshot API |
| **Secret** | `qwen_api_secret` | 存储 LLM API Key（通义千问、DeepSeek 等） |
| **External Access Integration** | `qwen_api_integration` | 外部访问集成，关联网络规则和 Secret，允许 UDF 调用外部 API |
| **UDF** | `QWEN_COMPLETE(model, prompt)` | Python UDF，调用外部 LLM API 生成文本 |
| **Stage** | `STREAMLIT_STAGE` | 存储 Streamlit 应用文件（Python 代码、配置等） |
| **Streamlit App** | `SEMANTIC_MODEL_GENERATOR` | 语义模型生成器 Streamlit 应用 |
| **Stored Procedure** | `ZIP_SRC_FILES(...)` | 辅助存储过程，用于压缩 Stage 中的源文件 |
| **Stored Procedure** | `GENERATE_SEMANTIC_FILE(...)` | 核心存储过程，自动生成语义模型 YAML 文件 |

**网络规则允许的域名：**
```
dashscope.aliyuncs.com:443     # 通义千问 DashScope API
api.deepseek.com:443           # DeepSeek API
api.moonshot.cn:443            # Kimi/Moonshot API
```

---

### 方案二：SPCS 私有化方案

> 部署脚本：`spcs_china/setup_sql/01-05_*.sql`

| 资源类型 | 资源名称 | 用途说明 |
|---------|---------|---------|
| **Database** | `SPCS_CHINA` | 存储 SPCS 私有化 LLM 服务相关对象 |
| **Schema** | `MODEL_SERVICE` | 模型服务的 Schema |
| **Compute Pool** | `GPU_NV_S_POOL` | GPU 计算池（NVIDIA T4 16GB），用于运行模型推理容器 |
| **Network Rule** | `modelscope_network_rule` | 出站网络规则，允许下载模型文件（HF-Mirror、ModelScope） |
| **External Access Integration** | `modelscope_access_integration` | 外部访问集成，允许 SPCS 服务下载模型 |
| **Image Repository** | `MODEL_SERVICE_REPO` | Docker 镜像仓库，存储 Qwen 服务镜像 |
| **Stage** | `MODEL_SERVICE_STAGE` | 存储 SPCS 服务规范文件 |
| **Service** | `QWEN_MODEL_SERVICE` | SPCS 容器服务，运行 Qwen 模型（vLLM 推理引擎） |
| **Service Function UDF** | `QWEN_COMPLETE(prompt)` | Service Function，将 SQL 调用路由到 SPCS 服务 |

**网络规则允许的域名（模型下载）：**
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

**Compute Pool 配置：**
- 实例类型：`GPU_NV_S` (NVIDIA T4 16GB / A10 24GB)
- 节点数：MIN=1, MAX=2
- 自动暂停：600 秒无请求后自动暂停
- 自动恢复：收到请求时自动恢复

**SPCS Service 容器资源：**
- CPU：2-4 核
- 内存：8-14 GB
- GPU：1 × NVIDIA T4/A10
- 端口：8000 (API), 8001 (Proxy)

---

### 资源架构图

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Snowflake China Region                                  │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                    方案一：外部 API 方案                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │   │
│  │  │           CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR          │   │   │
│  │  │  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────────┐  │   │   │
│  │  │  │ STREAMLIT_STAGE │  │ QWEN_COMPLETE   │  │ GENERATE_SEMANTIC  │  │   │   │
│  │  │  │ (App Files)     │  │ UDF (Python)    │  │ _FILE SP           │  │   │   │
│  │  │  └────────┬────────┘  └────────┬────────┘  └────────────────────┘  │   │   │
│  │  └───────────┼───────────────────┼────────────────────────────────────┘   │   │
│  │              │                   │                                         │   │
│  │              ▼                   ▼                                         │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │   │
│  │  │              qwen_api_integration (External Access)                  │   │   │
│  │  │    Network Rule: qwen_api_network_rule + Secret: qwen_api_secret     │   │   │
│  │  └──────────────────────────────┬──────────────────────────────────────┘   │   │
│  │                                 │                                          │   │
│  └─────────────────────────────────┼──────────────────────────────────────────┘   │
│                                    ▼                                              │
│                        ┌─────────────────────────┐                                │
│                        │  外部 LLM API           │                                │
│                        │  • DashScope (Qwen)     │                                │
│                        │  • DeepSeek             │                                │
│                        │  • Moonshot (Kimi)      │                                │
│                        └─────────────────────────┘                                │
│                                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                    方案二：SPCS 私有化方案                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │   │
│  │  │                    SPCS_CHINA.MODEL_SERVICE                          │   │   │
│  │  │  ┌──────────────────┐  ┌─────────────────┐  ┌────────────────────┐ │   │   │
│  │  │  │ MODEL_SERVICE    │  │ QWEN_COMPLETE   │  │ MODEL_SERVICE      │ │   │   │
│  │  │  │ _REPO (镜像仓库)  │  │ UDF (Svc Func)  │  │ _STAGE             │ │   │   │
│  │  │  └──────────────────┘  └────────┬────────┘  └────────────────────┘ │   │   │
│  │  └─────────────────────────────────┼──────────────────────────────────┘   │   │
│  │                                    │                                       │   │
│  │                                    ▼                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │   │
│  │  │                     QWEN_MODEL_SERVICE (SPCS)                        │   │   │
│  │  │  ┌───────────────────────────────────────────────────────────────┐  │   │   │
│  │  │  │                   GPU_NV_S_POOL (T4/A10 GPU)                   │  │   │   │
│  │  │  │  ┌─────────────────────────────────────────────────────────┐  │  │   │   │
│  │  │  │  │  qwen-service Container                                  │  │  │   │   │
│  │  │  │  │  ┌─────────────────┐    ┌─────────────────────────────┐ │  │  │   │   │
│  │  │  │  │  │ Snowflake Proxy │───▶│  vLLM + Qwen2.5-1.5B        │ │  │  │   │   │
│  │  │  │  │  │ (Port 8001)     │    │  (Port 8000)                │ │  │  │   │   │
│  │  │  │  │  └─────────────────┘    └─────────────────────────────┘ │  │  │   │   │
│  │  │  │  └─────────────────────────────────────────────────────────┘  │  │   │   │
│  │  │  └───────────────────────────────────────────────────────────────┘  │   │   │
│  │  │                                 │                                    │   │   │
│  │  │                                 │ modelscope_access_integration      │   │   │
│  │  │                                 ▼                                    │   │   │
│  │  │  ┌───────────────────────────────────────────────────────────────┐  │   │   │
│  │  │  │              模型下载源 (首次启动)                              │  │   │   │
│  │  │  │        HF-Mirror (hf-mirror.com) / ModelScope                 │  │   │   │
│  │  │  └───────────────────────────────────────────────────────────────┘  │   │   │
│  │  └─────────────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 资源清理

**清理外部 API 方案资源：**
```sql
-- 删除 Streamlit 应用
DROP STREAMLIT IF EXISTS CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.SEMANTIC_MODEL_GENERATOR;

-- 删除存储过程
DROP PROCEDURE IF EXISTS CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.GENERATE_SEMANTIC_FILE(STRING, STRING, INT, BOOLEAN, ARRAY);
DROP PROCEDURE IF EXISTS CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.ZIP_SRC_FILES(STRING, STRING, STRING, STRING, STRING, STRING);

-- 删除 UDF
DROP FUNCTION IF EXISTS CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.QWEN_COMPLETE(VARCHAR, VARCHAR);

-- 删除 Stage
DROP STAGE IF EXISTS CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.STREAMLIT_STAGE;

-- 删除外部访问集成、Secret 和网络规则
DROP EXTERNAL ACCESS INTEGRATION IF EXISTS qwen_api_integration;
DROP SECRET IF EXISTS CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.qwen_api_secret;
DROP NETWORK RULE IF EXISTS CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.qwen_api_network_rule;

-- 删除数据库 (慎用！会删除所有对象)
-- DROP DATABASE IF EXISTS CORTEX_ANALYST_SEMANTICS;
```

**清理 SPCS 私有化方案资源：**
```sql
-- 先停止服务
ALTER SERVICE SPCS_CHINA.MODEL_SERVICE.QWEN_MODEL_SERVICE SUSPEND;

-- 删除 UDF
DROP FUNCTION IF EXISTS SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE(VARCHAR);

-- 删除服务
DROP SERVICE IF EXISTS SPCS_CHINA.MODEL_SERVICE.QWEN_MODEL_SERVICE;

-- 删除外部访问集成和网络规则
DROP EXTERNAL ACCESS INTEGRATION IF EXISTS modelscope_access_integration;
DROP NETWORK RULE IF EXISTS SPCS_CHINA.MODEL_SERVICE.modelscope_network_rule;

-- 删除镜像仓库和 Stage
DROP IMAGE REPOSITORY IF EXISTS SPCS_CHINA.MODEL_SERVICE.MODEL_SERVICE_REPO;
DROP STAGE IF EXISTS SPCS_CHINA.MODEL_SERVICE.MODEL_SERVICE_STAGE;

-- 删除计算池 (确保无服务使用)
DROP COMPUTE POOL IF EXISTS GPU_NV_S_POOL;

-- 删除数据库 (慎用！会删除所有对象)
-- DROP DATABASE IF EXISTS SPCS_CHINA;
```

---

## 📚 参考资料

- [Snowflake Cortex Analyst 文档](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Snowflake Container Services 文档](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)
- [通义千问 DashScope API](https://help.aliyun.com/zh/dashscope/)
- [Qwen2.5 模型](https://github.com/QwenLM/Qwen2.5)
- [vLLM 推理框架](https://github.com/vllm-project/vllm)

---

## 📄 License

Apache 2.0 License

---

## 🤝 Contributing

欢迎贡献代码和提出建议！本项目基于 [Snowflake-Labs/semantic-model-generator](https://github.com/Snowflake-Labs/semantic-model-generator) 进行中国区适配。

