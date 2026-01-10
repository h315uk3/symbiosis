//! Elicitation MCP Server Example
//!
//! This example demonstrates the elicitation feature, which allows the MCP server
//! to request additional information from the user interactively during tool execution.
//!
//! Features demonstrated:
//! - Collecting authentication credentials
//! - Requesting confirmation for destructive operations
//! - Gathering missing parameters
//!
//! Usage:
//!   cargo run
//!
//! Test with MCP Inspector:
//!   cargo build --release
//!   npx @modelcontextprotocol/inspector ./target/release/elicitation-mcp-server

use anyhow::Result;
use rmcp::{
    ErrorData as McpError, RoleServer, ServerHandler, ServiceExt, elicit_safe,
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
// Elicitation Data Models
// ============================================================================

/// GitHub authentication token
#[derive(Debug, Serialize, Deserialize, schemars::JsonSchema)]
#[schemars(description = "GitHub personal access token")]
pub struct GitHubToken {
    /// Personal access token (starts with ghp_, github_pat_, etc.)
    #[schemars(description = "GitHub personal access token")]
    pub token: String,
}

// Mark as safe for elicitation
elicit_safe!(GitHubToken);

/// Confirmation for destructive operations
#[derive(Debug, Serialize, Deserialize, schemars::JsonSchema)]
#[schemars(description = "Confirmation for destructive operation")]
pub struct DeletionConfirmation {
    /// Type 'DELETE' to confirm
    #[schemars(description = "Must be exactly 'DELETE' to confirm")]
    pub confirmation: String,
}

elicit_safe!(DeletionConfirmation);

/// Email subject when missing
#[derive(Debug, Serialize, Deserialize, schemars::JsonSchema)]
#[schemars(description = "Email subject")]
pub struct EmailSubject {
    /// Email subject line
    #[schemars(description = "Subject line for the email")]
    pub subject: String,
}

elicit_safe!(EmailSubject);

/// User information
#[derive(Debug, Serialize, Deserialize, schemars::JsonSchema)]
#[schemars(description = "User profile information")]
pub struct UserInfo {
    /// User's full name
    #[schemars(description = "Full name")]
    pub name: String,

    /// User's email address
    #[schemars(description = "Email address")]
    pub email: String,
}

elicit_safe!(UserInfo);

// ============================================================================
// Tool Parameters
// ============================================================================

#[derive(Debug, Deserialize, schemars::JsonSchema)]
struct SendEmailParams {
    /// Recipient email address
    recipient: String,
    /// Email subject (if empty, will be requested from user)
    #[serde(default)]
    subject: String,
    /// Email body
    body: String,
}

#[derive(Debug, Deserialize, schemars::JsonSchema)]
struct DeleteDataParams {
    /// Target to delete (e.g., "all", "user:123", "file:abc")
    target: String,
}

// ============================================================================
// Server State
// ============================================================================

#[derive(Default)]
struct ServerState {
    /// Cached GitHub token
    github_token: Option<String>,
    /// Cached user profile
    user_profile: Option<UserInfo>,
}

// ============================================================================
// Server Implementation
// ============================================================================

#[derive(Clone)]
pub struct ElicitationServer {
    state: Arc<Mutex<ServerState>>,
    tool_router: ToolRouter<ElicitationServer>,
}

impl ElicitationServer {
    pub fn new() -> Self {
        Self {
            state: Arc::new(Mutex::new(ServerState::default())),
            tool_router: Self::tool_router(),
        }
    }
}

// ============================================================================
// Tool Implementations
// ============================================================================

#[tool_router]
impl ElicitationServer {
    /// Login to GitHub (requests token via elicitation)
    #[tool(
        description = "Login to GitHub using a personal access token. Token will be requested securely.",
        annotations(destructiveHint = false)
    )]
    async fn github_login(
        &self,
        context: RequestContext<RoleServer>,
    ) -> Result<CallToolResult, McpError> {
        let mut state = self.state.lock().await;

        // Check if already logged in
        if let Some(cached_token) = &state.github_token {
            return Ok(CallToolResult::success(vec![
                Content::text("Already logged in to GitHub"),
                Content::json(json!({
                    "status": "already_authenticated",
                    "token_prefix": &cached_token[..7]
                })),
            ]));
        }

        // Request token from user via elicitation
        tracing::info!("Requesting GitHub token from user");
        let token_input = context
            .peer
            .elicit::<GitHubToken>(
                "Please provide your GitHub personal access token.\n\nYou can create one at: https://github.com/settings/tokens\n\nRequired scopes: repo, user".to_string()
            )
            .await
            .map_err(|e| McpError::internal_error(
                format!("Failed to elicit token: {}", e),
                None,
            ))?;

        match token_input {
            Some(token_data) => {
                // Validate token format
                if !token_data.token.starts_with("ghp_")
                    && !token_data.token.starts_with("github_pat_") {
                    return Err(McpError::invalid_params(
                        "Invalid token format. Token should start with 'ghp_' or 'github_pat_'",
                        Some(json!({
                            "suggestion": "Create a new personal access token at https://github.com/settings/tokens"
                        })),
                    ));
                }

                // Store token
                state.github_token = Some(token_data.token.clone());

                Ok(CallToolResult::success(vec![
                    Content::text("Successfully logged in to GitHub"),
                    Content::json(json!({
                        "status": "authenticated",
                        "token_prefix": &token_data.token[..7]
                    })),
                ]))
            }
            None => {
                // User cancelled
                Err(McpError::invalid_params(
                    "GitHub token is required for login",
                    Some(json!({
                        "reason": "user_cancelled",
                        "suggestion": "Run the tool again when you have a GitHub token"
                    })),
                ))
            }
        }
    }

    /// Logout from GitHub
    #[tool(
        description = "Logout from GitHub (clears cached token)",
        annotations(destructiveHint = false)
    )]
    async fn github_logout(&self) -> Result<CallToolResult, McpError> {
        let mut state = self.state.lock().await;
        state.github_token = None;

        Ok(CallToolResult::success(vec![
            Content::text("Logged out from GitHub"),
        ]))
    }

    /// Check GitHub authentication status
    #[tool(
        description = "Check if authenticated with GitHub",
        annotations(readOnlyHint = true)
    )]
    async fn github_status(&self) -> Result<CallToolResult, McpError> {
        let state = self.state.lock().await;

        let authenticated = state.github_token.is_some();
        let token_prefix = state
            .github_token
            .as_ref()
            .map(|t| &t[..7])
            .unwrap_or("none");

        Ok(CallToolResult::success(vec![
            Content::text(if authenticated {
                format!("Authenticated (token: {}...)", token_prefix)
            } else {
                "Not authenticated".to_string()
            }),
            Content::json(json!({
                "authenticated": authenticated,
                "token_prefix": token_prefix
            })),
        ]))
    }

    /// Delete data with confirmation
    #[tool(
        description = "Delete data with user confirmation. Requires explicit 'DELETE' confirmation.",
        annotations(destructiveHint = true)
    )]
    async fn delete_data(
        &self,
        Parameters(params): Parameters<DeleteDataParams>,
        context: RequestContext<RoleServer>,
    ) -> Result<CallToolResult, McpError> {
        // Request confirmation via elicitation
        tracing::info!("Requesting deletion confirmation for: {}", params.target);

        let confirmation = context
            .peer
            .elicit::<DeletionConfirmation>(format!(
                "⚠️  WARNING: This will DELETE '{}'.\n\nThis action CANNOT be undone.\n\nType 'DELETE' to confirm:",
                params.target
            ))
            .await
            .map_err(|e| McpError::internal_error(
                format!("Failed to elicit confirmation: {}", e),
                None,
            ))?;

        match confirmation {
            Some(conf) if conf.confirmation == "DELETE" => {
                // Perform deletion (simulated)
                tracing::info!("Deletion confirmed, deleting: {}", params.target);

                Ok(CallToolResult::success(vec![
                    Content::text(format!("Deleted: {}", params.target)),
                    Content::json(json!({
                        "status": "deleted",
                        "target": params.target
                    })),
                ]))
            }
            Some(conf) => {
                // Wrong confirmation
                Err(McpError::invalid_params(
                    format!("Invalid confirmation '{}'. Expected 'DELETE'", conf.confirmation),
                    Some(json!({
                        "expected": "DELETE",
                        "received": conf.confirmation
                    })),
                ))
            }
            None => {
                // User cancelled
                Ok(CallToolResult::success(vec![
                    Content::text("Deletion cancelled by user"),
                    Content::json(json!({
                        "status": "cancelled"
                    })),
                ]))
            }
        }
    }

    /// Send email with subject elicitation if missing
    #[tool(
        description = "Send an email. If subject is empty, will request from user.",
        annotations(destructiveHint = false)
    )]
    async fn send_email(
        &self,
        Parameters(params): Parameters<SendEmailParams>,
        context: RequestContext<RoleServer>,
    ) -> Result<CallToolResult, McpError> {
        // Get subject (elicit if empty)
        let subject = if params.subject.is_empty() {
            tracing::info!("Subject missing, requesting from user");

            let subject_input = context
                .peer
                .elicit::<EmailSubject>(
                    "Email subject is missing. Please provide a subject line:".to_string()
                )
                .await
                .map_err(|e| McpError::internal_error(
                    format!("Failed to elicit subject: {}", e),
                    None,
                ))?;

            match subject_input {
                Some(s) if !s.subject.is_empty() => s.subject,
                _ => {
                    return Err(McpError::invalid_params(
                        "Email subject is required",
                        None,
                    ));
                }
            }
        } else {
            params.subject
        };

        // Send email (simulated)
        tracing::info!("Sending email to {} with subject '{}'", params.recipient, subject);

        Ok(CallToolResult::success(vec![
            Content::text(format!(
                "Email sent to {}\nSubject: {}\nBody: {}",
                params.recipient, subject, params.body
            )),
            Content::json(json!({
                "status": "sent",
                "recipient": params.recipient,
                "subject": subject
            })),
        ]))
    }

    /// Get user profile (elicits if not cached)
    #[tool(
        description = "Get user profile information. Will request from user if not cached.",
        annotations(readOnlyHint = false)
    )]
    async fn get_user_profile(
        &self,
        context: RequestContext<RoleServer>,
    ) -> Result<CallToolResult, McpError> {
        let mut state = self.state.lock().await;

        // Check cache
        if let Some(profile) = &state.user_profile {
            return Ok(CallToolResult::success(vec![
                Content::text(format!("Name: {}\nEmail: {}", profile.name, profile.email)),
                Content::json(json!({
                    "name": profile.name,
                    "email": profile.email,
                    "cached": true
                })),
            ]));
        }

        // Request profile from user
        tracing::info!("Requesting user profile");

        let profile = context
            .peer
            .elicit::<UserInfo>("Please provide your profile information:".to_string())
            .await
            .map_err(|e| McpError::internal_error(
                format!("Failed to elicit user info: {}", e),
                None,
            ))?;

        match profile {
            Some(info) => {
                // Cache profile
                state.user_profile = Some(UserInfo {
                    name: info.name.clone(),
                    email: info.email.clone(),
                });

                Ok(CallToolResult::success(vec![
                    Content::text(format!("Name: {}\nEmail: {}", info.name, info.email)),
                    Content::json(json!({
                        "name": info.name,
                        "email": info.email,
                        "cached": false
                    })),
                ]))
            }
            None => {
                Err(McpError::invalid_params(
                    "User profile information is required",
                    None,
                ))
            }
        }
    }

    /// Clear cached user profile
    #[tool(
        description = "Clear cached user profile",
        annotations(destructiveHint = false)
    )]
    async fn clear_profile(&self) -> Result<CallToolResult, McpError> {
        let mut state = self.state.lock().await;
        state.user_profile = None;

        Ok(CallToolResult::success(vec![
            Content::text("User profile cleared"),
        ]))
    }
}

