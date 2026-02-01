# with-me

**Claude Asks the Right Questions**

> Building something new? Claude helps you clarify what you need.
> No setup. No dependencies. (Just Claude Code itself.)

## Example

```
You: /with-me:good-question
Claude: Let's clarify your requirements. I'll ask a series of questions.

Question 1: What problem are you trying to solve?

• Automate a repetitive task
• Analyze or visualize data
• Build a user-facing application
• Something else

You: Build a user-facing application

Claude: Question 2: Who is the primary user?

• Internal team members
• External customers
• Both

You: External customers

Claude: Question 3: What's the main user goal?

You: Complete checkout quickly

Claude: Got it. Let's build a customer-facing application focused on
fast checkout. Ready to start implementation?

[Claude then generates a structured requirement specification]
```

> **After convergence**: Claude automatically generates a structured requirement specification including acceptance criteria, edge cases, and implementation guidance.

---

## Demo

![Adaptive Questioning Demo](https://h315uk3.github.io/symbiosis/assets/video/demo-with-me-questions.gif)

---

## Key Features

- **Adaptive Questioning** - Each question builds on previous answers
- **5 Dimensions** - Systematically covers purpose, data, behavior, constraints, quality
- **Information Theory** - Shannon Entropy measures uncertainty, EIG selects optimal questions
- **Bayesian Convergence** - Beliefs update with each answer until clarity is achieved
- **Local-First** - All data stays on your machine, no external services
- **Zero Dependencies** - Pure Python standard library only

---

## Documentation

- **[Technical Overview](./docs/technical-overview.md)** - Architecture, information theory, configuration, and design principles

---

## Installation

See [main README](../../README.md#installation) for installation instructions.

**Requirements:**
- Python 3.11+
- Claude Code CLI

---

## License

GNU AGPL v3 - [LICENSE](../../LICENSE)
