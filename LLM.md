# ACI Platform - AI Integration Guide

## Overview

**ACI.dev** is an open-source tool-calling platform that provides unified access to 600+ integrations through AI agents. It serves as infrastructure for "VibeOps" - automating DevOps through agentic IDEs with natural language instructions.

**Key Features:**
- Multi-agent architecture with granular permissions
- Dynamic function discovery through semantic search
- Universal authentication handling (OAuth2, API keys, no-auth)
- 600+ pre-built app integrations
- Dual access patterns: Python SDK and MCP server

## Core AI Architecture

### 1. Agent System

Agents are AI entities within projects that execute functions with specific permissions and capabilities.

#### Agent Configuration

```python
# From backend/aci/common/schemas/agent.py
class AgentCreate(BaseModel):
    name: str
    description: str
    allowed_apps: list[str] = []  # App-level access control
    custom_instructions: dict[str, ValidInstruction] = {}  # Function-level guardrails
```

#### Agent Permissions Model

**Three-Level Security:**
1. **Project Level**: Agents belong to specific projects
2. **App Level**: `allowed_apps` restricts which integrations agents can use
3. **Function Level**: `custom_instructions` provide natural language guardrails

```python
# Example: Create agent with restricted access
agent_config = {
    "name": "GitHub Assistant",
    "description": "Handles GitHub operations for this project",
    "allowed_apps": ["GITHUB", "SLACK"],
    "custom_instructions": {
        "GITHUB__DELETE_REPOSITORY": "Never delete repositories in production organizations",
        "SLACK__POST_MESSAGE": "Only post to channels starting with 'dev-'"
    }
}
```

### 2. Function Discovery & Execution Pattern

ACI uses a **three-step meta-function pattern** that allows AI agents to dynamically discover and execute functions:

#### Meta Functions

```python
# From backend/aci/server/agent/meta_functions.py

# 1. Search for relevant functions
ACI_SEARCH_FUNCTIONS_SCHEMA = {
    "name": "ACI_SEARCH_FUNCTIONS",
    "description": "Search for relevant executable functions based on intent",
    "parameters": {
        "intent": "Natural language description of what you're trying to accomplish",
        "limit": 20,  # Max functions to return
        "offset": 0   # Pagination offset
    }
}

# 2. Get complete function definition
ACI_GET_FUNCTION_DEFINITION_SCHEMA = {
    "name": "ACI_GET_FUNCTION_DEFINITION", 
    "parameters": {
        "function_name": "Exact function name from search results"
    }
}

# 3. Execute function with parameters
ACI_EXECUTE_FUNCTION_SCHEMA = {
    "name": "ACI_EXECUTE_FUNCTION",
    "parameters": {
        "function_name": "Function to execute",
        "function_arguments": {}  # Dictionary of parameters
    }
}
```

#### Discovery Flow Example

```python
# 1. Agent searches for functions
search_result = await agent.call_function("ACI_SEARCH_FUNCTIONS", {
    "intent": "I want to create a new GitHub repository",
    "limit": 5
})

# 2. Get detailed function definition
function_def = await agent.call_function("ACI_GET_FUNCTION_DEFINITION", {
    "function_name": "GITHUB__CREATE_REPOSITORY"
})

# 3. Execute with proper parameters
result = await agent.call_function("ACI_EXECUTE_FUNCTION", {
    "function_name": "GITHUB__CREATE_REPOSITORY",
    "function_arguments": {
        "name": "my-new-repo",
        "description": "A test repository",
        "private": True
    }
})
```

### 3. Semantic Search System

#### Embedding Generation

```python
# From backend/aci/common/embeddings.py
def generate_function_embedding(function: FunctionEmbeddingFields) -> list[float]:
    """Generate embeddings from function name, description, and parameters"""
    text_for_embedding = function.model_dump_json()
    return openai_client.embeddings.create(
        input=[text_for_embedding],
        model="text-embedding-3-small",
        dimensions=1536
    ).data[0].embedding

def generate_app_embedding(app: AppEmbeddingFields) -> list[float]:
    """Generate embeddings from app name, display_name, provider, description, categories"""
    text_for_embedding = app.model_dump_json()
    return generate_embedding(openai_client, embedding_model, dimensions, text_for_embedding)
```

