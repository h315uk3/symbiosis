# As You

**"I (Claude) act as you" - AI learns and mimics your habits**

Claude learns from your work patterns and builds knowledge automatically from your explicit notes.

**Version:** 0.3.0

---

## How It Works

### Automatic Learning Flow

```
1. During Session
   /as-you:learn "Investigating authentication feature bug"
   → Saved to .claude/as_you/session_notes.local.md

2. On SessionEnd (Automatic)
   → Archive session_notes.local.md
   → Save as .claude/as_you/session_archive/2026-01-22.md

3. Pattern Analysis & Scoring (Automatic)
   → Extract patterns from archive
   → Calculate BM25 distinctiveness scores (rare terms score higher)
   → Apply time decay (30-day half-life)
   → Track Bayesian confidence
   → Schedule SM-2 memory reviews
   → Compute composite scores
   → Auto-merge similar patterns (Levenshtein distance)
   → Save to .claude/as_you/pattern_tracker.json

4. Promotion Notification (Automatic)
   → Display patterns with high composite scores + confidence
   → Viewable with /as-you:memory
   → Thompson Sampling balances proven vs. uncertain patterns

5. Knowledge Application (Manual)
   → /as-you:apply to get pattern context
   → /as-you:memory to promote patterns to skills/agents
   → Save workflows for reuse
```

Patterns are automatically extracted from your session notes using statistical intelligence, building your personal knowledge base over time.

---

## Available Commands

```bash
# Learning (note taking + pattern capture)
/as-you:learn "text"     # Add timestamped note
/as-you:learn            # Learning dashboard (interactive)

# Memory (pattern analysis + confidence tracking)
/as-you:memory           # Memory dashboard with v0.3.0 scoring

# Apply (workflows + pattern context)
/as-you:apply "name"     # Save workflow
/as-you:apply            # Use patterns and workflows (interactive)

# Help
/as-you:help             # Show detailed documentation
```

---

## Key Features

### Local-First Architecture
- **No auth, no backend, no external APIs** - Completely local execution
- **Privacy by design** - Your data never leaves your machine
- **No telemetry** - Zero tracking or analytics

### Statistical Intelligence (v0.3.0)
- **BM25 Scoring** - Distinctiveness ranking based on term rarity (replaces TF-IDF)
- **Time Decay** - Exponential decay prioritizes recent patterns (configurable half-life)
- **Bayesian Confidence** - Tracks certainty with mean, variance, and confidence intervals
- **SM-2 Memory** - Spaced repetition scheduling for optimal review timing
- **Thompson Sampling** - Balances exploration (uncertain patterns) vs. exploitation (proven patterns)
- **Composite Scoring** - Weighted combination of multiple metrics

### Pattern Management
- **Automatic Extraction** - Patterns emerge from 3+ similar observations
- **Automatic Merging** - Similar patterns unified using Levenshtein distance and BK-trees
- **Context-Aware Retrieval** - Get relevant patterns for current task
- **Workflow Capture** - Save and reuse action sequences

### Interactive Commands
- **Simple dialog interface** - Clear options, minimal friction
- **Configurable algorithms** - Tune weights and parameters in `config/as-you.json`
- **Pure Python implementation** - Testable, maintainable code using Python standard library

---

## What's New in v0.3.0

### Enhanced Scoring System
- **BM25** replaces TF-IDF for distinctiveness ranking (rare terms score higher)
- **Time Decay** with configurable half-life (default: 30 days)
- **Composite Score** combines BM25 (40%) + PMI (30%) + Time Decay (30%)
- Weights configurable in `config/as-you.json`

### Confidence Tracking
- **Bayesian Learning** tracks pattern quality with mean and variance
- **95% Confidence Intervals** show probability ranges
- High confidence patterns weighted more in recommendations

### Memory Management
- **SM-2 Algorithm** schedules optimal review intervals
- **Easiness Factor** adapts to your recall performance
- Patterns reviewed at increasing intervals (1, 6, 15, 37+ days)

### Exploration-Exploitation Balance
- **Thompson Sampling** selects patterns probabilistically
- Balances:
  - Proven patterns (high confidence, high scores)
  - Uncertain patterns (need more data)
- Optimizes long-term knowledge building

### Unified Commands
- **7 → 4 commands** for simpler, more focused workflows
- `/learn` combines note-taking and pattern viewing
- `/memory` enhanced with all v0.3.0 scoring
- `/apply` integrates workflows and context retrieval
- `/help` updated with comprehensive documentation

---

## Configuration

**File:** `plugins/as-you/config/as-you.json`

