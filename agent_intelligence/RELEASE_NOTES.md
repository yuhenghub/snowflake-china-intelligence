# Release Notes - Agent Intelligence

## Version 3.2.0 (2026-02-28)

### New Features

#### 1. Personalized Greeting
- **First Name Display**: Greeting now shows user's first name (e.g., "Good morning, John")
- **Snowflake User Integration**: Extracts name from `DESCRIBE USER` or parses from username

#### 2. Data Insights Multi-turn Deep Dive
- **Conversation Context**: Insights tab now supports multi-turn conversations
- **Follow-up Analysis**: Ask follow-up questions based on previous query results
- **SQL History Awareness**: New queries consider previous SQL and results
- **Integrated Experience**: Data + Insights + Deep Dive in one conversation flow

#### 3. Separate History Storage
- **Independent Tables**: Agent Chat and Data Insights use separate table pairs
- **Same Schema**: All 4 tables in the configured history schema
- **Table Structure**:
  - `AGENT_CHAT_SESSIONS` / `AGENT_CHAT_MESSAGES` for Agent Chat
  - `INSIGHTS_SESSIONS` / `INSIGHTS_MESSAGES` for Data Insights

#### 4. Simplified Configuration
- **Conversations First**: History config merged into Conversations section
- **Auto-load History**: History sessions appear immediately after config
- **Removed Clear Button**: Streamlined UI without Clear Conversation

#### 5. Removed Features
- **Clear Conversation**: Removed (use New Chat instead)
- **Data Source Selection**: Removed (now driven by semantic model)

### Database Schema
```sql
-- Agent Chat tables
CREATE TABLE AGENT_CHAT_SESSIONS (
    session_id VARCHAR(36), user_id VARCHAR(255), title VARCHAR(500),
    created_at TIMESTAMP_NTZ, updated_at TIMESTAMP_NTZ,
    semantic_model_name VARCHAR(255), message_count INTEGER
);
CREATE TABLE AGENT_CHAT_MESSAGES (
    message_id VARCHAR(36), session_id VARCHAR(36), role VARCHAR(20),
    content TEXT, tool_info TEXT, query_result TEXT, created_at TIMESTAMP_NTZ
);

-- Insights tables
CREATE TABLE INSIGHTS_SESSIONS (
    session_id VARCHAR(36), user_id VARCHAR(255), title VARCHAR(500),
    created_at TIMESTAMP_NTZ, updated_at TIMESTAMP_NTZ,
    semantic_model_name VARCHAR(255), message_count INTEGER
);
CREATE TABLE INSIGHTS_MESSAGES (
    message_id VARCHAR(36), session_id VARCHAR(36), role VARCHAR(20),
    content TEXT, sql_query TEXT, query_result TEXT, insights TEXT,
    created_at TIMESTAMP_NTZ
);
```

---

## Version 3.0.0 (2026-02-28)

### New Features

#### 1. Chat History Persistence
- **Database Storage**: Chat conversations are now saved to Snowflake tables (`CHAT_SESSIONS` and `CHAT_HISTORY`)
- **Session Management**: Each conversation has a unique session ID for easy retrieval
- **Auto-save**: Messages are automatically saved as you chat
- **History Browser**: View and load previous conversations from the sidebar

#### 2. Collapsible Configuration Panel
- **Cleaner UI**: All configuration options (model selection, data source, semantic model) are now collapsed under an expandable "Configuration" section
- **Compact Status Display**: Current configuration status is always visible in a compact format
- **Reduced Clutter**: Sidebar is now focused on conversation management

#### 3. Enhanced Multi-turn Conversation Support
- **Improved Context Management**: Better formatting of conversation history for the LLM prompt
- **Smart Truncation**: Automatically truncates older messages to stay within token limits
- **Context Hints**: Includes relevant context from previous query results
- **Configurable Limits**: `MAX_HISTORY_MESSAGES` and `MAX_HISTORY_CHARS` settings

#### 4. Conversation Management
- **New Chat Button**: Start a fresh conversation with one click
- **Load History**: Browse and load previous conversations
- **Delete Sessions**: Remove unwanted conversation history
- **Session Titles**: Auto-generated from the first message

### Technical Details

#### Database Schema
```sql
-- Chat sessions table
CREATE TABLE CHAT_SESSIONS (
    session_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(255),
    title VARCHAR(500),
    created_at TIMESTAMP_NTZ,
    updated_at TIMESTAMP_NTZ,
    semantic_model_name VARCHAR(255),
    database_name VARCHAR(255),
    schema_name VARCHAR(255),
    message_count INTEGER
);

-- Chat messages table
CREATE TABLE CHAT_HISTORY (
    message_id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36),
    role VARCHAR(20),
    content TEXT,
    tool_info TEXT,
    query_result TEXT,
    created_at TIMESTAMP_NTZ
);
```

#### Multi-turn Prompt Design
The system now uses a structured approach to include conversation history:

```
## Previous Conversation:
[User]: Previous question...
[Assistant]: Previous response...
[User]: Follow-up question...
[Assistant]: Follow-up response...

---
[Context: Last query returned N rows with columns: col1, col2, ...]

[Current Question]: User's current question
```

**Key Features:**
- Last N messages included (configurable via `MAX_HISTORY_MESSAGES`)
- Total history limited to M characters (configurable via `MAX_HISTORY_CHARS`)
- Long messages truncated with `...[truncated]` indicator
- Recent messages prioritized (older ones dropped first)

### Configuration

#### Enable Chat History
1. Open the Configuration panel in the sidebar
2. Check "Enable chat history"
3. Select a schema where tables will be created
4. Click "Setup Tables" to create required tables

#### Adjust History Settings
In the code, you can modify:
```python
MAX_HISTORY_MESSAGES = 20  # Max messages to include in prompt
MAX_HISTORY_CHARS = 8000   # Max characters of history in prompt
```

### Migration Notes

- **No Breaking Changes**: Existing deployments will work without modification
- **Optional History**: Chat history feature is opt-in and disabled by default
- **Table Creation**: Tables are created on-demand when you click "Setup Tables"

---

## Version 2.0.0 (Previous)

### Features
- Semantic model support for improved SQL generation
- Multi-provider LLM support (DashScope, DeepSeek, Kimi, MiniMax)
- SPCS local model deployment option
- Data insights generation
- Natural language to SQL conversion

---

## Version 1.0.0 (Initial)

### Features
- Basic chat interface
- SQL execution
- Table structure browsing
- Snowflake connection management
