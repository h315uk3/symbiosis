//! Sampling MCP Server Example
//!
//! This example demonstrates the sampling feature, which allows the MCP server
//! to request LLM capabilities from the client. This enables servers to leverage
//! AI processing for complex tasks without implementing their own LLM.
//!
//! Features demonstrated:
//! - Requesting LLM completions from the client
//! - Setting model preferences (intelligence, speed, cost priorities)
//! - Handling streaming and non-streaming responses
//! - Different use cases (analysis, summarization, translation, etc.)
//!
//! Usage:
//!   cargo run
//!
//! Test with MCP Inspector:
//!   cargo build --release
//!   npx @modelcontextprotocol/inspector ./target/release/sampling-mcp-server

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
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

// ============================================================================
// Data Models
// ============================================================================

#[derive(Debug, Deserialize, schemars::JsonSchema)]
struct AnalyzeTextParams {
    /// Text to analyze
    text: String,
    /// Analysis focus (e.g., "sentiment", "keywords", "structure")
    #[serde(default = "default_focus")]
    focus: String,
}

fn default_focus() -> String {
    "general".to_string()
}

#[derive(Debug, Deserialize, schemars::JsonSchema)]
struct SummarizeParams {
    /// Text to summarize
    text: String,
    /// Maximum summary length in words
    #[serde(default = "default_summary_length")]
    max_length: usize,
}

fn default_summary_length() -> usize {
    100
}

#[derive(Debug, Deserialize, schemars::JsonSchema)]
struct TranslateParams {
    /// Text to translate
    text: String,
    /// Target language
    target_language: String,
}

#[derive(Debug, Deserialize, schemars::JsonSchema)]
struct AnswerQuestionParams {
    /// Question to answer
    question: String,
    /// Optional context information
    context: Option<String>,
}

#[derive(Debug, Deserialize, schemars::JsonSchema)]
struct CompareOptionsParams {
    /// Options to compare (comma-separated)
    options: String,
    /// Comparison criteria
    criteria: String,
}

// ============================================================================
// Server State
// ============================================================================

#[derive(Default)]
struct ServerState {
    sampling_count: u64,
}

// ============================================================================
// Server Implementation
// ============================================================================

#[derive(Clone)]
pub struct SamplingServer {
    state: Arc<Mutex<ServerState>>,
    tool_router: ToolRouter<SamplingServer>,
}

impl SamplingServer {
    pub fn new() -> Self {
        Self {
            state: Arc::new(Mutex::new(ServerState::default())),
            tool_router: Self::tool_router(),
        }
    }

    async fn increment_sampling_count(&self) {
        let mut state = self.state.lock().await;
        state.sampling_count += 1;
    }
}

// ============================================================================
// Tool Implementations
// ============================================================================

