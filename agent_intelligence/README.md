# Cortex Agent & Intelligence V2 (中国区)

> 适用于 Snowflake 中国区域的 Cortex Agent 和 Cortex Intelligence 替代方案

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `cortex_agent_sis_v2.py` | 主应用文件 (Streamlit in Snowflake) |
| `environment.yml` | SiS 依赖配置 |
| `setup_qwen_udf.sql` | UDF 部署脚本 |

## 🚀 部署步骤

### 1. 部署 UDF

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
CREATE OR REPLACE STREAMLIT YOUR_DB.YOUR_SCHEMA.CORTEX_AGENT_V2
    ROOT_LOCATION = '@YOUR_DB.YOUR_SCHEMA.AGENT_STAGE'
    MAIN_FILE = 'cortex_agent_sis_v2.py'
    TITLE = "Snowflake China Intelligence V2"
    QUERY_WAREHOUSE = YOUR_WAREHOUSE
    EXTERNAL_ACCESS_INTEGRATIONS = (qwen_api_integration);
```

### 3. 配置 UDF 路径

在 `cortex_agent_sis_v2.py` 中修改 UDF 路径（约第 258-264 行）：

```python
MODEL_BACKENDS = {
    "SPCS (Local)": {
        "udf_path": "YOUR_DB.YOUR_SCHEMA.QWEN_COMPLETE"  # SPCS 版本
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

### SPCS (本地部署)
- 需要先部署 `spcs_china/` 中的容器服务

## 📚 功能特性

1. **Agent Chat** - 基于语义模型的智能对话
2. **Data Insights** - 自然语言转 SQL + 数据洞察
3. **Toolbox** - SQL 查询、表结构、数据统计

## ⚠️ 注意事项

- 需要通义千问 API Key (DashScope)
- 需要创建 External Access Integration
- 建议配合语义模型使用以提高准确性

