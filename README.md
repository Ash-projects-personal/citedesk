# CiteDesk

A support bot that shows its proof, or hands off to a human.

CiteDesk answers customer questions for NorthPeak Home, a fictional smart
home company. The knowledge base in this repo is a sample: 19 short help
articles written for this demo. NorthPeak Home is not a real company, and
the contact details in it are demonstration details.

## The idea

Most support bots answer everything, including questions they have no
basis for. CiteDesk works the other way.

- Every answer is extractive. It is built only from passages retrieved
  from the knowledge base. Nothing is generated from thin air.
- Every answer shows its evidence: the article each passage came from,
  and a groundedness score from 0 to 100 derived from the retrieval
  evidence.
- Before answering, a confidence gate checks two things. The best article
  must clear an evidence bar, and at least half of the question's key
  words must exist somewhere in the knowledge base. If either check
  fails, CiteDesk does not guess.
- When it cannot prove an answer, it escalates. The human agent gets a
  structured handoff brief: the customer's exact question, the closest
  articles, why it escalated, what the human needs, and contact options.

## Guided workflows

Two step by step flows run as state machines, and each step cites the
knowledge base article it follows.

- Device will not connect to WiFi: pairing light, 2.4 GHz check, device
  restart, router restart, then resolution or an escalation brief that
  lists every step already tried.
- Start a return: checks the 30 day window and the item condition, takes
  the refund method, and then takes a real action by creating the return
  and a prepaid label reference. Cases outside the policy escalate with a
  brief instead of being forced through.

The page also has a short pre-chat form (name, product, topic). It is
saved with the handoff brief so a human starts with context.

## Measured results

Evaluation set: 30 questions I authored for this demo, labeled answer or
escalate, in eval/questions.json. Run it yourself with the command below.
Measured on Nov 12, 2026:

- 29 of 30 behaved as labeled.
- 24 of 24 in-scope questions were answered, each from the correct
  article.
- 5 of 6 out-of-scope questions were escalated instead of answered.
- One known miss: "Will the doorbell camera work under water if I mount
  it by my pool?" was answered from the doorbell battery article. The
  question reuses product words for a topic the knowledge base does not
  cover, and the evidence bar alone does not catch that. It is recorded
  in eval/results.json, not hidden.

The confidence gate was tuned against this same authored set during
development, so treat these numbers as a demo measurement, not a
benchmark. The unit test suite has 11 tests covering retrieval, the
gate, both workflows, and their escalation paths. All 11 pass.

## Run it

Python 3.10 or newer. No packages to install, no API keys, no network
calls. The app and the bot use only the standard library.

    python3 app.py

Then open http://localhost:8000. Set PORT to change the port.

Run the tests and the evaluation (pytest installs into a local venv):

    python3 -m venv .venv
    .venv/bin/pip install pytest
    .venv/bin/python -m pytest tests/ -q
    .venv/bin/python eval/run_eval.py

## How it is built

- bot.py: BM25 retrieval over knowledge base sentences (plus each
  article title), extractive answer composition, the confidence gate,
  handoff briefs, and the two workflow state machines.
- app.py: a small HTTP server (standard library http.server) with a JSON
  API: /api/ask, /api/flow/start, /api/flow/choose, /api/health.
- static/index.html: one page with the pre-chat form, the chat, citation
  chips, the groundedness meter, workflow buttons, and the live handoff
  brief panel.
- kb/kb.json: the sample knowledge base.
- eval/: the authored evaluation set, the runner, and the recorded
  results.

## Notes on how this was made

AI sometimes sped up the manual coding where Ash controlled the code,
and every line was reviewed before it shipped. The design, the knowledge
base, the evaluation set, and all product decisions are the author's.
