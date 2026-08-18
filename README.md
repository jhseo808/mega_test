# MEGA Loop Test Agent

MEGA Loop 테스트를 위한 아주 작은 Python 예제 프로젝트입니다.

이 repo의 목적은 실제 서비스 코드처럼 복잡하게 만드는 것이 아니라,
MEGA Loop가 다음 흐름을 제대로 수행하는지 확인하는 것입니다.

1. Langfuse에 실패 trace가 쌓인다.
2. MEGA Loop가 실패를 감지한다.
3. 같은 원인의 실패를 bug group으로 묶는다.
4. root cause를 설명한다.
5. auto-fix로 Draft PR을 만든다.

## 예제 코드

`src/agent.py`에는 주문 최종 결제 금액을 계산하는 함수가 있습니다.

```python
calculate_final_price(order)
```

입력 예시:

```python
{
    "item_price": 10000,
    "quantity": 2,
    "member_level": "vip",
    "coupon_code": "MEGA50",
}
```

## 일부러 심어둔 버그

등록되지 않은 쿠폰 코드가 들어오면 `KeyError`가 발생합니다.

문제 위치:

```python
discount_rate = COUPON_DISCOUNTS[coupon_code]
```

예를 들어 `MEGA50`, `SUMMER30`, `BLACKFRIDAY` 같은 쿠폰은 현재 사전에 없기 때문에 실패합니다.

MEGA Loop가 이 문제를 찾아서 다음처럼 고치는지 확인하면 됩니다.

- 없는 쿠폰 코드가 들어와도 프로그램이 죽지 않는다.
- 기존 정상 쿠폰 동작은 깨지지 않는다.
- VIP 할인 계산도 그대로 유지된다.

## 로컬 테스트

```powershell
python -m pytest
```

현재는 일부러 버그를 남겨두었기 때문에 테스트 1개가 실패하는 것이 정상입니다.

## Langfuse trace 올리기

먼저 `.env.example`을 참고해서 로컬 전용 `.env` 파일을 만듭니다.

```env
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
MEGA_LOOP_RUN_ID=release-order-bug-20260818
```

그 다음 아래 명령을 실행합니다.

```powershell
python scripts\emit_langfuse_ingestion_events.py --include-failure
```

`.env` 파일은 `.gitignore`에 포함되어 있으므로 GitHub에 올라가지 않습니다.
