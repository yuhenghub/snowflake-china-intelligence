# Agent Intelligence (智能分析助手)

> Snowflake China Intelligence 的核心组件 - 为 Snowflake 中国区提供自然语言数据分析能力

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `cortex_agent_sis_v2.py` | 主应用文件 (Streamlit in Snowflake) |
| `environment.yml` | SiS 依赖配置 |
| `setup_qwen_udf.sql` | 外部 API UDF 部署脚本 |

## 🚀 部署步骤

### 1. 部署 LLM UDF

首先需要在 Snowflake 中创建 QWEN_COMPLETE UDF：

1. 打开 `setup_qwen_udf.sql`
2. 修改以下变量：
   - `DATABASE_NAME`: 你的数据库名称
   - `SCHEMA_NAME`: 你的 Schema 名称  
   - `QWEN_API_KEY`: 你的通义千问 API Key (从 [DashScope](https://dashscope.console.aliyun.com/) 获取)
3. 在 Snowsight SQL Worksheet 中执行脚本

### 2. 部署 Streamlit 应用

```sql
-- 创建 Stage
CREATE OR REPLACE STAGE YOUR_DB.YOUR_SCHEMA.AGENT_STAGE
    DIRECTORY = (ENABLE = true);

-- 上传文件 (在本地执行)
PUT file://cortex_agent_sis_v2.py @YOUR_DB.YOUR_SCHEMA.AGENT_STAGE/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;
PUT file://environment.yml @YOUR_DB.YOUR_SCHEMA.AGENT_STAGE/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;

-- 创建 Streamlit 应用
CREATE OR REPLACE STREAMLIT YOUR_DB.YOUR_SCHEMA.CHINA_INTELLIGENCE
    ROOT_LOCATION = '@YOUR_DB.YOUR_SCHEMA.AGENT_STAGE'
    MAIN_FILE = 'cortex_agent_sis_v2.py'
    TITLE = "Snowflake China Intelligence"
    QUERY_WAREHOUSE = YOUR_WAREHOUSE
    EXTERNAL_ACCESS_INTEGRATIONS = (qwen_api_integration);
```

### 3. 配置 UDF 路径

在 `cortex_agent_sis_v2.py` 中修改 UDF 路径（约第 258-264 行）：

```python
MODEL_BACKENDS = {
    "SPCS (Local)": {
        "udf_path": "SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE"  # SPCS 私有化版本
    },
    "External API": {
        "udf_path": "YOUR_DB.YOUR_SCHEMA.QWEN_COMPLETE"  # 外部 API 版本
    }
}
```

## 🧠 支持的模型

### External API (DashScope)
- `qwen-max` - 最强大，适合复杂任务
- `qwen-plus` - 平衡性价比
- `qwen-turbo` - 快速响应

### SPCS (私有化部署)
- 需要先部署 `spcs_china/` 中的容器服务
- 支持 Qwen2.5-1.5B-Instruct 等开源模型

## 📚 功能特性

| 功能模块 | 说明 |
|---------|------|
| **Agent Chat** | 基于语义模型的智能对话，自然语言转 SQL |
| **Data Insights** | 自动分析查询结果，生成数据洞察 |
| **Visualization** | 自动生成适合的数据可视化图表 |
| **Toolbox** | SQL 查询、表结构浏览、数据统计 |

## ⚠️ 注意事项

- 需要通义千问 API Key (DashScope) 或 SPCS 私有化服务
- 需要创建 External Access Integration (外部 API 方案)
- 建议配合语义模型使用以提高 SQL 生成准确性
- 中国区 Streamlit 版本可能与最新版有差异，已做兼容处理

## 🔗 相关文档

- [主项目 README](../README.md) - Snowflake China Intelligence 总览
- [SPCS 私有化部署](../spcs_china/README.md) - 私有化 LLM 服务部署指南
