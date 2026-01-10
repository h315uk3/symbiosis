//! Progress Notifications MCP Server Example
//!
//! This example demonstrates how to send progress notifications to clients during
//! long-running operations. Progress notifications allow the client to track the
//! status of operations and provide feedback to users.
//!
//! Features demonstrated:
//! - Progress notifications with numeric and string tokens
//! - Progress with and without total counts
//! - Different patterns for progress reporting
//!
//! Usage:
//!   cargo run
//!
//! Test with MCP Inspector:
//!   cargo build --release
//!   npx @modelcontextprotocol/inspector ./target/release/progress-mcp-server

use anyhow::Result;
use rmcp::{
    ErrorData as McpError, RoleServer, ServerHandler, ServiceExt,
    handler::server::{router::tool::ToolRouter, wrapper::Parameters},
    model::*,
    service::RequestContext,
    tool, tool_handler, tool_router,
    transport::stdio,
};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::time::{sleep, Duration};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

// ============================================================================
// Data Models
// ============================================================================

#[derive(Debug, Deserialize, schemars::JsonSchema)]
struct ProcessFileParams {
    /// File path to process
    filename: String,
    /// Number of chunks to process (default: 100)
    #[serde(default = "default_chunks")]
    chunks: usize,
}

fn default_chunks() -> usize {
    100
}

#[derive(Debug, Deserialize, schemars::JsonSchema)]
struct AnalyzeTextParams {
    /// Text to analyze
    text: String,
}

#[derive(Debug, Deserialize, schemars::JsonSchema)]
struct BatchOperationParams {
    /// Number of items to process
    #[serde(default = "default_items")]
    items: usize,
}

fn default_items() -> usize {
    50
}

#[derive(Debug, Deserialize, schemars::JsonSchema)]
struct DownloadDataParams {
    /// URL to download from
    url: String,
    /// Size in MB (simulated)
    #[serde(default = "default_size")]
    size_mb: usize,
}

fn default_size() -> usize {
    10
}

// ============================================================================
// Server State
// ============================================================================

#[derive(Default)]
struct ServerState {
    operation_count: u64,
}

// ============================================================================
// Server Implementation
// ============================================================================

#[derive(Clone)]
pub struct ProgressServer {
    state: Arc<Mutex<ServerState>>,
    tool_router: ToolRouter<ProgressServer>,
}

impl ProgressServer {
    pub fn new() -> Self {
        Self {
            state: Arc::new(Mutex::new(ServerState::default())),
            tool_router: Self::tool_router(),
        }
    }

    async fn increment_operation_count(&self) {
        let mut state = self.state.lock().await;
        state.operation_count += 1;
    }
}

// ============================================================================
// Tool Implementations
// ============================================================================

