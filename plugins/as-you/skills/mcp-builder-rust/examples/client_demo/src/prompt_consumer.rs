//! Example 3: Prompt Consumer
//!
//! This example demonstrates:
//! - Connecting to an MCP server via stdio
//! - Listing available prompts
//! - Getting prompts without arguments
//! - Getting prompts with arguments
//! - Handling prompt messages
//! - Proper cleanup
//!
//! Prerequisites:
//!   This example uses the macros_demo_server which provides various prompts.
//!
//! Usage:
//!   cargo run --bin prompt_consumer

use rmcp::{ServiceExt, model::GetPromptRequestParam, transport::TokioChildProcess};
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

    tracing::info!("Starting MCP prompt consumer demo");

    // 1. Create transport - Connect to macros_demo_server
    let transport = TokioChildProcess::new(
        Command::new("cargo")
            .arg("run")
            .arg("--manifest-path")
            .arg("../macros_demo_server/Cargo.toml")
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

    // 4. List all prompts
    tracing::info!("Fetching available prompts...");
    let prompts = client.list_all_prompts().await?;

    if prompts.is_empty() {
        tracing::warn!("No prompts available from this server");
    } else {
        tracing::info!("Available prompts: {}", prompts.len());

        for prompt in &prompts {
            tracing::info!("  - {} : {}", prompt.name, prompt.description.as_deref().unwrap_or(""));
            if let Some(args) = &prompt.arguments {
                tracing::info!("    Arguments: {:?}", args);
            }
        }

        tracing::info!("");

        // 5. Get simple prompts (no arguments)
        for prompt in &prompts {
            // Skip prompts that require arguments for this simple demo
            if prompt.arguments.is_some() && !prompt.arguments.as_ref().unwrap().is_empty() {
                continue;
            }

            tracing::info!("Getting prompt: {}", prompt.name);

            match client.get_prompt(GetPromptRequestParam {
                name: prompt.name.clone(),
                arguments: None,
            }).await {
                Ok(result) => {
                    tracing::info!("Prompt description: {:?}", result.description);
                    tracing::info!("Messages ({}):", result.messages.len());

                    for (i, msg) in result.messages.iter().enumerate() {
                        tracing::info!("  Message {}:", i + 1);
                        tracing::info!("    Role: {:?}", msg.role);

                        // Extract text from content
                        let text = msg.content.text().unwrap_or_default();
                        let preview = if text.len() > 200 {
                            format!("{}...", &text[..200])
                        } else {
                            text.to_string()
                        };
                        tracing::info!("    Content: {}", preview);
                    }
                }
                Err(e) => {
                    tracing::error!("Failed to get prompt '{}': {}", prompt.name, e);
                }
            }

            tracing::info!("");
        }

        // 6. Get a prompt with arguments (code_review example)
        if prompts.iter().any(|p| p.name == "code_review") {
            tracing::info!("Getting code_review prompt with arguments...");

            let result = client.get_prompt(GetPromptRequestParam {
                name: "code_review".into(),
                arguments: Some(
                    serde_json::json!({
                        "language": "rust",
                        "file_path": "src/main.rs",
                        "focus_areas": ["performance", "safety"]
                    })
                    .as_object()
                    .cloned()
                ),
            }).await?;

            tracing::info!("Code review prompt messages:");
            for (i, msg) in result.messages.iter().enumerate() {
                tracing::info!("  Message {}:", i + 1);
                tracing::info!("    Role: {:?}", msg.role);

                let text = msg.content.text().unwrap_or_default();
                let preview = if text.len() > 300 {
                    format!("{}...", &text[..300])
                } else {
                    text.to_string()
                };
                tracing::info!("    Content: {}", preview);
            }

            tracing::info!("");
        }

        // 7. Get writing_assistant prompt with arguments
        if prompts.iter().any(|p| p.name == "writing_assistant") {
            tracing::info!("Getting writing_assistant prompt with arguments...");

            let result = client.get_prompt(GetPromptRequestParam {
                name: "writing_assistant".into(),
                arguments: Some(
                    serde_json::json!({
                        "topic": "Rust async programming",
                        "style": "technical",
                        "length": "medium"
                    })
                    .as_object()
                    .cloned()
                ),
            }).await?;

            tracing::info!("Writing assistant prompt:");
            for msg in &result.messages {
                let text = msg.content.text().unwrap_or_default();
                tracing::info!("  {}", text);
            }

            tracing::info!("");
        }
    }

    // 8. Cleanup
    tracing::info!("Shutting down client...");
    client.cancel().await?;

    tracing::info!("Client shutdown complete");
    Ok(())
}
