# CiteDesk, Devpost description

## Submission blurb (150 word limit, for the eGain submission fields)

Agent name: CiteDesk
Industry: Consumer smart home (sample company: NorthPeak Home)
Use case: Customer support that proves its answers or escalates.

Support bots guess. CiteDesk refuses to.
CiteDesk is a support bot for NorthPeak Home, a fictional smart home
company with a 19 article sample knowledge base. Every answer is
extractive: built only from retrieved help passages, shown with the
article it came from and a groundedness score. A confidence gate checks
the evidence before anything is sent. If the proof is weak, CiteDesk
does not answer. It writes a structured handoff brief for a human: the
question, the closest articles, why it escalated, and what the agent
needs. Two guided workflows, WiFi troubleshooting and starting a return,
cite the article behind each step, and the return flow takes a real
action by creating the return label. On an authored 30 question test
set, it answered 24 of 24 in-scope questions from the right article and
escalated 5 of 6 out-of-scope questions.

## The problem

AI support bots are confident even when they are wrong. A customer asks
something the help content does not cover, and the bot invents a policy,
a timeline, or a step that does not exist. The customer acts on it, and
the company owns the damage. The usual fix, adding a human fallback,
often means a dead end that loses everything the customer already typed.

## The solution

CiteDesk treats an answer as a claim that needs evidence.

- Answers are extractive, never free generated. If a sentence is not in
  the knowledge base, it is not in the answer.
- Citations and a groundedness score are shown with every answer, so the
  customer and the support team can see exactly what the answer stands
  on.
- A two part confidence gate runs before any answer: the best matching
  article must clear an evidence bar, and at least half of the
  question's key words must exist in the knowledge base at all.
- Escalation is a product feature, not a failure page. The handoff brief
  carries the question, the closest articles, the reason for escalating,
  what the human needs, and two or more contact options with
  demonstration contact details.
- Guided workflows follow the knowledge base out loud. Each step names
  the article it follows. The WiFi flow ends in a resolution or a brief
  listing every step tried. The return flow checks the policy window and
  item condition, then takes a real action: it creates the return and a
  prepaid label reference. Cases the policy does not settle escalate
  instead of being forced.

## How it was built

Python, standard library only. BM25 retrieval runs over knowledge base
sentences plus article titles. Answers are composed from the top
passages of the best article, in reading order. The gate, the brief
builder, and both workflows are plain state machines and functions in
one module. A small HTTP server exposes a JSON API, and one HTML page
provides the pre-chat form, chat, citations, groundedness meter, and
the live brief panel. No external APIs, no model keys, nothing leaves
the machine.

## Measured results

Authored evaluation set of 30 questions (24 in scope, 6 out of scope),
recorded in the repo under eval/results.json:

- 29 of 30 behaved as labeled.
- 24 of 24 in-scope questions answered from the correct article.
- 5 of 6 out-of-scope questions escalated.
- One recorded miss: an underwater-use question that reuses product
  vocabulary for a topic the knowledge base does not cover.

11 unit tests cover retrieval, the gate, and both workflows. All pass.
The gate was tuned on this same authored set during development, so
these are demo measurements, not benchmark claims.

## What is sample and what is real

NorthPeak Home is fictional and its knowledge base is a sample written
for this demo, as stated in the repo. The bot, the gate, the briefs, the
workflows, the tests, and the evaluation are real and run as shipped.
