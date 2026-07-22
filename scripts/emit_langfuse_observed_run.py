import argparse
import os
import sys
from pathlib import Path

from langfuse import get_client, observe

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agent import classify_ticket


TICKETS = [
    {
        "id": "observed-success-low",
        "priority": "low",
        "customer_tier": "standard",
        "message": "How do I update my billing email?",
    },
    {
        "id": "observed-success-urgent",
        "priority": "urgent",
        "customer_tier": "enterprise",
        "message": "Checkout outage for VIP customer",
    },
    {
        "id": "observed-failure-critical",
        "priority": "critical",
        "customer_tier": "enterprise",
        "message": "Production checkout outage",
    },
    {
        "id": "observed-failure-vip-critical",
        "priority": "vip_critical",
        "customer_tier": "enterprise",
        "message": "Payment agent is down for a top customer",
    },
    {
        "id": "observed-failure-sev1",
        "priority": "sev1",
        "customer_tier": "enterprise",
        "message": "Search agent returns empty responses during incident",
    },
    {
        "id": "observed-failure-missing-priority",
        "customer_tier": "enterprise",
        "message": "Ticket was created by an external webhook without priority",
    },
]


@observe(name="support-ticket-agent", as_type="agent")
def run_support_ticket_agent(ticket):
    langfuse = get_client()
    run_id = os.getenv("MEGA_LOOP_RUN_ID", "observed")
    langfuse.update_current_trace(
        name=f"mega-loop-observed-{run_id}-{ticket['id']}",
        session_id=f"mega-loop-observed-{run_id}",
        user_id="qa-user",
        input=ticket,
        tags=["mega-loop", "beta-test", "observed-agent"],
        metadata={
            "component": "support-ticket-agent",
            "repository": "jhseo808/mega_test",
            "file": "src/agent.py",
            "entrypoint": "classify_ticket",
            "test_case": ticket["id"],
            "run_id": run_id,
            "input.value": str(ticket),
            "openinference.span.kind": "agent",
        },
    )
    route = classify_ticket(ticket)
    output = {"route": route}
    langfuse.update_current_trace(output=output)
    return output


def main():
    parser = argparse.ArgumentParser(
        description="Emit natural @observe Langfuse traces for MEGA Loop testing."
    )
    parser.add_argument("--include-failure", action="store_true")
    args = parser.parse_args()

    required_env = [
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_BASE_URL",
    ]
    missing = [name for name in required_env if not os.getenv(name)]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        return 2

    exit_code = 0
    tickets = TICKETS if args.include_failure else TICKETS[:2]

    for ticket in tickets:
        try:
            result = run_support_ticket_agent(ticket)
            print(f"{ticket['id']}: {result['route']}")
        except Exception as exc:
            exit_code = 1
            print(f"{ticket['id']}: failed with {type(exc).__name__}: {exc}")

    get_client().flush()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
