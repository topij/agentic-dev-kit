# Writing for agents

How to write a document an agent reads: a workflow doc, a skill adapter, `AGENTS.md`,
`CLAUDE.md`, a `.claude/rules/` file, or a doc one of those points at. The packaging
differs; the writing does not. Read this before proposing a rule or workflow edit
(`post-merge-systemize`'s shared-rule route, a `triage-friction-log` ticket that changes
a standing instruction) and before writing a new workflow.

The aim is not the same output every run. It is the same *process* every run: an
agent that reaches the right material, takes the right steps, and knows when each
step is done. Every rule below serves that.

## Pointers decide what gets read

A **pointer** is text that sits in the agent's context, names material that is not
there, and says when to fetch it. A skill's `description` is one. A line in
`AGENTS.md` naming a doc is another. The pointer's wording, not the material behind
it, decides whether the agent reaches that material. When a must-read doc goes unread,
sharpen the pointer first; inline the material only if that fails.

A pointer names what the material is and the distinct cases that should send the agent
to it:

- Put the word that triggers it first.
- Give one trigger per distinct case. Synonyms for one case are one case written
  twice.
- Leave out what the material itself says.

A skill description is a pointer the runtime loads on every turn, so it pays for every
word. The kit's own repository runs a routing check that scores its skill
descriptions against the requests people type (#1221).

## Two costs

Every line spends one of two budgets:

- **Context cost**: always-loaded text (`AGENTS.md`, a skill description) takes room
  and attention on every turn, whether or not it applies.
- **Operator cost**: the operator has to remember which documents exist and when to
  reach for each. That is the price of keeping a decision with a person. Spend it
  where judgement matters and remove it where it does not.

Material behind a pointer costs only the pointer's line until it is fetched. Material
with no pointer at all costs the operator, who has to remember to ask for it.

## Steps and reference

A document holds **steps** (actions in order) and **reference** (rules, definitions,
facts consulted when needed). Place each piece by how soon the agent needs it:

1. **Steps in the file**: what the agent does, in order.
2. **Reference in the file**: consulted on demand. A flat list of rules is fine.
3. **Reference behind a pointer**: a separate file, read only when the pointer fires.
   The kit's split workflows do this (`pr-watch/`, `triage-friction-log/`).

Move too little down and the steps drown. Move too much and the agent misses what it
needed. The test: inline what every path through the document needs, and put behind a
pointer what only some paths reach. Reference left inline among steps makes each step
easier to skip.

Keep a concept's definition, rules and exceptions under one heading. Scattered
material forces the agent to assemble a meaning from several places, and it will not
always find them all.

**Sprawl** is the failure: a document too long even when every line is true. Attention
thins over the excess. The cure is the ladder above: move reference
behind pointers, and split by path so each path carries only what it needs.
`doc_budgets` in `config/dev-model.yaml` is the tripwire for the files every session
loads.

## Every step needs a finish line

Each step ends on a **completion criterion**: the condition that tells the agent the
step is done.

- **Checkable.** The agent can tell done from not done. "Until understanding is
  reached" invites stopping early, because the steps still ahead pull attention
  forward. Sharpen the criterion before anything else.
- **Demanding.** "Every changed path accounted for" makes the agent dig; "produce a
  list of changes" does not. A demanding criterion binds reference too: "every rule
  applied" makes a flat rule list exhaustive.

When a step is still rushed after its criterion is sharp, split the sequence across a
real context boundary (a subagent, a hand-off) so the later steps are out of view. An
inline section break hides nothing.

## Words that carry weight

A compact word the model already understands (*tripwire*, *receipt*, *frozen*,
*green*) anchors a whole behaviour in a few tokens. Use the same word every time; do
not paraphrase it, or the agent may read two concepts. Prefer an existing word to a
coined one: a coined word recruits nothing and must be defined.

Turn a fuzzy gate into a binary one where you can: "the test goes red on the bug" is
observable; "a convincing reproduction" is not.

State the behaviour you want. A prohibition names the unwanted behaviour and keeps it
in view. Use one only as a hard guardrail you cannot phrase positively, and pair it
with the positive target. The kit's safety guardrails (never merge without authority,
never skip a test) are that case.

## Pruning

- **One home per meaning.** Each rule lives in one place, so changing it is a
  one-place edit. The kit puts shared doctrine in `docs/agentic-dev-kit/` and keeps
  adapters thin for this reason. A restated rule drifts from its source.
- **The repository is a source too.** A document that restates `config/dev-model.yaml`,
  a script's `--help` or the directory layout is a copy that will go stale. Write down
  what the agent cannot find by looking: the unwritten convention, the reason behind
  a choice, the trap no config reveals.
- **Relevance.** Each line must still bear on what the document does. Lines that never
  did, or that describe a behaviour since changed, settle into **sediment**: layers
  kept because removing feels riskier than adding. *Prose that goes false* in
  `AGENTS.md` is the kit's rule for the false ones.
- **No-ops.** Delete a sentence that does not change the agent's behaviour from what it
  would do anyway. Delete the whole sentence, not words from it. Whether a sentence is
  a no-op is settled by running the document, not by argument.
- **Fold before adding.** A new rule that extends an existing one belongs inside it.
  Rule proposals state their net line change for this reason (#1176).
- **Mechanism before prose.** A rule an agent can skip is weaker than a check that
  fails (Principle #8, *Mechanism over memory*). Write prose for the judgement calls a check cannot make.

## Source

Adapted from Matt Pocock's `writing-for-agents` skill
([`mattpocock/skills`](https://github.com/mattpocock/skills),
`skills/productivity/writing-for-agents/` at `5beb35b`), used under the MIT License:

> Copyright (c) 2026 Matt Pocock
>
> Permission is hereby granted, free of charge, to any person obtaining a copy of this
> software and associated documentation files (the "Software"), to deal in the Software
> without restriction, including without limitation the rights to use, copy, modify,
> merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
> permit persons to whom the Software is furnished to do so, subject to the following
> conditions:
>
> The above copyright notice and this permission notice shall be included in all copies
> or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
> INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
> PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
> HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
> CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
> OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
