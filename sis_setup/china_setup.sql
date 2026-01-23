-- ============================================================================
-- Semantic Model Generator - China Region Deployment Setup
-- 适用于 Snowflake 中国区域的部署脚本
-- 使用通义千问 (Qwen) API 替代 Cortex LLM 功能
-- ============================================================================

SET (streamlit_warehouse)=(SELECT CURRENT_WAREHOUSE());

-- ============================================================================
-- Step 1: 创建数据库和 Schema
-- ============================================================================
CREATE DATABASE IF NOT EXISTS CORTEX_ANALYST_SEMANTICS
COMMENT = '{"origin": "sf_sit",
            "name": "skimantics",
            "version": {"major": 2, "minor": 0},
            "attributes": {"deployment": "sis_china"}}';

CREATE SCHEMA IF NOT EXISTS CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR
COMMENT = '{"origin": "sf_sit",
            "name": "skimantics",
            "version": {"major": 2, "minor": 0},
            "attributes": {"deployment": "sis_china"}}';

USE DATABASE CORTEX_ANALYST_SEMANTICS;
USE SCHEMA SEMANTIC_MODEL_GENERATOR;

-- ============================================================================
-- Step 2: 创建 Qwen API 外部访问集成 (External Access Integration)
-- 请将 <YOUR_QWEN_API_KEY> 替换为您的通义千问 API Key
-- ============================================================================

-- 创建网络规则允许访问通义千问 API
CREATE OR REPLACE NETWORK RULE qwen_api_network_rule
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = ('dashscope.aliyuncs.com:443');

-- 创建 Secret 存储 API Key (请替换为您的实际 API Key)
-- 注意: 在实际部署时,请使用安全的方式管理 API Key
CREATE OR REPLACE SECRET qwen_api_secret
    TYPE = GENERIC_STRING
    SECRET_STRING = '<YOUR_QWEN_API_KEY>';

-- 创建外部访问集成
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION qwen_api_integration
    ALLOWED_NETWORK_RULES = (qwen_api_network_rule)
    ALLOWED_AUTHENTICATION_SECRETS = (qwen_api_secret)
    ENABLED = TRUE;

-- ============================================================================
-- Step 3: 创建 Qwen Complete UDF (替代 Cortex COMPLETE 函数)
-- ============================================================================
CREATE OR REPLACE FUNCTION QWEN_COMPLETE(model VARCHAR, prompt VARCHAR)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
PACKAGES = ('requests')
HANDLER = 'qwen_complete'
EXTERNAL_ACCESS_INTEGRATIONS = (qwen_api_integration)
SECRETS = ('api_key' = qwen_api_secret)
AS $$
import requests
import json
import _snowflake

def qwen_complete(model: str, prompt: str) -> str:
    """
    调用通义千问 API 生成文本
    支持的模型: qwen-turbo, qwen-plus, qwen-max
    """
    api_key = _snowflake.get_generic_secret_string('api_key')
    
    # 模型映射 - 将 Cortex 模型名映射到 Qwen 模型
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
        return f"Error calling Qwen API: {str(e)}"
$$;

-- 测试 Qwen UDF
-- SELECT QWEN_COMPLETE('qwen-turbo', '你好，请用一句话介绍你自己。');

-- ============================================================================
-- Step 4: 创建 Stage 用于存储应用文件
-- ============================================================================
CREATE OR REPLACE STAGE CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.STREAMLIT_STAGE
DIRECTORY = (ENABLE = true)
COMMENT = '{"origin": "sf_sit",
            "name": "skimantics",
            "version": {"major": 2, "minor": 0},
            "attributes": {"deployment": "sis_china"}}';

-- ============================================================================
-- Step 5: 上传应用文件 (需要从项目根目录运行)
-- ============================================================================
-- 上传第三方包
PUT file://app_utils/*.zip @CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.STREAMLIT_STAGE OVERWRITE = TRUE AUTO_COMPRESS = FALSE;

-- 上传应用逻辑
PUT file://app.py @CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.STREAMLIT_STAGE/semantic_model_generator/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;
PUT file://environment.yml @CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.STREAMLIT_STAGE/semantic_model_generator/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;
PUT file://semantic_model_generator/*.py @CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.STREAMLIT_STAGE/semantic_model_generator/semantic_model_generator/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;
PUT file://semantic_model_generator/data_processing/*.py @CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.STREAMLIT_STAGE/semantic_model_generator/semantic_model_generator/data_processing/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;
PUT file://semantic_model_generator/protos/*.p* @CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.STREAMLIT_STAGE/semantic_model_generator/semantic_model_generator/protos/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;
PUT file://semantic_model_generator/snowflake_utils/*.py @CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.STREAMLIT_STAGE/semantic_model_generator/semantic_model_generator/snowflake_utils/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;
PUT file://semantic_model_generator/validate/*.py @CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.STREAMLIT_STAGE/semantic_model_generator/semantic_model_generator/validate/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;
PUT file://images/*.png @CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.STREAMLIT_STAGE/semantic_model_generator/images/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;
PUT file://journeys/*.py @CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.STREAMLIT_STAGE/semantic_model_generator/journeys/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;
PUT file://partner/*.py @CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.STREAMLIT_STAGE/semantic_model_generator/partner/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;
PUT file://app_utils/*.py @CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.STREAMLIT_STAGE/semantic_model_generator/app_utils/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;

