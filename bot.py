"""CiteDesk core: BM25 retrieval, extractive answers with citations, a
confidence gate that escalates instead of guessing, structured handoff
briefs, and two guided workflows. Standard library only. No external calls.
"""
import json
import math
import os
import random
import re
import string
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
KB_PATH = os.path.join(BASE, "kb", "kb.json")

STOPWORDS = set(
    "a an the is are was were be been do does did have has had will would shall "
    "i you he she it we they me him her us them my your his its our their this "
    "that these those to of for in on at by with from as and or but if then so "
    "can could should may might must how what when where why which who whom "
    "up down out about into over per via many much something anything "
    "everything someone anyone thing things get got".split()
)

TOKEN_RE = re.compile(r"[a-z0-9]+")
SENT_RE = re.compile(r"[^.!?]+[.!?]")


def tokens(text):
    out = []
    for tok in TOKEN_RE.findall(text.lower()):
        if tok in STOPWORDS:
            continue
        if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
            tok = tok[:-1]
        out.append(tok)
    return out


def split_sentences(body):
    parts = [p.strip() for p in SENT_RE.findall(body)]
    return [p for p in parts if len(p.split()) >= 3]


class Chunk:
    def __init__(self, article_id, title, sentence, position, is_title=False):
        self.article_id = article_id
        self.title = title
        self.sentence = sentence
        self.position = position
        self.is_title = is_title
        self.toks = tokens(sentence)
        self.tf = Counter(self.toks)


class Retriever:
    """BM25 over KB sentences plus one title chunk per article."""

    def __init__(self, kb):
        self.articles = {a["id"]: a for a in kb["articles"]}
        self.chunks = []
        for art in kb["articles"]:
            self.chunks.append(Chunk(art["id"], art["title"], art["title"], -1, True))
            for pos, sent in enumerate(split_sentences(art["body"])):
                self.chunks.append(Chunk(art["id"], art["title"], sent, pos))
        n = len(self.chunks)
        self.avgdl = sum(len(c.toks) for c in self.chunks) / max(n, 1)
        df = Counter()
        for c in self.chunks:
            for t in set(c.toks):
                df[t] += 1
        self.idf = {
            t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()
        }
        self.vocab = set(self.idf)

    def _score(self, qtoks, chunk, k1=1.5, b=0.75):
        score = 0.0
        dl = len(chunk.toks) or 1
        for t in qtoks:
            if t not in chunk.tf:
                continue
            tf = chunk.tf[t]
            denom = tf + k1 * (1 - b + b * dl / self.avgdl)
            score += self.idf.get(t, 0.0) * (tf * (k1 + 1) / denom)
        return score

    def rank(self, question, top=8):
        qtoks = tokens(question)
        scored = [(self._score(qtoks, c), c) for c in self.chunks]
        scored.sort(key=lambda x: -x[0])
        return scored[:top]

    def is_known(self, tok):
        """A question word counts as known if it appears in the KB or shares
        a 5+ letter prefix with a KB word (installing vs installation)."""
        if tok in self.vocab:
            return True
        for v in self.vocab:
            if len(v) >= 5 and len(tok) >= 5:
                n = 0
                for a, b in zip(tok, v):
                    if a != b:
                        break
                    n += 1
                if n >= 5:
                    return True
        return False


# Confidence gate: the best article must clear this BM25 evidence bar,
# tuned on the authored eval set in eval/questions.json.
GATE = 3.2


def groundedness(best_score):
    """Saturating map from raw BM25 evidence to a 0..100 display score."""
    return int(round(100 * best_score / (best_score + 5.0)))


def make_brief(question, reason, ranked, need):
    closest = []
    seen = set()
    for score, chunk in ranked:
        if score <= 0 or chunk.article_id in seen:
            continue
        seen.add(chunk.article_id)
        closest.append({"article": chunk.title, "score": round(score, 2)})
        if len(closest) >= 3:
            break
    return {
        "type": "escalation",
        "question": question,
        "reason": reason,
        "closest_matches": closest,
        "what_the_human_needs": need,
        "contact_options": [
            "Live chat with a human agent (demo queue)",
            "Email support@northpeakhome.example (demonstration address)",
            "Phone 1-800-555-0142, Mon to Fri, 8 am to 8 pm CT (demonstration number)",
        ],
    }


