#!/bin/bash
# ============================================================================
# Semantic Model Generator - Deploy to SNOWFLAKE_PROD_USER1.CORTEX_ANALYST
# ============================================================================

set -e

echo "=========================================="
echo "部署到 SNOWFLAKE_PROD_USER1.CORTEX_ANALYST"
echo "=========================================="

# 配置变量
SNOW_CONNECTION="china_dev"
DATABASE="SNOWFLAKE_PROD_USER1"
SCHEMA="CORTEX_ANALYST"
QWEN_API_KEY="${QWEN_API_KEY:-sk-974d67fdc0744f1fb0723686c810f327}"

# 检查 Snow CLI
if ! command -v snow &> /dev/null; then
    echo "❌ 错误: Snowflake CLI 未安装"
    exit 1
fi

# 检查连接配置
echo ""
echo "📡 验证 Snowflake 连接 ($SNOW_CONNECTION)..."
snow connection test --connection $SNOW_CONNECTION || {
    echo "❌ 连接测试失败"
    exit 1
}

echo "✅ 连接验证成功"

# 切换到项目目录
cd "$(dirname "$0")"

echo ""
echo "📦 Step 1: 创建数据库、Schema..."
echo "-------------------------------------------"

snow sql -q "CREATE DATABASE IF NOT EXISTS ${DATABASE};" --connection $SNOW_CONNECTION
snow sql -q "CREATE SCHEMA IF NOT EXISTS ${DATABASE}.${SCHEMA};" --connection $SNOW_CONNECTION
snow sql -q "USE DATABASE ${DATABASE}; USE SCHEMA ${SCHEMA};" --connection $SNOW_CONNECTION

echo ""
echo "🌐 Step 2: 创建网络规则和 External Access Integration..."

# 创建网络规则
snow sql -q "CREATE OR REPLACE NETWORK RULE ${DATABASE}.${SCHEMA}.qwen_api_network_rule MODE = EGRESS TYPE = HOST_PORT VALUE_LIST = ('dashscope.aliyuncs.com:443');" --connection $SNOW_CONNECTION

# 创建 Secret
echo ""
echo "🔐 Step 3: 创建 Qwen API Secret..."
snow sql -q "CREATE OR REPLACE SECRET ${DATABASE}.${SCHEMA}.qwen_api_secret TYPE = GENERIC_STRING SECRET_STRING = '$QWEN_API_KEY';" --connection $SNOW_CONNECTION

# 创建外部访问集成
snow sql -q "CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION ${DATABASE}_${SCHEMA}_qwen_integration ALLOWED_NETWORK_RULES = (${DATABASE}.${SCHEMA}.qwen_api_network_rule) ALLOWED_AUTHENTICATION_SECRETS = (${DATABASE}.${SCHEMA}.qwen_api_secret) ENABLED = TRUE;" --connection $SNOW_CONNECTION

echo ""
echo "🤖 Step 4: 创建 Qwen Complete UDF..."

cat > /tmp/qwen_udf.sql << EOSQL
USE DATABASE ${DATABASE};
USE SCHEMA ${SCHEMA};

CREATE OR REPLACE FUNCTION QWEN_COMPLETE(model VARCHAR, prompt VARCHAR)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
PACKAGES = ('requests')
HANDLER = 'qwen_complete'
EXTERNAL_ACCESS_INTEGRATIONS = (${DATABASE}_${SCHEMA}_qwen_integration)
SECRETS = ('api_key' = ${DATABASE}.${SCHEMA}.qwen_api_secret)
AS \$\$
import requests
import json
import _snowflake

def qwen_complete(model: str, prompt: str) -> str:
    api_key = _snowflake.get_generic_secret_string('api_key')
    
    model_mapping = {
        'llama3-8b': 'qwen-turbo',
        'mistral-large2': 'qwen-max',
        'mixtral-8x7b': 'qwen-plus',
    }
    qwen_model = model_mapping.get(model.lower(), model)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": qwen_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048,
        "temperature": 0.7,
    }
    
    try:
        response = requests.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        return ""
    except Exception as e:
        return f"Error: {str(e)}"
\$\$;
EOSQL

snow sql -f /tmp/qwen_udf.sql --connection $SNOW_CONNECTION

echo ""
echo "📦 Step 5: 创建 Stage 并上传文件..."

snow sql -q "CREATE OR REPLACE STAGE ${DATABASE}.${SCHEMA}.STREAMLIT_STAGE DIRECTORY = (ENABLE = true);" --connection $SNOW_CONNECTION

# 上传文件
echo "上传第三方包..."
snow sql -q "PUT file://$(pwd)/app_utils/*.zip @${DATABASE}.${SCHEMA}.STREAMLIT_STAGE OVERWRITE = TRUE AUTO_COMPRESS = FALSE;" --connection $SNOW_CONNECTION

