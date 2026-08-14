---
description: Write and run pytest tests for a just-implemented Spendly feature, using the test-planner and test-runner subagents
argument-hint: "Feature/spec name or step number, e.g. 'login-logout' or '03'"
allowed-tools: Agent
---

You are orchestrating test coverage for a Spendly feature that was
just implemented. You have access to exactly two subagents for this
command: `test-planner` and `test-runner`. Do not do the work
yourself, do not use any other tool, and do not invoke either
subagent outside of this command.

User input: $ARGUMENTS

## Step 1 — Identify the feature

From `$ARGUMENTS`, determine which feature/spec is being tested. If
it's empty or ambiguous, infer the most recently implemented feature
from git history and `.claude/specs/`, and confirm with the user
before proceeding.

## Step 2 — Run test-planner

Invoke the `test-planner` subagent (via the Agent tool,
`subagent_type: "test-planner"`) to write pytest tests for the
identified feature, based on its spec in `.claude/specs/` — not the
implementation. Wait for it to finish before continuing; do not run
test-runner in parallel with it.

## Step 3 — Run test-runner

Once test-planner has finished and reports which test file(s) it
wrote, invoke the `test-runner` subagent (`subagent_type:
"test-runner"`) to run exactly those test file(s) and produce its
diagnostic report (pass/fail counts, root-cause classification per
failure, improvement suggestions grouped by bug nature).

## Step 4 — Report to the user

Relay test-runner's report to the user. Don't re-summarize it into
something thinner than what it produced — the classification per
failure and the grouped improvement suggestions are the point. If
test-planner or test-runner failed to complete (e.g. couldn't find a
matching spec), say so plainly instead of fabricating a report.
