//! HTTP MCP Server Example
//!
//! This example demonstrates an MCP server with HTTP (Streamable HTTP) transport.
//! It provides the same calculator tools as the basic server, but accessible over HTTP.
//!
//! Features:
//! - HTTP transport with session management
//! - Multi-client support
//! - Graceful shutdown
//! - Optional authentication middleware
//!
//! Usage:
//!   cargo run                    # Run HTTP server on port 3000
//!   cargo run -- --stdio         # Run with stdio transport (for testing)
//!   cargo run -- --port 8080     # Run HTTP server on custom port

use anyhow::Result;
use rmcp::{
    ErrorData as McpError, RoleServer, ServerHandler, ServiceExt,
    handler::server::{
        router::{prompt::PromptRouter, tool::ToolRouter},
        wrapper::Parameters,
    },
    model::*,
    prompt, prompt_handler, prompt_router,
    service::RequestContext,
    tool, tool_handler, tool_router,
    transport::{
        stdio,
        streamable_http_server::{
            StreamableHttpService, StreamableHttpServerConfig,
            session::local::LocalSessionManager,
        },
    },
};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::sync::Arc;
use tokio::io::{stdin, stdout};
use tokio::sync::Mutex;
use tokio_util::sync::CancellationToken;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

// ============================================================================
// Data Models
// ============================================================================

#[derive(Debug, Deserialize, schemars::JsonSchema)]
struct ArithmeticParams {
    /// First number
    a: f64,
    /// Second number
    b: f64,
}

#[derive(Debug, Deserialize, schemars::JsonSchema)]
struct EchoParams {
    /// Message to echo back
    message: String,
}

#[derive(Debug, Deserialize, schemars::JsonSchema)]
struct CalculationPromptArgs {
    /// Type of calculation (e.g., "financial", "scientific")
    calculation_type: String,
    /// Description of what to calculate
    description: String,
}

#[derive(Default)]
struct ServerState {
    operation_count: u64,
}

// ============================================================================
// Server Implementation
// ============================================================================

#[derive(Clone)]
pub struct HttpServer {
    state: Arc<Mutex<ServerState>>,
    tool_router: ToolRouter<HttpServer>,
    prompt_router: PromptRouter<HttpServer>,
}

impl HttpServer {
    pub fn new() -> Self {
        Self {
            state: Arc::new(Mutex::new(ServerState::default())),
            tool_router: Self::tool_router(),
            prompt_router: Self::prompt_router(),
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
impl HttpServer {
    #[tool(
        description = "Add two numbers together",
        annotations(readOnlyHint = true, idempotentHint = true)
    )]
    async fn calculator_add(
        &self,
        Parameters(params): Parameters<ArithmeticParams>,
    ) -> Result<CallToolResult, McpError> {
        self.increment_operation_count().await;
        let result = params.a + params.b;

        Ok(CallToolResult::success(vec![
            Content::text(format!("{} + {} = {}", params.a, params.b, result)),
            Content::json(json!({
                "operation": "add",
                "a": params.a,
                "b": params.b,
                "result": result
            })),
        ]))
    }

    #[tool(
        description = "Subtract second number from first number",
        annotations(readOnlyHint = true, idempotentHint = true)
    )]
    async fn calculator_subtract(
        &self,
        Parameters(params): Parameters<ArithmeticParams>,
    ) -> Result<CallToolResult, McpError> {
        self.increment_operation_count().await;
        let result = params.a - params.b;

        Ok(CallToolResult::success(vec![
            Content::text(format!("{} - {} = {}", params.a, params.b, result)),
            Content::json(json!({
                "operation": "subtract",
                "a": params.a,
                "b": params.b,
                "result": result
            })),
        ]))
    }

    #[tool(
        description = "Multiply two numbers together",
        annotations(readOnlyHint = true, idempotentHint = true)
    )]
    async fn calculator_multiply(
        &self,
        Parameters(params): Parameters<ArithmeticParams>,
    ) -> Result<CallToolResult, McpError> {
        self.increment_operation_count().await;
        let result = params.a * params.b;

        Ok(CallToolResult::success(vec![
            Content::text(format!("{} × {} = {}", params.a, params.b, result)),
            Content::json(json!({
                "operation": "multiply",
                "a": params.a,
                "b": params.b,
                "result": result
            })),
        ]))
    }

    #[tool(
        description = "Divide first number by second number",
        annotations(readOnlyHint = true, idempotentHint = true)
    )]
    async fn calculator_divide(
        &self,
        Parameters(params): Parameters<ArithmeticParams>,
    ) -> Result<CallToolResult, McpError> {
        self.increment_operation_count().await;

        if params.b == 0.0 {
            return Err(McpError::invalid_params(
                "Cannot divide by zero",
                Some(json!({
                    "field": "b",
                    "value": params.b,
                    "suggestion": "Provide a non-zero divisor"
                })),
            ));
        }

        let result = params.a / params.b;

        Ok(CallToolResult::success(vec![
            Content::text(format!("{} ÷ {} = {}", params.a, params.b, result)),
            Content::json(json!({
                "operation": "divide",
                "a": params.a,
                "b": params.b,
                "result": result
            })),
        ]))
    }

    #[tool(
        description = "Echo a message back (useful for testing)",
        annotations(readOnlyHint = true, idempotentHint = true)
    )]
    async fn echo(
        &self,
        Parameters(params): Parameters<EchoParams>,
    ) -> Result<CallToolResult, McpError> {
        Ok(CallToolResult::success(vec![Content::text(format!(
            "Echo: {}",
            params.message
        ))]))
    }

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
// Prompt Implementations
// ============================================================================