#[tool_router]
impl SamplingServer {
    /// Analyze text using client's LLM
    #[tool(
        description = "Analyze text using AI. The server requests the client's LLM to perform \
                       analysis based on the specified focus area.",
        annotations(readOnlyHint = true)
    )]
    async fn analyze_with_ai(
        &self,
        Parameters(params): Parameters<AnalyzeTextParams>,
        context: RequestContext<RoleServer>,
    ) -> Result<CallToolResult, McpError> {
        self.increment_sampling_count().await;

        tracing::info!("Analyzing text with focus: {}", params.focus);

        // Request LLM completion from client
        let response = context
            .peer
            .create_message(CreateMessageRequestParam {
                messages: vec![SamplingMessage {
                    role: Role::User,
                    content: Content::text(format!(
                        "Analyze the following text with focus on '{}':\n\n{}",
                        params.focus, params.text
                    )),
                }],
                model_preferences: Some(ModelPreferences {
                    hints: Some(vec![ModelHint {
                        name: Some("claude-3-5-sonnet-20241022".to_string()),
                    }]),
                    intelligence_priority: Some(0.8),
                    speed_priority: Some(0.5),
                    cost_priority: Some(0.3),
                }),
                system_prompt: Some("You are a helpful text analysis assistant.".to_string()),
                include_context: Some(IncludeContext::None),
                temperature: Some(0.7),
                max_tokens: 500,
                stop_sequences: None,
                metadata: None,
            })
            .await
            .map_err(|e| {
                McpError::internal_error(format!("Failed to request LLM: {}", e), None)
            })?;

        // Extract text content from response
        let analysis = response
            .content
            .text()
            .unwrap_or("No analysis generated".to_string());

        Ok(CallToolResult::success(vec![
            Content::text(format!("Analysis (focus: {}):\n\n{}", params.focus, analysis)),
            Content::json(json!({
                "focus": params.focus,
                "analysis": analysis,
                "model": response.model,
                "stop_reason": format!("{:?}", response.stop_reason)
            })),
        ]))
    }

    /// Generate summary using client's LLM
    #[tool(
        description = "Generate a concise summary of the given text using AI.",
        annotations(readOnlyHint = true)
    )]
    async fn generate_summary(
        &self,
        Parameters(params): Parameters<SummarizeParams>,
        context: RequestContext<RoleServer>,
    ) -> Result<CallToolResult, McpError> {
        self.increment_sampling_count().await;

        tracing::info!(
            "Generating summary with max length: {} words",
            params.max_length
        );

        // Request LLM completion from client
        let response = context
            .peer
            .create_message(CreateMessageRequestParam {
                messages: vec![SamplingMessage {
                    role: Role::User,
                    content: Content::text(format!(
                        "Summarize the following text in no more than {} words:\n\n{}",
                        params.max_length, params.text
                    )),
                }],
                model_preferences: Some(ModelPreferences {
                    hints: Some(vec![ModelHint {
                        name: Some("claude-3-5-sonnet-20241022".to_string()),
                    }]),
                    intelligence_priority: Some(0.6),
                    speed_priority: Some(0.7),
                    cost_priority: Some(0.5),
                }),
                system_prompt: Some("You are a concise summarization assistant.".to_string()),
                include_context: Some(IncludeContext::None),
                temperature: Some(0.5),
                max_tokens: params.max_length * 2, // Rough token estimate
                stop_sequences: None,
                metadata: None,
            })
            .await
            .map_err(|e| {
                McpError::internal_error(format!("Failed to request LLM: {}", e), None)
            })?;

        let summary = response
            .content
            .text()
            .unwrap_or("No summary generated".to_string());

        Ok(CallToolResult::success(vec![
            Content::text(format!("Summary:\n\n{}", summary)),
            Content::json(json!({
                "summary": summary,
                "max_length": params.max_length,
                "model": response.model
            })),
        ]))
    }

    /// Translate text using client's LLM
    #[tool(
        description = "Translate text to a target language using AI.",
        annotations(readOnlyHint = true)
    )]
    async fn translate_text(
        &self,
        Parameters(params): Parameters<TranslateParams>,
        context: RequestContext<RoleServer>,
    ) -> Result<CallToolResult, McpError> {
        self.increment_sampling_count().await;

        tracing::info!("Translating to: {}", params.target_language);

        // Request LLM completion from client
        let response = context
            .peer
            .create_message(CreateMessageRequestParam {
                messages: vec![SamplingMessage {
                    role: Role::User,
                    content: Content::text(format!(
                        "Translate the following text to {}:\n\n{}",
                        params.target_language, params.text
                    )),
                }],
                model_preferences: Some(ModelPreferences {
                    hints: Some(vec![ModelHint {
                        name: Some("claude-3-5-sonnet-20241022".to_string()),
                    }]),
                    intelligence_priority: Some(0.7),
                    speed_priority: Some(0.6),
                    cost_priority: Some(0.4),
                }),
                system_prompt: Some("You are a professional translator.".to_string()),
                include_context: Some(IncludeContext::None),
                temperature: Some(0.3),
                max_tokens: 1000,
                stop_sequences: None,
                metadata: None,
            })
            .await
            .map_err(|e| {
                McpError::internal_error(format!("Failed to request LLM: {}", e), None)
            })?;

        let translation = response
            .content
            .text()
            .unwrap_or("No translation generated".to_string());

        Ok(CallToolResult::success(vec![
            Content::text(format!("Translation:\n\n{}", translation)),
            Content::json(json!({
                "translation": translation,
                "target_language": params.target_language,
                "model": response.model
            })),
        ]))
    }

    /// Answer question using client's LLM
    #[tool(
        description = "Answer a question using AI, optionally with provided context.",
        annotations(readOnlyHint = true)
    )]
    async fn answer_question(
        &self,
        Parameters(params): Parameters<AnswerQuestionParams>,
        context: RequestContext<RoleServer>,
    ) -> Result<CallToolResult, McpError> {
        self.increment_sampling_count().await;

        tracing::info!("Answering question: {}", params.question);

        // Build prompt with optional context
        let prompt = if let Some(ctx) = params.context {
            format!(
                "Given the following context:\n\n{}\n\nAnswer the question: {}",
                ctx, params.question
            )
        } else {
            format!("Answer the following question: {}", params.question)
        };

        // Request LLM completion from client
        let response = context
            .peer
            .create_message(CreateMessageRequestParam {
                messages: vec![SamplingMessage {
                    role: Role::User,
                    content: Content::text(prompt),
                }],
                model_preferences: Some(ModelPreferences {
                    hints: Some(vec![ModelHint {
                        name: Some("claude-3-5-sonnet-20241022".to_string()),
                    }]),
                    intelligence_priority: Some(0.9),
                    speed_priority: Some(0.4),
                    cost_priority: Some(0.3),
                }),
                system_prompt: Some(
                    "You are a knowledgeable assistant that provides accurate answers.".to_string(),
                ),
                include_context: Some(IncludeContext::None),
                temperature: Some(0.7),
                max_tokens: 800,
                stop_sequences: None,
                metadata: None,
            })
            .await
            .map_err(|e| {
                McpError::internal_error(format!("Failed to request LLM: {}", e), None)
            })?;

        let answer = response
            .content
            .text()
            .unwrap_or("No answer generated".to_string());

        Ok(CallToolResult::success(vec![
            Content::text(format!("Answer:\n\n{}", answer)),
            Content::json(json!({
                "question": params.question,
                "answer": answer,
                "had_context": params.context.is_some(),
                "model": response.model
            })),
        ]))
    }

    /// Compare options using client's LLM
    #[tool(
        description = "Compare multiple options based on given criteria using AI.",
        annotations(readOnlyHint = true)
    )]
    async fn compare_options(
        &self,
        Parameters(params): Parameters<CompareOptionsParams>,
        context: RequestContext<RoleServer>,
    ) -> Result<CallToolResult, McpError> {
        self.increment_sampling_count().await;

        tracing::info!("Comparing options by: {}", params.criteria);

        // Request LLM completion from client
        let response = context
            .peer
            .create_message(CreateMessageRequestParam {
                messages: vec![SamplingMessage {
                    role: Role::User,
                    content: Content::text(format!(
                        "Compare the following options based on '{}':\n\nOptions: {}\n\n\
                         Provide a detailed comparison and recommendation.",
                        params.criteria, params.options
                    )),
                }],
                model_preferences: Some(ModelPreferences {
                    hints: Some(vec![ModelHint {
                        name: Some("claude-3-5-sonnet-20241022".to_string()),
                    }]),
                    intelligence_priority: Some(0.8),
                    speed_priority: Some(0.5),
                    cost_priority: Some(0.4),
                }),
                system_prompt: Some(
                    "You are an analytical assistant that provides balanced comparisons."
                        .to_string(),
                ),
                include_context: Some(IncludeContext::None),
                temperature: Some(0.6),
                max_tokens: 1000,
                stop_sequences: None,
                metadata: None,
            })
            .await
            .map_err(|e| {
                McpError::internal_error(format!("Failed to request LLM: {}", e), None)
            })?;

        let comparison = response
            .content
            .text()
            .unwrap_or("No comparison generated".to_string());

        Ok(CallToolResult::success(vec![
            Content::text(format!("Comparison:\n\n{}", comparison)),
            Content::json(json!({
                "options": params.options,
                "criteria": params.criteria,
                "comparison": comparison,
                "model": response.model
            })),
        ]))
    }

    /// Get server statistics
    #[tool(
        description = "Get server statistics including sampling count",
        annotations(readOnlyHint = true)
    )]
    async fn get_stats(&self) -> Result<CallToolResult, McpError> {
        let state = self.state.lock().await;

        Ok(CallToolResult::success(vec![
            Content::text(format!(
                "Total sampling requests: {}",
                state.sampling_count
            )),
            Content::json(json!({
                "sampling_count": state.sampling_count
            })),
        ]))
    }
}

