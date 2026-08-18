import argparse
import os
import sys
from pathlib import Path

from langfuse import get_client, observe

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.env_loader import load_env_file
from src.agent import calculate_final_price


ORDERS = [
    {
        "id": "observed-success-normal",
        "item_price": 10000,
        "quantity": 2,
        "member_level": "normal",
    },
    {
        "id": "observed-success-welcome-coupon",
        "item_price": 10000,
        "quantity": 2,
        "member_level": "vip",
        "coupon_code": "WELCOME10",
    },
    {
        "id": "observed-failure-mega50",
        "item_price": 10000,
        "quantity": 2,
        "member_level": "vip",
        "coupon_code": "MEGA50",
    },
    {
        "id": "observed-failure-summer30",
        "item_price": 30000,
        "quantity": 1,
        "member_level": "normal",
        "coupon_code": "SUMMER30",
    },
    {
        "id": "observed-failure-blackfriday",
        "item_price": 50000,
        "quantity": 1,
        "member_level": "vip",
        "coupon_code": "BLACKFRIDAY",
    },
    {
        "id": "observed-failure-vip-only",
        "item_price": 12000,
        "quantity": 3,
        "member_level": "vip",
        "coupon_code": "VIP_ONLY",
    },
]


@observe(name="order-price-agent", as_type="agent")
def run_order_price_agent(order):
    langfuse = get_client()
    run_id = os.getenv("MEGA_LOOP_RUN_ID", "observed")
    langfuse.update_current_trace(
        name=f"mega-loop-observed-order-{run_id}-{order['id']}",
        session_id=f"mega-loop-observed-order-{run_id}",
        user_id="qa-user",
        input=order,
        tags=["mega-loop", "beta-test", "observed-order-agent"],
        metadata={
            "component": "order-price-agent",
            "repository": "jhseo808/mega_test",
            "file": "src/agent.py",
            "entrypoint": "calculate_final_price",
            "test_case": order["id"],
            "run_id": run_id,
            "input.value": str(order),
            "openinference.span.kind": "agent",
        },
    )
    final_price = calculate_final_price(order)
    output = {"final_price": final_price}
    langfuse.update_current_trace(output=output)
    return output


def main():
    load_env_file()

    parser = argparse.ArgumentParser(
        description="Emit natural @observe Langfuse traces for the order discount seed bug."
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
    orders = ORDERS if args.include_failure else ORDERS[:2]

    for order in orders:
        try:
            result = run_order_price_agent(order)
            print(f"{order['id']}: {result['final_price']}")
        except Exception as exc:
            exit_code = 1
            print(f"{order['id']}: failed with {type(exc).__name__}: {exc}")

    get_client().flush()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
