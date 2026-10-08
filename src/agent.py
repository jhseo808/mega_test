# 쿠폰 코드별 할인율입니다.
# 예: WELCOME10은 10% 할인, VIP20은 20% 할인입니다.
COUPON_DISCOUNTS = {
    "WELCOME10": 0.10,
    "VIP20": 0.20,
}


def calculate_final_price(order):
    """주문 금액, 회원 등급, 쿠폰 코드를 기준으로 최종 결제 금액을 계산합니다."""
    item_price = order.get("item_price", 0)
    quantity = order.get("quantity", 1)
    member_level = order.get("member_level", "normal")
    coupon_code = order.get("coupon_code")

    # 1. 상품 가격과 수량으로 기본 주문 금액을 계산합니다.
    total_price = item_price * quantity

    # 2. VIP 회원은 항상 5% 추가 할인을 받습니다.
    if member_level == "vip":
        total_price = total_price * 0.95

    # 3. 쿠폰 코드가 있으면 등록된 쿠폰 할인율을 적용합니다.
    # 등록되지 않은 쿠폰 코드는 할인율 0으로 처리합니다.
    if coupon_code:
        discount_rate = COUPON_DISCOUNTS.get(coupon_code, 0)
        total_price = total_price * (1 - discount_rate)

    # 4. 결제 금액은 소수점 없이 반올림해서 반환합니다.
    return round(total_price)


def main():
    # 이 주문은 등록되지 않은 쿠폰을 사용하므로 현재 코드에서는 일부러 실패합니다.
    sample_order = {
        "item_price": 10000,
        "quantity": 2,
        "member_level": "vip",
        "coupon_code": "MEGA50",
    }
    print(calculate_final_price(sample_order))


if __name__ == "__main__":
    main()