#[prompt_router]
impl HttpServer {
    #[prompt(
        name = "calculation_helper",
        description = "Generate a prompt to help with calculations"
    )]
    async fn calculation_helper_prompt(
        &self,
        Parameters(args): Parameters<CalculationPromptArgs>,
        _context: RequestContext<RoleServer>,
    ) -> Result<GetPromptResult, McpError> {
        let messages = vec![PromptMessage::new_text(
            PromptMessageRole::User,
            format!(
                "I need help with a {} calculation.\n\nDescription: {}\n\nAvailable tools:\n- calculator_add\n- calculator_subtract\n- calculator_multiply\n- calculator_divide\n\nPlease help me solve this calculation step by step.",
                args.calculation_type, args.description
            ),
        )];

        Ok(GetPromptResult {
            description: Some(format!(
                "Calculation helper for {} calculation",
                args.calculation_type
            )),
            messages,
        })
    }
}

// ============================================================================
// ServerHandler Trait Implementation
// ============================================================================

#[tool_handler]
#[prompt_handler]
impl ServerHandler for HttpServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo {
            protocol_version: ProtocolVersion::V_2024_11_05,
            capabilities: ServerCapabilities::builder()
                .enable_tools()
                .enable_prompts()
                .enable_resources()
                .build(),
            server_info: Implementation {
                name: "http-mcp-server".to_string(),
                version: env!("CARGO_PKG_VERSION").to_string(),
            },
            instructions: Some(
                "HTTP MCP server providing calculator tools. Available tools: \
                calculator_add, calculator_subtract, calculator_multiply, calculator_divide, \
                echo, get_stats. Also provides calculation_helper prompt template."
                    .to_string(),
            ),
        }
    }

    async fn initialize(
        &self,
        _request: InitializeRequestParam,
        _context: RequestContext<RoleServer>,
    ) -> Result<InitializeResult, McpError> {
        tracing::info!("Server initialized");
        Ok(self.get_info())
    }

    async fn list_resources(
        &self,
        _request: Option<PaginatedRequestParam>,
        _context: RequestContext<RoleServer>,
    ) -> Result<ListResourcesResult, McpError> {
        Ok(ListResourcesResult {
            resources: vec![RawResource::new(
                "config://server",
                "Server Configuration".to_string(),
            )
            .with_description("Current server configuration and status")
            .with_mime_type("application/json")
            .no_annotation()],
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
            "config://server" => {
                let state = self.state.lock().await;
                let config = json!({
                    "server": {
                        "name": "http-mcp-server",
                        "version": env!("CARGO_PKG_VERSION"),
                        "protocol_version": "2024-11-05",
                        "transport": "HTTP (Streamable HTTP)"
                    },
                    "statistics": {
                        "operation_count": state.operation_count
                    },
                    "capabilities": {
                        "tools": true,
                        "prompts": true,
                        "resources": true
                    }
                });

                Ok(ReadResourceResult {
                    contents: vec![ResourceContents::text(
                        serde_json::to_string_pretty(&config)
                            .map_err(|e| McpError::internal_error(e.to_string(), None))?,
                        uri,
                    )],
                })
            }
            _ => Err(McpError::resource_not_found(
                "Resource not found",
                Some(json!({ "uri": uri })),
            )),
        }
    }

    async fn list_resource_templates(
        &self,
        _request: Option<PaginatedRequestParam>,
        _context: RequestContext<RoleServer>,
    ) -> Result<ListResourceTemplatesResult, McpError> {
        Ok(ListResourceTemplatesResult {
            resource_templates: Vec::new(),
            next_cursor: None,
            meta: None,
        })
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
                .unwrap_or_else(|_| "http_mcp_server=info".into()),
        )
        .with(tracing_subscriber::fmt::layer().with_writer(std::io::stderr))
        .init();

    // Parse command line arguments
    let args: Vec<String> = std::env::args().collect();
    let mut use_stdio = false;
    let mut port = 3000u16;

    for (i, arg) in args.iter().enumerate() {
        match arg.as_str() {
            "--stdio" => use_stdio = true,
            "--port" => {
                if let Some(port_str) = args.get(i + 1) {
                    port = port_str.parse().unwrap_or(3000);
                }
            }
            _ => {}
        }
    }

    if use_stdio {
        run_stdio().await
    } else {
        run_http(port).await
    }
}

