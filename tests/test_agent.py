from src.agent import calculate_final_price


def test_normal_order_without_coupon():
    order = {
        "item_price": 10000,
        "quantity": 2,
        "member_level": "normal",
    }

    assert calculate_final_price(order) == 20000


def test_vip_order_with_valid_coupon():
    order = {
        "item_price": 10000,
        "quantity": 2,
        "member_level": "vip",
        "coupon_code": "WELCOME10",
    }

    assert calculate_final_price(order) == 17100


def test_unknown_coupon_should_not_crash():
    order = {
        "item_price": 10000,
        "quantity": 2,
        "member_level": "vip",
        "coupon_code": "MEGA50",
    }

    assert calculate_final_price(order) == 19000
