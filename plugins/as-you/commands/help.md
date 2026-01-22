---
description: "As You v0.3.0 help: learn from work, build knowledge, apply patterns"
allowed-tools: []
---

# As You Plugin Help (v0.3.0)

**A personal memory plugin that learns from your work patterns using statistical intelligence**

---

## Core Commands

### 📚 `/as-you:learn [note]`

**Capture insights and build knowledge**

With argument:
- `/as-you:learn "your observation"` - Add timestamped note (auto-translated to English)

Without argument:
- Interactive dashboard with options:
  - Add notes
  - View note history (7 days)
  - Analyze patterns
  - Clear session notes

**Example:**
```
/as-you:learn "JWT tokens expire after 1 hour"
/as-you:learn "User.findById() null check is critical"
```

---

### 🧠 `/as-you:memory`

**Analyze patterns with advanced scoring**

Interactive memory dashboard with:
- Pattern analysis (BM25, time decay, composite scores)
- Bayesian confidence tracking
- SM-2 spaced repetition review
- Thompson Sampling recommendations
- Promotion candidate review
- Similar pattern detection
- Deep analysis with AI agent

**New in v0.3.0:**
- BM25 relevance scoring (replaces TF-IDF)
- Time decay with configurable half-life
- Composite score weighting
- Bayesian confidence intervals
- SM-2 memory review scheduling

---

### 🚀 `/as-you:apply [workflow]`

**Use learned patterns and workflows**

With argument:
- `/as-you:apply "workflow-name"` - Save recent work as workflow

Without argument:
- Interactive dashboard with options:
  - View/execute workflows
  - Get pattern context for current task
  - List all workflows
  - Save new workflow

**Pattern context features:**
- BM25 relevance matching
- Time-decayed recency
- Confidence-weighted recommendations
- Thompson Sampling (exploration/exploitation)

**Example:**
```
/as-you:apply "api-endpoint-setup"
/as-you:apply  # Browse and execute workflows
```

---

### ❓ `/as-you:help`

**Display this help guide**

---

## How It Works

### Learning Cycle

```
1. Capture → 2. Analyze → 3. Promote → 4. Apply
    ↑                                        ↓
    └────────────← Feedback Loop ←──────────┘
```

**1. Capture (Learn)**
- Add explicit notes during work
- Notes auto-archived on session end
- Pattern detection runs automatically

**2. Analyze (Memory)**
- BM25 calculates term relevance
- Time decay prioritizes recent patterns
- Composite scoring combines metrics
- Bayesian tracking builds confidence
- SM-2 schedules optimal reviews

**3. Promote**
- High-scoring patterns flagged
- AI determines Skill vs Agent
- Generate reusable components
- Update knowledge base

**4. Apply**
- Context-aware pattern retrieval
- Workflow execution
- Thompson Sampling balances exploration/exploitation

---

## Scoring System (v0.3.0)

### BM25 Score
- **What:** Relevance based on term frequency and document length
- **Range:** 0.0+ (unbounded, normalized for ranking)
- **Use:** Identifies distinctive, important patterns
- **Formula:** Saturation function with k1=1.5, b=0.75

### Time Decay Score
- **What:** Exponential decay based on last_seen date
- **Range:** 0.0 to 1.0
- **Use:** Prioritizes recent patterns
- **Half-life:** 30 days (configurable)
- **Formula:** 0.5^(days_elapsed / half_life)

### Composite Score
- **What:** Weighted combination of all metrics
- **Range:** 0.0 to 1.0
- **Use:** Final ranking for patterns
- **Weights:** BM25 (40%) + PMI (30%) + Time Decay (30%)
- **Config:** Adjustable in `config/as-you.json`

### Bayesian Confidence
- **What:** Confidence in pattern quality
- **Components:**
  - Mean: Expected quality (0-1)
  - Variance: Uncertainty
  - 95% CI: Probability range
- **Use:** Weight recommendations by certainty
- **Updates:** After each success/failure observation

### SM-2 Memory
- **What:** Spaced repetition scheduling
- **Components:**
  - Easiness Factor: Recall quality (min 1.3)
  - Interval: Days until next review
  - Repetitions: Consecutive successes
- **Use:** Optimal review timing
- **Algorithm:** SuperMemo 2 (1987)

### Thompson Sampling
- **What:** Exploration-exploitation balance
- **Distribution:** Beta(alpha, beta)
- **Use:** Select patterns for promotion/review
- **Balance:** Proven patterns vs. uncertain patterns

---

## Configuration

