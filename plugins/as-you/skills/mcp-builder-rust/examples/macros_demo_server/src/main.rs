//! rmcp-macros Demonstration Server
//!
//! This example demonstrates all rmcp-macros features:
//! - #[tool], #[tool_router], #[tool_handler] for implementing MCP tools
//! - #[prompt], #[prompt_router], #[prompt_handler] for implementing prompts
//! - State management with macros
//! - Multiple routers combined
//! - All annotation types
//!
//! Features demonstrated:
//! - Tool macros with automatic JSON schema generation
//! - Prompt macros with typed arguments
//! - Combining tools and prompts in one server
//! - State management across tools
//! - Doc comments as descriptions
//! - Tool annotations (readOnly, destructive, etc.)
//! - Error handling patterns
//!
//! Usage:
//!   cargo run
//!
//! Test with MCP Inspector:
//!   cargo build --release
//!   npx @modelcontextprotocol/inspector ./target/release/macros-demo-mcp-server

use anyhow::Result;
use rmcp::{
    ErrorData as McpError, RoleServer, ServerHandler, ServiceExt,
    handler::server::{router::tool::ToolRouter, router::prompt::PromptRouter, wrapper::Parameters},
    model::*,
    service::RequestContext,
    tool, tool_handler, tool_router,
    prompt, prompt_handler, prompt_router,
    transport::stdio,
};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

// ============================================================================
// Data Models for Tools
// ============================================================================

/// Parameters for calculator operations
#[derive(Debug, Deserialize, schemars::JsonSchema)]
#[schemars(description = "Calculator operation parameters")]
struct CalcParams {
    /// First number
    #[schemars(description = "First operand")]
    a: f64,
    /// Second number
    #[schemars(description = "Second operand")]
    b: f64,
}

/// Parameters for counter operations
#[derive(Debug, Deserialize, schemars::JsonSchema)]
#[schemars(description = "Counter increment parameters")]
struct IncrementParams {
    /// Amount to increment by
    #[schemars(description = "Increment amount (default: 1)")]
    #[serde(default = "default_increment")]
    amount: i32,
}

fn default_increment() -> i32 {
    1
}

/// Parameters for echo tool
#[derive(Debug, Deserialize, schemars::JsonSchema)]
#[schemars(description = "Echo message parameters")]
struct EchoParams {
    /// Message to echo
    #[schemars(description = "Message to echo back")]
    message: String,
    /// Number of times to repeat
    #[schemars(description = "Repetition count (default: 1)")]
    #[serde(default = "default_repeat")]
    repeat: usize,
}

fn default_repeat() -> usize {
    1
}

// ============================================================================
// Data Models for Prompts
// ============================================================================

/// Arguments for code review prompt
#[derive(Debug, Deserialize, schemars::JsonSchema)]
#[schemars(description = "Code review parameters")]
struct CodeReviewArgs {
    /// Programming language
    #[schemars(description = "Programming language of the code")]
    language: String,
    /// File path or code snippet
    #[schemars(description = "Path to file or code snippet")]
    code: String,
    /// Focus areas (e.g., "security", "performance")
    #[schemars(description = "Areas to focus the review on")]
    focus_areas: Option<Vec<String>>,
}

/// Arguments for writing assistant prompt
#[derive(Debug, Deserialize, schemars::JsonSchema)]
#[schemars(description = "Writing assistant parameters")]
struct WritingArgs {
    /// Content type (email, blog, documentation, etc.)
    #[schemars(description = "Type of content to write")]
    content_type: String,
    /// Target audience
    #[schemars(description = "Who will read this content")]
    audience: String,
    /// Key points to cover
    #[schemars(description = "Main points to include")]
    key_points: Vec<String>,
}

/// Arguments for greeting prompt
#[derive(Debug, Deserialize, schemars::JsonSchema)]
#[schemars(description = "Greeting parameters")]
struct GreetingArgs {
    /// Name to greet
    #[schemars(description = "Name of the person")]
    name: String,
    /// Language for greeting
    #[schemars(description = "Language (default: English)")]
    #[serde(default = "default_language")]
    language: String,
}

fn default_language() -> String {
    "English".to_string()
}

// ============================================================================
// Server State
// ============================================================================

#[derive(Default)]
struct ServerState {
    /// Operation counter
    counter: i32,
    /// Total calculations performed
    calc_count: u64,
}

// ============================================================================
// Server Implementation
// ============================================================================