class Bot:
    def __init__(self, kb_path=KB_PATH):
        with open(kb_path) as f:
            self.kb = json.load(f)
        self.retriever = Retriever(self.kb)

    def ask(self, question):
        question = (question or "").strip()
        qtoks = tokens(question)
        if len(qtoks) < 2:
            return {
                "type": "escalation",
                "brief": make_brief(
                    question,
                    "The question was too short to match against the knowledge base.",
                    [],
                    ["Ask the customer what they need help with, in their own words."],
                ),
            }
        novel = [t for t in dict.fromkeys(qtoks) if not self.retriever.is_known(t)]
        if len(novel) * 2 >= len(set(qtoks)):
            return {
                "type": "escalation",
                "brief": make_brief(
                    question,
                    "The knowledge base has no content about key parts of this "
                    "question (for example: "
                    + ", ".join(novel[:4])
                    + "). There is nothing to ground an answer in, so this goes "
                    "to a human.",
                    self.retriever.rank(question),
                    [
                        "The customer's exact question, shown in this brief.",
                        "A topic the knowledge base does not cover yet; the answer may need new content.",
                    ],
                ),
            }
        ranked = self.retriever.rank(question, top=len(self.retriever.chunks))
        by_article = {}
        for score, chunk in ranked:
            by_article.setdefault(chunk.article_id, []).append((score, chunk))
        article_scores = {
            aid: sum(s for s, _ in items[:2]) for aid, items in by_article.items()
        }
        best_id = max(article_scores, key=article_scores.get)
        best = article_scores[best_id]
        if best < GATE:
            return {
                "type": "escalation",
                "brief": make_brief(
                    question,
                    "No knowledge base passage cleared the confidence gate "
                    f"(best evidence score {best:.2f}, gate {GATE}). Answering "
                    "would mean guessing, so this goes to a human.",
                    ranked,
                    [
                        "The customer's exact question, shown in this brief.",
                        "The closest knowledge base articles, listed here, in case one is relevant.",
                        "A decision the knowledge base does not cover, or new content for it.",
                    ],
                ),
            }
        body_items = [it for it in by_article[best_id] if not it[1].is_title]
        if not body_items:
            body_items = by_article[best_id]
        chosen = sorted(body_items[:3], key=lambda x: x[1].position)
        answer = " ".join(c.sentence for _, c in chosen)
        citations = []
        for _, c in chosen:
            if c.title not in citations:
                citations.append(c.title)
        return {
            "type": "answer",
            "answer": answer,
            "citations": citations,
            "groundedness": groundedness(best),
            "evidence_score": round(best, 2),
            "sources": [
                {"article": c.title, "passage": c.sentence, "score": round(s, 2)}
                for s, c in chosen
            ],
        }


# ---------------- Guided workflows (state machines) ----------------
# Each step cites the KB article it follows. A step ends the flow with
# outcome "resolved", "action" (a real action taken), or "escalated".