```json
{
  "version": 1,
  "scoring": {
    "bm25": {
      "enabled": true,
      "k1": 1.5,        // Term frequency saturation
      "b": 0.75         // Length normalization
    },
    "pmi": {
      "enabled": true,
      "min_cooccurrence": 2,
      "window_size": 5
    },
    "time_decay": {
      "enabled": true,
      "half_life_days": 30  // Adjust for faster/slower decay
    },
    "weights": {
      "bm25": 0.4,          // Distinctiveness weight
      "pmi": 0.3,           // Co-occurrence weight
      "time_decay": 0.3     // Recency weight
    }
  },
  "memory": {
    "sm2": {
      "enabled": true,
      "initial_easiness": 2.5,
      "min_easiness": 1.3
    }
  },
  "confidence": {
    "bayesian": {
      "enabled": true,
      "prior_mean": 0.5,     // Neutral prior
      "prior_variance": 0.04
    },
    "thompson_sampling": {
      "enabled": true,
      "initial_alpha": 1.0,
      "initial_beta": 1.0
    }
  },
  "promotion": {
    "threshold": 0.3,         // Minimum composite score
    "min_observations": 3,    // Minimum frequency
    "min_confidence": 0.6     // Minimum Bayesian confidence
  }
}
```

### Tuning Tips

**Increase recent pattern importance:**
- Lower `half_life_days` (e.g., 15)
- Increase `time_decay` weight (e.g., 0.4)

**Prioritize distinctiveness over recency:**
- Increase `bm25` weight (e.g., 0.5)
- Decrease `time_decay` weight (e.g., 0.2)

**More aggressive promotion:**
- Lower `threshold` (e.g., 0.2)
- Lower `min_confidence` (e.g., 0.5)

**Conservative promotion:**
- Raise `threshold` (e.g., 0.4)
- Raise `min_confidence` (e.g., 0.7)

---

## Data Storage

**Location:** `.claude/as_you/`

**Structure:**
```
.claude/as_you/
├── session_notes.local.md          # Current session (not committed)
├── session_archive/
│   ├── 2026-01-20.md
│   ├── 2026-01-21.md
│   └── 2026-01-22.md
├── pattern_tracker.json            # Pattern database with scores
├── workflows/
│   ├── api-endpoint-setup.md
│   └── react-component-testing.md
└── skill-usage-stats.json          # Knowledge base metrics
```

**Pattern Tracker Schema (v0.3.0):**
```json
{
  "patterns": {
    "pattern text": {
      "count": 5,
      "last_seen": "2026-01-22",
      "bm25_score": 0.842,
      "pmi_score": 0.651,
      "time_decay_score": 0.945,
      "composite_score": 0.812,
      "bayesian_state": {
        "mean": 0.75,
        "variance": 0.02
      },
      "sm2_state": {
        "easiness_factor": 2.6,
        "interval": 15,
        "repetitions": 3
      }
    }
  },
  "promotion_candidates": ["pattern1", "pattern2"],
  "cooccurrences": [...]
}
```

---

## Installation

See [marketplace README](../../README.md#installation) for installation instructions.

**Requirements:**
- Python 3.11+
- Claude Code CLI

**Verify installation:**
```bash
python3 --version  # Should show 3.11 or higher
/as-you:help       # Should display help
```

---

## Development

### Architecture

- **Pure Python** - Standard library only, no external dependencies
- **Doctest-driven** - Every function has executable examples
- **Modular design** - Each algorithm in separate file
- **Orchestrated workflow** - Unified pipeline in `analysis_orchestrator.py`

### Running Tests

```bash
# All doctests
python3 tests/run_doctests.py

# Single module
python3 plugins/as-you/as_you/lib/bm25_calculator.py --test

# With mise
mise run test           # All tests
mise run test:verbose   # Verbose output
```

### Code Style

```bash
mise run format  # Format with ruff
mise run lint    # Lint with ruff
```

---

## References

### Algorithms

- **BM25**: Robertson & Zaragoza (2009). "The Probabilistic Relevance Framework: BM25 and Beyond"
- **SM-2**: Wozniak (1990). "Optimization of Learning" - SuperMemo algorithm
- **Bayesian Inference**: Bishop (2006). "Pattern Recognition and Machine Learning"
- **Thompson Sampling**: Agrawal & Goyal (2012). "Analysis of Thompson Sampling for the Multi-armed Bandit Problem"

### Implementation

- Python standard library only
- No ML frameworks (TensorFlow, PyTorch, etc.)
- No NLP libraries (NLTK, spaCy, transformers)
- Transparent, auditable algorithms

---

## Philosophy

### Explicit Over Implicit
You choose what to capture. No automatic surveillance or passive tracking.

### Statistical Intelligence
Proven mathematical approaches, not black-box models. Every score is explainable.

### Local-First
Your data stays on your machine. No cloud services, no authentication required.

### Progressive Accumulation
Knowledge builds gradually from repeated patterns. Quality emerges from quantity.

---

## License

GNU AGPL v3 - [LICENSE](../../LICENSE)

---

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for version history.
