# Changelog

All notable changes to the As You plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-01-22

### Added

#### Scoring Algorithms
- **BM25 Calculator** - Improved relevance ranking with term frequency saturation and document length normalization (k1=1.5, b=0.75)
- **Ebbinghaus Forgetting Curve** - Replaces exponential decay; memory strength increases with repetition, modeling cognitive psychology research
- **Shannon Entropy** - Pattern diversity measurement; distinguishes general-purpose from specialized patterns
- **Composite Score Calculator** - Weighted combination of BM25 (40%), PMI (30%), and Ebbinghaus (30%)
- **Analysis Orchestrator** - Unified workflow replacing sequential script calls

#### Memory and Confidence
- **Bayesian Learning** - Confidence tracking with mean, variance, posterior updating based on composite scores
- **Thompson Sampling (Beta-Binomial)** - Exploration-exploitation balance for pattern selection with success/failure tracking

#### Configuration
- **Unified Config File** - `config/as-you.json` for all algorithm parameters
- **JSON Schema Validation** - `config/as-you.schema.json` for configuration structure
- **Configurable Weights** - Tune scoring weights without code changes

#### Testing and Benchmarking
- **Comprehensive Doctests** - 200+ doctests across all modules

### Changed

#### Command Restructuring (7 → 4 commands)
- **`/as-you:learn`** - Unified learning workflow (replaces `/note` and `/notes`)
  - Add notes with arguments
  - Learning dashboard without arguments
  - Pattern analysis integration
- **`/as-you:memory`** - Enhanced memory analysis (improved `/memory`)
  - BM25, Ebbinghaus, Shannon Entropy, Composite scores
  - Bayesian confidence display
  - Thompson Sampling recommendations
- **`/as-you:apply`** - Pattern application (replaces `/workflow-save` and `/workflows`)
  - Save workflows with arguments
  - Apply dashboard without arguments
  - Context-aware pattern retrieval
- **`/as-you:help`** - Comprehensive v0.3.0 documentation (improved `/help`)

#### Algorithm Improvements
- **BM25 replaces TF-IDF** - Better handling of term frequency saturation and document length normalization
- **Ebbinghaus replaces exponential decay** - Memory strength grows with repetition; cognitive psychology-based forgetting curve
- **Shannon Entropy** - Measures pattern diversity across contexts (sessions, categories)
- **Bayesian confidence tracking** - Sequential belief updating with posterior mean and variance
- **Thompson Sampling** - Beta-Binomial exploration-exploitation for pattern selection

### Improved
- **Configuration Management** - Enhanced `common.py` with settings validation
- **Error Handling** - Better error messages and recovery
- **Code Organization** - Modular design with clear separation of concerns
- **Documentation** - Comprehensive inline documentation and examples

### Technical Details

#### New Modules
- `as_you/lib/bm25_calculator.py` - BM25 relevance scoring
- `as_you/lib/ebbinghaus_calculator.py` - Ebbinghaus forgetting curve (replaces time decay)
- `as_you/lib/shannon_entropy_calculator.py` - Shannon entropy for pattern diversity
- `as_you/lib/bayesian_learning.py` - Bayesian confidence tracking
- `as_you/lib/thompson_sampling.py` - Thompson Sampling (Beta-Binomial)
- `as_you/lib/composite_score_calculator.py` - Multi-metric scoring (BM25, PMI, Ebbinghaus)
- `as_you/lib/analysis_orchestrator.py` - Unified analysis workflow

#### Modules Kept for Future Use
- `as_you/lib/sm2_memory.py` - SM-2 spaced repetition (implemented but not integrated; planned for v0.4.0)
- `as_you/lib/time_decay_calculator.py` - Exponential decay (deprecated; use ebbinghaus_calculator.py)

#### Updated Modules
- `as_you/lib/common.py` - Configuration loading and validation
- `plugins/as-you/config/as-you.json` - Centralized settings
- `plugins/as-you/config/as-you.schema.json` - Configuration schema

#### Testing Infrastructure
- `tests/run_doctests.py` - Comprehensive doctest runner
- `tests/validate_plugins.py` - Configuration validation

