from src.agent import classify_ticket


def test_urgent_enterprise_ticket_escalates():
    ticket = {
        "priority": "urgent",
        "customer_tier": "enterprise",
        "message": "Checkout outage for VIP customer",
    }

    assert classify_ticket(ticket) == "escalate"


def test_low_priority_standard_ticket_is_low_touch():
    ticket = {
        "priority": "low",
        "customer_tier": "standard",
        "message": "How do I update my billing email?",
    }

    assert classify_ticket(ticket) == "low_touch"


def test_unknown_priority_does_not_crash():
    ticket = {
        "priority": "critical",
        "customer_tier": "enterprise",
        "message": "Production checkout outage",
    }

    assert classify_ticket(ticket) == "escalate"
