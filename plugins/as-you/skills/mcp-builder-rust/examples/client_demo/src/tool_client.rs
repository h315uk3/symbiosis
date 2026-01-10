//! Example 1: Simple Tool Client
//!
//! This example demonstrates:
//! - Connecting to an MCP server via stdio (child process)
//! - Getting server information
//! - Listing available tools
//! - Calling a tool with parameters
//! - Proper cleanup
//!
//! Usage:
//!   cargo run --bin tool_client

use rmcp::{ServiceExt, model::CallToolRequestParam, transport::TokioChildProcess};
use tokio::process::Command;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive(tracing::Level::INFO.into()),
        )
        .init();

    tracing::info!("Starting MCP tool client demo");

    // 1. Create transport - Connect to a local MCP server via stdio
    //
    // This example connects to the basic_server example.
    // Make sure to have it running or adjust the command below.
    let transport = TokioChildProcess::new(
        Command::new("cargo")
            .arg("run")
            .arg("--manifest-path")
            .arg("../basic_server/Cargo.toml")
    )?;

    tracing::info!("Connecting to MCP server...");

    // 2. Serve client (connect to server)
    let client = ().serve(transport).await?;

    // 3. Get server info
    let server_info = client.peer_info();
    tracing::info!(
        "Connected to: {} v{}",
        server_info.server_info.name,
        server_info.server_info.version
    );
    tracing::info!("Server capabilities: {:?}", server_info.capabilities);

    // 4. List available tools
    tracing::info!("Fetching available tools...");
    let tools = client.list_all_tools().await?;
    tracing::info!("Available tools: {}", tools.len());

    for tool in &tools {
        tracing::info!(
            "  - {} : {}",
            tool.name,
            tool.description.as_deref().unwrap_or("")
        );
    }

    // 5. Call a tool with parameters
    if tools.iter().any(|t| t.name == "calculator_add") {
        tracing::info!("Calling calculator_add tool...");

        let result = client.call_tool(CallToolRequestParam {
            name: "calculator_add".into(),
            arguments: Some(
                serde_json::json!({
                    "a": 15,
                    "b": 27
                })
                .as_object()
                .cloned()
            ),
        }).await?;

        // 6. Handle result
        if result.is_error == Some(true) {
            tracing::error!("Tool execution failed");
        } else {
            tracing::info!("Tool execution succeeded");
        }

        for content in &result.content {
            match content {
                rmcp::model::Content::Text(text_content) => {
                    tracing::info!("Result: {}", text_content.text);
                }
                rmcp::model::Content::Image(img_content) => {
                    tracing::info!("Image data: {} bytes", img_content.data.len());
                }
                rmcp::model::Content::Resource(res_content) => {
                    tracing::info!("Resource: {}", res_content.resource.uri);
                }
            }
        }
    } else {
        tracing::warn!("calculator_add tool not found");
    }

    // 7. Call echo tool
    if tools.iter().any(|t| t.name == "echo") {
        tracing::info!("Calling echo tool...");

        let result = client.call_tool(CallToolRequestParam {
            name: "echo".into(),
            arguments: Some(
                serde_json::json!({
                    "message": "Hello from MCP client!"
                })
                .as_object()
                .cloned()
            ),
        }).await?;

        for content in &result.content {
            if let rmcp::model::Content::Text(text_content) = content {
                tracing::info!("Echo response: {}", text_content.text);
            }
        }
    }

    // 8. Cleanup - Always cancel the client to clean up resources
    tracing::info!("Shutting down client...");
    client.cancel().await?;

    tracing::info!("Client shutdown complete");
    Ok(())
}