// ============================================================================
// ServerHandler Trait Implementation
// ============================================================================

#[tool_handler]
impl ServerHandler for SamplingServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo {
            protocol_version: ProtocolVersion::V_2024_11_05,
            capabilities: ServerCapabilities::builder()
                .enable_tools()
                .enable_sampling()
                .build(),
            server_info: Implementation {
                name: "sampling-mcp-server".to_string(),
                version: env!("CARGO_PKG_VERSION").to_string(),
            },
            instructions: Some(
                "Sampling demo server. Tools:\n\
                - analyze_with_ai: Analyze text using AI\n\
                - generate_summary: Generate summary using AI\n\
                - translate_text: Translate text using AI\n\
                - answer_question: Answer questions using AI\n\
                - compare_options: Compare options using AI\n\
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
        tracing::info!("Sampling server initialized");
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
                .unwrap_or_else(|_| "sampling_mcp_server=info".into()),
        )
        .with(tracing_subscriber::fmt::layer().with_writer(std::io::stderr))
        .init();

    tracing::info!("Starting Sampling MCP Server");

    // Create server instance
    let server = SamplingServer::new();

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
        let router = SamplingServer::tool_router();

        assert!(router.has_route("analyze_with_ai"));
        assert!(router.has_route("generate_summary"));
        assert!(router.has_route("translate_text"));
        assert!(router.has_route("answer_question"));
        assert!(router.has_route("compare_options"));
        assert!(router.has_route("get_stats"));

        let tools = router.list_all();
        assert_eq!(tools.len(), 6);
    }
}