echo "上传应用文件..."
snow sql -q "PUT file://$(pwd)/app.py @${DATABASE}.${SCHEMA}.STREAMLIT_STAGE/semantic_model_generator/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;" --connection $SNOW_CONNECTION
snow sql -q "PUT file://$(pwd)/environment.yml @${DATABASE}.${SCHEMA}.STREAMLIT_STAGE/semantic_model_generator/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;" --connection $SNOW_CONNECTION
snow sql -q "PUT file://$(pwd)/semantic_model_generator/*.py @${DATABASE}.${SCHEMA}.STREAMLIT_STAGE/semantic_model_generator/semantic_model_generator/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;" --connection $SNOW_CONNECTION
snow sql -q "PUT file://$(pwd)/semantic_model_generator/data_processing/*.py @${DATABASE}.${SCHEMA}.STREAMLIT_STAGE/semantic_model_generator/semantic_model_generator/data_processing/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;" --connection $SNOW_CONNECTION
snow sql -q "PUT file://$(pwd)/semantic_model_generator/protos/*.p* @${DATABASE}.${SCHEMA}.STREAMLIT_STAGE/semantic_model_generator/semantic_model_generator/protos/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;" --connection $SNOW_CONNECTION
snow sql -q "PUT file://$(pwd)/semantic_model_generator/snowflake_utils/*.py @${DATABASE}.${SCHEMA}.STREAMLIT_STAGE/semantic_model_generator/semantic_model_generator/snowflake_utils/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;" --connection $SNOW_CONNECTION
snow sql -q "PUT file://$(pwd)/semantic_model_generator/validate/*.py @${DATABASE}.${SCHEMA}.STREAMLIT_STAGE/semantic_model_generator/semantic_model_generator/validate/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;" --connection $SNOW_CONNECTION
snow sql -q "PUT file://$(pwd)/images/*.png @${DATABASE}.${SCHEMA}.STREAMLIT_STAGE/semantic_model_generator/images/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;" --connection $SNOW_CONNECTION
snow sql -q "PUT file://$(pwd)/journeys/*.py @${DATABASE}.${SCHEMA}.STREAMLIT_STAGE/semantic_model_generator/journeys/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;" --connection $SNOW_CONNECTION
snow sql -q "PUT file://$(pwd)/partner/*.py @${DATABASE}.${SCHEMA}.STREAMLIT_STAGE/semantic_model_generator/partner/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;" --connection $SNOW_CONNECTION
snow sql -q "PUT file://$(pwd)/app_utils/*.py @${DATABASE}.${SCHEMA}.STREAMLIT_STAGE/semantic_model_generator/app_utils/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;" --connection $SNOW_CONNECTION

echo ""
echo "🎯 Step 6: 创建 Streamlit 应用..."

cat > /tmp/create_streamlit.sql << EOSQL
SET (streamlit_warehouse)=(SELECT CURRENT_WAREHOUSE());

CREATE OR REPLACE STREAMLIT ${DATABASE}.${SCHEMA}.SEMANTIC_MODEL_GENERATOR
ROOT_LOCATION = '@${DATABASE}.${SCHEMA}.STREAMLIT_STAGE/semantic_model_generator'
MAIN_FILE = 'app.py'
TITLE = "Semantic Model Generator"
IMPORTS = ('@${DATABASE}.${SCHEMA}.STREAMLIT_STAGE/looker_sdk.zip',
'@${DATABASE}.${SCHEMA}.STREAMLIT_STAGE/strictyaml.zip')
QUERY_WAREHOUSE = \$streamlit_warehouse
EXTERNAL_ACCESS_INTEGRATIONS = (${DATABASE}_${SCHEMA}_qwen_integration)
COMMENT = '{"origin": "sf_sit", "name": "skimantics", "version": {"major": 2, "minor": 0}, "attributes": {"deployment": "prod_user1"}}';
EOSQL

snow sql -f /tmp/create_streamlit.sql --connection $SNOW_CONNECTION

echo ""
echo "📦 Step 7: 创建存储过程..."

cat > /tmp/create_procedures.sql << EOSQL
USE DATABASE ${DATABASE};
USE SCHEMA ${SCHEMA};

-- Zip 存储过程
CREATE OR REPLACE PROCEDURE ${DATABASE}.${SCHEMA}.ZIP_SRC_FILES(
    database STRING,
    schema STRING,
    stage STRING,
    source_path STRING,
    target_parent STRING,
    zip_filename STRING
)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = 3.10
PACKAGES = ('snowflake-snowpark-python==1.18.0')
HANDLER='zip_staged_files'
EXECUTE AS CALLER
AS \$\$
from snowflake.snowpark import Session
from typing import Optional

def get_staged_files(session: Session, database: str, schema: str, stage: str,
                     target_parent: Optional[str] = None, source_path: Optional[str] = None) -> dict[str, str]:
    query = f"ls @{database}.{schema}.{stage}/{source_path}"
    file_result = session.sql(query).collect()
    file_data = {}
    for row in file_result:
        filename = row['name'].split('/',1)[1]
        if target_parent:
            filename = filename.replace(source_path, f"{target_parent}")
        full_file_path = f"@{database}.{schema}.{row['name']}"
        file_data[filename] = session.file.get_stream(f"{full_file_path}").read().decode('utf-8')
    return file_data

