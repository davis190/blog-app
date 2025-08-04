---
title: "Part 2 — Quality in the Age of LLMs"
date: 2025-08-04T08:00:00-05:00
draft: false
description: "As we continue to look at the world of software development with AI, quality is always the first topic to come up. How do you know that you are producing quality. "
tags: [GenAI, LLM, AI SDLC, SDLC, Quality Engineering]
---

You can see part 1 [here](/post/008-ai-sdlc-hybrid-approach/index.html)

**“Ship faster, break… nothing.”**

In Part 1 we argued that AI collapses the gap between strategy and execution. The obvious next question: **How do we keep quality high when code ships every hour?** This post unpacks why classical Test-Driven Development (TDD) isn’t dead—but it is mutating—and how richer, AI-refined requirements become the new guardrail against hallucinations and regressions.

### **Why Speed Amplifies Quality Risk**

GenAI reduces the marginal cost of an iteration. That’s great—until mistakes propagate at lightning speed.

* **LLMs hallucinate.** A faulty schema migration or an insecure auth flow can be deployed minutes after it’s generated.  
* **Context fades.** When agents write 80% of the code, humans review a shrinking slice of the logic.  
* **Change compounds.** Incorrect or poorly written code can compound quickly serving as context for every following iteration.

The answer isn’t “slow down.” It’s to **bake quality into each micro-loop**—from prompt → code → test → deploy—in an automated, additive way.

### **TDD, Reversed:** 

### **Build → Lock → Guard**

| Classical TDD | AI-Accelerated Workflow |
| ----- | ----- |
| 1\. Write a failing test  2\. Write minimal code to pass  3\. Refactor | 1\. **Generate feature code** with an LLM  2\. **Human-in-the-Loop (HITL)** clicks through UI / runs service to validate behavior  3\. **Lock** behaviour by *auto-generating tests* against the known-good state iterating on tests until you have full coverage |

**Why flip the order?**

1. **Faster feedback.** Non-technical stakeholders validate a clickable prototype instead of reading Given/When/Then.  
2. **Concrete ground truth.** Tests are generated *after* behaviour is accepted, so they describe reality—not an idealised spec.   
3. **Context enrichment.** Generating test based on requirements and working code provides the AI with additional context by which to build robust tests  
4. **Validate everything.** Creating AI generated tests first is hard to validate without code and using unvalidated tests as context to generate code could be a harmful cycle.

#### **Practical recipe**

1. **Generate code:** Cursor, GitHub Copilot, Q Developer, or your in-house agent.  
2. **Review live:** Ephemeral preview URL for stakeholders to validate functionality to provide acceptance  
3. **Auto-write tests:** Using the requirements and the code write unit/integration tests, iterating until you get acceptable coverage  
4. **Pipeline guard:** Merge blocked unless the fresh tests pass and coverage delta ≥ target.

### **The Three-Layer Quality Stack**

| Layer | Purpose | Who/What Owns It | Cadence |
| ----- | ----- | ----- | ----- |
| **A. Human Exploratory** | Catch UX, domain, and “smell” issues | Product, QA, SMEs | Each feature build |
| **B. AI-Generated Regression** | Freeze accepted behaviour | LLM-driven test writers | Immediately after acceptance |
| **C. Classical Automation** | Deep logic, perf, security | Devs \+ existing CI tooling | Continuous / scheduled |

Layers B \+ C run in CI; Layer A is asynchronous but tight (hours, not sprints). Together they create a **high-frequency quality loop** that matches AI-driven delivery speed.

### **Requirements 2.0 — From Bullet Points to Context Blocks**

Bad requirements have always sunk projects. With AI, they become outright dangerous:

* Vague language fuels hallucinations.  
* Omitted edge cases break downstream auto-tests.  
* Slice-and-dice user stories may starve the model of context.

#### **Evolving pattern**

1. **Raw capture:** Zoom/Teams transcript, Figma comments, Jira ticket.  
2. **AI expansion agent:** Enrich with domain facts (“PCI rules”, “multi-tenant SaaS”, industry), architectural constraints, and acceptance criteria.  
3. **Context block:** A single, long-form artifact (Markdown/PR description) that feeds both code-generation and test-generation prompts.

**Net effect:** The richer the requirement, the *less* you need to micro-split stories. AI thrives on **coherent chunks**—think “feature-size prompt” instead of 4 “bite-sized” Jira cards.

### **Tooling Signals to Watch (2025-2026)**

| Capability | Emerging Tools\* | What to Evaluate |
| ----- | ----- | ----- |
| AI code review | Refraction, Qodo AICodium PR-Agent | Custom lint rules, OWASP checks |
| Test synthesis | DeepEval, Qodo AICodiumAI, Google Gemini Code Assist | Accuracy on complex branches, fixture reuse |
| Exploratory QA bots | Diffblue Cover, Replay.ai | Browser vs. API coverage, false-positive rate |
| Traceability graph | Graphite, Athenia, Neo4j plugins | Link density, query ease |
| Risk analytics | LinearB \+ GPT, Sleuth DevEx | Correlate deployment frequency & escaped defects |

\* Market is shifting monthly; run quarterly bake-offs rather than annual tool “lock-ins.” Also be aware that tools constantly leap frog each other. Don’t panic if you tool fall behind briefly as long as it continues to evolve and meet your needs

### **Conclusion & What’s Next**

AI hasn’t killed testing; it has **compressed and inverted** it. Quality now emerges from a feedback flywheel:

**Prompt → Code → Human click → Auto-tests → Metrics → Next prompt**

In **Part 3** we’ll talk about how you measure productiivy in an AI tooling world.

Stay tuned—your deployment frequency (and your sleep schedule) may depend on it.