#[derive(Clone)]
pub struct MacrosDemoServer {
    state: Arc<Mutex<ServerState>>,
    tool_router: ToolRouter<MacrosDemoServer>,
    prompt_router: PromptRouter<MacrosDemoServer>,
}

impl MacrosDemoServer {
    pub fn new() -> Self {
        Self {
            state: Arc::new(Mutex::new(ServerState::default())),
            tool_router: Self::tool_router(),
            prompt_router: Self::prompt_router(),
        }
    }
}

// ============================================================================
// Tool Implementations
// ============================================================================

#[tool_router]
impl MacrosDemoServer {
    /// Add two numbers
    ///
    /// This tool demonstrates:
    /// - Automatic description from doc comment
    /// - JSON schema generation from Parameters<T>
    /// - readOnlyHint annotation
    #[tool(annotations(readOnlyHint = true))]
    async fn add(
        &self,
        Parameters(params): Parameters<CalcParams>,
    ) -> Result<CallToolResult, McpError> {
        let mut state = self.state.lock().await;
        state.calc_count += 1;

        let result = params.a + params.b;

        Ok(CallToolResult::success(vec![
            Content::text(format!("{} + {} = {}", params.a, params.b, result)),
            Content::json(json!({
                "operation": "add",
                "a": params.a,
                "b": params.b,
                "result": result,
                "calc_count": state.calc_count
            })),
        ]))
    }

    /// Subtract two numbers
    #[tool(annotations(readOnlyHint = true))]
    async fn subtract(
        &self,
        Parameters(params): Parameters<CalcParams>,
    ) -> Result<CallToolResult, McpError> {
        let mut state = self.state.lock().await;
        state.calc_count += 1;

        let result = params.a - params.b;

        Ok(CallToolResult::success(vec![
            Content::text(format!("{} - {} = {}", params.a, params.b, result)),
            Content::json(json!({
                "operation": "subtract",
                "result": result,
                "calc_count": state.calc_count
            })),
        ]))
    }

    /// Multiply two numbers
    #[tool(annotations(readOnlyHint = true))]
    async fn multiply(
        &self,
        Parameters(params): Parameters<CalcParams>,
    ) -> Result<CallToolResult, McpError> {
        let mut state = self.state.lock().await;
        state.calc_count += 1;

        let result = params.a * params.b;

        Ok(CallToolResult::success(vec![
            Content::text(format!("{} × {} = {}", params.a, params.b, result)),
            Content::json(json!({
                "operation": "multiply",
                "result": result,
                "calc_count": state.calc_count
            })),
        ]))
    }

    /// Divide two numbers
    ///
    /// Demonstrates error handling within a tool
    #[tool(annotations(readOnlyHint = true))]
    async fn divide(
        &self,
        Parameters(params): Parameters<CalcParams>,
    ) -> Result<CallToolResult, McpError> {
        if params.b == 0.0 {
            return Err(McpError::invalid_params(
                "Division by zero",
                Some(json!({
                    "error": "Cannot divide by zero",
                    "suggestion": "Use a non-zero divisor"
                })),
            ));
        }

        let mut state = self.state.lock().await;
        state.calc_count += 1;

        let result = params.a / params.b;

        Ok(CallToolResult::success(vec![
            Content::text(format!("{} ÷ {} = {}", params.a, params.b, result)),
            Content::json(json!({
                "operation": "divide",
                "result": result,
                "calc_count": state.calc_count
            })),
        ]))
    }

    /// Increment the server counter
    ///
    /// Demonstrates:
    /// - destructiveHint annotation (modifies state)
    /// - State management
    #[tool(annotations(destructiveHint = true))]
    async fn increment(
        &self,
        Parameters(params): Parameters<IncrementParams>,
    ) -> Result<CallToolResult, McpError> {
        let mut state = self.state.lock().await;
        state.counter += params.amount;

        Ok(CallToolResult::success(vec![
            Content::text(format!(
                "Counter incremented by {} to {}",
                params.amount, state.counter
            )),
            Content::json(json!({
                "counter": state.counter,
                "increment": params.amount
            })),
        ]))
    }

    /// Get current counter value
    #[tool(annotations(readOnlyHint = true))]
    async fn get_counter(&self) -> Result<CallToolResult, McpError> {
        let state = self.state.lock().await;

        Ok(CallToolResult::success(vec![
            Content::text(format!("Counter: {}", state.counter)),
            Content::json(json!({
                "counter": state.counter
            })),
        ]))
    }