**Location:** `plugins/as-you/config/as-you.json`

**Key settings:**

```json
{
  "scoring": {
    "bm25": {"k1": 1.5, "b": 0.75},
    "time_decay": {"half_life_days": 30},
    "weights": {
      "bm25": 0.4,
      "pmi": 0.3,
      "time_decay": 0.3
    }
  },
  "confidence": {
    "bayesian": {"prior_mean": 0.5, "prior_variance": 0.04},
    "thompson_sampling": {"initial_alpha": 1.0, "initial_beta": 1.0}
  },
  "memory": {
    "sm2": {"initial_easiness": 2.5, "min_easiness": 1.3}
  }
}
```

**Tuning tips:**
- Increase `half_life_days` to keep old patterns longer
- Adjust `weights` to prioritize different scoring dimensions
- Change `prior_mean` for optimistic/pessimistic confidence

---

## Data Storage

**Location:** `.claude/as_you/`

**Files:**
- `session_notes.local.md` - Current session notes (local only)
- `session_archive/YYYY-MM-DD.md` - Archived notes
- `pattern_tracker.json` - Pattern database with scores
- `workflows/*.md` - Saved workflows
- `skill-usage-stats.json` - Knowledge base metrics

**Note:** All data stays local. No external services, no telemetry.

---

## Privacy & Philosophy

### Local-First
- No network calls
- No external services
- No authentication required
- Complete data ownership

### Explicit Over Implicit
- You choose what to capture
- No automatic surveillance
- Intentional knowledge building
- Transparent algorithms

### Statistical Intelligence
- BM25: Information retrieval (proven since 1994)
- SM-2: Spaced repetition (proven since 1987)
- Bayesian inference: Confidence tracking
- Thompson Sampling: Optimal exploration
- No black-box ML models

---

## Best Practices

### Good Notes
✅ Specific: "JWT validation in authMiddleware.js:42"
✅ Actionable: "Always check user.role before admin ops"
✅ Context-rich: "PostgreSQL EXPLAIN shows seq scan"

❌ Vague: "Fixed bug"
❌ Obvious: "Wrote code"
❌ Unactionable: "It's complicated"

### Pattern Emergence
- Patterns detected after 3+ occurrences
- High-scoring patterns (composite > 0.7) prioritized
- High-confidence patterns (Bayesian mean > 0.7) trusted
- Recent patterns (time decay > 0.75) preferred

### Workflow Capture
- Save after completing 5-20 related actions
- Use "generic" style for reusability
- Include context and rationale
- Test before relying on workflows

---

## Troubleshooting

**No patterns detected?**
- Add more specific notes (3+ similar observations needed)
- Wait for session end (analysis runs automatically)
- Run manual analysis: `/as-you:memory`

**Low scores for important patterns?**
- Check `last_seen` date (time decay may be low)
- Review BM25 score (may need more distinctive terms)
- Verify composite weights in config

**Uncertain confidence?**
- Pattern needs more observations
- Use pattern to build confidence
- Check Bayesian variance (high = uncertain)

**SM-2 review not working?**
- Pattern needs initial review
- Check interval hasn't elapsed yet
- Verify `last_review` date in tracker

---

## Version History

**v0.3.0 (Current)**
- BM25 scoring replaces TF-IDF
- Time decay with configurable half-life
- Composite score calculator
- Bayesian confidence tracking
- SM-2 spaced repetition
- Thompson Sampling
- Command restructuring (7 → 4 commands)
- Analysis orchestrator for unified workflow

**v0.2.0**
- TF-IDF scoring
- PMI co-occurrence analysis
- Pattern promotion system
- Workflow management
- Knowledge base integration

**v0.1.0**
- Initial release
- Basic note taking
- Pattern detection
- Session archiving

---

## Getting Help

**Documentation:** This help file
**Issues:** https://github.com/h315uk3/symbiosis/issues
**License:** MIT

---

## Quick Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `/as-you:learn "note"` | Add observation | `/as-you:learn "Use React.memo"` |
| `/as-you:learn` | Learning dashboard | Interactive note management |
| `/as-you:memory` | Analyze patterns | View scores, confidence, review |
| `/as-you:apply "name"` | Save workflow | `/as-you:apply "deploy-api"` |
| `/as-you:apply` | Use patterns | Get context, execute workflows |
| `/as-you:help` | Show help | This guide |

---

**Remember:** As You learns from what you explicitly capture. The more intentional notes you add, the better your personal knowledge base becomes.

Happy learning! 📚🧠🚀