### Backward Compatibility
- **Data Format** - v0.3.0 adds new fields to existing pattern_tracker.json
- **No Migration Required** - New scoring fields automatically added on first run
- **Old Commands** - Backed up in `commands/.backup-v0.2.0/`

## [0.2.0] - Previous Version

### Added
- TF-IDF scoring for pattern relevance
- PMI (Pointwise Mutual Information) for co-occurrence analysis
- Pattern promotion system to skills/agents
- Workflow management (save and execute)
- Knowledge base integration
- Interactive command interface

### Features
- Pattern detection from session notes
- Automatic pattern merging (Levenshtein distance)
- Promotion candidates based on composite scores
- Session archiving
- Note history browsing

## [0.1.0] - Initial Release

### Added
- Basic note taking (`/as-you:note`)
- Session notes (`/as-you:notes`)
- Pattern detection
- Session archiving on end
- Local-only storage
- Privacy-first architecture

---

## Migration Guide (v0.2.0 → v0.3.0)

### For Users

**No action required.** v0.3.0 is backward compatible.

1. **First Run**: New scoring algorithms will automatically initialize
2. **Existing Data**: Pattern tracker will be enhanced with new fields
3. **Commands**: Old command names in `.backup-v0.2.0/` for reference

**Recommended:**
- Review new `/as-you:help` for v0.3.0 features
- Try `/as-you:memory` to see new scoring
- Configure weights in `config/as-you.json` if desired

### For Developers

**Breaking Changes:**
- Command structure changed (7 → 4 commands)
- Scoring system replaced (TF-IDF → BM25)
- New configuration file required

**Migration Steps:**
1. Update command references in documentation
2. Review `config/as-you.json` for tuning opportunities
3. Run `mise run test` to verify all doctests pass
4. Test commands interactively in Claude Code

---

## Upgrade Instructions

### From v0.2.0 to v0.3.0

1. **Pull latest code:**
   ```bash
   git pull origin main
   ```

2. **Verify Python version:**
   ```bash
   python3 --version  # Should be 3.11+
   ```

3. **Run tests:**
   ```bash
   mise run test
   ```

4. **Try new commands:**
   ```bash
   /as-you:learn "Testing v0.3.0 upgrade"
   /as-you:memory
   ```

5. **Review configuration:**
   - Check `plugins/as-you/config/as-you.json`
   - Adjust weights if needed

---

## Performance Improvements

### v0.3.0 Benchmarks

**Operation Performance** (vs. targets):
- Note add: 0.002s (target: 0.5s) ✅
- BM25 calculation (100 patterns): 0.007s (target: 1.0s) ✅
- Time decay calculation (100 patterns): 0.001s (target: 0.5s) ✅
- Composite score calculation: 0.003s (target: 0.5s) ✅

**All operations significantly under performance targets.**

### Memory Usage
- Pattern tracker: ~100KB for 100 patterns
- Archive: ~10KB per session
- Workflows: ~5KB each

---

## Known Issues

### v0.3.0
- PMI calculation not yet integrated into AnalysisOrchestrator (planned for v0.3.1)
- Pattern merging not yet using new composite scores (planned for v0.3.1)
- SM-2 spaced repetition not integrated (implemented but deferred to v0.4.0)

### Workarounds
- PMI scores still calculated but not used in composite score
- Pattern merging uses Levenshtein distance as before
- SM-2 module exists but not called from AnalysisOrchestrator

---

## Future Plans

### v0.3.1 (Planned)
- Integrate PMI into composite scoring
- Use composite scores for pattern merging
- Enhanced similarity detection with BK-tree

### v0.4.0 (Planned)
- SM-2 review prompts and UI
- Pattern review workflow
- Memory consolidation features
- Export/import patterns

### v1.0.0 (Future)
- Multi-project pattern sharing
- Advanced pattern analytics
- Custom scoring algorithms
- Integration with more Claude Code features

---

## Support

**Issues**: https://github.com/h315uk3/as_you/issues
**Documentation**: `/as-you:help`
**License**: GNU AGPL v3

---

**Note**: This is a living document. New features and improvements are added regularly based on usage patterns and user feedback.