    /// Reset the counter to zero
    ///
    /// Demonstrates destructiveHint for data-modifying operations
    #[tool(annotations(destructiveHint = true))]
    async fn reset_counter(&self) -> Result<CallToolResult, McpError> {
        let mut state = self.state.lock().await;
        let old_value = state.counter;
        state.counter = 0;

        Ok(CallToolResult::success(vec![
            Content::text(format!("Counter reset from {} to 0", old_value)),
            Content::json(json!({
                "old_value": old_value,
                "new_value": 0
            })),
        ]))
    }

    /// Echo a message back to the user
    ///
    /// Demonstrates:
    /// - Simple tool without state
    /// - Optional parameters with defaults
    /// - idempotentHint annotation
    #[tool(annotations(readOnlyHint = true, idempotentHint = true))]
    async fn echo(
        &self,
        Parameters(params): Parameters<EchoParams>,
    ) -> Result<CallToolResult, McpError> {
        let repeated = (0..params.repeat)
            .map(|_| params.message.clone())
            .collect::<Vec<_>>()
            .join(" ");

        Ok(CallToolResult::success(vec![
            Content::text(repeated.clone()),
            Content::json(json!({
                "message": params.message,
                "repeat": params.repeat,
                "result": repeated
            })),
        ]))
    }

    /// Get server statistics
    #[tool(annotations(readOnlyHint = true))]
    async fn get_stats(&self) -> Result<CallToolResult, McpError> {
        let state = self.state.lock().await;

        Ok(CallToolResult::success(vec![
            Content::text(format!(
                "Counter: {}, Calculations: {}",
                state.counter, state.calc_count
            )),
            Content::json(json!({
                "counter": state.counter,
                "calc_count": state.calc_count
            })),
        ]))
    }
}

// ============================================================================
// Prompt Implementations
// ============================================================================

#[prompt_router]
impl MacrosDemoServer {
    /// Simple greeting prompt
    ///
    /// Demonstrates:
    /// - Basic prompt with parameters
    /// - Returning Vec<PromptMessage>
    #[prompt]
    async fn greeting(
        &self,
        Parameters(args): Parameters<GreetingArgs>,
    ) -> Vec<PromptMessage> {
        vec![
            PromptMessage::new_text(
                PromptMessageRole::User,
                format!("Please greet {} in {}", args.name, args.language),
            ),
            PromptMessage::new_text(
                PromptMessageRole::Assistant,
                format!("Hello, {}! (in {})", args.name, args.language),
            ),
        ]
    }

    /// Code review prompt generator
    ///
    /// Demonstrates:
    /// - Returning GetPromptResult for full control
    /// - Optional parameters
    /// - Complex prompt construction
    #[prompt(
        name = "code_review",
        description = "Generate a structured code review prompt"
    )]
    async fn code_review(
        &self,
        Parameters(args): Parameters<CodeReviewArgs>,
    ) -> Result<GetPromptResult, McpError> {
        let focus_areas = args
            .focus_areas
            .unwrap_or_else(|| vec!["correctness".to_string(), "performance".to_string()]);

        let messages = vec![
            PromptMessage::new_text(
                PromptMessageRole::Assistant,
                format!("You are an expert {} code reviewer.", args.language),
            ),
            PromptMessage::new_text(
                PromptMessageRole::User,
                format!(
                    "Review the following {} code. Focus on: {}\n\nCode:\n{}",
                    args.language,
                    focus_areas.join(", "),
                    args.code
                ),
            ),
            PromptMessage::new_text(
                PromptMessageRole::Assistant,
                format!(
                    "I'll review your {} code focusing on {}. Let me analyze...",
                    args.language,
                    focus_areas.join(" and ")
                ),
            ),
        ];

        Ok(GetPromptResult {
            description: Some(format!(
                "Code review for {} focusing on {}",
                args.language,
                focus_areas.join(", ")
            )),
            messages,
        })
    }

    /// Writing assistant prompt
    ///
    /// Demonstrates:
    /// - Complex argument structure
    /// - Multiple key points handling
    #[prompt]
    async fn writing_assistant(
        &self,
        Parameters(args): Parameters<WritingArgs>,
    ) -> Result<GetPromptResult, McpError> {
        let key_points_text = args
            .key_points
            .iter()
            .enumerate()
            .map(|(i, point)| format!("{}. {}", i + 1, point))
            .collect::<Vec<_>>()
            .join("\n");

        let messages = vec![
            PromptMessage::new_text(
                PromptMessageRole::Assistant,
                format!(
                    "You are a professional {} writer for {}.",
                    args.content_type, args.audience
                ),
            ),
            PromptMessage::new_text(
                PromptMessageRole::User,
                format!(
                    "Write a {} for {}. Cover these key points:\n\n{}",
                    args.content_type, args.audience, key_points_text
                ),
            ),
        ];

        Ok(GetPromptResult {
            description: Some(format!(
                "{} for {} covering {} points",
                args.content_type,
                args.audience,
                args.key_points.len()
            )),
            messages,
        })
    }

    /// Simple help prompt without parameters
    ///
    /// Demonstrates:
    /// - Prompt without Parameters
    /// - Static prompt content
    #[prompt(description = "Get help on using this MCP server")]
    async fn help(&self) -> Vec<PromptMessage> {
        vec![
            PromptMessage::new_text(
                PromptMessageRole::Assistant,
                "I'm a demonstration MCP server showcasing rmcp-macros features.",
            ),
            PromptMessage::new_text(
                PromptMessageRole::User,
                "What can you help me with?",
            ),
            PromptMessage::new_text(
                PromptMessageRole::Assistant,
                "I provide:\n\
                - Calculator tools (add, subtract, multiply, divide)\n\
                - Counter tools (increment, get_counter, reset_counter)\n\
                - Echo tool for message repetition\n\
                - Code review prompts\n\
                - Writing assistant prompts\n\
                - Greeting prompts\n\n\
                All tools and prompts are implemented using rmcp-macros!",
            ),
        ]
    }
}