#### Intent-to-Function Matching

The search system uses semantic similarity between user intent and function embeddings to surface relevant capabilities without overwhelming the LLM's context window.

### 4. Parameter Visibility System

Functions use a **visibility-based parameter schema** to control what AI agents see and must provide:

```json
{
  "parameters": {
    "properties": {
      "header": {
        "properties": {
          "authorization": {"type": "string"},
          "user-agent": {"type": "string", "default": "ACI::GITHUB"}
        },
        "visible": []  // Hidden from AI - auto-injected
      },
      "path": {
        "properties": {
          "owner": {"type": "string"},
          "repo": {"type": "string"}
        },
        "visible": ["owner", "repo"]  // AI must provide these
      },
      "body": {
        "properties": {
          "name": {"type": "string"},
          "description": {"type": "string"},
          "private": {"type": "boolean", "default": false}
        },
        "visible": ["name", "description", "private"]
      }
    }
  }
}
```

**Parameter Types:**
- **Visible + Required**: AI must provide (e.g., repository name)
- **Visible + Optional**: AI may provide (e.g., description)
- **Invisible + Required**: Auto-injected with defaults (e.g., auth headers)
- **Invisible + Optional**: Omitted unless defaults provided

## App Integration Architecture

### App Definition Structure

```json
// backend/apps/github/app.json
{
  "name": "GITHUB",
  "display_name": "GitHub", 
  "provider": "GitHub",
  "description": "GitHub API for repository management, PRs, issues, and more",
  "security_schemes": {
    "oauth2": {
      "location": "header",
      "name": "Authorization",
      "prefix": "Bearer",
      "client_id": "{{ AIPOLABS_GITHUB_APP_CLIENT_ID }}",
      "client_secret": "{{ AIPOLABS_GITHUB_APP_CLIENT_SECRET }}",
      "scope": "repo delete_repo admin:org gist user workflow",
      "authorize_url": "https://github.com/login/oauth/authorize",
      "access_token_url": "https://github.com/login/oauth/access_token"
    }
  },
  "categories": ["Dev Tools"],
  "visibility": "public",
  "active": true
}
```

### Function Definition Structure

```json
// backend/apps/github/functions.json
{
  "name": "GITHUB__CREATE_REPOSITORY",
  "description": "Create a new repository for the authenticated user",
  "tags": ["repository", "create"],
  "visibility": "public",
  "active": true,
  "protocol": "rest",
  "protocol_data": {
    "method": "POST",
    "path": "/user/repos",
    "server_url": "https://api.github.com"
  },
  "parameters": {
    // Parameter schema with visibility controls
  }
}
```

### Protocol Types

**REST Protocol**: Direct HTTP API calls
```json
{
  "protocol": "rest",
  "protocol_data": {
    "method": "GET|POST|PUT|DELETE",
    "path": "/api/endpoint/{param}",
    "server_url": "https://api.service.com"
  }
}
```

**Connector Protocol**: Custom Python logic
```json
{
  "protocol": "connector",
  "protocol_data": {}  // Routes to Python connector class
}
```

## Multi-Tenant Architecture

### Hierarchy

```
Organization
├── Projects (isolation boundary)
    ├── Agents (AI entities with API keys)
    ├── App Configurations (project-specific app instances)
    └── Linked Accounts (user credentials per app)
```

### Authentication Schemes

**OAuth2 Flow:**
```python
# From backend/aci/server/oauth2_manager.py
class OAuth2Manager:
    async def get_authorization_url(self, app_name: str, project_id: str) -> str:
        """Generate OAuth2 authorization URL for user"""
        
    async def handle_callback(self, code: str, state: str) -> LinkedAccount:
        """Exchange authorization code for access token"""
        
    async def refresh_access_token(self, linked_account: LinkedAccount) -> str:
        """Refresh expired access token"""
```

