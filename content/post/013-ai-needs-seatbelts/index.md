---
title: "AI Needs Seatbelts, Not Just a Policy"
date: 2026-11-23T08:00:00-06:00
draft: false
description: "Enterprise AI safety has to be engineered into the platforms we build, not just written into the policies we enforce."
tags: [GenAI, LLM, Strategy, AI-Safety, Governance]
---

*Why enterprise AI safety needs to be engineered into the platforms we build, not just written into the policies we enforce.*

Companies are racing to adopt AI. We're moving from chatbots that answer questions to agents that write code, access sensitive data, interact with business systems, and increasingly take actions on our behalf.

But there's a problem. We're giving AI more responsibility faster than we're building the systems to safely manage it.

For many organizations, the answer to AI safety has been governance policies, acceptable-use guidelines, approved tool lists, and restrictions on what employees can do. Those things have their place, but they aren't enough.

**You can't build a safe AI strategy with a policy document and a list of things employees aren't allowed to do.**

You need infrastructure. You need guardrails. You need observability, access controls, testing, and the ability to intervene when things go wrong. More importantly, you need to make these capabilities available in a way that encourages employees to experiment safely rather than discouraging them.

The companies that figure this out won't just be safer. They'll have a competitive advantage because they can adopt AI faster without taking on uncontrolled risk.

## We've Solved Versions of This Problem Before

I was recently listening to Greg Brockman, OpenAI's co-founder and president, on [The Knowledge Project](https://fs.blog/knowledge-project-podcast/greg-brockman/). He made an interesting comparison between AI safety and the evolution of safety in other industries, particularly automobiles and electricity.

Think about cars.

When automobiles were first introduced, they didn't come with the safety systems we take for granted today. Seatbelts, airbags, crash testing, traffic signals, standardized road signs, driver's licenses, and the regulations surrounding vehicle safety all evolved over time.

We didn't make cars safe by simply telling people to drive carefully.

We built an entire ecosystem around the technology that made it safer to operate.

Electricity is another example. Today, you can plug something into an outlet without giving much thought to what is happening behind the wall. But that's only possible because of decades of work developing electrical codes, circuit breakers, grounding requirements, inspections, and standardized components.

The electrical system doesn't assume everything will always work perfectly. It assumes things will fail and provides ways to prevent those failures from becoming catastrophic.

That's an important distinction.

**Safety isn't just about making the underlying technology better. It's about building systems around that technology that account for what happens when something goes wrong.**

Brockman's broader argument is that AI will require a similar evolution. Model developers have a responsibility to make their models safer, but society and enterprises also need the surrounding systems, standards, and practices that allow us to use those models responsibly.

I agree with that thinking. But I think there's an important difference this time.

## We Don't Have Decades to Figure This Out

The safety systems surrounding cars and electricity matured over many years. Some improvements came from research and proactive engineering. Others came after accidents, failures, and lessons learned the hard way.

Those industries had time to develop safety practices as adoption expanded at a reasonable pace.

AI is moving at a very different pace.

We're seeing meaningful capability improvements in months, not decades. The tools we were experimenting with a year ago are already being replaced by significantly more capable systems. What started as generating text and summarizing documents has evolved into autonomous agents that can execute workflows across multiple business systems.

And businesses can't simply sit this one out.

If your organization's approach to AI safety is to prohibit experimentation until every potential risk has been addressed, you're going to fall behind competitors who are figuring out how to adopt these capabilities responsibly.

But the opposite extreme isn't any better. Giving everyone unrestricted access to AI tools and hoping nothing goes wrong isn't a strategy either.

We have two competing needs:

- **Move quickly.** Give employees access to new capabilities, encourage experimentation, and find opportunities to improve how the business operates.
- **Maintain control.** Protect sensitive information, meet compliance obligations, understand what AI is doing, and prevent systems from taking actions they shouldn't.

Too often these are treated as opposing objectives. The more control you introduce, the slower innovation becomes. The more freedom you provide, the greater the potential risk.

I don't think that tradeoff has to be inevitable.

The answer is to build platforms and systems where safety is part of the infrastructure rather than something every individual employee or development team needs to figure out for themselves.

## A Policy Is Not a Safety System

Imagine trying to manage electrical safety by sending employees an acceptable electricity use policy.

Don't overload outlets. Don't touch exposed wires. Don't use damaged equipment. Make sure everything is grounded properly.

