PRIORITY_WEIGHTS = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
    "urgent": 4,
}


def classify_ticket(ticket):
    """Classify a support ticket into a routing queue."""
    priority = ticket.get("priority")
    customer_tier = ticket.get("customer_tier", "standard")
    message = ticket.get("message", "")

    score = PRIORITY_WEIGHTS[priority]

    if customer_tier == "enterprise":
        score += 1

    if "refund" in message.lower() or "outage" in message.lower():
        score += 1

    if score >= 4:
        return "escalate"

    if score >= 2:
        return "normal"

    return "low_touch"


def main():
    sample_ticket = {
        "priority": "critical",
        "customer_tier": "enterprise",
        "message": "Production outage for checkout agent",
    }
    print(classify_ticket(sample_ticket))


if __name__ == "__main__":
    main()
