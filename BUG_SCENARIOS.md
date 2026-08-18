# MEGA Loop Seed Bug Scenarios

이 repo에는 MEGA Loop 테스트를 위한 의도적인 버그가 들어 있습니다.

## Grouping target

`src/agent.py`의 `calculate_final_price()`는 등록되지 않은 쿠폰 코드가 들어오면 `KeyError`를 발생시킵니다.

실패해야 하는 입력:

- `coupon_code="MEGA50"`
- `coupon_code="SUMMER30"`
- `coupon_code="BLACKFRIDAY"`
- `coupon_code="VIP_ONLY"`

위 입력들은 모두 같은 root cause를 가리켜야 합니다.

```python
discount_rate = COUPON_DISCOUNTS[coupon_code]
```

## Expected fix

- 등록되지 않은 쿠폰 코드는 할인율 0%로 처리한다.
- 기존 정상 쿠폰인 `WELCOME10`, `VIP20`은 계속 동작해야 한다.
- VIP 회원 5% 할인도 계속 유지되어야 한다.

## Baseline passing inputs

- 일반 회원, 쿠폰 없음 -> 정가
- VIP 회원, 정상 쿠폰 `WELCOME10` -> VIP 할인 후 쿠폰 할인
