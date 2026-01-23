import os
import yaml
from snowflake.connector import SnowflakeConnection


def _is_china_region(conn: SnowflakeConnection) -> bool:
    """
    Check if running in China region by examining environment and connection.
    Always returns True for China region to use local validation instead of Cortex Analyst.
    """
    # Check environment variable first
    if os.environ.get("USE_QWEN_FOR_CHINA", "").lower() == "true":
        return True
    
    # Check connection host for China region indicators
    try:
        host = conn.host or ""
        if any(x in host.lower() for x in [".cn", "cn-", "china", "amazonaws.com.cn"]):
            return True
    except Exception:
        pass
    
    # Check region from Snowflake
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_REGION()")
        region = cursor.fetchone()[0] or ""
        if "cn-" in region.lower() or "china" in region.lower():
            return True
    except Exception:
        pass
    
    # Check account for China region
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_ACCOUNT()")
        account = cursor.fetchone()[0] or ""
        if any(x in account.lower() for x in ["cn-", ".cn"]):
            return True
    except Exception:
        pass
    
    # Default: assume China region if Cortex is not available
    # This ensures we don't try to call Cortex Analyst in China
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3-8b', 'test')")
        return False  # Cortex works, not China region
    except Exception:
        return True  # Cortex doesn't work, assume China region


def load_yaml(yaml_path: str) -> str:
    """
    Load local yaml file into str.

    yaml_path: str The absolute path to the location of your yaml file. Something like path/to/your/file.yaml.
    """
    with open(yaml_path) as f:
        yaml_str = f.read()
    return yaml_str


def _validate_yaml_structure(yaml_str: str) -> None:
    """
    Validate the YAML structure for semantic model.
    This is a basic validation that checks required fields.
    """
    try:
        data = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML 解析错误: {e}")
    
    if not data:
        raise ValueError("YAML 文件为空")
    
    # Check required top-level fields
    if "name" not in data:
        raise ValueError("语义模型缺少 'name' 字段")
    
    if "tables" not in data or not data["tables"]:
        raise ValueError("语义模型缺少 'tables' 字段或表列表为空")
    
    # Validate each table
    for i, table in enumerate(data["tables"]):
        if "name" not in table:
            raise ValueError(f"表 {i+1} 缺少 'name' 字段")
        
        if "base_table" not in table:
            raise ValueError(f"表 '{table.get('name', i+1)}' 缺少 'base_table' 字段")
        
        base_table = table["base_table"]
        for field in ["database", "schema", "table"]:
            if field not in base_table:
                raise ValueError(f"表 '{table.get('name', i+1)}' 的 base_table 缺少 '{field}' 字段")
        
        # Check that at least one of dimensions, time_dimensions, or measures exists
        has_columns = any(
            table.get(col_type) 
            for col_type in ["dimensions", "time_dimensions", "measures"]
        )
        if not has_columns:
            raise ValueError(f"表 '{table.get('name', i+1)}' 至少需要定义一个 dimension、time_dimension 或 measure")


def _validate_tables_exist(yaml_str: str, conn: SnowflakeConnection) -> None:
    """
    Validate that the base tables referenced in the semantic model exist in Snowflake.
    """
    data = yaml.safe_load(yaml_str)
    
    for table in data.get("tables", []):
        base_table = table.get("base_table", {})
        db = base_table.get("database", "")
        schema = base_table.get("schema", "")
        tbl = base_table.get("table", "")
        
        fqn = f"{db}.{schema}.{tbl}"
        
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT 1 FROM {fqn} LIMIT 1")
        except Exception as e:
            raise ValueError(f"无法访问表 '{fqn}': {str(e)}")


def validate(yaml_str: str, conn: SnowflakeConnection) -> None:
    """
    Validate semantic model YAML.
    
    For China region or when Cortex Analyst is not available, performs local YAML validation
    and checks that referenced tables exist.
    
    For other regions with Cortex Analyst enabled, uses Cortex Analyst API for validation.

    yaml_str: yaml content in string format.
    conn: SnowflakeConnection Snowflake connection to pass in
    """
    
    # Always check at runtime if we're in China region
    if _is_china_region(conn):
        # For China region, do local validation (no Cortex Analyst)
        _validate_yaml_structure(yaml_str)
        _validate_tables_exist(yaml_str, conn)
    else:
        # For other regions, use Cortex Analyst for validation
        from app_utils.chat import send_message
        dummy_request = [
            {"role": "user", "content": [{"type": "text", "text": "SMG app validation"}]}
        ]
        send_message(conn, yaml_str, dummy_request)


def validate_from_local_path(yaml_path: str, conn: SnowflakeConnection) -> None:
    yaml_str = load_yaml(yaml_path)
    validate(yaml_str, conn)
