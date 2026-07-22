import argparse
import os
import sys
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

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
    {
        "id": "ticket-failure-vip-critical",
        "priority": "vip_critical",
        "customer_tier": "enterprise",
        "message": "Payment agent is down for a top customer",
    },
    {
        "id": "ticket-failure-sev1",
        "priority": "sev1",
        "customer_tier": "enterprise",
        "message": "Search agent returns empty responses during incident",
    },
    {
        "id": "ticket-failure-missing-priority",
        "customer_tier": "enterprise",
        "message": "Ticket was created by an external webhook without priority",
    },
]


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def event(event_type, body):
    return {
        "id": str(uuid.uuid4()),
        "type": event_type,
        "timestamp": utc_now(),
        "body": body,
    }


def build_events(ticket):
    run_id = os.getenv("MEGA_LOOP_RUN_ID", "manual")
    trace_id = str(uuid.uuid4())
    span_id = str(uuid.uuid4())
    generation_id = str(uuid.uuid4())
    start_time = utc_now()
    prompt = (
        "Classify this support ticket into one of: "
        "low_touch, normal, escalate.\n\n"
        f"Ticket: {ticket}"
    )

    trace_body = {
        "id": trace_id,
        "timestamp": start_time,
        "name": f"mega-loop-test-{run_id}-{ticket['id']}",
        "input": prompt,
        "sessionId": "mega-loop-beta-manual-test",
        "userId": "qa-user",
        "tags": ["mega-loop", "beta-test", "support-ticket-agent"],
        "metadata": {
            "component": "support-ticket-agent",
            "repository": "jhseo808/mega_test",
            "file": "src/agent.py",
            "test_case": ticket["id"],
            "run_id": run_id,
            "input.value": prompt,
            "openinference.span.kind": "agent",
        },
    }

    span_body = {
        "id": span_id,
        "traceId": trace_id,
        "name": "classify-support-ticket",
        "startTime": start_time,
        "input": prompt,
        "metadata": trace_body["metadata"],
    }

    generation_body = {
        "id": generation_id,
        "traceId": trace_id,
        "parentObservationId": span_id,
        "name": "ticket-routing-decision",
        "startTime": start_time,
        "input": prompt,
        "model": "test-agent-rules-engine",
        "metadata": {
            **trace_body["metadata"],
            "openinference.span.kind": "llm",
        },
    }

    try:
        result = classify_ticket(ticket)
    except Exception as exc:
        end_time = utc_now()
        error_output = {
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback": traceback.format_exc(),
        }
        error_text = f"{type(exc).__name__}: {exc}"
        trace_body["output"] = error_text
        span_body.update(
            {
                "endTime": end_time,
                "output": error_text,
                "level": "ERROR",
                "statusMessage": error_text,
                "metadata": {**trace_body["metadata"], **error_output},
            }
        )
        generation_body.update(
            {
                "endTime": end_time,
                "output": error_text,
                "level": "ERROR",
                "statusMessage": error_text,
                "metadata": {**generation_body["metadata"], **error_output},
            }
        )
        return [
            event("trace-create", trace_body),
            event("span-create", span_body),
            event("generation-create", generation_body),
        ], 1

    end_time = utc_now()
    success_text = f"Route: {result}"
    trace_body["output"] = success_text
    span_body.update(
        {
            "endTime": end_time,
            "output": success_text,
            "level": "DEFAULT",
        }
    )
    generation_body.update(
        {
            "endTime": end_time,
            "output": success_text,
            "level": "DEFAULT",
        }
    )
    return [
        event("trace-create", trace_body),
        event("span-create", span_body),
        event("generation-create", generation_body),
    ], 0


def main():
    parser = argparse.ArgumentParser(
        description="Emit direct Langfuse ingestion events for MEGA Loop testing."
    )
    parser.add_argument("--include-failure", action="store_true")
    args = parser.parse_args()

    host = os.getenv("LANGFUSE_BASE_URL") or os.getenv("LANGFUSE_HOST")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    missing = [
        name
        for name, value in {
            "LANGFUSE_BASE_URL": host,
            "LANGFUSE_PUBLIC_KEY": public_key,
            "LANGFUSE_SECRET_KEY": secret_key,
        }.items()
        if not value
    ]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        return 2

    batch = []
    exit_code = 0
    selected_tickets = TICKETS if args.include_failure else TICKETS[:2]
    for ticket in selected_tickets:
        events, ticket_exit_code = build_events(ticket)
        batch.extend(events)
        exit_code = max(exit_code, ticket_exit_code)

    response = requests.post(
        f"{host.rstrip('/')}/api/public/ingestion",
        auth=(public_key, secret_key),
        json={
            "batch": batch,
            "metadata": {
                "source": "mega-loop-test-agent",
                "batch_size": len(batch),
            },
        },
        timeout=30,
    )
    print(f"Langfuse ingestion status: {response.status_code}")
    print(response.text)
    response.raise_for_status()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
