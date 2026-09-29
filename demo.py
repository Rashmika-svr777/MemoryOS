"""Before/after learning-loop demo: same question, answered before and after the agent learns."""
from .agents import AgentRuntime

def run_learning_demo(rt: AgentRuntime) -> dict:
    q = "Contoso users report login timeouts on the Azure gateway. How do we resolve it?"
    before = rt.act("support", q)
    f = rt.learn("support", "Restart the Contoso Azure gateway to fix login timeouts", False,
                 "timeouts returned within an hour", ["login", "gateway"], ["Contoso", "Azure Gateway"])
    s = rt.learn("support", "Rotate the expired TLS certificate on the Contoso Azure gateway to fix login timeouts", True,
                 "resolved permanently, customer confirmed", ["login", "gateway", "certificate"], ["Contoso", "Azure Gateway"])
    after = rt.act("support", q)
    cross = rt.act("devops", "Contoso Azure gateway login timeouts incident")  # another agent, same brain
    return {"question": q, "before_learning": before, "learned": [f["memory"]["text"], s["memory"]["text"]],
            "after_learning": after, "other_agent_benefits": cross,
            "improved": (not before["memory_used"]) and after["memory_used"]}
