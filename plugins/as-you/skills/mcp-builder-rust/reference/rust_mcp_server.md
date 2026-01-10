# Rust MCP Server Implementation Guide

This guide covers Rust-specific patterns and best practices for building MCP servers using the rmcp SDK.

## Table of Contents

1. [Project Setup](#project-setup)
2. [Dependencies](#dependencies)
3. [Transport Options](#transport-options)
4. [Server Architecture](#server-architecture)
5. [Implementing Tools](#implementing-tools)
6. [Implementing Resources](#implementing-resources)
7. [Implementing Prompts](#implementing-prompts)
8. [Error Handling](#error-handling)
9. [rmcp-macros](#rmcp-macros)
10. [Advanced Features](#advanced-features)
   - [HTTP Transport (Streamable HTTP)](#http-transport-streamable-http)
   - [Elicitation](#elicitation)
   - [Progress Notifications](#progress-notifications)
   - [Sampling (LLM Calls)](#sampling-llm-calls)
11. [Testing](#testing)
12. [Complete Examples](#complete-examples)
13. [Quality Checklist](#quality-checklist)

---

## Project Setup

### Initialize a New Project

```bash
cargo new my-mcp-server
cd my-mcp-server
```

### Project Structure

```
my-mcp-server/
├── Cargo.toml
├── src/
│   ├── main.rs          # Server entry point
│   ├── lib.rs           # Library root (optional)
│   ├── server.rs        # Server implementation with ServerHandler trait
│   ├── tools/           # Tool implementations
│   │   ├── mod.rs
│   │   ├── github.rs
│   │   └── utils.rs
│   ├── models.rs        # Data models with serde + schemars
│   └── error.rs         # Error types
├── tests/               # Integration tests
│   └── integration_test.rs
└── README.md
```

---

## Dependencies

### Cargo.toml

```toml
[package]
name = "my-mcp-server"
version = "0.1.0"
edition = "2021"

[dependencies]
# MCP SDK
rmcp = { version = "0.8", features = ["server"] }

# Async runtime
tokio = { version = "1", features = ["full"] }

# Serialization
serde = { version = "1", features = ["derive"] }
serde_json = "1"

# JSON Schema generation
schemars = { version = "0.8", features = ["preserve_order"] }

# Error handling
thiserror = "1"
anyhow = "1"

# HTTP client (if needed)
reqwest = { version = "0.12", features = ["json"] }

# Logging
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }

[dev-dependencies]
tokio-test = "0.4"
```

### Feature Flags

- `rmcp` with `server` feature: Enables server-side MCP functionality
- `tokio` with `full`: Enables all tokio features (use specific features for production)
- `schemars` with `preserve_order`: Maintains field order in JSON schemas

### Additional Dependencies for HTTP Transport

If you need HTTP transport (for remote servers), add:

```toml
# For HTTP transport
axum = "0.7"
tokio-util = "0.7"
```

---

## Transport Options

MCP servers support two transport mechanisms. **Unless specified otherwise, use stdio transport** (standard input/output) for local development and simple integrations.

### stdio Transport (Default, Recommended)

**Use for:**
- Local development and testing
- IDE integrations
- Desktop application integrations
- Claude Desktop integration
- Simple command-line tools
- Single-user scenarios

**Characteristics:**
- Process-to-process communication
- Parent process spawns server as child
- 1-to-1 connection (one client per server instance)
- No network configuration needed
- Simple setup

**Example:**
```rust
use rmcp::{ServiceExt, transport::stdio};
use tokio::io::{stdin, stdout};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let server = MyServer::new();
    let transport = (stdin(), stdout());
    let connection = server.serve(transport).await?;
    connection.waiting().await?;
    Ok(())
}
```

### HTTP Transport (Streamable HTTP)

**Use for:**
- Production deployments
- Remote server access
- Multi-client scenarios
- Web service integrations
- Cloud hosting (Docker, Kubernetes)
- Enterprise environments requiring authentication

**Characteristics:**
- Network communication (HTTP/HTTPS)
- Multiple concurrent clients
- Session management required
- Scalable and load-balancable
- Requires additional configuration

**When to choose HTTP:**
- You need remote access over a network
- Multiple clients need to connect simultaneously
- You're deploying to production/cloud
- You need authentication and security features
- You need to scale horizontally

See [HTTP Transport (Streamable HTTP)](#http-transport-streamable-http) section for implementation details.

### Comparison

| Feature | stdio | HTTP |
|---------|-------|------|
| Setup Complexity | Simple | Moderate |
| Network Access | Local only | Remote capable |
| Client Count | Single | Multiple |
| Authentication | Not needed | Required |
| Scalability | Not scalable | Horizontally scalable |
| Use Case | Development, local tools | Production, web services |

**Default Choice: Use stdio unless you have a specific reason to use HTTP.**

---

## Server Architecture

### Basic Server Structure

```rust
// src/server.rs
use rmcp::{
    ErrorData as McpError,
    RoleServer,
    ServerHandler,
    handler::server::{
        router::{tool::ToolRouter, prompt::PromptRouter},
        wrapper::Parameters,
    },
    model::*,
    service::RequestContext,
    tool, tool_router, tool_handler,
    prompt, prompt_router, prompt_handler,
};
use std::sync::Arc;
use tokio::sync::Mutex;

#[derive(Clone)]
pub struct MyServer {
    // Shared state (use Arc<Mutex<T>> for mutable state)
    state: Arc<Mutex<ServerState>>,
    // Tool router (generated by macro)
    tool_router: ToolRouter<MyServer>,
    // Prompt router (generated by macro)
    prompt_router: PromptRouter<MyServer>,
}

#[derive(Default)]
struct ServerState {
    // Your server's state
    counter: i32,
}

impl MyServer {
    pub fn new() -> Self {
        Self {
            state: Arc::new(Mutex::new(ServerState::default())),
            tool_router: Self::tool_router(),
            prompt_router: Self::prompt_router(),
        }
    }
}
```

### ServerHandler Trait Implementation

```rust
#[tool_handler]
#[prompt_handler]
impl ServerHandler for MyServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo {
            protocol_version: ProtocolVersion::V_2024_11_05,
            capabilities: ServerCapabilities::builder()
                .enable_tools()
                .enable_prompts()
                .enable_resources()
                .build(),
            server_info: Implementation::from_build_env(),
            instructions: Some(
                "This MCP server provides tools for...".to_string()
            ),
        }
    }

    async fn initialize(
        &self,
        _request: InitializeRequestParam,
        _context: RequestContext<RoleServer>,
    ) -> Result<InitializeResult, McpError> {
        Ok(self.get_info())
    }

    // Implement other required methods...
}
```

---

## Implementing Tools

### Define Tool Input Schema

```rust
// src/models.rs
use serde::{Deserialize, Serialize};
use schemars::JsonSchema;

#[derive(Debug, Deserialize, JsonSchema)]
pub struct CreateIssueParams {
    /// Repository name (e.g., "owner/repo")
    pub repository: String,

    /// Issue title
    pub title: String,

    /// Issue body/description
    #[serde(skip_serializing_if = "Option::is_none")]
    pub body: Option<String>,

    /// Labels to add to the issue
    #[serde(default)]
    pub labels: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize, JsonSchema)]
pub struct IssueResponse {
    /// Issue number
    pub number: u64,

    /// Issue URL
    pub url: String,

    /// Issue state (open/closed)
    pub state: String,
}
```

### Implement Tool with Macro

```rust
// src/server.rs
#[tool_router]
impl MyServer {
    /// Create a new GitHub issue
    #[tool(
        description = "Create a new issue in a GitHub repository",
        annotations(
            readOnlyHint = false,
            destructiveHint = false,
            idempotentHint = false
        )
    )]
    async fn github_create_issue(
        &self,
        Parameters(params): Parameters<CreateIssueParams>,
    ) -> Result<CallToolResult, McpError> {
        // Validate input
        if params.title.is_empty() {
            return Err(McpError::invalid_params(
                "Title cannot be empty",
                None,
            ));
        }

        // Call GitHub API (example)
        let response = self.create_issue_api_call(params).await?;

        // Return structured result
        Ok(CallToolResult::success(vec![
            Content::text(format!("Created issue #{}", response.number)),
            Content::json(serde_json::to_value(response)?),
        ]))
    }

    /// List issues in a repository
    #[tool(
        description = "List issues in a GitHub repository with pagination",
        annotations(
            readOnlyHint = true,
            openWorldHint = true
        )
    )]
    async fn github_list_issues(
        &self,
        Parameters(params): Parameters<ListIssuesParams>,
    ) -> Result<CallToolResult, McpError> {
        let issues = self.list_issues_api_call(params).await?;

        Ok(CallToolResult::success(vec![
            Content::text(format!("Found {} issues", issues.len())),
            Content::json(serde_json::to_value(issues)?),
        ]))
    }
}
```

### Tool Best Practices

1. **Naming**: Use `{service}_{action}_{resource}` pattern (e.g., `github_create_issue`)
2. **Parameters**: Use strongly-typed structs with `Deserialize` and `JsonSchema`
3. **Documentation**: Add doc comments (///); they become tool descriptions
4. **Validation**: Validate inputs early and return clear error messages
5. **Results**: Return both human-readable text and structured JSON data
6. **Async**: Use `async fn` for I/O operations
7. **Annotations**: Add hints for tool behavior (readOnly, destructive, etc.)

---

## Implementing Resources

Resources provide access to data or content that LLMs can read.

```rust
#[tool_handler]
#[prompt_handler]
impl ServerHandler for MyServer {
    async fn list_resources(
        &self,
        request: Option<PaginatedRequestParam>,
        _context: RequestContext<RoleServer>,
    ) -> Result<ListResourcesResult, McpError> {
        let resources = vec![
            RawResource::new(
                "file:///path/to/config.json",
                "Configuration".to_string(),
            )
            .with_description("Server configuration file")
            .no_annotation(),

            RawResource::new(
                "memo://insights",
                "Business Insights".to_string(),
            )
            .with_mime_type("text/markdown")
            .no_annotation(),
        ];

        Ok(ListResourcesResult {
            resources,
            next_cursor: None,
            meta: None,
        })
    }

    async fn read_resource(
        &self,
        ReadResourceRequestParam { uri }: ReadResourceRequestParam,
        _context: RequestContext<RoleServer>,
    ) -> Result<ReadResourceResult, McpError> {
        match uri.as_str() {
            "file:///path/to/config.json" => {
                let content = std::fs::read_to_string("/path/to/config.json")
                    .map_err(|e| McpError::internal_error(e.to_string(), None))?;

                Ok(ReadResourceResult {
                    contents: vec![ResourceContents::text(content, uri)],
                })
            }
            "memo://insights" => {
                let markdown = "# Business Insights\n\n...";
                Ok(ReadResourceResult {
                    contents: vec![ResourceContents::text(markdown, uri)],
                })
            }
            _ => Err(McpError::resource_not_found(
                "Resource not found",
                Some(serde_json::json!({ "uri": uri })),
            )),
        }
    }
}
```

---

## Implementing Prompts

Prompts provide reusable prompt templates for LLMs.

```rust
// src/models.rs
#[derive(Debug, Deserialize, JsonSchema)]
pub struct CodeReviewPromptArgs {
    /// Code to review
    pub code: String,

    /// Programming language
    pub language: String,

    /// Focus areas (e.g., "security", "performance")
    #[serde(default)]
    pub focus: Vec<String>,
}

// src/server.rs
#[prompt_router]
impl MyServer {
    /// Generate a code review prompt
    #[prompt(
        name = "code_review",
        description = "Generate a prompt for code review"
    )]
    async fn code_review_prompt(
        &self,
        Parameters(args): Parameters<CodeReviewPromptArgs>,
        _context: RequestContext<RoleServer>,
    ) -> Result<GetPromptResult, McpError> {
        let focus_text = if args.focus.is_empty() {
            "general code quality".to_string()
        } else {
            args.focus.join(", ")
        };

        let messages = vec![
            PromptMessage::new_text(
                PromptMessageRole::User,
                format!(
                    "Please review the following {} code with focus on: {}\n\n```{}\n{}\n```",
                    args.language,
                    focus_text,
                    args.language,
                    args.code
                ),
            ),
        ];

        Ok(GetPromptResult {
            description: Some(format!(
                "Code review for {} code",
                args.language
            )),
            messages,
        })
    }
}
```

---

## Error Handling

### Custom Error Types

```rust
// src/error.rs
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ServerError {
    #[error("GitHub API error: {0}")]
    GitHubApi(String),

    #[error("Invalid parameter: {0}")]
    InvalidParam(String),

    #[error("Resource not found: {0}")]
    NotFound(String),

    #[error("Authentication failed: {0}")]
    AuthFailed(String),
}

impl From<ServerError> for rmcp::ErrorData {
    fn from(err: ServerError) -> Self {
        use rmcp::model::ErrorCode;

        match err {
            ServerError::InvalidParam(msg) => {
                rmcp::ErrorData::new(ErrorCode::InvalidParams, msg, None)
            }
            ServerError::NotFound(msg) => {
                rmcp::ErrorData::new(ErrorCode::Custom(-32001), msg, None)
            }
            ServerError::AuthFailed(msg) => {
                rmcp::ErrorData::new(ErrorCode::Custom(-32002), msg, None)
            }
            ServerError::GitHubApi(msg) => {
                rmcp::ErrorData::new(ErrorCode::InternalError, msg, None)
            }
        }
    }
}
```

### Error Handling Patterns

```rust
async fn github_create_issue(
    &self,
    Parameters(params): Parameters<CreateIssueParams>,
) -> Result<CallToolResult, McpError> {
    // Validate early
    if params.title.is_empty() {
        return Err(McpError::invalid_params(
            "Title cannot be empty",
            Some(serde_json::json!({
                "field": "title",
                "suggestion": "Provide a non-empty title"
            })),
        ));
    }

    // API call with proper error handling
    let response = self.api_client
        .create_issue(&params.repository, &params.title, params.body.as_deref())
        .await
        .map_err(|e| McpError::internal_error(
            format!("GitHub API error: {}", e),
            Some(serde_json::json!({
                "repository": params.repository,
                "error": e.to_string()
            })),
        ))?;

    Ok(CallToolResult::success(vec![
        Content::text(format!("Created issue #{}", response.number))
    ]))
}
```

---

## rmcp-macros

rmcp-macros provides procedural macros that significantly simplify MCP server development. These macros handle boilerplate code generation, automatic JSON schema creation, and routing infrastructure.

### Key Macros

**Tool Macros**:
- `#[tool]` - Mark a function as an MCP tool with automatic metadata generation
- `#[tool_router]` - Generate a router from all `#[tool]`-marked functions
- `#[tool_handler]` - Auto-implement `call_tool` and `list_tools` for `ServerHandler`

**Prompt Macros**:
- `#[prompt]` - Mark a function as a prompt generator
- `#[prompt_router]` - Generate a router from all `#[prompt]`-marked functions
- `#[prompt_handler]` - Auto-implement `get_prompt` and `list_prompts` for `ServerHandler`

### Quick Example

```rust
use rmcp::{tool, tool_router, tool_handler};

#[derive(Clone)]
struct MyServer {
    tool_router: ToolRouter<MyServer>,
}

#[tool_router]
impl MyServer {
    pub fn new() -> Self {
        Self {
            tool_router: Self::tool_router(),  // Generated by macro
        }
    }

    /// Add two numbers
    #[tool(annotations(readOnlyHint = true))]
    async fn add(
        &self,
        Parameters(params): Parameters<AddParams>,
    ) -> Result<CallToolResult, McpError> {
        let result = params.a + params.b;
        Ok(CallToolResult::success(vec![
            Content::text(format!("{} + {} = {}", params.a, params.b, result))
        ]))
    }
}

#[tool_handler]
impl ServerHandler for MyServer {
    fn get_info(&self) -> ServerInfo {
        // ...
    }
    // call_tool and list_tools are auto-generated!
}
```

### Benefits

1. **Reduced Boilerplate**: Eliminates manual tool registration and routing
2. **Type Safety**: Automatic JSON schema generation from Rust types
3. **Doc Comments**: Function doc comments become tool descriptions
4. **Annotations**: Built-in support for readOnly, destructive, idempotent hints
5. **Modular Design**: Combine multiple routers easily

### Learn More

For comprehensive documentation, examples, and best practices:
- [📖 rmcp-macros Complete Guide](./rmcp_macros.md)
- [🚀 Macros Demo Server Example](../examples/macros_demo_server/)

---

## Advanced Features

This section covers advanced MCP features that extend basic server functionality. These features are optional and should be used when specific requirements demand them.

### HTTP Transport (Streamable HTTP)

HTTP transport enables remote server access and multi-client scenarios. Use this when you need to deploy your MCP server as a network service.

#### Dependencies

Add to your `Cargo.toml`:

```toml
[dependencies]
axum = "0.7"
tokio-util = "0.7"
```

#### Basic HTTP Server Setup

```rust
use rmcp::transport::streamable_http_server::{
    StreamableHttpService,
    StreamableHttpServerConfig,
    session::local::LocalSessionManager,
};
use tokio_util::sync::CancellationToken;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let ct = CancellationToken::new();

    // Create HTTP service
    let service = StreamableHttpService::new(
        || Ok(MyServer::new()),                    // Factory function
        LocalSessionManager::default().into(),     // Session manager
        StreamableHttpServerConfig {
            cancellation_token: ct.child_token(),
            ..Default::default()
        },
    );

    // Setup router
    let router = axum::Router::new()
        .nest_service("/mcp", service);

    // Bind and serve
    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await?;

    tracing::info!("HTTP server listening on http://0.0.0.0:3000/mcp");

    axum::serve(listener, router)
        .with_graceful_shutdown(async move {
            tokio::signal::ctrl_c().await.unwrap();
            ct.cancel();
        })
        .await?;

    Ok(())
}
```

#### Key Components

**Factory Function:**
```rust
|| Ok(MyServer::new())
```
- Creates a new server instance for each session
- Enables independent state per client
- Must return `Result<ServerType, Error>`

**Session Manager:**
```rust
LocalSessionManager::default().into()
```
- Manages client sessions
- Maintains state across HTTP requests
- `LocalSessionManager` stores sessions in memory
- For production, consider distributed session storage

**Cancellation Token:**
```rust
CancellationToken::new()
```
- Enables graceful shutdown
- Propagates cancellation to all services
- Use `Ctrl+C` handler for shutdown signal

#### Configuration Options

```rust
StreamableHttpServerConfig {
    cancellation_token: ct.child_token(),
    // Optional: customize behavior
    ..Default::default()
}
```

#### Testing HTTP Server

```bash
# Start server
cargo run

# Test with curl
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
```

#### Production Considerations

1. **HTTPS**: Use reverse proxy (nginx, Traefik) for TLS
2. **Authentication**: Implement middleware for token validation
3. **Rate Limiting**: Protect against abuse
4. **Monitoring**: Add metrics and health checks
5. **Load Balancing**: Use session-aware load balancer

**Example with Authentication:**

```rust
use axum::{
    middleware,
    http::{Request, StatusCode},
    response::Response,
};

async fn auth_middleware<B>(
    request: Request<B>,
    next: axum::middleware::Next<B>,
) -> Result<Response, StatusCode> {
    let token = request
        .headers()
        .get("Authorization")
        .and_then(|v| v.to_str().ok())
        .and_then(|v| v.strip_prefix("Bearer "));

    match token {
        Some(token) if validate_token(token) => {
            Ok(next.run(request).await)
        }
        _ => Err(StatusCode::UNAUTHORIZED),
    }
}

// Apply middleware
let router = axum::Router::new()
    .nest_service("/mcp", service)
    .layer(middleware::from_fn(auth_middleware));
```

See `examples/http_server/` for a complete HTTP server implementation.

---

### Elicitation

Elicitation allows your server to request additional information from the user interactively during tool execution.

#### Use Cases

- Collecting user credentials
- Requesting confirmation for destructive operations
- Gathering missing parameters
- Interactive workflows

#### Implementation

**1. Define the elicitation schema:**

```rust
use serde::{Deserialize, Serialize};
use rmcp::{schemars::JsonSchema, elicit_safe};

#[derive(Debug, Serialize, Deserialize, JsonSchema)]
#[schemars(description = "User credentials")]
pub struct Credentials {
    #[schemars(description = "Username")]
    pub username: String,

    #[schemars(description = "Password")]
    pub password: String,
}

// Mark as safe for elicitation
elicit_safe!(Credentials);
```

**2. Request user input in tool:**

```rust
#[tool(description = "Login to service")]
async fn login(
    &self,
    context: RequestContext<RoleServer>,
) -> Result<CallToolResult, McpError> {
    // Request credentials from user
    let credentials = context
        .peer
        .elicit::<Credentials>("Please provide your credentials".to_string())
        .await
        .map_err(|e| McpError::internal_error(
            format!("Failed to elicit credentials: {}", e),
            None,
        ))?;

    match credentials {
        Some(creds) => {
            // Use credentials
            let success = authenticate(&creds.username, &creds.password).await?;

            if success {
                Ok(CallToolResult::success(vec![
                    Content::text("Login successful")
                ]))
            } else {
                Err(McpError::invalid_params(
                    "Invalid credentials",
                    None,
                ))
            }
        }
        None => {
            // User cancelled or client doesn't support elicitation
            Err(McpError::invalid_params(
                "Credentials required",
                None,
            ))
        }
    }
}
```

#### Best Practices

- Always handle `None` case (user cancellation)
- Provide clear description of what is being requested
- Use appropriate types with validation
- Don't store sensitive data longer than necessary
- Mark sensitive fields appropriately

See `examples/elicitation_server/` for a complete elicitation implementation with multiple use cases.

---

### Progress Notifications

Progress notifications allow your server to report long-running operation progress to the client.

#### Use Cases

- File processing with progress
- Large data transfers
- Multi-step operations
- Background tasks

#### Implementation

```rust
use rmcp::model::{ProgressNotificationParam, ProgressToken, NumberOrString};

#[tool(description = "Process large file with progress")]
async fn process_large_file(
    &self,
    Parameters(params): Parameters<ProcessFileParams>,
    context: RequestContext<RoleServer>,
) -> Result<CallToolResult, McpError> {
    let total_chunks = 100;

    for i in 0..total_chunks {
        // Process chunk
        process_chunk(i).await?;

        // Send progress notification
        let progress_param = ProgressNotificationParam {
            progress_token: ProgressToken(NumberOrString::Number(i as i64)),
            progress: i as f64,
            total: Some(total_chunks as f64),
            message: Some(format!("Processing chunk {} of {}", i + 1, total_chunks)),
        };

        context
            .peer
            .notify_progress(progress_param)
            .await
            .map_err(|e| McpError::internal_error(
                format!("Failed to send progress: {}", e),
                None,
            ))?;

        // Simulate work
        tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
    }

    Ok(CallToolResult::success(vec![
        Content::text("File processed successfully")
    ]))
}
```

#### Progress Token

The `progress_token` can be either a number or string:

```rust
// Numeric token
ProgressToken(NumberOrString::Number(42))

// String token (useful for named tasks)
ProgressToken(NumberOrString::String("task_123".to_string()))
```

#### Progress Fields

- `progress_token`: Unique identifier for this progress stream
- `progress`: Current progress value
- `total`: Optional total value (for percentage calculation)
- `message`: Optional human-readable status message

#### Best Practices

- Send progress updates at reasonable intervals (not too frequent)
- Always provide meaningful messages
- Handle notification errors gracefully (client may not support progress)
- Complete the operation even if progress notification fails

See `examples/progress_server/` for a complete implementation with various progress reporting patterns.

---

### Sampling (LLM Calls)

Sampling allows your MCP server to request LLM capabilities from the client. This enables servers to leverage AI for processing.

#### Use Cases

- Content analysis
- Text summarization
- Code generation
- Question answering with context

#### Implementation

```rust
use rmcp::model::{
    CreateMessageRequestParam,
    SamplingMessage,
    Role,
    ModelPreferences,
    ModelHint,
    ContextInclusion,
};

#[tool(description = "Analyze text using LLM")]
async fn analyze_text(
    &self,
    Parameters(params): Parameters<AnalyzeParams>,
    context: RequestContext<RoleServer>,
) -> Result<CallToolResult, McpError> {
    // Request LLM analysis
    let response = context
        .peer
        .create_message(CreateMessageRequestParam {
            messages: vec![SamplingMessage {
                role: Role::User,
                content: Content::text(format!(
                    "Analyze the following text:\n\n{}",
                    params.text
                )),
            }],
            model_preferences: Some(ModelPreferences {
                hints: Some(vec![ModelHint {
                    name: Some("claude".to_string()),
                }]),
                cost_priority: Some(0.3),
                speed_priority: Some(0.7),
                intelligence_priority: Some(0.8),
            }),
            system_prompt: Some("You are a text analysis expert.".to_string()),
            include_context: Some(ContextInclusion::None),
            temperature: Some(0.7),
            max_tokens: 500,
            stop_sequences: None,
            metadata: None,
        })
        .await
        .map_err(|e| McpError::internal_error(
            format!("LLM sampling failed: {}", e),
            None,
        ))?;

    Ok(CallToolResult::success(vec![
        Content::text(format!("Analysis: {}", response.content))
    ]))
}
```

#### Model Preferences

Control which model is used and how:

```rust
ModelPreferences {
    hints: Some(vec![
        ModelHint { name: Some("claude".to_string()) },
        ModelHint { name: Some("gpt-4".to_string()) },
    ]),
    cost_priority: Some(0.3),      // 0.0 = cheapest, 1.0 = most expensive
    speed_priority: Some(0.8),     // 0.0 = slowest, 1.0 = fastest
    intelligence_priority: Some(0.7), // 0.0 = simplest, 1.0 = most capable
}
```

#### Context Inclusion

Control what context the LLM receives:

```rust
ContextInclusion::None          // No additional context
ContextInclusion::ThisServer    // Context from this server only
ContextInclusion::AllServers    // Context from all connected servers
```

#### Best Practices

- Provide clear system prompts
- Set appropriate max_tokens to control cost
- Handle sampling failures gracefully (not all clients support it)
- Consider rate limiting for cost control
- Cache results when appropriate

See `examples/sampling_server/` for a complete implementation with multiple LLM use cases.

---

## Testing

### Unit Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_increment_tool() {
        let server = MyServer::new();
        let params = serde_json::json!({});

        let result = server.increment(
            Parameters(params.as_object().unwrap().clone())
        ).await;

        assert!(result.is_ok());
    }

    #[test]
    fn test_tool_router_registration() {
        let router = MyServer::tool_router();
        assert!(router.has_route("github_create_issue"));
        assert!(router.has_route("github_list_issues"));

        let tools = router.list_all();
        assert_eq!(tools.len(), 2);
    }
}
```

### Integration Tests

```rust
// tests/integration_test.rs
use rmcp::{ServiceExt, transport::TokioStdioTransport};

#[tokio::test]
async fn test_server_initialization() {
    let server = my_mcp_server::MyServer::new();

    // Test with stdio transport
    let (stdin, stdout) = (
        tokio::io::stdin(),
        tokio::io::stdout(),
    );

    let result = server.serve((stdin, stdout)).await;
    assert!(result.is_ok());
}
```

### Testing with MCP Inspector

```bash
# Build the server
cargo build --release

# Run MCP Inspector
npx @modelcontextprotocol/inspector ./target/release/my-mcp-server
```

---

## Complete Example

### main.rs

```rust
use anyhow::Result;
use rmcp::ServiceExt;
use tokio::io::{stdin, stdout};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

mod server;
use server::MyServer;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::from_default_env())
        .with(tracing_subscriber::fmt::layer())
        .init();

    tracing::info!("Starting MCP server");

    // Create server instance
    let server = MyServer::new();

    // Serve over stdio
    let transport = (stdin(), stdout());
    let connection = server.serve(transport).await?;

    // Wait for shutdown
    let quit_reason = connection.waiting().await?;
    tracing::info!("Server shutdown: {:?}", quit_reason);

    Ok(())
}
```

### For HTTP Transport

```rust
use axum::{routing::post, Router};
use rmcp::transport::axum::AxumStreamableHttpHandler;

#[tokio::main]
async fn main() -> Result<()> {
    let server = MyServer::new();

    let handler = AxumStreamableHttpHandler::new(server);

    let app = Router::new()
        .route("/mcp", post(handler.handle));

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await?;
    tracing::info!("Server listening on {}", listener.local_addr()?);

    axum::serve(listener, app).await?;

    Ok(())
}
```

---

## Quality Checklist

### Before Deployment

- [ ] All tools have clear descriptions and parameter documentation
- [ ] Tool names follow `{service}_{action}_{resource}` convention
- [ ] Input schemas use `schemars::JsonSchema` for validation
- [ ] Error messages are actionable and specific
- [ ] Pagination is implemented for list operations
- [ ] All async operations use proper error handling
- [ ] Code passes `cargo clippy` without warnings
- [ ] Code is formatted with `cargo fmt`
- [ ] Unit tests cover main functionality
- [ ] Integration tests verify MCP protocol compliance
- [ ] Server info provides clear instructions
- [ ] Dependencies are minimal and necessary
- [ ] Documentation is complete (README, doc comments)

### Performance

- [ ] No blocking operations in async functions
- [ ] Shared state uses appropriate concurrency primitives (Arc<Mutex<T>>)
- [ ] HTTP client connections are reused
- [ ] Large responses use streaming where possible
- [ ] Memory usage is bounded (no unbounded buffers)

### Security

- [ ] Input validation on all tool parameters
- [ ] Authentication tokens are stored securely
- [ ] API keys are loaded from environment variables
- [ ] No sensitive data in logs or error messages
- [ ] Rate limiting for external API calls

---

## Additional Resources

- rmcp GitHub: https://github.com/modelcontextprotocol/rust-sdk
- rmcp docs.rs: https://docs.rs/rmcp/latest/rmcp/
- MCP Specification: https://modelcontextprotocol.io/
- Tokio Tutorial: https://tokio.rs/tokio/tutorial
- Serde Guide: https://serde.rs/
- Schemars: https://docs.rs/schemars/latest/schemars/