FLOWS = {
    "wifi": {
        "name": "Device will not connect to WiFi",
        "start": "power",
        "steps": {
            "power": {
                "text": "Let us fix the connection step by step. First: is the "
                        "device powered on, with its status light blinking blue? "
                        "Blinking blue means it is ready to pair.",
                "cite": "Device will not connect to WiFi",
                "choices": [
                    {"label": "Yes, light is blinking blue", "next": "band"},
                    {"label": "No light, or a different color", "next": "power_fix"},
                ],
            },
            "power_fix": {
                "text": "Plug the device in, or charge it if it runs on battery. "
                        "Then press and hold the reset button for 10 seconds until "
                        "the light flashes orange, and wait for it to blink blue. "
                        "Is it blinking blue now?",
                "cite": "Factory reset a device",
                "choices": [
                    {"label": "Yes, blinking blue now", "next": "band"},
                    {"label": "Still no blue light", "next": "escalated",
                     "reason": "Device shows no pairing light after a reset. "
                               "This looks like a hardware fault."},
                ],
            },
            "band": {
                "text": "NorthPeak devices connect to 2.4 GHz WiFi only. Is the "
                        "network you are joining a 2.4 GHz network?",
                "cite": "Connecting a device to WiFi",
                "choices": [
                    {"label": "Yes, it is 2.4 GHz", "next": "restart_device"},
                    {"label": "It is 5 GHz only", "next": "band_fix"},
                    {"label": "I am not sure", "next": "restart_device"},
                ],
            },
            "band_fix": {
                "text": "Open your router settings and turn on the 2.4 GHz band. "
                        "Most routers can run both bands at once, sometimes under "
                        "one name. Then try setup again in the app. Did the device "
                        "connect?",
                "cite": "Connecting a device to WiFi",
                "choices": [
                    {"label": "Yes, it connected", "next": "resolved"},
                    {"label": "Still will not connect", "next": "restart_router"},
                ],
            },
            "restart_device": {
                "text": "Unplug the device for 10 seconds, plug it back in, and "
                        "run setup again in the app, staying within 30 feet of "
                        "the router. Did it connect this time?",
                "cite": "Device will not connect to WiFi",
                "choices": [
                    {"label": "Yes, it connected", "next": "resolved"},
                    {"label": "No, still failing", "next": "restart_router"},
                ],
            },
            "restart_router": {
                "text": "Last step: unplug your router for 30 seconds, plug it "
                        "back in, wait 2 minutes, then run setup once more. Did "
                        "the device connect?",
                "cite": "Device will not connect to WiFi",
                "choices": [
                    {"label": "Yes, it connected", "next": "resolved"},
                    {"label": "No, it never connects", "next": "escalated",
                     "reason": "All documented WiFi steps were tried: pairing "
                               "light confirmed, 2.4 GHz checked, device and "
                               "router restarted. The device still will not "
                               "connect."},
                ],
            },
            "resolved": {
                "text": "Your device is connected. It will finish any pending "
                        "firmware update overnight, and you can now add it to a "
                        "room in the app.",
                "cite": "Firmware updates",
                "outcome": "resolved",
                "choices": [],
            },
        },
    },
    "return": {
        "name": "Start a return",
        "start": "window",
        "steps": {
            "window": {
                "text": "I can start that return now. Did the order arrive "
                        "within the last 30 days?",
                "cite": "Returns policy",
                "choices": [
                    {"label": "Yes, within 30 days", "next": "condition"},
                    {"label": "No, more than 30 days ago", "next": "escalated",
                     "reason": "The return is outside the 30 day window in the "
                               "returns policy. Only a human can review an "
                               "exception."},
                ],
            },
            "condition": {
                "text": "Is the item in its original condition, with all "
                        "accessories included?",
                "cite": "Returns policy",
                "choices": [
                    {"label": "Yes, complete and undamaged", "next": "method"},
                    {"label": "No, something is missing or damaged",
                     "next": "escalated",
                     "reason": "The item is missing parts or is damaged, which "
                               "the returns policy does not settle on its own. "
                               "A human needs to review the condition."},
                ],
            },
            "method": {
                "text": "How would you like the refund? Money back to your "
                        "original payment method reaches your account in 5 to 7 "
                        "business days after we process it. Store credit arrives "
                        "by email within 1 business day.",
                "cite": "Refunds: timing and methods",
                "choices": [
                    {"label": "Original payment method", "next": "label"},
                    {"label": "Store credit", "next": "label"},
                ],
            },
            "label": {
                "text": "Done. I created your return and emailed you a prepaid "
                        "return label. Pack the item with all accessories, attach "
                        "the label, and drop the package off with the carrier. "
                        "We email you when the return arrives and when your "
                        "refund is processed.",
                "cite": "Returns policy",
                "outcome": "action",
                "action": "Prepaid return label created and emailed (demo action)",
                "choices": [],
            },
        },
    },
}


class FlowSession:
    def __init__(self, flow_id):
        self.flow_id = flow_id
        self.flow = FLOWS[flow_id]
        self.step_id = self.flow["start"]
        self.trail = []
        self.rma = None

    def view(self):
        if self.step_id == "escalated":
            return {
                "flow": self.flow_id,
                "flow_name": self.flow["name"],
                "step": "escalated",
                "text": "",
                "cite": "",
                "choices": [],
                "done": True,
                "outcome": "escalated",
            }
        step = self.flow["steps"][self.step_id]
        out = {
            "flow": self.flow_id,
            "flow_name": self.flow["name"],
            "step": self.step_id,
            "text": step["text"],
            "cite": step["cite"],
            "choices": [c["label"] for c in step["choices"]],
            "done": "outcome" in step or self.step_id == "escalated",
        }
        if self.step_id == "escalated":
            out["done"] = True
            out["outcome"] = "escalated"
        if "outcome" in step:
            out["outcome"] = step["outcome"]
        if step.get("action"):
            if not self.rma:
                self.rma = "RMA-" + "".join(
                    random.choice(string.digits) for _ in range(6)
                )
            out["action"] = step["action"]
            out["rma"] = self.rma
        return out

    def choose(self, index):
        step = self.flow["steps"][self.step_id]
        choice = step["choices"][index]
        self.trail.append(f"{self.flow['name']} > {self.step_id}: {choice['label']}")
        nxt = choice["next"]
        if nxt == "escalated":
            self.step_id = "escalated"
            question = f"Guided workflow: {self.flow['name']}"
            brief = make_brief(
                question,
                choice.get("reason", "The workflow reached a case it cannot settle."),
                [],
                [
                    "The workflow steps the customer already tried: "
                    + "; ".join(self.trail) + ".",
                    "A decision on the exception described in the reason.",
                ],
            )
            view = self.view()
            view["brief"] = brief
            view["text"] = (
                "This one needs a human. I have sent them a brief with every "
                "step you already tried, so you will not have to repeat them."
            )
            view["cite"] = step["cite"]
            return view
        self.step_id = nxt
        return self.view()
