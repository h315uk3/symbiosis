# Rust MCP Client Implementation Guide

This guide covers how to build MCP (Model Context Protocol) clients in Rust using the rmcp SDK. Clients connect to MCP servers to use their tools, access resources, and retrieve prompts.

## Table of Contents

1. [Overview](#overview)
2. [Client Architecture](#client-architecture)
3. [Transport Options](#transport-options)
   - [stdio Transport](#stdio-transport)
   - [HTTP Transport](#http-transport)
4. [Basic Client Operations](#basic-client-operations)
   - [Initialization](#initialization)
   - [Listing Tools](#listing-tools)
   - [Calling Tools](#calling-tools)
   - [Reading Resources](#reading-resources)
   - [Getting Prompts](#getting-prompts)
5. [Advanced Features](#advanced-features)
   - [Handling Sampling Requests](#handling-sampling-requests)
   - [Progress Notifications](#progress-notifications)
   - [Multiple Client Management](#multiple-client-management)
6. [Error Handling](#error-handling)
7. [Complete Examples](#complete-examples)
8. [Best Practices](#best-practices)

---

## Overview

MCP clients connect to servers to:
- **Call Tools**: Execute server-provided functionality
- **Read Resources**: Access server-managed data
- **Get Prompts**: Retrieve prompt templates for LLM interactions
- **Handle Sampling**: Respond to server requests for LLM capabilities

---

## Client Architecture

### Basic Structure

```rust
use rmcp::{
    ServiceExt,
    transport::TokioChildProcess,
};
use tokio::process::Command;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // 1. Create transport
    let transport = TokioChildProcess::new(
        Command::new("uvx")
            .arg("mcp-server-git")
    )?;

    // 2. Serve client (connect to server)
    let client = ().serve(transport).await?;

    // 3. Use client to interact with server
    let tools = client.list_tools(Default::default()).await?;

    // 4. Cleanup
    client.cancel().await?;

    Ok(())
}
```

### Key Components

1. **Transport**: Communication channel (stdio or HTTP)
2. **Client Service**: The `().serve(transport)` pattern creates a client
3. **Peer Interface**: Access to server capabilities via `client` methods
4. **Error Handling**: Proper Result types and error propagation

---

## Transport Options

### stdio Transport

Use stdio for local servers running as child processes.

#### Basic stdio Client

```rust
use rmcp::{
    ServiceExt,
    transport::{TokioChildProcess, ConfigureCommandExt},
};
use tokio::process::Command;

async fn create_stdio_client() -> Result<impl ServiceExt, Box<dyn std::error::Error>> {
    let client = ()
        .serve(
            TokioChildProcess::new(
                Command::new("uvx").configure(|cmd| {
                    cmd.arg("mcp-server-git");
                })
            )?
        )
        .await?;

    Ok(client)
}
```

#### Custom Command Arguments

```rust
let client = ()
    .serve(
        TokioChildProcess::new(
            Command::new("cargo")
                .arg("run")
                .arg("--example")
                .arg("my-server")
                .env("LOG_LEVEL", "debug")
        )?
    )
    .await?;
```

---

### HTTP Transport

Use HTTP for remote servers or network-based connections.

#### Dependencies

Add to `Cargo.toml`:

```toml
[dependencies]
rmcp = { version = "0.8", features = ["transport-streamable-http-client-reqwest"] }
reqwest = "0.12"
```

#### Basic HTTP Client

```rust
use rmcp::{
    ServiceExt,
    transport::streamable_http_client::{
        StreamableHttpClientTransport,
        StreamableHttpClientTransportConfig,
    },
};

async fn create_http_client() -> Result<impl ServiceExt, Box<dyn std::error::Error>> {
    let transport = StreamableHttpClientTransport::new(
        StreamableHttpClientTransportConfig::with_uri("http://localhost:3000/mcp")
    );

    let client = ().serve(transport).await?;

    Ok(client)
}
```

#### With Custom HTTP Client

```rust
use reqwest::Client;

let http_client = Client::builder()
    .timeout(std::time::Duration::from_secs(30))
    .build()?;

let transport = StreamableHttpClientTransport::with_client(
    http_client,
    StreamableHttpClientTransportConfig::with_uri("http://localhost:3000/mcp")
);

let client = ().serve(transport).await?;
```

---

## Basic Client Operations

### Initialization

When a client connects, it automatically performs the MCP initialization handshake.

```rust
let client = ().serve(transport).await?;

// Get server information
let server_info = client.peer_info();
println!("Server name: {}", server_info.server_info.name);
println!("Server version: {}", server_info.server_info.version);
println!("Capabilities: {:?}", server_info.capabilities);
```

---

### Listing Tools

```rust
use rmcp::model::PaginatedRequestParam;

// List all tools (automatic pagination)
let tools = client.list_all_tools().await?;
for tool in &tools {
    println!("Tool: {} - {}", tool.name, tool.description.as_deref().unwrap_or(""));
}

// Manual pagination
let page1 = client.list_tools(PaginatedRequestParam {
    cursor: None,
}).await?;

if let Some(next_cursor) = page1.next_cursor {
    let page2 = client.list_tools(PaginatedRequestParam {
        cursor: Some(next_cursor),
    }).await?;
}
```

---

### Calling Tools

```rust
use rmcp::model::CallToolRequestParam;
use serde_json::json;

// Simple tool call without arguments
let result = client.call_tool(CallToolRequestParam {
    name: "get_status".into(),
    arguments: None,
}).await?;

// Tool call with arguments
let result = client.call_tool(CallToolRequestParam {
    name: "add".into(),
    arguments: Some(json!({
        "a": 5,
        "b": 3
    }).as_object().cloned()),
}).await?;

// Handle result
for content in &result.content {
    match content {
        rmcp::model::Content::Text(text_content) => {
            println!("Result: {}", text_content.text);
        }
        rmcp::model::Content::Image(img_content) => {
            println!("Image data: {} bytes", img_content.data.len());
        }
        rmcp::model::Content::Resource(res_content) => {
            println!("Resource: {}", res_content.resource.uri);
        }
    }
}

// Check for errors
if result.is_error == Some(true) {
    eprintln!("Tool execution failed");
}
```

---

### Reading Resources

```rust
use rmcp::model::ReadResourceRequestParam;

// List all resources
let resources = client.list_all_resources().await?;
for resource in &resources {
    println!("Resource: {} - {}", resource.uri, resource.name);
}

// Read a specific resource
let resource_result = client.read_resource(ReadResourceRequestParam {
    uri: "file:///path/to/config.json".into(),
}).await?;

for content in &resource_result.contents {
    match content {
        rmcp::model::ResourceContents::Text(text_content) => {
            println!("Resource text: {}", text_content.text);
        }
        rmcp::model::ResourceContents::Blob(blob_content) => {
            println!("Resource blob: {} bytes", blob_content.blob.len());
        }
    }
}
```

---

### Getting Prompts

```rust
use rmcp::model::GetPromptRequestParam;

// List all prompts
let prompts = client.list_all_prompts().await?;
for prompt in &prompts {
    println!("Prompt: {} - {}", prompt.name, prompt.description.as_deref().unwrap_or(""));
}

// Get a simple prompt (no arguments)
let prompt_result = client.get_prompt(GetPromptRequestParam {
    name: "greeting".into(),
    arguments: None,
}).await?;

// Get a prompt with arguments
let prompt_result = client.get_prompt(GetPromptRequestParam {
    name: "code_review".into(),
    arguments: Some(json!({
        "language": "rust",
        "file_path": "src/main.rs",
        "focus_areas": ["performance", "safety"]
    }).as_object().cloned()),
}).await?;

// Use prompt messages
for message in &prompt_result.messages {
    println!("{:?}: {}", message.role, message.content.text().unwrap_or_default());
}
```

---

## Advanced Features

### Handling Sampling Requests

When a server requests LLM capabilities via sampling, the client must respond.

```rust
use rmcp::{
    ServiceExt,
    model::{CreateMessageResult, SamplingMessage, StopReason},
    service::SamplingHandler,
};

// Implement sampling handler
struct MyClient;

impl SamplingHandler for MyClient {
    async fn create_message(
        &self,
        request: rmcp::model::CreateMessageRequestParam,
    ) -> Result<CreateMessageResult, rmcp::ErrorData> {
        // Call your LLM here
        let llm_response = call_my_llm(&request.messages).await?;

        Ok(CreateMessageResult {
            role: rmcp::model::Role::Assistant,
            content: rmcp::model::Content::text(llm_response),
            model: "my-model".to_string(),
            stop_reason: Some(StopReason::EndTurn),
        })
    }
}

// Use custom client with sampling support
let client = MyClient.serve(transport).await?;
```

---

### Progress Notifications

Handle progress updates from long-running server operations.

```rust
use rmcp::model::ProgressNotificationParam;

// Client automatically receives progress notifications
// Set up logging to see them:
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

tracing_subscriber::registry()
    .with(tracing_subscriber::EnvFilter::from_default_env())
    .with(tracing_subscriber::fmt::layer())
    .init();

// Progress notifications will be logged automatically
let result = client.call_tool(CallToolRequestParam {
    name: "process_large_file".into(),
    arguments: Some(json!({ "filename": "data.csv" }).as_object().cloned()),
}).await?;
```

---

### Multiple Client Management

Manage multiple server connections.

```rust
use std::collections::HashMap;

struct ClientManager {
    clients: HashMap<String, Box<dyn ServiceExt>>,
}

impl ClientManager {
    async fn add_client(&mut self, name: String, transport: impl Transport) -> Result<(), Error> {
        let client = ().serve(transport).await?;
        self.clients.insert(name, Box::new(client.into_dyn()));
        Ok(())
    }

    async fn call_tool_on_all(&self, tool_name: &str) -> Vec<Result<CallToolResult, Error>> {
        let mut results = Vec::new();

        for client in self.clients.values() {
            let result = client.call_tool(CallToolRequestParam {
                name: tool_name.into(),
                arguments: None,
            }).await;
            results.push(result);
        }

        results
    }
}
```

---

## Error Handling

### Error Types

```rust
use rmcp::RmcpError;

match client.call_tool(request).await {
    Ok(result) => {
        // Success
    }
    Err(RmcpError::ProtocolError(e)) => {
        eprintln!("Protocol error: {}", e);
    }
    Err(RmcpError::TransportError(e)) => {
        eprintln!("Transport error: {}", e);
    }
    Err(e) => {
        eprintln!("Other error: {}", e);
    }
}
```

### Graceful Shutdown

```rust
// Always cancel the client to clean up resources
async fn shutdown_client(client: impl ServiceExt) -> Result<(), RmcpError> {
    client.cancel().await?;
    Ok(())
}

// With timeout
use tokio::time::{timeout, Duration};

async fn shutdown_with_timeout(client: impl ServiceExt) -> Result<(), Box<dyn std::error::Error>> {
    timeout(Duration::from_secs(5), client.cancel()).await??;
    Ok(())
}
```

---

## Complete Examples

### Example 1: Simple Tool Client

```rust
use rmcp::{ServiceExt, model::CallToolRequestParam, transport::TokioChildProcess};
use tokio::process::Command;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Connect to server
    let client = ()
        .serve(TokioChildProcess::new(Command::new("my-mcp-server"))?)
        .await?;

    // Get server info
    println!("Connected to: {}", client.peer_info().server_info.name);

    // List tools
    let tools = client.list_all_tools().await?;
    println!("Available tools: {}", tools.len());

    // Call a tool
    let result = client.call_tool(CallToolRequestParam {
        name: "echo".into(),
        arguments: Some(serde_json::json!({ "message": "Hello!" }).as_object().cloned()),
    }).await?;

    println!("Result: {:?}", result);

    // Cleanup
    client.cancel().await?;
    Ok(())
}
```

### Example 2: Resource Reader

```rust
use rmcp::{
    ServiceExt,
    model::ReadResourceRequestParam,
    transport::streamable_http_client::{
        StreamableHttpClientTransport,
        StreamableHttpClientTransportConfig,
    },
};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Connect via HTTP
    let transport = StreamableHttpClientTransport::new(
        StreamableHttpClientTransportConfig::with_uri("http://localhost:3000/mcp")
    );

    let client = ().serve(transport).await?;

    // List all resources
    let resources = client.list_all_resources().await?;

    // Read each resource
    for resource in resources {
        println!("Reading resource: {}", resource.uri);

        let content = client.read_resource(ReadResourceRequestParam {
            uri: resource.uri.clone(),
        }).await?;

        for item in &content.contents {
            if let rmcp::model::ResourceContents::Text(text) = item {
                println!("Content: {}", text.text);
            }
        }
    }

    client.cancel().await?;
    Ok(())
}
```

### Example 3: Prompt Consumer

```rust
use rmcp::{ServiceExt, model::GetPromptRequestParam, transport::TokioChildProcess};
use tokio::process::Command;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = ()
        .serve(TokioChildProcess::new(Command::new("my-prompt-server"))?)
        .await?;

    // List prompts
    let prompts = client.list_all_prompts().await?;

    for prompt in &prompts {
        println!("Getting prompt: {}", prompt.name);

        let result = client.get_prompt(GetPromptRequestParam {
            name: prompt.name.clone(),
            arguments: None,
        }).await?;

        println!("Messages:");
        for msg in &result.messages {
            println!("  {:?}: {}", msg.role, msg.content.text().unwrap_or_default());
        }
    }

    client.cancel().await?;
    Ok(())
}
```

### Working Examples

Complete, runnable implementations of these examples are available in `examples/client_demo/`:

1. **Tool Client** (`src/tool_client.rs`): Basic stdio client that connects to a server, lists tools, and calls them
   - Demonstrates tool listing and calling
   - Shows proper error handling
   - Includes cleanup patterns

2. **Resource Reader** (`src/resource_reader.rs`): HTTP client that reads server resources
   - Connects via HTTP transport
   - Lists and reads resources
   - Handles both text and binary content

3. **Prompt Consumer** (`src/prompt_consumer.rs`): Client that retrieves and uses prompts
   - Gets prompts without arguments
   - Gets prompts with custom parameters
   - Processes prompt messages

Run these examples:
```bash
# Tool client (requires basic_server running)
cargo run --bin tool_client --manifest-path examples/client_demo/Cargo.toml

# Resource reader (requires HTTP server at localhost:3000)
cargo run --bin resource_reader --manifest-path examples/client_demo/Cargo.toml

# Prompt consumer (requires macros_demo_server running)
cargo run --bin prompt_consumer --manifest-path examples/client_demo/Cargo.toml
```

---

## Best Practices

### 1. Always Clean Up

```rust
// Use RAII or explicit cleanup
async fn use_client() -> Result<(), Box<dyn std::error::Error>> {
    let client = create_client().await?;

    // Do work...

    client.cancel().await?;  // Always cancel
    Ok(())
}
```

### 2. Handle Errors Gracefully

```rust
match client.call_tool(request).await {
    Ok(result) if result.is_error == Some(true) => {
        // Tool reported an error
        eprintln!("Tool error");
    }
    Ok(result) => {
        // Success
    }
    Err(e) => {
        // Connection or protocol error
        eprintln!("Client error: {}", e);
    }
}
```

### 3. Use Pagination for Large Lists

```rust
// Automatic pagination (recommended)
let all_tools = client.list_all_tools().await?;

// Manual pagination (for memory-constrained scenarios)
let mut cursor = None;
loop {
    let page = client.list_tools(PaginatedRequestParam { cursor }).await?;
    process_tools(&page.tools);

    match page.next_cursor {
        Some(next) => cursor = Some(next),
        None => break,
    }
}
```

### 4. Validate Tool Arguments

```rust
use schemars::JsonSchema;

#[derive(serde::Serialize, JsonSchema)]
struct AddParams {
    a: i32,
    b: i32,
}

let params = AddParams { a: 5, b: 3 };
let json = serde_json::to_value(params)?;

let result = client.call_tool(CallToolRequestParam {
    name: "add".into(),
    arguments: json.as_object().cloned(),
}).await?;
```

### 5. Implement Timeouts

```rust
use tokio::time::{timeout, Duration};

async fn call_with_timeout(
    client: &impl ServiceExt,
    request: CallToolRequestParam,
) -> Result<CallToolResult, Box<dyn std::error::Error>> {
    let result = timeout(
        Duration::from_secs(30),
        client.call_tool(request)
    ).await??;

    Ok(result)
}
```

### 6. Log Important Events

```rust
use tracing::{info, error};

let client = ().serve(transport).await?;
info!("Connected to server: {}", client.peer_info().server_info.name);

match client.call_tool(request).await {
    Ok(result) => info!("Tool call succeeded"),
    Err(e) => error!("Tool call failed: {}", e),
}
```

---

## Reference

- **Client Examples**: `examples/client_demo/`
- **Transport Options**: See [Transport Options](#transport-options)
- **Error Handling**: See [Error Handling](#error-handling)
- **rmcp Client API**: https://docs.rs/rmcp/latest/rmcp/