def create_zip(file_data: dict[str, str]) -> bytes:
    import io
    import zipfile
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for filename, content in file_data.items():
            zipf.writestr(filename, content)
    return zip_buffer.getvalue()

def upload_zip(session: Session, database: str, schema: str, stage: str,
               zip_file: bytes, zip_filename: str) -> None:
    import io
    session.file.put_stream(io.BytesIO(zip_file),
                f"@{database}.{schema}.{stage}/{zip_filename.replace('zip','')}.zip",
                auto_compress=False, overwrite=True)

def zip_staged_files(session: Session, database: str, schema: str, stage: str,
                     source_path: Optional[str] = None, target_parent: Optional[str] = None,
                     zip_filename: Optional[str] = None) -> str:
    file_data = get_staged_files(session, database, schema, stage, target_parent, source_path)
    zip_file = create_zip(file_data)
    if zip_filename:
        zip_filename = zip_filename
    elif target_parent is not None:
        zip_filename = target_parent
    elif source_path is not None:
        zip_filename = source_path
    else:
        zip_filename = "zipped_files"
    upload_zip(session, database, schema, stage, zip_file, zip_filename)
    return f"Files zipped and uploaded to {database}.{schema}.{stage}/{zip_filename}.zip."
\$\$;

-- 执行压缩
CALL ${DATABASE}.${SCHEMA}.ZIP_SRC_FILES(
    '${DATABASE}',
    '${SCHEMA}',
    'STREAMLIT_STAGE',
    'semantic_model_generator/semantic_model_generator',
    'semantic_model_generator',
    'semantic_model_generator'
);

-- 生成存储过程
CREATE OR REPLACE PROCEDURE ${DATABASE}.${SCHEMA}.GENERATE_SEMANTIC_FILE(
    STAGE_NAME STRING,
    MODEL_NAME STRING,
    SAMPLE_VALUE INT,
    ALLOW_JOINS BOOLEAN,
    TABLE_LIST ARRAY
)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = 3.10
PACKAGES = (
    'pandas==2.2.2', 'tqdm==4.66.5', 'loguru==0.5.3', 'protobuf==3.20.3',
    'pydantic==2.8.2', 'pyyaml==6.0.1', 'ruamel.yaml==0.17.21', 'pyarrow==14.0.2',
    'sqlglot==25.10.0', 'numpy==1.26.4', 'python-dotenv==0.21.0', 'urllib3==2.2.2',
    'types-pyyaml==6.0.12.12', 'types-protobuf==4.25.0.20240417',
    'snowflake-snowpark-python==1.18.0', 'cattrs==23.1.2', 'filelock'
)
IMPORTS = ('@${DATABASE}.${SCHEMA}.STREAMLIT_STAGE/semantic_model_generator.zip',
    '@${DATABASE}.${SCHEMA}.STREAMLIT_STAGE/strictyaml.zip')
HANDLER='run_generation'
EXECUTE AS CALLER
AS \$\$
from snowflake.snowpark import Session

def import_src_zip(zip_name = 'semantic_model_generator.zip'):
    import os, sys, zipfile
    from filelock import FileLock
    IMPORT_DIRECTORY_NAME = "snowflake_import_directory"
    import_dir = sys._xoptions[IMPORT_DIRECTORY_NAME]
    zip_file_path = import_dir + zip_name
    extracted = f'/tmp/{zip_name.replace(".zip", "")}'
    with FileLock('/tmp/extract.lock'):
        if not os.path.isdir(extracted):
            with zipfile.ZipFile(zip_file_path, 'r') as myzip:
                myzip.extractall(extracted)
    sys.path.insert(0,extracted)

def run_generation(session: Session, STAGE_NAME: str, MODEL_NAME: str,
                   SAMPLE_VALUE: int, ALLOW_JOINS: bool, TABLE_LIST: list[str]) -> str:
    import io
    import_src_zip()
    from semantic_model_generator.generate_model import generate_model_str_from_snowflake
    if not MODEL_NAME:
        raise ValueError("Please provide a name for your semantic model.")
    elif not TABLE_LIST:
        raise ValueError("Please select at least one table to proceed.")
    else:
        yaml_str = generate_model_str_from_snowflake(
            base_tables=TABLE_LIST, semantic_model_name=MODEL_NAME,
            n_sample_values=SAMPLE_VALUE, conn=session.connection, allow_joins=ALLOW_JOINS)
        session.file.put_stream(io.BytesIO(yaml_str.encode('utf-8')),
               f"@{STAGE_NAME}/{MODEL_NAME}.yaml", auto_compress=False, overwrite=True)
        return f"Semantic model file {MODEL_NAME}.yaml has been generated and saved to {STAGE_NAME}."
\$\$;
EOSQL

snow sql -f /tmp/create_procedures.sql --connection $SNOW_CONNECTION

echo ""
echo "=========================================="
echo "✅ 部署完成!"
echo "=========================================="
echo ""
echo "🚀 打开应用:"
echo "   snow streamlit get-url SEMANTIC_MODEL_GENERATOR --open \\"
echo "       --database ${DATABASE} \\"
echo "       --schema ${SCHEMA} \\"
echo "       --connection $SNOW_CONNECTION"
echo ""