#[tool_router]
impl ProgressServer {
    /// Process a large file with progress notifications
    #[tool(
        description = "Process a large file in chunks with progress notifications. \
                       Demonstrates progress with numeric tokens and total count.",
        annotations(readOnlyHint = false)
    )]
    async fn process_large_file(
        &self,
        Parameters(params): Parameters<ProcessFileParams>,
        context: RequestContext<RoleServer>,
    ) -> Result<CallToolResult, McpError> {
        self.increment_operation_count().await;

        tracing::info!(
            "Processing file '{}' in {} chunks",
            params.filename,
            params.chunks
        );

        let total_chunks = params.chunks;
        let mut processed_data = Vec::new();

        for i in 0..total_chunks {
            // Simulate chunk processing
            sleep(Duration::from_millis(50)).await;

            // Send progress notification with numeric token
            let progress_param = ProgressNotificationParam {
                progress_token: ProgressToken(NumberOrString::Number(i as i64)),
                progress: i as f64,
                total: Some(total_chunks as f64),
                message: Some(format!(
                    "Processing chunk {} of {}",
                    i + 1,
                    total_chunks
                )),
            };

            context
                .peer
                .notify_progress(progress_param)
                .await
                .map_err(|e| {
                    McpError::internal_error(format!("Failed to send progress: {}", e), None)
                })?;

            processed_data.push(format!("chunk_{}", i));
        }

        // Final progress notification
        let progress_param = ProgressNotificationParam {
            progress_token: ProgressToken(NumberOrString::Number(total_chunks as i64)),
            progress: total_chunks as f64,
            total: Some(total_chunks as f64),
            message: Some("Processing complete".to_string()),
        };

        context
            .peer
            .notify_progress(progress_param)
            .await
            .map_err(|e| {
                McpError::internal_error(format!("Failed to send progress: {}", e), None)
            })?;

        Ok(CallToolResult::success(vec![
            Content::text(format!(
                "Successfully processed '{}' in {} chunks",
                params.filename, total_chunks
            )),
            Content::json(json!({
                "filename": params.filename,
                "chunks_processed": total_chunks,
                "data": processed_data
            })),
        ]))
    }

    /// Analyze text with progress notifications (no total count)
    #[tool(
        description = "Analyze text word by word with progress notifications. \
                       Demonstrates progress without total count (unknown duration).",
        annotations(readOnlyHint = true)
    )]
    async fn analyze_text(
        &self,
        Parameters(params): Parameters<AnalyzeTextParams>,
        context: RequestContext<RoleServer>,
    ) -> Result<CallToolResult, McpError> {
        self.increment_operation_count().await;

        let words: Vec<&str> = params.text.split_whitespace().collect();
        tracing::info!("Analyzing {} words", words.len());

        let mut analysis_results = Vec::new();

        for (i, word) in words.iter().enumerate() {
            // Simulate word analysis
            sleep(Duration::from_millis(30)).await;

            // Send progress notification without total (using string token)
            let progress_param = ProgressNotificationParam {
                progress_token: ProgressToken(NumberOrString::String(format!("word_{}", i))),
                progress: i as f64,
                total: None, // No total count
                message: Some(format!("Analyzing word: '{}'", word)),
            };

            context
                .peer
                .notify_progress(progress_param)
                .await
                .map_err(|e| {
                    McpError::internal_error(format!("Failed to send progress: {}", e), None)
                })?;

            analysis_results.push(json!({
                "word": word,
                "length": word.len(),
                "uppercase": word.to_uppercase(),
            }));
        }

        // Final progress notification
        let progress_param = ProgressNotificationParam {
            progress_token: ProgressToken(NumberOrString::String("complete".to_string())),
            progress: words.len() as f64,
            total: None,
            message: Some("Analysis complete".to_string()),
        };

        context
            .peer
            .notify_progress(progress_param)
            .await
            .map_err(|e| {
                McpError::internal_error(format!("Failed to send progress: {}", e), None)
            })?;

        Ok(CallToolResult::success(vec![
            Content::text(format!("Analyzed {} words", words.len())),
            Content::json(json!({
                "word_count": words.len(),
                "results": analysis_results
            })),
        ]))
    }

    /// Batch operation with progress notifications
    #[tool(
        description = "Process multiple items in a batch with progress notifications. \
                       Demonstrates progress with percentage calculations.",
        annotations(readOnlyHint = false)
    )]
    async fn batch_operation(
        &self,
        Parameters(params): Parameters<BatchOperationParams>,
        context: RequestContext<RoleServer>,
    ) -> Result<CallToolResult, McpError> {
        self.increment_operation_count().await;

        tracing::info!("Processing {} items in batch", params.items);

        let total_items = params.items;
        let mut results = Vec::new();

        for i in 0..total_items {
            // Simulate item processing
            sleep(Duration::from_millis(40)).await;

            let percentage = ((i + 1) as f64 / total_items as f64) * 100.0;

            // Send progress notification with percentage
            let progress_param = ProgressNotificationParam {
                progress_token: ProgressToken(NumberOrString::Number(i as i64)),
                progress: (i + 1) as f64,
                total: Some(total_items as f64),
                message: Some(format!(
                    "Processing item {} of {} ({:.1}%)",
                    i + 1,
                    total_items,
                    percentage
                )),
            };

            context
                .peer
                .notify_progress(progress_param)
                .await
                .map_err(|e| {
                    McpError::internal_error(format!("Failed to send progress: {}", e), None)
                })?;

            results.push(format!("item_{}_processed", i));
        }

        Ok(CallToolResult::success(vec![
            Content::text(format!("Batch operation completed: {} items", total_items)),
            Content::json(json!({
                "items_processed": total_items,
                "results": results
            })),
        ]))
    }

    /// Download data with progress notifications
    #[tool(
        description = "Simulate downloading data with progress notifications. \
                       Demonstrates progress with size-based tracking.",
        annotations(readOnlyHint = false)
    )]
    async fn download_data(
        &self,
        Parameters(params): Parameters<DownloadDataParams>,
        context: RequestContext<RoleServer>,
    ) -> Result<CallToolResult, McpError> {
        self.increment_operation_count().await;

        tracing::info!(
            "Downloading {} MB from '{}'",
            params.size_mb,
            params.url
        );

        let total_mb = params.size_mb;
        let chunks = 20; // Download in 20 chunks

        for i in 0..chunks {
            // Simulate chunk download
            sleep(Duration::from_millis(100)).await;

            let downloaded_mb = (total_mb as f64 / chunks as f64) * (i + 1) as f64;
            let percentage = (downloaded_mb / total_mb as f64) * 100.0;

            // Send progress notification
            let progress_param = ProgressNotificationParam {
                progress_token: ProgressToken(NumberOrString::String(format!(
                    "download_{}",
                    i
                ))),
                progress: downloaded_mb,
                total: Some(total_mb as f64),
                message: Some(format!(
                    "Downloaded {:.1}/{} MB ({:.1}%)",
                    downloaded_mb, total_mb, percentage
                )),
            };

            context
                .peer
                .notify_progress(progress_param)
                .await
                .map_err(|e| {
                    McpError::internal_error(format!("Failed to send progress: {}", e), None)
                })?;
        }

        // Final notification
        let progress_param = ProgressNotificationParam {
            progress_token: ProgressToken(NumberOrString::String("complete".to_string())),
            progress: total_mb as f64,
            total: Some(total_mb as f64),
            message: Some("Download complete".to_string()),
        };

        context
            .peer
            .notify_progress(progress_param)
            .await
            .map_err(|e| {
                McpError::internal_error(format!("Failed to send progress: {}", e), None)
            })?;

        Ok(CallToolResult::success(vec![
            Content::text(format!(
                "Successfully downloaded {} MB from '{}'",
                total_mb, params.url
            )),
            Content::json(json!({
                "url": params.url,
                "size_mb": total_mb,
                "status": "complete"
            })),
        ]))
    }

    /// Get server statistics
    #[tool(
        description = "Get server statistics including operation count",
        annotations(readOnlyHint = true)
    )]
    async fn get_stats(&self) -> Result<CallToolResult, McpError> {
        let state = self.state.lock().await;

        Ok(CallToolResult::success(vec![
            Content::text(format!(
                "Total operations performed: {}",
                state.operation_count
            )),
            Content::json(json!({
                "operation_count": state.operation_count
            })),
        ]))
    }
}

