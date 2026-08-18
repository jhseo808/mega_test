import argparse
import os
import sys
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agent import calculate_final_price


ORDERS = [
    {
        "id": "order-success-normal",
        "item_price": 10000,
        "quantity": 2,
        "member_level": "normal",
    },
    {
        "id": "order-success-welcome-coupon",
        "item_price": 10000,
        "quantity": 2,
        "member_level": "vip",
        "coupon_code": "WELCOME10",
    },
    {
        "id": "order-failure-mega50",
        "item_price": 10000,
        "quantity": 2,
        "member_level": "vip",
        "coupon_code": "MEGA50",
    },
    {
        "id": "order-failure-summer30",
        "item_price": 30000,
        "quantity": 1,
        "member_level": "normal",
        "coupon_code": "SUMMER30",
    },
    {
        "id": "order-failure-blackfriday",
        "item_price": 50000,
        "quantity": 1,
        "member_level": "vip",
        "coupon_code": "BLACKFRIDAY",
    },
    {
        "id": "order-failure-vip-only",
        "item_price": 12000,
        "quantity": 3,
        "member_level": "vip",
        "coupon_code": "VIP_ONLY",
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


def build_events(order):
    run_id = os.getenv("MEGA_LOOP_RUN_ID", "manual")
    trace_id = str(uuid.uuid4())
    span_id = str(uuid.uuid4())
    generation_id = str(uuid.uuid4())
    start_time = utc_now()
    prompt = f"주문 최종 결제 금액을 계산해 주세요. Order: {order}"

    metadata = {
        "component": "order-price-agent",
        "repository": "jhseo808/mega_test",
        "file": "src/agent.py",
        "entrypoint": "calculate_final_price",
        "test_case": order["id"],
        "run_id": run_id,
        "input.value": prompt,
        "openinference.span.kind": "agent",
    }

    trace_body = {
        "id": trace_id,
        "timestamp": start_time,
        "name": f"mega-loop-order-{run_id}-{order['id']}",
        "input": prompt,
        "sessionId": "mega-loop-order-test",
        "userId": "qa-user",
        "tags": ["mega-loop", "beta-test", "order-price-agent"],
        "metadata": metadata,
    }

    span_body = {
        "id": span_id,
        "traceId": trace_id,
        "name": "calculate-final-price",
        "startTime": start_time,
        "input": prompt,
        "metadata": metadata,
    }

    generation_body = {
        "id": generation_id,
        "traceId": trace_id,
        "parentObservationId": span_id,
        "name": "order-price-decision",
        "startTime": start_time,
        "input": prompt,
        "model": "test-agent-rules-engine",
        "metadata": {
            **metadata,
            "openinference.span.kind": "llm",
        },
    }

    try:
        result = calculate_final_price(order)
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
                "metadata": {**metadata, **error_output},
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
    success_text = f"최종 결제 금액: {result}원"
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
        description="Emit Langfuse ingestion events for the order discount seed bug."
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
    selected_orders = ORDERS if args.include_failure else ORDERS[:2]
    for order in selected_orders:
        events, order_exit_code = build_events(order)
        batch.extend(events)
        exit_code = max(exit_code, order_exit_code)

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