// ============================================================================
// ServerHandler Trait Implementation
// ============================================================================

#[tool_handler]
#[prompt_handler]
impl ServerHandler for MacrosDemoServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo {
            protocol_version: ProtocolVersion::V_2024_11_05,
            capabilities: ServerCapabilities::builder()
                .enable_tools()
                .enable_prompts()
                .build(),
            server_info: Implementation {
                name: "macros-demo-mcp-server".to_string(),
                version: env!("CARGO_PKG_VERSION").to_string(),
            },
            instructions: Some(
                "rmcp-macros demonstration server.\n\n\
                Tools:\n\
                - add, subtract, multiply, divide: Calculator operations\n\
                - increment, get_counter, reset_counter: Counter management\n\
                - echo: Message echo with repetition\n\
                - get_stats: Server statistics\n\n\
                Prompts:\n\
                - greeting: Personalized greeting\n\
                - code_review: Code review prompt generator\n\
                - writing_assistant: Writing help\n\
                - help: Server usage help"
                    .to_string(),
            ),
        }
    }

    async fn initialize(
        &self,
        _request: InitializeRequestParam,
        _context: RequestContext<RoleServer>,
    ) -> Result<InitializeResult, McpError> {
        tracing::info!("Macros demo server initialized");
        Ok(self.get_info())
    }

    // call_tool, list_tools, get_prompt, list_prompts are auto-generated by macros!
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
                .unwrap_or_else(|_| "macros_demo_mcp_server=info".into()),
        )
        .with(tracing_subscriber::fmt::layer().with_writer(std::io::stderr))
        .init();

    tracing::info!("Starting rmcp-macros Demo MCP Server");

    // Create server instance
    let server = MacrosDemoServer::new();

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
        let router = MacrosDemoServer::tool_router();

        // Check all tools are registered
        assert!(router.has_route("add"));
        assert!(router.has_route("subtract"));
        assert!(router.has_route("multiply"));
        assert!(router.has_route("divide"));
        assert!(router.has_route("increment"));
        assert!(router.has_route("get_counter"));
        assert!(router.has_route("reset_counter"));
        assert!(router.has_route("echo"));
        assert!(router.has_route("get_stats"));

        let tools = router.list_all();
        assert_eq!(tools.len(), 9);
    }

    #[test]
    fn test_prompt_router_registration() {
        let router = MacrosDemoServer::prompt_router();

        // Check all prompts are registered
        assert!(router.has_route("greeting"));
        assert!(router.has_route("code_review"));
        assert!(router.has_route("writing_assistant"));
        assert!(router.has_route("help"));

        let prompts = router.list_all();
        assert_eq!(prompts.len(), 4);
    }

    #[tokio::test]
    async fn test_calculator_operations() {
        let server = MacrosDemoServer::new();

        // Test add
        let params = CalcParams { a: 5.0, b: 3.0 };
        // Would need to create proper context to test, but router is verified above
    }
}