All reasonable things to ask.

But nobody would consider that an adequate substitute for circuit breakers, electrical codes, and properly designed infrastructure.

Yet that's effectively how some organizations are approaching AI.

They publish guidelines about what information can be shared with AI tools, establish a list of approved models, and tell employees not to use AI for certain activities.

Then they consider the problem solved.

The problem is that policies depend on individuals knowing the rules, understanding the risks, and consistently making the right decisions.

And the people experimenting with AI aren't necessarily security engineers, compliance experts, or AI specialists. They're product managers, developers, salespeople, analysts, and operations teams trying to get their jobs done.

If someone has to understand the nuances of model data retention policies, prompt injection, and enterprise identity management before they can safely experiment with AI, we've created an adoption problem.

Worse, when the approved path is too difficult, people may look for ways around it. They use personal accounts, unapproved tools, or services that don't provide the controls the company needs.

We've seen versions of this problem before with shadow IT.

**The goal shouldn't be to make it harder for employees to use AI. It should be to make the safe way of using AI the easiest and most productive way.**

That requires more than policy. It requires engineering.

## Build the Roads, Not Just the Rules

This is where I think enterprises need to invest.

Instead of having every team independently select models, integrate with vendors, implement security controls, and figure out how to monitor AI usage, organizations should establish shared capabilities that make responsible experimentation easier.

Think of it as building a paved road for AI adoption.

An employee shouldn't have to submit a lengthy request and wait weeks just to experiment with an idea. They should have access to an environment where they can start building, with the appropriate protections already in place.

What does that look like?

### 1. A Safe Place to Experiment

Give employees an approved environment where they can explore models, build prototypes, integrate with corporate systems, and test ideas without introducing unnecessary risk.

That might mean sandboxed environments, synthetic or appropriately de-identified data, limited access to external systems, and spending controls that prevent someone from accidentally generating a massive bill.

The important thing is that these protections are provided by the platform rather than requiring each employee to implement them.

An engineer should be able to experiment with a new agent framework without first needing to become an expert in enterprise AI governance.

### 2. Centralized Access and Control

Organizations need visibility into which models are being used, what data they can access, and what actions they're permitted to take.

A shared AI platform can provide model access through approved interfaces, enforce authentication and authorization, apply data protection controls, and maintain appropriate audit trails.

This doesn't mean everyone must use the same model or application. The platform should support flexibility while enforcing common protections and role based access to enterprise systems.

You can allow experimentation with different models and techniques without allowing unrestricted access to every internal system.

### 3. Guardrails That Actually Enforce Something

Telling an AI agent not to perform a dangerous action is not the same as preventing it from performing that action.

Suppose an agent has access to a customer management system. A prompt might instruct it to only retrieve customer information, but if the underlying integration gives it permission to modify or delete records, the potential for unintended behavior still exists.

A better approach is to enforce restrictions outside the model.

Give the agent read-only credentials when it only needs to read data. Require explicit approval before executing sensitive actions. Validate inputs and outputs. Establish limits on what systems an agent can reach.

These are the AI equivalent of circuit breakers.

They don't require the model to behave perfectly. They constrain the consequences when it doesn't.

### 4. Observability, Testing, and Incident Response

We would never deploy a critical application without considering logging, monitoring, testing, and recovery.

Why should AI be different?

Organizations need to understand how their AI applications behave, what decisions they're making, and whether they're operating within expected boundaries.

That means collecting appropriate traces of agent actions, evaluating outputs against expected behaviors, monitoring for anomalies, and identifying changes in performance as models evolve.

It also means having a way to stop or isolate an AI application when something goes wrong.

An agent operating in a production environment should have defined boundaries and a recovery plan, just like any other critical system.

The details will vary depending on the use case, but the underlying engineering principles aren't new.

## Not Every AI Application Needs the Same Seatbelts

One mistake organizations can make is applying the same governance requirements to every AI use case.

Someone using AI to brainstorm ideas for an internal presentation doesn't introduce the same level of risk as an autonomous agent modifying financial records.

Treating those situations identically creates unnecessary friction.

Instead, we need to apply controls proportionate to risk.

Consider three examples.

**Experimentation:** An employee wants to test whether an LLM can help generate product descriptions. Give them a sandbox, approved model access, and appropriate data boundaries. Let them experiment without going through a formal architecture review.

