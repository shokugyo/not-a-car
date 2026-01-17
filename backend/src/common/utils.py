from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))


def get_jst_now() -> datetime:
    return datetime.now(JST)


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_currency(amount: float, currency: str = "JPY") -> str:
    if currency == "JPY":
        return f"{amount:,.0f}"
    return f"{amount:,.2f}"


def format_duration(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}{mins}"
    return f"{mins}"
