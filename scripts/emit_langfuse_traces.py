import argparse
import os
import sys
import traceback
from pathlib import Path

from langfuse import get_client, propagate_attributes

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agent import classify_ticket


TICKETS = [
    {
        "id": "ticket-success-low",
        "priority": "low",
        "customer_tier": "standard",
        "message": "How do I update my billing email?",
    },
    {
        "id": "ticket-success-urgent",
        "priority": "urgent",
        "customer_tier": "enterprise",
        "message": "Checkout outage for VIP customer",
    },
    {
        "id": "ticket-failure-critical",
        "priority": "critical",
        "customer_tier": "enterprise",
        "message": "Production checkout outage",
    },
]


def emit_ticket_trace(ticket):
    langfuse = get_client()

    with langfuse.start_as_current_span(
        name="classify-support-ticket",
        input=ticket,
        metadata={
            "component": "support-ticket-agent",
            "repository": "jhseo808/mega_test",
            "file": "src/agent.py",
            "test_case": ticket["id"],
        },
    ) as span:
        langfuse.update_current_trace(
            name=f"mega-loop-test-{ticket['id']}",
            input=ticket,
            session_id="mega-loop-beta-manual-test",
            user_id="qa-user",
            metadata={
                "component": "support-ticket-agent",
                "repository": "jhseo808/mega_test",
                "file": "src/agent.py",
                "test_case": ticket["id"],
            },
            tags=["mega-loop", "beta-test", "support-ticket-agent"],
        )
        with propagate_attributes(
            session_id="mega-loop-beta-manual-test",
            user_id="qa-user",
            metadata={"trace_label": f"mega-loop-test-{ticket['id']}"},
            tags=["mega-loop", "beta-test", "support-ticket-agent"],
        ):
            try:
                result = classify_ticket(ticket)
            except Exception as exc:
                error_output = {
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "traceback": traceback.format_exc(),
                }
                span.update(
                    level="ERROR",
                    status_message=f"{type(exc).__name__}: {exc}",
                    output=error_output,
                )
                langfuse.update_current_trace(output=error_output)
                raise

            span.update(output={"route": result})
            langfuse.update_current_trace(output={"route": result})
            return result


def main():
    parser = argparse.ArgumentParser(
        description="Emit sample Langfuse traces for MEGA Loop testing."
    )
    parser.add_argument(
        "--include-failure",
        action="store_true",
        help="Also send the intentionally failing critical-priority ticket.",
    )
    args = parser.parse_args()

    required_env = [
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_HOST",
    ]
    missing = [name for name in required_env if not os.getenv(name)]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        return 2

    selected_tickets = TICKETS if args.include_failure else TICKETS[:2]
    exit_code = 0

    for ticket in selected_tickets:
        try:
            route = emit_ticket_trace(ticket)
            print(f"{ticket['id']}: {route}")
        except Exception as exc:
            exit_code = 1
            print(f"{ticket['id']}: failed with {type(exc).__name__}: {exc}")

    get_client().flush()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