**API Key Authentication:**
```python
# Simple API key storage with encryption
linked_account = {
    "app_name": "OPENAI",
    "security_scheme": "api_key",
    "credentials": {
        "api_key": "encrypted_key_value"
    }
}
```

**No Auth:** For public APIs requiring no authentication.

## Prompt Engineering & Custom Instructions

### Agent Prompting System

```python
# From backend/aci/server/agent/prompt.py
def convert_to_openai_messages(messages: list[ClientMessage]) -> list[ChatCompletionMessageParam]:
    """Convert client messages to OpenAI format with tool invocations"""
    openai_messages = []
    
    for message in messages:
        if message.tool_invocations:
            # Handle function calls and results
            for ti in message.tool_invocations:
                openai_messages.append({
                    "type": "function_call",
                    "call_id": ti.tool_call_id,
                    "name": ti.tool_name,
                    "arguments": json.dumps(ti.args)
                })
                if ti.result:
                    openai_messages.append({
                        "type": "function_call_output", 
                        "call_id": ti.tool_call_id,
                        "output": json.dumps(ti.result)
                    })
        else:
            # Regular text message
            openai_messages.append({
                "role": message.role,
                "type": "message",
                "content": [{"type": "input_text", "text": message.content}]
            })
    
    return openai_messages
```

### Custom Instructions as Guardrails

Natural language boundaries for function execution:

```python
custom_instructions = {
    "GMAIL__SEND_EMAIL": "Don't send emails to people outside my organization",
    "BRAVE_SEARCH__WEB_SEARCH": "Only search for AI-related topics", 
    "GITHUB__DELETE_REPOSITORY": "Never delete repositories in production",
    "SLACK__POST_MESSAGE": "Only post to channels I'm a member of"
}
```

## Development Patterns

### Creating New App Integrations

#### 1. Define App Configuration

```json
// backend/apps/myapp/app.json
{
  "name": "MYAPP",
  "display_name": "My App",
  "provider": "MyApp Inc",
  "description": "Integration with My App service",
  "security_schemes": {
    "api_key": {
      "location": "header",
      "name": "X-API-Key"
    }
  },
  "categories": ["Productivity"],
  "visibility": "public", 
  "active": true
}
```

#### 2. Define Functions

```json
// backend/apps/myapp/functions.json
[
  {
    "name": "MYAPP__GET_USER_DATA",
    "description": "Retrieve user data from My App",
    "protocol": "rest",
    "protocol_data": {
      "method": "GET",
      "path": "/api/users/{user_id}",
      "server_url": "https://api.myapp.com"
    },
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "type": "object",
          "properties": {
            "user_id": {"type": "string"}
          },
          "visible": ["user_id"],
          "required": ["user_id"]
        }
      }
    }
  }
]
```

#### 3. Using CLI Tools

```bash
# Upsert app configuration
python -m aci.cli upsert-app backend/apps/myapp/app.json

# Upsert functions 
python -m aci.cli upsert-functions backend/apps/myapp/functions.json

# Test function execution
python -m aci.cli fuzzy-test-function-execution MYAPP__GET_USER_DATA
```

### Custom Connector Development

For complex integrations requiring custom logic:

```python
# backend/aci/server/app_connectors/myapp.py
from .base import BaseAppConnector

class MyAppConnector(BaseAppConnector):
    async def execute_function(
        self,
        function_name: str,
        function_arguments: dict,
        linked_account: LinkedAccount
    ) -> dict:
        """Custom execution logic for MyApp functions"""
        if function_name == "MYAPP__COMPLEX_OPERATION":
            # Custom logic here
            return await self._handle_complex_operation(function_arguments)
        
        # Fall back to standard REST execution
        return await super().execute_function(
            function_name, function_arguments, linked_account
        )
```

## Testing & Evaluation

### Synthetic Intent Generation

```python
# From backend/evals/synthetic_intent_generator.py
class SyntheticIntentGenerator:
    def generate_intents_for_function(self, function: Function) -> list[str]:
        """Generate realistic user intents for testing function discovery"""
        prompt = f"""
        Generate 5 realistic user intents that would require calling this function:
        Function: {function.name}
        Description: {function.description}
        
        Return natural language requests a user might make.
        """
        return self.llm.generate(prompt)
```

