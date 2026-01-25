# As You - Technical Documentation

**Version:** 0.3.0

This document provides detailed technical information about the As You plugin's architecture, algorithms, configuration, and data structures.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Available Commands](#available-commands)
- [Statistical Intelligence](#statistical-intelligence)
- [Configuration](#configuration)
- [Data Storage](#data-storage)
- [Development](#development)
- [References](#references)
- [Philosophy](#philosophy)

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
   → Calculate BM25 relevance scores
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

## Statistical Intelligence

### v0.3.0 Scoring System

The plugin uses multiple statistical approaches to identify and prioritize patterns:

#### BM25 Scoring
- **Purpose**: Relevance ranking with term saturation (replaces TF-IDF)
- **How it works**: Accounts for term frequency saturation and document length normalization
- **Parameters**: `k1` (term frequency saturation), `b` (length normalization)

#### Time Decay
- **Purpose**: Prioritizes recent patterns over older ones
- **How it works**: Exponential decay with configurable half-life (default: 30 days)
- **Formula**: `score = base_score * exp(-λ * days_since_last_seen)`

#### Bayesian Confidence
- **Purpose**: Tracks certainty about pattern quality
- **How it works**: Maintains mean, variance, and 95% confidence intervals
- **Benefit**: High confidence patterns weighted more in recommendations

#### SM-2 Memory Algorithm
- **Purpose**: Spaced repetition scheduling for optimal review timing
- **How it works**: Adapts review intervals based on recall performance
- **Schedule**: Patterns reviewed at increasing intervals (1, 6, 15, 37+ days)
- **Parameters**: Easiness factor adapts to your recall success

#### Thompson Sampling
- **Purpose**: Balances exploration vs. exploitation
- **How it works**: Probabilistic pattern selection based on confidence distributions
- **Balances**:
  - Proven patterns (high confidence, high scores)
  - Uncertain patterns (need more data)
- **Benefit**: Optimizes long-term knowledge building

#### Composite Scoring
- **Purpose**: Weighted combination of multiple metrics
- **Default weights**:
  - BM25: 40% (relevance)
  - PMI: 30% (co-occurrence)
  - Time Decay: 30% (recency)
- **Configurable**: Adjust in `config/as-you.json`

### Pattern Management

- **Automatic Extraction**: Patterns emerge from 3+ similar observations
- **Automatic Merging**: Similar patterns unified using Levenshtein distance and BK-trees
- **Context-Aware Retrieval**: Get relevant patterns for current task
- **Workflow Capture**: Save and reuse action sequences

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
      "bm25": 0.4,          // Relevance weight
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

**Prioritize relevance over recency:**
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

## Contributing

See [CONTRIBUTING.md](../../../CONTRIBUTING.md) for development setup, testing, and contribution guidelines.
