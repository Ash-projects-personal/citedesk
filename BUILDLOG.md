# CiteDesk build log

Event: eGain "Build, Demo, and Take Home a Working AI Support Bot" (Devpost 31948).
Started: Nov 12, 2026, about 19:40 CST. Builder target: tonight.

## Step 0, rules check (done 19:37 to 19:45 CST)
- AI policy: PASS. eGain hackathon page states: "Generative AI and other
  development tools are permitted." Plagiarism and misrepresentation are banned.
  Nothing bars AI-assisted building.
- Platform: the event is built around the eGain AI Agent platform. The eGain
  page says "Build a useful customer-service AI Agent with eGain" and "Use an
  existing eGain account or create a trial account with a working email
  address." Judging includes "Effective use of eGain" (20 of 125 points), and
  the submission asks for confirmation that all required workflows were
  published and tested. Signup is self-serve (trial account, working email).
  Plan: build the independent CiteDesk bot tonight as the working demo, code,
  KB content, workflow designs and eval evidence, and flag to the parent that
  the eGain console build (trial signup plus published agent) is a browser
  step the parent owns.
- Deadline: both the Devpost page and the eGain page, read tonight, say submit
  by November 15, 11:59 PM PST. An earlier scout read recorded Nov 12, 8:30 PM
  PST on the live page. Building tonight regardless per Ash's order.
- Submission fields (from the pages): participant info; agent name, industry,
  use case; working demo link; description up to 150 words (problem, intended
  user, business value, distinctive features); one-minute video showing a
  content-based answer, at least one workflow, and the most distinctive
  feature; confirmation that all required workflows were published and tested.

## Step 1, name (done)
- ProofDesk: REJECTED. Multiple existing products, including a knowledge desk
  with the same "refuses to guess" idea (proofdesk.beamline.io) and several
  Devpost and lablab entries.
- AnswerProof: REJECTED. Live PyPI package, products, and a Devpost project.
- CiteDesk: CHOSEN. No software product with this exact name found in web
  screening. Nearest neighbours are CitationDesk (academic writing tool),
  CityDesk, CEDESK, Citizen Desk. Screening only, not a legal clearance.
- GroundBrief: not needed (CiteDesk was clear and earlier in the list).

## Step 2, build (done, ~20:35 CST)
- [x] KB articles (19) for fictional NorthPeak Home
- [x] bot.py: BM25 retrieval, extractive answers, confidence gate, briefs, flows
- [x] app.py + UI (stdlib http.server; pre-chat form, citations, brief panel)
- [x] tests green: 11 passed
- [x] eval run, numbers recorded in eval/results.json
- [x] README, DESCRIPTION, VIDEO-SCRIPT
- [ ] git commit

## Gate design and eval history (honest record)
- Gate v1 (BM25 article score only): eval 23/30. Out-of-scope questions that
  reuse product words scored high and got answered.
- Gate v2: added article title chunks, a novel-term rule (escalate when at
  least half the question's key words appear nowhere in the KB), and an
  is_known prefix match so installing vs installation does not trip it.
- Two debugging fixes: question words (how, what, up) and filler words were
  missing from the stopword list, which polluted BM25 and the novel check.
- One eval label corrected during development and disclosed in
  eval/questions.json: the final-sale refund question is labeled "answer"
  because the returns policy states the final sale rule directly.
- Final measured eval: 29/30. 24/24 in-scope answered from the correct
  article. 5/6 out-of-scope escalated. Known miss kept on the record: the
  underwater doorbell question is answered from the battery article.
- Smoke test: server ran on port 8123; /api/health ok (19 articles),
  /api/ask answered with citations, /api/flow/start returned the return
  flow, UI returned HTTP 200.

## What the parent still owns
- GitHub repo creation (connector 403s on create; browser route), push.
- Render deploy for the public demo link (run command: python3 app.py,
  PORT env is read automatically).
- eGain console side: the event is judged partly on "Effective use of
  eGain" and asks for confirmation that workflows were published and
  tested. Trial signup is self-serve (working email) at eGain. The
  CiteDesk KB content, workflow designs, and eval evidence in this repo
  are the material to mirror into the eGain agent.
- Record the 60 second video from VIDEO-SCRIPT.md and submit on Devpost
  (project 31948 manage page). Submission description limit is 150 words;
  DESCRIPTION.md carries a 141 word blurb plus the long version.