### Function Search Evaluation

```python
# From backend/evals/search_evaluator.py
class SearchEvaluator:
    def evaluate_search_accuracy(self, test_cases: list[TestCase]) -> dict:
        """Evaluate search performance with metrics"""
        results = {
            "accuracy": 0.0,           # Top-1 correct function
            "mrr": 0.0,               # Mean Reciprocal Rank
            "top_5_accuracy": 0.0,     # Success in top 5 results
            "avg_response_time": 0.0   # Performance metric
        }
        
        for test_case in test_cases:
            search_results = self.search_functions(test_case.intent)
            # Calculate metrics...
            
        return results
```

### Integration Testing

```python
# backend/aci/server/tests/routes/functions/test_functions_execute.py
async def test_function_execution_with_oauth2():
    """Test complete function execution flow"""
    # 1. Create linked account with OAuth2
    linked_account = await create_oauth2_linked_account()
    
    # 2. Execute function
    response = await client.post("/functions/execute", json={
        "function_name": "GITHUB__LIST_REPOSITORIES",
        "function_arguments": {"visibility": "public"}
    })
    
    # 3. Verify results
    assert response.status_code == 200
    assert "repositories" in response.json()
```

## Advanced Patterns

### Multi-Agent Coordination

```python
# Example: Multi-agent workflow
class DevOpsOrchestrator:
    def __init__(self):
        self.github_agent = Agent(
            name="GitHub Agent",
            allowed_apps=["GITHUB"]
        )
        self.slack_agent = Agent(
            name="Slack Agent", 
            allowed_apps=["SLACK"]
        )
    
    async def deploy_and_notify(self, repo_name: str):
        # Agent 1: Create GitHub release
        release = await self.github_agent.execute("GITHUB__CREATE_RELEASE", {
            "owner": "myorg",
            "repo": repo_name,
            "tag_name": "v1.0.0"
        })
        
        # Agent 2: Notify team via Slack
        await self.slack_agent.execute("SLACK__POST_MESSAGE", {
            "channel": "#deployments",
            "text": f"🚀 Released {repo_name} v1.0.0: {release['html_url']}"
        })
```

### Context-Aware Function Selection

```python
class ContextAwareAgent:
    def __init__(self):
        self.conversation_history = []
        self.user_preferences = {}
    
    async def process_request(self, user_input: str):
        # Enhance search with context
        context = self._build_context()
        enhanced_intent = f"{user_input}\n\nContext: {context}"
        
        # Search with enhanced intent
        functions = await self.search_functions(enhanced_intent)
        
        # Execute with preference-aware parameter selection
        return await self._execute_with_preferences(functions[0])
```

### Function Chaining Workflows

```python
class WorkflowEngine:
    async def execute_workflow(self, steps: list[WorkflowStep]):
        """Execute multi-step workflows with dependency management"""
        results = {}
        
        for step in steps:
            # Use previous step results as inputs
            enhanced_args = self._merge_args(step.args, results)
            
            result = await self.execute_function(
                step.function_name,
                enhanced_args
            )
            
            results[step.output_key] = result
            
        return results

# Example workflow
workflow = [
    WorkflowStep(
        function_name="GITHUB__SEARCH_REPOSITORIES",
        args={"q": "python web framework"},
        output_key="search_results"
    ),
    WorkflowStep(
        function_name="GITHUB__GET_REPOSITORY", 
        args={"owner": "{{search_results.items[0].owner.login}}", 
              "repo": "{{search_results.items[0].name}}"},
        output_key="repo_details"
    )
]
```

## Performance Optimization

### Embedding Caching Strategy

```python
# Cache function embeddings for faster search
@lru_cache(maxsize=10000)
def get_function_embedding(function_signature: str) -> list[float]:
    return generate_function_embedding(function_signature)

# Batch embedding generation
async def batch_generate_embeddings(functions: list[Function]):
    """Generate embeddings in batches for efficiency"""
    batch_size = 100
    for i in range(0, len(functions), batch_size):
        batch = functions[i:i + batch_size]
        embeddings = await generate_embeddings_batch(batch)
        await store_embeddings(batch, embeddings)
```

