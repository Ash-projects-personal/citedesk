import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import Bot, FlowSession

bot = Bot()


def test_shipping_question_answers_from_shipping_article():
    res = bot.ask("How long does standard shipping take and what does it cost?")
    assert res["type"] == "answer"
    assert "Shipping times and costs" in res["citations"]
    assert "3 to 5 business days" in res["answer"]
    assert res["groundedness"] >= 40


def test_return_question_cites_returns_policy():
    res = bot.ask("Can I return a product if I changed my mind?")
    assert res["type"] == "answer"
    assert "Returns policy" in res["citations"]
    assert "30 days" in res["answer"]


def test_refund_timing_is_consistent():
    res = bot.ask("When will my refund reach my bank account?")
    assert res["type"] == "answer"
    assert "5 to 7 business days" in res["answer"]


def test_out_of_scope_question_escalates_with_brief():
    res = bot.ask("What is the capital of France?")
    assert res["type"] == "escalation"
    brief = res["brief"]
    assert brief["question"] == "What is the capital of France?"
    assert brief["what_the_human_needs"]
    assert len(brief["contact_options"]) >= 2


def test_uncovered_product_question_escalates():
    res = bot.ask("Do you sell solar panels and can you install them on my roof?")
    assert res["type"] == "escalation"


def test_every_answer_has_citations_and_score():
    for q in [
        "How long does the doorbell battery last?",
        "Does the warranty cover a broken screen from a drop?",
        "How do I change the card you bill each month?",
    ]:
        res = bot.ask(q)
        assert res["type"] == "answer", q
        assert res["citations"], q
        assert 0 <= res["groundedness"] <= 100, q
        assert res["sources"], q


def walk(flow_id, choices):
    sess = FlowSession(flow_id)
    view = sess.view()
    for c in choices:
        view = sess.choose(c)
    return view


def test_wifi_flow_happy_path_resolves():
    view = walk("wifi", [0, 0, 0])  # light ok, 2.4 GHz, restart device works
    assert view["outcome"] == "resolved"


def test_wifi_flow_dead_device_escalates_with_trail():
    view = walk("wifi", [1, 1])  # no light, reset does not help
    assert view["outcome"] == "escalated"
    assert "brief" in view
    assert "power" in view["brief"]["what_the_human_needs"][0]


def test_wifi_flow_full_failure_escalates():
    view = walk("wifi", [0, 0, 1, 1])  # ok light, 2.4, device restart no, router restart no
    assert view["outcome"] == "escalated"


def test_return_flow_creates_label_action():
    view = walk("return", [0, 0, 0])  # in window, good condition, original payment
    assert view["outcome"] == "action"
    assert view["rma"].startswith("RMA-")


def test_return_flow_outside_window_escalates():
    view = walk("return", [1])
    assert view["outcome"] == "escalated"
    assert "brief" in view