async fn run_stdio() -> Result<()> {
    tracing::info!("Starting MCP Server with stdio transport");

    let server = HttpServer::new();
    let transport = (stdin(), stdout());
    let connection = server.serve(transport).await?;

    tracing::info!("Server running with stdio, waiting for requests");

    let quit_reason = connection.waiting().await?;
    tracing::info!("Server shutdown: {:?}", quit_reason);

    Ok(())
}

async fn run_http(port: u16) -> Result<()> {
    tracing::info!("Starting MCP Server with HTTP transport on port {}", port);

    let ct = CancellationToken::new();

    // Create HTTP service
    let service = StreamableHttpService::new(
        || Ok(HttpServer::new()),
        LocalSessionManager::default().into(),
        StreamableHttpServerConfig {
            cancellation_token: ct.child_token(),
            ..Default::default()
        },
    );

    // Setup router
    let router = axum::Router::new().nest_service("/mcp", service);

    // Bind and serve
    let addr = format!("0.0.0.0:{}", port);
    let listener = tokio::net::TcpListener::bind(&addr).await?;

    tracing::info!("HTTP server listening on http://{}/mcp", addr);
    tracing::info!("Press Ctrl+C to shutdown");
    tracing::info!("");
    tracing::info!("Test with curl:");
    tracing::info!(
        "  curl -X POST http://localhost:{}/mcp \\",
        port
    );
    tracing::info!("    -H 'Content-Type: application/json' \\");
    tracing::info!("    -d '{{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{{}}}}'");

    axum::serve(listener, router)
        .with_graceful_shutdown(async move {
            tokio::signal::ctrl_c().await.unwrap();
            tracing::info!("Shutdown signal received");
            ct.cancel();
        })
        .await?;

    tracing::info!("Server stopped");
    Ok(())
}

// ============================================================================
// Tests
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_calculator_add() {
        let server = HttpServer::new();
        let params = ArithmeticParams { a: 5.0, b: 3.0 };

        let result = server
            .calculator_add(Parameters(
                serde_json::to_value(params)
                    .unwrap()
                    .as_object()
                    .unwrap()
                    .clone(),
            ))
            .await;

        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_calculator_divide_by_zero() {
        let server = HttpServer::new();
        let params = ArithmeticParams { a: 5.0, b: 0.0 };

        let result = server
            .calculator_divide(Parameters(
                serde_json::to_value(params)
                    .unwrap()
                    .as_object()
                    .unwrap()
                    .clone(),
            ))
            .await;

        assert!(result.is_err());
    }

    #[test]
    fn test_tool_router_registration() {
        let router = HttpServer::tool_router();

        assert!(router.has_route("calculator_add"));
        assert!(router.has_route("calculator_subtract"));
        assert!(router.has_route("calculator_multiply"));
        assert!(router.has_route("calculator_divide"));
        assert!(router.has_route("echo"));
        assert!(router.has_route("get_stats"));

        let tools = router.list_all();
        assert_eq!(tools.len(), 6);
    }
}