### Search Index Optimization

```python
class OptimizedSearchIndex:
    def __init__(self):
        self.vector_index = {}  # Function embeddings
        self.keyword_index = {}  # Text-based search fallback
    
    def hybrid_search(self, intent: str, limit: int = 20) -> list[Function]:
        """Combine semantic and keyword search for better results"""
        # 1. Semantic search via embeddings
        semantic_results = self.semantic_search(intent, limit * 2)
        
        # 2. Keyword search for exact matches
        keyword_results = self.keyword_search(intent, limit)
        
        # 3. Merge and rank results
        return self.merge_and_rank(semantic_results, keyword_results, limit)
```

### Rate Limiting & Quota Management

```python
# From backend/aci/server/quota_manager.py
class QuotaManager:
    async def check_quota(self, project_id: str, function_name: str) -> bool:
        """Check if project has quota remaining for function execution"""
        
    async def consume_quota(self, project_id: str, tokens_used: int):
        """Deduct tokens from project quota"""
        
    async def get_quota_status(self, project_id: str) -> QuotaStatus:
        """Get current quota usage and limits"""
```

## Security Best Practices

### Credential Encryption

```python
# From backend/aci/common/encryption.py
class CredentialEncryption:
    @staticmethod
    def encrypt_credentials(credentials: dict, key: str) -> str:
        """Encrypt sensitive credential data"""
        
    @staticmethod 
    def decrypt_credentials(encrypted_data: str, key: str) -> dict:
        """Decrypt credentials for function execution"""
```

### Access Control Lists (ACL)

```python
# From backend/aci/server/acl.py
class ACLManager:
    def check_function_access(
        self, 
        agent: Agent, 
        function_name: str,
        project_id: str
    ) -> bool:
        """Verify agent has permission to execute function"""
        # 1. Check app-level permissions
        app_name = function_name.split("__")[0]
        if app_name not in agent.allowed_apps:
            return False
            
        # 2. Check custom instructions
        if function_name in agent.custom_instructions:
            # Apply natural language constraints
            return self._evaluate_custom_instruction(
                agent.custom_instructions[function_name]
            )
            
        return True
```

### Audit Logging

```python
class AuditLogger:
    def log_function_execution(
        self,
        agent_id: str,
        function_name: str, 
        arguments: dict,
        result: dict,
        execution_time: float
    ):
        """Log all function executions for audit trail"""
        log_entry = {
            "timestamp": datetime.utcnow(),
            "agent_id": agent_id,
            "function_name": function_name,
            "arguments": self._sanitize_sensitive_data(arguments),
            "success": result.get("success", False),
            "execution_time_ms": execution_time * 1000,
            "tokens_used": result.get("tokens_used", 0)
        }
        self.audit_log.info(json.dumps(log_entry))
```

## Monitoring & Analytics

### Function Usage Analytics

```python
# From backend/aci/server/routes/analytics.py
class AnalyticsManager:
    def track_function_usage(
        self,
        project_id: str,
        function_name: str,
        success: bool,
        execution_time: float
    ):
        """Track function usage metrics"""
        
    def get_popular_functions(self, project_id: str) -> list[dict]:
        """Get most frequently used functions"""
        
    def get_performance_metrics(self, function_name: str) -> dict:
        """Get performance metrics for specific function"""
        return {
            "avg_execution_time": 0.0,
            "success_rate": 0.0,
            "total_executions": 0
        }
```

### Error Tracking

```python
# Integration with Sentry for error monitoring
# From backend/aci/server/sentry.py
import sentry_sdk

def track_function_error(function_name: str, error: Exception, context: dict):
    """Track function execution errors"""
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("function_name", function_name)
        scope.set_context("function_context", context)
        sentry_sdk.capture_exception(error)
```

## Troubleshooting Guide

### Common Issues