// ============================================================================
// ServerHandler Trait Implementation
// ============================================================================

#[tool_handler]
impl ServerHandler for ProgressServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo {
            protocol_version: ProtocolVersion::V_2024_11_05,
            capabilities: ServerCapabilities::builder()
                .enable_tools()
                .build(),
            server_info: Implementation {
                name: "progress-mcp-server".to_string(),
                version: env!("CARGO_PKG_VERSION").to_string(),
            },
            instructions: Some(
                "Progress notifications demo server. Tools:\n\
                - process_large_file: Process file with progress tracking\n\
                - analyze_text: Analyze text with progress (no total)\n\
                - batch_operation: Batch processing with percentage\n\
                - download_data: Simulate download with size tracking\n\
                - get_stats: Get server statistics"
                    .to_string(),
            ),
        }
    }

    async fn initialize(
        &self,
        _request: InitializeRequestParam,
        _context: RequestContext<RoleServer>,
    ) -> Result<InitializeResult, McpError> {
        tracing::info!("Progress server initialized");
        Ok(self.get_info())
    }
}

// ============================================================================
// Main Entry Point
// ============================================================================

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "progress_mcp_server=info".into()),
        )
        .with(tracing_subscriber::fmt::layer().with_writer(std::io::stderr))
        .init();

    tracing::info!("Starting Progress MCP Server");

    // Create server instance
    let server = ProgressServer::new();

    // Serve over stdio
    let connection = server.serve(stdio()).await?;

    tracing::info!("Server running, waiting for requests");

    // Wait for shutdown
    let quit_reason = connection.waiting().await?;
    tracing::info!("Server shutdown: {:?}", quit_reason);

    Ok(())
}

// ============================================================================
// Tests
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tool_router_registration() {
        let router = ProgressServer::tool_router();

        assert!(router.has_route("process_large_file"));
        assert!(router.has_route("analyze_text"));
        assert!(router.has_route("batch_operation"));
        assert!(router.has_route("download_data"));
        assert!(router.has_route("get_stats"));

        let tools = router.list_all();
        assert_eq!(tools.len(), 5);
    }
}