**Internal productivity:** A team wants to build an assistant that can search internal documentation and answer questions. Now data access becomes more important. The system needs to respect existing permissions, prevent inappropriate information disclosure, and provide useful monitoring.

**Autonomous action:** A team wants an agent that can update customer records, issue refunds, or make changes to production infrastructure. That's a different level of risk. It calls for stricter permissions, more extensive testing, transaction limits, approval workflows, and well-defined rollback procedures.

The controls increase as the potential consequences increase.

This is how we avoid turning governance into a bottleneck.

A safe platform should provide a path from experimentation to production, with clear expectations at each stage. Teams can start small, prove their use case, and take on additional capabilities as the application demonstrates that it can operate safely.

The goal is to make that progression repeatable instead of requiring every new project to navigate an entirely custom approval process.

## The Industry Is Building Standards. Don't Wait for Them to Finish.

Fortunately, organizations don't have to start from scratch.

The [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) provides guidance on governing, identifying, measuring, and managing AI risks.

[ISO/IEC 42001](https://www.iso.org/standard/42001) establishes requirements for organizational AI management systems.

And [OWASP's guidance for LLM applications](https://genai.owasp.org/llm-top-10/) helps identify concrete technical risks, including prompt injection, sensitive information disclosure, and excessive agency.

These are valuable foundations.

But adopting a framework isn't the same as implementing a working safety system.

You can have an AI governance committee, an approved-use policy, and a risk register while still having very little understanding of what AI agents are doing inside your environment.

The real work is translating governance requirements into technical controls, operating procedures, and platforms that people actually use.

And those systems will need to evolve.

The capabilities available today are not the capabilities we'll have a year from now. A governance model that requires months to evaluate each change will struggle to keep up. Organizations need automated controls, continuous evaluation, and feedback loops that allow their safety practices to improve alongside the technology.

The objective isn't to achieve a perfect, permanent definition of AI safety before moving forward.

It's to create a system that can adapt as the risks and capabilities change.

## Safety Can Be an Accelerator, Not a Bottleneck

Here's the part I think businesses are missing.

When you build safety into the platform, you're not just reducing risk. You're also removing friction.

Every development team no longer needs to independently negotiate vendor agreements, build authentication integrations, implement audit logging, or determine how to isolate an agent from sensitive systems.

Those foundational capabilities are already available.

Your security team doesn't need to review every minor experiment because the experimentation environment already enforces the appropriate boundaries.

And when a promising proof of concept is ready to move toward production, there's an established path to do so.

This is the same reason organizations invest in cloud landing zones, CI/CD pipelines, infrastructure as code, and centralized identity management.

We didn't build those capabilities just to make auditors happy. We built them because standardization and automation allow teams to move faster without recreating the same infrastructure and controls for every project.

AI should be no different.

**Done correctly, AI governance shouldn't be the thing that tells your teams to slow down. It should be the infrastructure that gives them the confidence to move faster.**

## What Is Your Company Building?

We're still early in understanding how AI will reshape the way businesses operate.

Model providers will continue improving their safety practices. Governments and standards organizations will continue developing rules and frameworks. And we'll undoubtedly learn difficult lessons as the technology becomes more capable and more deeply integrated into our lives.

But companies can't afford to wait for all of that to happen.

The organizations adopting AI today are already making decisions about which systems it can access, how much autonomy it receives, and how employees can interact with it.

Those decisions are creating the foundation for enterprise AI, whether they're being made intentionally or not.

So I'd challenge business and technology leaders to ask themselves a few questions.

Do your employees have a safe, accessible environment where they can experiment with AI?

Do you have visibility into which models and agents are being used, what information they can access, and what actions they can perform?

Are your safety controls enforced by the underlying infrastructure, or are you relying on people to follow a document?

Can your organization detect, contain, and recover from an AI failure?

And most importantly, **are you investing as much thought into the systems that make AI safe to use as you are into the capabilities you want AI to deliver?**

We didn't make cars safe by just building better engines. We built the roads, the rules, and the safety systems around them.

We didn't make electricity safe by asking everyone to be careful. We built the infrastructure to make safe usage repeatable.

AI needs that same thinking, but on a much more compressed timeline.

The answer isn't to stop people from driving until we've perfected the seatbelt.

**It's to start building the seatbelts now, so we can keep moving forward.**