**1. Function Not Found in Search**
```python
# Debug search results
search_results = await agent.search_functions("create github repository")
if not search_results:
    # Check if app is enabled and agent has access
    app_config = await get_app_config("GITHUB", project_id)
    agent_permissions = await get_agent_permissions(agent_id)
```

**2. Authentication Failures**
```python
# Debug OAuth2 token issues
try:
    result = await execute_function(function_name, args)
except AuthenticationError as e:
    # Check token expiration and refresh
    if "expired" in str(e):
        await refresh_oauth2_token(linked_account_id)
        result = await execute_function(function_name, args)
```

**3. Parameter Validation Errors**
```python
# Debug parameter schema mismatches
function_def = await get_function_definition("GITHUB__CREATE_REPOSITORY")
required_params = extract_required_params(function_def.parameters)
provided_params = set(function_arguments.keys())
missing_params = required_params - provided_params
```

### Debug Mode

```python
# Enable detailed logging for debugging
import logging
logging.getLogger("aci.server.function_executors").setLevel(logging.DEBUG)
logging.getLogger("aci.common.embeddings").setLevel(logging.DEBUG)
```

### Performance Debugging

```python
class PerformanceProfiler:
    def profile_function_execution(self, function_name: str):
        """Profile function execution performance"""
        with self.timer(f"execute_{function_name}"):
            # Time each phase
            with self.timer("search_phase"):
                functions = self.search_functions(intent)
            
            with self.timer("definition_phase"):
                definition = self.get_function_definition(function_name)
                
            with self.timer("execution_phase"):
                result = self.execute_function(function_name, args)
                
        return self.get_timing_report()
```

## Framework Integration Examples

### LangChain Integration

```python
from langchain.tools import BaseTool
from aci import ACIClient

class ACITool(BaseTool):
    def __init__(self, aci_client: ACIClient, function_name: str):
        self.aci_client = aci_client
        self.function_name = function_name
        
        # Get function definition for tool metadata
        definition = aci_client.get_function_definition(function_name)
        self.name = function_name
        self.description = definition["description"]
    
    def _run(self, **kwargs):
        return self.aci_client.execute_function(self.function_name, kwargs)

# Usage in LangChain agent
tools = [
    ACITool(aci_client, "GITHUB__CREATE_REPOSITORY"),
    ACITool(aci_client, "SLACK__POST_MESSAGE")
]
agent = create_langchain_agent(llm, tools)
```

### AutoGen Integration

```python
import autogen
from aci import ACIClient

class ACIFunctionAgent(autogen.AssistantAgent):
    def __init__(self, aci_client: ACIClient, **kwargs):
        super().__init__(**kwargs)
        self.aci_client = aci_client
        
        # Register ACI functions as tools
        self.register_function(
            function_map={
                "search_functions": self.aci_client.search_functions,
                "execute_function": self.aci_client.execute_function
            }
        )

# Create multi-agent conversation
github_agent = ACIFunctionAgent(
    aci_client=aci_client,
    name="GitHub_Agent",
    system_message="You handle GitHub operations using ACI functions"
)
```

### MCP Server Integration

```python
# ACI provides a unified MCP server for agentic IDEs
# Configure in your IDE (Cursor, Cline, etc.)
{
  "mcpServers": {
    "aci": {
      "command": "npx",
      "args": ["@aipolabs/aci-mcp-server"],
      "env": {
        "ACI_API_KEY": "your-api-key",
        "ACI_PROJECT_ID": "your-project-id"
      }
    }
  }
}
```

## CLI Reference

### Development Commands

```bash
# Create new project
python -m aci.cli create-project "My AI Project"

# Create agent with specific permissions
python -m aci.cli create-agent \
  --name "GitHub Bot" \
  --allowed-apps GITHUB,SLACK \
  --custom-instructions "GITHUB__DELETE_REPOSITORY:Never delete production repos"

# Upsert app configuration
python -m aci.cli upsert-app backend/apps/myapp/app.json

# Upsert functions for an app
python -m aci.cli upsert-functions backend/apps/myapp/functions.json

# Test function execution
python -m aci.cli fuzzy-test-function-execution GITHUB__CREATE_REPOSITORY

# Generate random API key for testing
python -m aci.cli create-random-api-key
```

