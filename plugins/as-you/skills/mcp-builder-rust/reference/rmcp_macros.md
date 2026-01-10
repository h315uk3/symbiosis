# rmcp-macros - Procedural Macros for MCP Server Development

`rmcp-macros` provides procedural macros that dramatically simplify MCP server development in Rust. These macros handle boilerplate code generation, automatic JSON schema creation, and routing infrastructure.

## Table of Contents

1. [Overview](#overview)
2. [Tool Macros](#tool-macros)
   - [#[tool]](#tool)
   - [#[tool_router]](#tool_router)
   - [#[tool_handler]](#tool_handler)
3. [Prompt Macros](#prompt-macros)
   - [#[prompt]](#prompt)
   - [#[prompt_router]](#prompt_router)
   - [#[prompt_handler]](#prompt_handler)
4. [Advanced Patterns](#advanced-patterns)
5. [Complete Example](#complete-example)

---

## Overview

rmcp-macros provides six main macros divided into two categories:

**Tool Macros** (for implementing MCP tools):
- `#[tool]` - Mark a function as an MCP tool
- `#[tool_router]` - Generate a router for tool functions
- `#[tool_handler]` - Implement ServerHandler trait methods automatically

**Prompt Macros** (for implementing MCP prompts):
- `#[prompt]` - Mark a function as a prompt generator
- `#[prompt_router]` - Generate a router for prompt functions
- `#[prompt_handler]` - Implement ServerHandler trait methods automatically

---

## Tool Macros

### #[tool]

Marks a function as an MCP tool handler. Automatically generates tool metadata and JSON schema.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `String` | Tool name (defaults to function name) |
| `description` | `String` | Tool description (uses doc comment if omitted) |
| `input_schema` | `Expr` | Custom JSON Schema (auto-generated from `Parameters<T>` if omitted) |
| `annotations` | `ToolAnnotationsAttribute` | Tool annotations (readOnly, destructive, etc.) |

#### Basic Usage

```rust
use rmcp::{tool, handler::server::wrapper::Parameters};

#[derive(Debug, Deserialize, schemars::JsonSchema)]
struct AddParams {
    a: i32,
    b: i32,
}

/// Add two numbers
#[tool]
async fn add(
    &self,
    Parameters(params): Parameters<AddParams>,
) -> Result<CallToolResult, McpError> {
    let result = params.a + params.b;
    Ok(CallToolResult::success(vec![
        Content::text(format!("{} + {} = {}", params.a, params.b, result))
    ]))
}
```

#### With Explicit Parameters

```rust
#[tool(
    name = "custom_add",
    description = "Adds two numbers with custom name",
    annotations(readOnlyHint = true)
)]
async fn add(&self, Parameters(params): Parameters<AddParams>) -> Result<CallToolResult, McpError> {
    // Implementation
}
```

#### Tool Annotations

```rust
#[tool(
    annotations(
        readOnlyHint = true,        // Tool only reads data
        destructiveHint = false,    // Tool doesn't modify data
        idempotentHint = true,      // Multiple calls produce same result
        title = "Addition Tool"     // Display title
    )
)]
async fn safe_add(...) -> Result<CallToolResult, McpError> {
    // Implementation
}
```

---

### #[tool_router]

Generates a router function that registers all `#[tool]`-marked functions in an impl block.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `router` | `Ident` | Router function name (defaults to `tool_router`) |
| `vis` | `Visibility` | Visibility modifier (defaults to private) |

#### Basic Usage

```rust
use rmcp::{tool, tool_router, handler::server::router::tool::ToolRouter};

#[derive(Clone)]
struct MyServer {
    tool_router: ToolRouter<MyServer>,
}

#[tool_router]
impl MyServer {
    pub fn new() -> Self {
        Self {
            tool_router: Self::tool_router(),  // Generated function
        }
    }

    #[tool(description = "Add two numbers")]
    async fn add(&self, Parameters(params): Parameters<AddParams>) -> Result<CallToolResult, McpError> {
        // Implementation
    }

    #[tool(description = "Subtract two numbers")]
    async fn subtract(&self, Parameters(params): Parameters<SubParams>) -> Result<CallToolResult, McpError> {
        // Implementation
    }
}
```

#### Combining Multiple Routers

```rust
mod math {
    #[tool_router(router = math_router, vis = "pub")]
    impl MyServer {
        #[tool]
        async fn add(&self, ...) -> Result<CallToolResult, McpError> { }

        #[tool]
        async fn subtract(&self, ...) -> Result<CallToolResult, McpError> { }
    }
}

mod string {
    #[tool_router(router = string_router, vis = "pub")]
    impl MyServer {
        #[tool]
        async fn concat(&self, ...) -> Result<CallToolResult, McpError> { }

        #[tool]
        async fn uppercase(&self, ...) -> Result<CallToolResult, McpError> { }
    }
}

impl MyServer {
    pub fn new() -> Self {
        Self {
            // Combine routers with + operator
            tool_router: math::math_router() + string::string_router(),
        }
    }
}
```

---

### #[tool_handler]

Automatically implements `call_tool` and `list_tools` methods for `ServerHandler` trait using a `ToolRouter`.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `router` | `Expr` | Expression to access ToolRouter (defaults to `self.tool_router`) |

#### Basic Usage

```rust
use rmcp::{tool_handler, ServerHandler, RoleServer};

#[tool_handler]
impl ServerHandler for MyServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo {
            protocol_version: ProtocolVersion::V_2024_11_05,
            capabilities: ServerCapabilities::builder()
                .enable_tools()
                .build(),
            server_info: Implementation {
                name: "my-server".to_string(),
                version: "1.0.0".to_string(),
            },
            instructions: None,
        }
    }

    async fn initialize(
        &self,
        _request: InitializeRequestParam,
        _context: RequestContext<RoleServer>,
    ) -> Result<InitializeResult, McpError> {
        Ok(self.get_info())
    }

    // call_tool and list_tools are auto-generated!
}
```

#### Custom Router Expression

```rust
#[tool_handler(router = self.get_dynamic_router().await)]
impl ServerHandler for MyServer {
    // Other handler methods
}
```

#### What Gets Generated

The macro expands to:

```rust
impl ServerHandler for MyServer {
    async fn call_tool(
        &self,
        request: CallToolRequestParam,
        context: RequestContext<RoleServer>,
    ) -> Result<CallToolResult, rmcp::ErrorData> {
        let tcc = ToolCallContext::new(self, request, context);
        self.tool_router.call(tcc).await
    }

    async fn list_tools(
        &self,
        _request: Option<PaginatedRequestParam>,
        _context: RequestContext<RoleServer>,
    ) -> Result<ListToolsResult, rmcp::ErrorData> {
        let items = self.tool_router.list_all();
        Ok(ListToolsResult::with_all_items(items))
    }
}
```

---

## Prompt Macros

### #[prompt]

Marks a function as a prompt generator. Automatically creates prompt metadata and argument schemas.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `String` | Prompt name (defaults to function name) |
| `description` | `String` | Prompt description (uses doc comment if omitted) |
| `arguments` | `Expr` | Custom prompt arguments (auto-generated from `Parameters<T>` if omitted) |

#### Basic Usage

```rust
use rmcp::{prompt, model::PromptMessage, handler::server::wrapper::Parameters};

#[derive(Debug, Deserialize, schemars::JsonSchema)]
struct GreetingArgs {
    name: String,
    language: Option<String>,
}

/// Generate a greeting prompt
#[prompt]
async fn greeting(
    &self,
    Parameters(args): Parameters<GreetingArgs>,
) -> Vec<PromptMessage> {
    let lang = args.language.unwrap_or_else(|| "English".to_string());
    vec![
        PromptMessage::new_text(
            PromptMessageRole::User,
            format!("Please greet {} in {}", args.name, lang),
        ),
    ]
}
```

#### With Explicit Parameters

```rust
#[prompt(
    name = "code_review",
    description = "Generate a code review prompt with best practices"
)]
async fn code_review_prompt(
    &self,
    Parameters(args): Parameters<CodeReviewArgs>,
) -> Result<GetPromptResult, McpError> {
    let messages = vec![
        PromptMessage::new_text(
            PromptMessageRole::Assistant,
            format!("You are an expert {} code reviewer.", args.language),
        ),
        PromptMessage::new_text(
            PromptMessageRole::User,
            format!("Review the code at: {}", args.file_path),
        ),
    ];

    Ok(GetPromptResult {
        description: Some("Code review with best practices".to_string()),
        messages,
    })
}
```

#### Return Types

Prompt functions can return:
- `Vec<PromptMessage>` - Simple message list
- `GetPromptResult` - Full result with description
- `Result<Vec<PromptMessage>, McpError>` - With error handling
- `Result<GetPromptResult, McpError>` - Full result with error handling

---

### #[prompt_router]

Generates a router function that registers all `#[prompt]`-marked functions in an impl block.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `router` | `Ident` | Router function name (defaults to `prompt_router`) |
| `vis` | `Visibility` | Visibility modifier (defaults to private) |

#### Basic Usage

```rust
use rmcp::{prompt, prompt_router, handler::server::router::prompt::PromptRouter};

#[derive(Clone)]
struct MyServer {
    prompt_router: PromptRouter<MyServer>,
}

#[prompt_router]
impl MyServer {
    pub fn new() -> Self {
        Self {
            prompt_router: Self::prompt_router(),  // Generated function
        }
    }

    #[prompt(description = "Greeting prompt")]
    async fn greeting(&self, Parameters(args): Parameters<GreetingArgs>) -> Vec<PromptMessage> {
        // Implementation
    }

    #[prompt(description = "Code review prompt")]
    async fn code_review(&self, Parameters(args): Parameters<CodeReviewArgs>) -> Result<GetPromptResult, McpError> {
        // Implementation
    }
}
```

---

### #[prompt_handler]

Automatically implements `get_prompt` and `list_prompts` methods for `ServerHandler` trait using a `PromptRouter`.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `router` | `Expr` | Expression to access PromptRouter (defaults to `self.prompt_router`) |

#### Basic Usage

```rust
use rmcp::{prompt_handler, ServerHandler};

#[prompt_handler]
impl ServerHandler for MyServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo {
            protocol_version: ProtocolVersion::V_2024_11_05,
            capabilities: ServerCapabilities::builder()
                .enable_prompts()
                .build(),
            // Other fields...
        }
    }

    // get_prompt and list_prompts are auto-generated!
}
```

---

## Advanced Patterns

### Combining Tools and Prompts

A server can provide both tools and prompts:

```rust
use rmcp::{tool, tool_router, tool_handler, prompt, prompt_router, prompt_handler};

#[derive(Clone)]
struct MyServer {
    tool_router: ToolRouter<MyServer>,
    prompt_router: PromptRouter<MyServer>,
}

#[tool_router]
#[prompt_router]
impl MyServer {
    pub fn new() -> Self {
        Self {
            tool_router: Self::tool_router(),
            prompt_router: Self::prompt_router(),
        }
    }

    // Tools
    #[tool]
    async fn add(&self, ...) -> Result<CallToolResult, McpError> { }

    // Prompts
    #[prompt]
    async fn greeting(&self, ...) -> Vec<PromptMessage> { }
}

#[tool_handler]
#[prompt_handler]
impl ServerHandler for MyServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo {
            capabilities: ServerCapabilities::builder()
                .enable_tools()
                .enable_prompts()
                .build(),
            // Other fields...
        }
    }

    // Other handler methods...
}
```

### State Management with Macros

```rust
use std::sync::Arc;
use tokio::sync::Mutex;

#[derive(Clone)]
struct StatefulServer {
    state: Arc<Mutex<ServerState>>,
    tool_router: ToolRouter<StatefulServer>,
}

struct ServerState {
    counter: i32,
}

#[tool_router]
impl StatefulServer {
    pub fn new() -> Self {
        Self {
            state: Arc::new(Mutex::new(ServerState { counter: 0 })),
            tool_router: Self::tool_router(),
        }
    }

    #[tool(description = "Increment the counter")]
    async fn increment(&self) -> Result<CallToolResult, McpError> {
        let mut state = self.state.lock().await;
        state.counter += 1;

        Ok(CallToolResult::success(vec![
            Content::text(format!("Counter: {}", state.counter))
        ]))
    }

    #[tool(description = "Get counter value")]
    async fn get_counter(&self) -> Result<CallToolResult, McpError> {
        let state = self.state.lock().await;

        Ok(CallToolResult::success(vec![
            Content::text(format!("Counter: {}", state.counter))
        ]))
    }
}
```

### Using RequestContext

```rust
#[tool]
async fn context_aware_tool(
    &self,
    Parameters(params): Parameters<MyParams>,
    context: RequestContext<RoleServer>,
) -> Result<CallToolResult, McpError> {
    // Access client capabilities
    let client_info = context.meta;

    // Use peer for advanced features
    let progress_result = context.peer.notify_progress(...).await;

    // Implementation
    Ok(CallToolResult::success(vec![Content::text("Done")]))
}
```

---

## Complete Example

See `examples/macros_demo_server/` for a comprehensive example demonstrating all macro features:

- **Tools**: Calculator operations with various annotations
- **Prompts**: Code review, data analysis, writing assistant
- **State Management**: Shared state across tools
- **Error Handling**: Proper error propagation
- **Combined Features**: Tools and prompts in a single server

---

## Best Practices

1. **Use Doc Comments**: They automatically become descriptions
   ```rust
   /// This is the tool description
   #[tool]
   async fn my_tool(...) { }
   ```

2. **Type Safety**: Always use `Parameters<T>` with `JsonSchema`-derived types
   ```rust
   #[derive(Debug, Deserialize, schemars::JsonSchema)]
   struct MyParams { }
   ```

3. **Annotations**: Add appropriate hints for tools
   ```rust
   #[tool(annotations(readOnlyHint = true, destructiveHint = false))]
   ```

4. **Error Handling**: Return `Result<_, McpError>` for fallible operations
   ```rust
   async fn fallible_tool(...) -> Result<CallToolResult, McpError> { }
   ```

5. **Modular Routers**: Split large servers into modules with separate routers
   ```rust
   let router = module_a::router() + module_b::router();
   ```

6. **Testing**: Tool routers provide `has_route()` and `list_all()` methods
   ```rust
   #[test]
   fn test_tools_registered() {
       let router = MyServer::tool_router();
       assert!(router.has_route("add"));
       assert_eq!(router.list_all().len(), 5);
   }
   ```

---

## Reference

- **rmcp-macros crate**: https://crates.io/crates/rmcp-macros
- **Source code**: https://github.com/modelcontextprotocol/rust-sdk/tree/main/crates/rmcp-macros
- **Examples**: See `examples/macros_demo_server/` in this skills directory
