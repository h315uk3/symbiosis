#!/bin/bash
set -u
# Suggest promotions from patterns to skills or agents

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CLAUDE_DIR="${CLAUDE_DIR:-$PROJECT_ROOT/.claude}"
TRACKER_FILE="$CLAUDE_DIR/as-you/pattern-tracker.json"

# Output empty array if no tracker
if [ ! -f "$TRACKER_FILE" ]; then
	echo "[]"
	exit 0
fi

# Use jq to process everything
jq '[
    .promotion_candidates[] |
    . as $candidate |
    $candidate.pattern as $pattern |

    # Get contexts from patterns
    ($TRACKER.patterns[$pattern].contexts // []) as $contexts |

    # Determine type based on context analysis
    (
        if ($contexts | join(" ") | test("analyze|generate|validate|check|review|test|build|deploy|run|execute|create|update|delete|fix"; "i")) then
            "agent"
        else
            "skill"
        end
    ) as $type |

    # Generate suggested name (kebab-case from pattern)
    ($pattern | ascii_downcase | gsub("_"; "-")) as $suggested_name |

    # Generate description from contexts (first 100 chars)
    (
        if ($contexts | length) > 0 then
            ($contexts[0:3] | join(" ") | gsub("\\[[0-9][0-9]:[0-9][0-9]\\] "; "") | gsub(" +"; " ") | .[0:100])
        else
            ""
        end
    ) as $description |

    {
        type: $type,
        pattern: $pattern,
        suggested_name: $suggested_name,
        count: $candidate.count,
        sessions: $candidate.sessions,
        contexts: $contexts,
        suggested_description: $description,
        reason: $candidate.reason
    }
]' --argjson TRACKER "$(cat "$TRACKER_FILE")" "$TRACKER_FILE"