// ============================================================================
// ServerHandler Trait Implementation
// ============================================================================

#[tool_handler]
impl ServerHandler for ElicitationServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo {
            protocol_version: ProtocolVersion::V_2024_11_05,
            capabilities: ServerCapabilities::builder()
                .enable_tools()
                .build(),
            server_info: Implementation {
                name: "elicitation-mcp-server".to_string(),
                version: env!("CARGO_PKG_VERSION").to_string(),
            },
            instructions: Some(
                "Elicitation demo server. Tools:\n\
                - github_login: Login to GitHub (requests token)\n\
                - github_logout: Logout from GitHub\n\
                - github_status: Check authentication status\n\
                - delete_data: Delete data with confirmation\n\
                - send_email: Send email (requests subject if missing)\n\
                - get_user_profile: Get user profile (requests if not cached)\n\
                - clear_profile: Clear cached profile"
                    .to_string(),
            ),
        }
    }

    async fn initialize(
        &self,
        _request: InitializeRequestParam,
        _context: RequestContext<RoleServer>,
    ) -> Result<InitializeResult, McpError> {
        tracing::info!("Elicitation server initialized");
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
                .unwrap_or_else(|_| "elicitation_mcp_server=info".into()),
        )
        .with(tracing_subscriber::fmt::layer().with_writer(std::io::stderr))
        .init();

    tracing::info!("Starting Elicitation MCP Server");

    // Create server instance
    let server = ElicitationServer::new();

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
        let router = ElicitationServer::tool_router();

        assert!(router.has_route("github_login"));
        assert!(router.has_route("github_logout"));
        assert!(router.has_route("github_status"));
        assert!(router.has_route("delete_data"));
        assert!(router.has_route("send_email"));
        assert!(router.has_route("get_user_profile"));
        assert!(router.has_route("clear_profile"));

        let tools = router.list_all();
        assert_eq!(tools.len(), 7);
    }
}
