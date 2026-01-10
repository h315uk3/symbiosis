//! Example 2: Resource Reader
//!
//! This example demonstrates:
//! - Connecting to an MCP server via HTTP
//! - Listing available resources
//! - Reading resource contents
//! - Handling both text and binary resources
//! - Proper cleanup
//!
//! Prerequisites:
//!   This example requires an HTTP MCP server running at http://localhost:3000/mcp
//!   You can use the http_server example with HTTP transport enabled.
//!
//! Usage:
//!   1. Start the HTTP server:
//!      cargo run --bin http_server --features http
//!   2. Run this client:
//!      cargo run --bin resource_reader

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
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive(tracing::Level::INFO.into()),
        )
        .init();

    tracing::info!("Starting MCP resource reader demo");

    // 1. Create HTTP transport
    tracing::info!("Connecting to HTTP MCP server at http://localhost:3000/mcp");

    let transport = StreamableHttpClientTransport::new(
        StreamableHttpClientTransportConfig::with_uri("http://localhost:3000/mcp")
    );

    // 2. Serve client (connect to server)
    let client = match ().serve(transport).await {
        Ok(c) => c,
        Err(e) => {
            tracing::error!("Failed to connect to server: {}", e);
            tracing::error!("Make sure the HTTP server is running at http://localhost:3000/mcp");
            tracing::error!("Start it with: cargo run --bin http_server --features http");
            return Err(e.into());
        }
    };

    // 3. Get server info
    let server_info = client.peer_info();
    tracing::info!(
        "Connected to: {} v{}",
        server_info.server_info.name,
        server_info.server_info.version
    );

    // 4. List all resources
    tracing::info!("Fetching available resources...");
    let resources = client.list_all_resources().await?;

    if resources.is_empty() {
        tracing::warn!("No resources available from this server");
    } else {
        tracing::info!("Available resources: {}", resources.len());

        // 5. Read each resource
        for resource in resources {
            tracing::info!("Reading resource: {}", resource.uri);
            tracing::info!("  Name: {}", resource.name);
            if let Some(desc) = &resource.description {
                tracing::info!("  Description: {}", desc);
            }
            if let Some(mime) = &resource.mime_type {
                tracing::info!("  MIME type: {}", mime);
            }

            // Read the resource content
            match client.read_resource(ReadResourceRequestParam {
                uri: resource.uri.clone(),
            }).await {
                Ok(content) => {
                    for item in &content.contents {
                        match item {
                            rmcp::model::ResourceContents::Text(text) => {
                                tracing::info!("  Text content ({} chars):", text.text.len());
                                // Print first 100 chars
                                let preview = if text.text.len() > 100 {
                                    format!("{}...", &text.text[..100])
                                } else {
                                    text.text.clone()
                                };
                                tracing::info!("  {}", preview);
                            }
                            rmcp::model::ResourceContents::Blob(blob) => {
                                tracing::info!("  Binary content: {} bytes", blob.blob.len());
                                if let Some(mime) = &blob.mime_type {
                                    tracing::info!("  MIME type: {}", mime);
                                }
                            }
                        }
                    }
                }
                Err(e) => {
                    tracing::error!("  Failed to read resource: {}", e);
                }
            }

            tracing::info!("");
        }
    }

    // 6. Try to read a specific resource (example)
    tracing::info!("Attempting to read specific resource...");
    let test_uri = "resource://config";

    match client.read_resource(ReadResourceRequestParam {
        uri: test_uri.into(),
    }).await {
        Ok(content) => {
            tracing::info!("Successfully read resource: {}", test_uri);
            for item in &content.contents {
                if let rmcp::model::ResourceContents::Text(text) = item {
                    tracing::info!("Content: {}", text.text);
                }
            }
        }
        Err(e) => {
            tracing::warn!("Resource {} not found or error: {}", test_uri, e);
        }
    }

    // 7. Cleanup
    tracing::info!("Shutting down client...");
    client.cancel().await?;

    tracing::info!("Client shutdown complete");
    Ok(())
}