## Environment Configuration

### Required Environment Variables

```bash
# Core configuration
ACI_DATABASE_URL=postgresql://user:pass@localhost/aci
ACI_SECRET_KEY=your-secret-key
ACI_ENVIRONMENT=development|staging|production

# OpenAI integration (for embeddings and LLM)
OPENAI_API_KEY=your-openai-api-key

# OAuth2 app credentials (for integrations)
AIPOLABS_GITHUB_APP_CLIENT_ID=your-github-client-id
AIPOLABS_GITHUB_APP_CLIENT_SECRET=your-github-client-secret
AIPOLABS_GOOGLE_CLIENT_ID=your-google-client-id
AIPOLABS_GOOGLE_CLIENT_SECRET=your-google-client-secret

# Encryption key for sensitive data
ACI_ENCRYPTION_KEY=your-encryption-key

# Optional: Sentry for error tracking
SENTRY_DSN=your-sentry-dsn
```

### Development Setup

```bash
# 1. Clone and setup
git clone https://github.com/aipotheosis-labs/aci.git
cd aci

# 2. Backend setup
cd backend
uv sync
uv run alembic upgrade head

# 3. Frontend setup  
cd ../frontend
npm install
npm run build

# 4. Run development stack
docker-compose up -d  # Database and services
uv run python -m aci.server  # Backend server
npm run dev  # Frontend (in separate terminal)
```

## API Reference

### Core Endpoints

**Function Search**
```http
POST /functions/search
Content-Type: application/json

{
  "intent": "create a new github repository",
  "limit": 10,
  "offset": 0
}
```

**Function Definition**
```http
GET /functions/{function_name}/definition
```

**Function Execution**
```http
POST /functions/execute
Content-Type: application/json

{
  "function_name": "GITHUB__CREATE_REPOSITORY",
  "function_arguments": {
    "name": "my-repo",
    "description": "Test repository",
    "private": true
  }
}
```

**Agent Management**
```http
POST /agents
Content-Type: application/json

{
  "name": "My Agent",
  "description": "Description of agent capabilities",
  "allowed_apps": ["GITHUB", "SLACK"],
  "custom_instructions": {}
}
```

### SDK Usage

```python
from aci import ACIClient

# Initialize client
client = ACIClient(
    api_key="your-api-key",
    base_url="https://api.aci.dev"
)

# Search and execute functions
functions = await client.search_functions("send slack message")
result = await client.execute_function(
    "SLACK__POST_MESSAGE",
    {"channel": "#general", "text": "Hello from ACI!"}
)

# Agent management
agent = await client.create_agent(
    name="Slack Bot",
    allowed_apps=["SLACK"],
    custom_instructions={
        "SLACK__POST_MESSAGE": "Only post to channels I'm a member of"
    }
)
```

## Contributing to ACI

### Adding New Integrations

1. **Create app definition** in `backend/apps/{app_name}/app.json`
2. **Define functions** in `backend/apps/{app_name}/functions.json` 
3. **Test integration** using CLI tools
4. **Submit PR** with integration tests

### Custom Connector Development

For complex integrations requiring custom logic, implement a connector:

```python
# backend/aci/server/app_connectors/myapp.py
from .base import BaseAppConnector

class MyAppConnector(BaseAppConnector):
    async def execute_function(self, function_name: str, args: dict, account: LinkedAccount):
        # Custom execution logic
        pass
```

## Resources

- **Platform**: https://aci.dev
- **Documentation**: https://docs.aci.dev  
- **GitHub Repository**: https://github.com/aipotheosis-labs/aci
- **Developer Discord**: https://discord.gg/aci-dev
- **MCP Server**: https://github.com/aipotheosis-labs/aci-mcp-server
- **Examples**: https://github.com/aipotheosis-labs/aci/tree/main/examples

---

*This guide covers the comprehensive AI integration patterns and architecture of the ACI platform. For specific implementation details, refer to the codebase and API documentation.*