-- ============================================================================
-- Step 6: 创建 Streamlit 应用 (中国区专用，使用 Qwen 替代 Cortex)
-- ============================================================================
CREATE OR REPLACE STREAMLIT CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.SEMANTIC_MODEL_GENERATOR
ROOT_LOCATION = '@CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.STREAMLIT_STAGE/semantic_model_generator'
MAIN_FILE = 'app.py'
TITLE = "语义模型生成器 (中国区)"
IMPORTS = ('@cortex_analyst_semantics.semantic_model_generator.streamlit_stage/looker_sdk.zip',
'@cortex_analyst_semantics.semantic_model_generator.streamlit_stage/strictyaml.zip')
QUERY_WAREHOUSE = $streamlit_warehouse
EXTERNAL_ACCESS_INTEGRATIONS = (qwen_api_integration)
COMMENT = '{"origin": "sf_sit",
            "name": "skimantics",
            "version": {"major": 2, "minor": 0},
            "attributes": {"deployment": "sis_china"}}';

-- ============================================================================
-- Step 7: 创建 Callable Semantic Generation 存储过程
-- ============================================================================

-- 压缩源文件的辅助存储过程
CREATE OR REPLACE PROCEDURE CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.ZIP_SRC_FILES(
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
PACKAGES = (
    'snowflake-snowpark-python==1.18.0'
)
HANDLER='zip_staged_files'
EXECUTE AS CALLER
AS $$
from snowflake.snowpark import Session
from typing import Optional

def get_staged_files(session: Session,
                     database: str,
                     schema: str,
                     stage: str,
                     target_parent: Optional[str] = None,
                     source_path: Optional[str] = None,
                     ) -> dict[str, str]:
    
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
    zip_bytes = zip_buffer.getvalue()
    return zip_bytes

def upload_zip(session: Session,
               database: str,
               schema: str,
               stage: str,
               zip_file: bytes,
               zip_filename: str,
               ) -> None:
    import io
    session.file.put_stream(
                io.BytesIO(zip_file),
                f"@{database}.{schema}.{stage}/{zip_filename.replace('zip','')}.zip",
                auto_compress=False,
                overwrite=True,
            )
    
def zip_staged_files(session: Session,
                     database: str,
                     schema: str,
                     stage: str,
                     source_path: Optional[str] = None,
                     target_parent: Optional[str] = None,
                     zip_filename: Optional[str] = None,
                     ) -> str:
    
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

$$;

-- 执行压缩
CALL CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.ZIP_SRC_FILES(
    'CORTEX_ANALYST_SEMANTICS',
    'SEMANTIC_MODEL_GENERATOR',
    'streamlit_stage',
    'semantic_model_generator/semantic_model_generator',
    'semantic_model_generator',
    'semantic_model_generator'
);

-- 创建 Semantic Model 生成存储过程 (使用 Qwen 替代 Cortex)
CREATE OR REPLACE PROCEDURE CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.GENERATE_SEMANTIC_FILE(
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
    'pandas==2.2.2',
    'tqdm==4.66.5',
    'loguru==0.5.3',
    'protobuf==3.20.3',
    'pydantic==2.8.2',
    'pyyaml==6.0.1',
    'ruamel.yaml==0.17.21',
    'pyarrow==14.0.2',
    'sqlglot==25.10.0',
    'numpy==1.26.4',
    'python-dotenv==0.21.0',
    'urllib3==2.2.2',
    'types-pyyaml==6.0.12.12',
    'types-protobuf==4.25.0.20240417',
    'snowflake-snowpark-python==1.18.0',
    'cattrs==23.1.2',
    'filelock'
)
IMPORTS = ('@CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.STREAMLIT_STAGE/semantic_model_generator.zip',
    '@cortex_analyst_semantics.semantic_model_generator.streamlit_stage/strictyaml.zip'
            )
HANDLER='run_generation'
EXECUTE AS CALLER
AS $$
from snowflake.snowpark import Session

def import_src_zip(zip_name = 'semantic_model_generator.zip'):
    import os
    import sys
    import zipfile
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

def run_generation(session: Session,
                   STAGE_NAME: str,
                   MODEL_NAME: str,
                   SAMPLE_VALUE: int,
                   ALLOW_JOINS: bool,
                   TABLE_LIST: list[str]) -> str:

    import io

    import_src_zip()
    from semantic_model_generator.generate_model import generate_model_str_from_snowflake

    if not MODEL_NAME:
        raise ValueError("Please provide a name for your semantic model.")
    elif not TABLE_LIST:
        raise ValueError("Please select at least one table to proceed.")
    else:
        yaml_str = generate_model_str_from_snowflake(
            base_tables=TABLE_LIST,
            semantic_model_name=MODEL_NAME,
            n_sample_values=SAMPLE_VALUE,
            conn=session.connection,
            allow_joins=ALLOW_JOINS,
        )

        session.file.put_stream(
                io.BytesIO(yaml_str.encode('utf-8')),
               f"@{STAGE_NAME}/{MODEL_NAME}.yaml",
               auto_compress=False,
               overwrite=True,
           )
        return f"Semantic model file {MODEL_NAME}.yaml has been generated and saved to {STAGE_NAME}."
$$;

-- ============================================================================
-- 部署完成！
-- ============================================================================
-- 使用以下命令打开 Streamlit 应用:
-- snow streamlit get-url SEMANTIC_MODEL_GENERATOR --open --database cortex_analyst_semantics --schema semantic_model_generator --connection china
-- 
-- 或者直接在 Snowsight 中打开应用
-- ============================================================================

