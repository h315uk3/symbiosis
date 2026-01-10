//! Basic MCP Server Example
//!
//! This example demonstrates a simple MCP server with:
//! - Calculator tools (add, subtract, multiply, divide)
//! - Echo tool for testing
//! - Resource access (configuration)
//! - Prompt templates
//!
//! Run with: cargo run

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
};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::sync::Arc;
use tokio::io::{stdin, stdout};
use tokio::sync::Mutex;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

// ============================================================================
// Data Models
// ============================================================================

/// Parameters for arithmetic operations
#[derive(Debug, Deserialize, schemars::JsonSchema)]
struct ArithmeticParams {
    /// First number
    a: f64,
    /// Second number
    b: f64,
}

/// Parameters for echo tool
#[derive(Debug, Deserialize, schemars::JsonSchema)]
struct EchoParams {
    /// Message to echo back
    message: String,
}

/// Parameters for calculation prompt
#[derive(Debug, Deserialize, schemars::JsonSchema)]
struct CalculationPromptArgs {
    /// Type of calculation (e.g., "financial", "scientific")
    calculation_type: String,
    /// Description of what to calculate
    description: String,
}

/// Server state
#[derive(Default)]
struct ServerState {
    /// Counter for tracking number of operations
    operation_count: u64,
}

// ============================================================================
// Server Implementation
// ============================================================================

#[derive(Clone)]
pub struct BasicServer {
    state: Arc<Mutex<ServerState>>,
    tool_router: ToolRouter<BasicServer>,
    prompt_router: PromptRouter<BasicServer>,
}

impl BasicServer {
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
impl BasicServer {
    /// Add two numbers
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

    /// Subtract two numbers
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

    /// Multiply two numbers
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

    /// Divide two numbers
    #[tool(
        description = "Divide first number by second number",
        annotations(readOnlyHint = true, idempotentHint = true)
    )]
    async fn calculator_divide(
        &self,
        Parameters(params): Parameters<ArithmeticParams>,
    ) -> Result<CallToolResult, McpError> {
        self.increment_operation_count().await;

        // Validate: division by zero
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

    /// Echo a message back
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
// Prompt Implementations
// ============================================================================

#[prompt_router]
impl BasicServer {
    /// Generate a calculation prompt
    #[prompt(
        name = "calculation_helper",
        description = "Generate a prompt to help with calculations"
    )]
    async fn calculation_helper_prompt(
        &self,
        Parameters(args): Parameters<CalculationPromptArgs>,
        _context: RequestContext<RoleServer>,
    ) -> Result<GetPromptResult, McpError> {
        let messages = vec![
            PromptMessage::new_text(
                PromptMessageRole::User,
                format!(
                    "I need help with a {} calculation.\n\nDescription: {}\n\nAvailable tools:\n- calculator_add\n- calculator_subtract\n- calculator_multiply\n- calculator_divide\n\nPlease help me solve this calculation step by step.",
                    args.calculation_type,
                    args.description
                ),
            ),
        ];

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
impl ServerHandler for BasicServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo {
            protocol_version: ProtocolVersion::V_2024_11_05,
            capabilities: ServerCapabilities::builder()
                .enable_tools()
                .enable_prompts()
                .enable_resources()
                .build(),
            server_info: Implementation {
                name: "basic-mcp-server".to_string(),
                version: env!("CARGO_PKG_VERSION").to_string(),
            },
            instructions: Some(
                "Basic MCP server providing calculator tools. Available tools: \
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
            resources: vec![
                RawResource::new("config://server", "Server Configuration".to_string())
                    .with_description("Current server configuration and status")
                    .with_mime_type("application/json")
                    .no_annotation(),
            ],
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
                        "name": "basic-mcp-server",
                        "version": env!("CARGO_PKG_VERSION"),
                        "protocol_version": "2024-11-05"
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
                .unwrap_or_else(|_| "basic_mcp_server=info".into()),
        )
        .with(tracing_subscriber::fmt::layer().with_writer(std::io::stderr))
        .init();

    tracing::info!("Starting Basic MCP Server");

    // Create server instance
    let server = BasicServer::new();

    // Serve over stdio
    let transport = (stdin(), stdout());
    let connection = server.serve(transport).await?;

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

    #[tokio::test]
    async fn test_calculator_add() {
        let server = BasicServer::new();
        let params = ArithmeticParams { a: 5.0, b: 3.0 };

        let result = server
            .calculator_add(Parameters(
                serde_json::to_value(params).unwrap().as_object().unwrap().clone(),
            ))
            .await;

        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_calculator_divide_by_zero() {
        let server = BasicServer::new();
        let params = ArithmeticParams { a: 5.0, b: 0.0 };

        let result = server
            .calculator_divide(Parameters(
                serde_json::to_value(params).unwrap().as_object().unwrap().clone(),
            ))
            .await;

        assert!(result.is_err());
    }

    #[test]
    fn test_tool_router_registration() {
        let router = BasicServer::tool_router();

        assert!(router.has_route("calculator_add"));
        assert!(router.has_route("calculator_subtract"));
        assert!(router.has_route("calculator_multiply"));
        assert!(router.has_route("calculator_divide"));
        assert!(router.has_route("echo"));
        assert!(router.has_route("get_stats"));

        let tools = router.list_all();
        assert_eq!(tools.len(), 6);
    }

    #[test]
    fn test_prompt_router_registration() {
        let router = BasicServer::prompt_router();

        assert!(router.has_route("calculation_helper"));

        let prompts = router.list_all();
        assert_eq!(prompts.len(), 1);
    }
}
