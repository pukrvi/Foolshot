from datetime import date, time, timezone
from typing import Literal, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, PositiveInt, field_validator, model_validator


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Settings(Record):
    model_config = ConfigDict(strict=True)
    study_id: str = Field(min_length=1)
    mode: Literal["replay"]
    capital_paise: PositiveInt
    pilot_exposure_paise: PositiveInt
    trade_loss_paise: PositiveInt
    daily_loss_paise: PositiveInt
    weekly_loss_paise: PositiveInt
    study_loss_paise: PositiveInt
    max_attempts: PositiveInt
    max_positions: Literal[1]

    @model_validator(mode="after")
    def check_limits(self) -> Self:
        if self.pilot_exposure_paise > self.capital_paise or not (
            self.trade_loss_paise <= self.daily_loss_paise <= self.weekly_loss_paise
            <= self.study_loss_paise <= self.capital_paise
        ):
            raise ValueError("inconsistent exposure or loss limits")
        return self


class Hours(Record):
    open: time
    close: time

    @model_validator(mode="after")
    def check_hours(self) -> Self:
        if self.open.tzinfo or self.close.tzinfo or self.open >= self.close:
            raise ValueError("expected increasing intraday local times")
        return self


class Calendar(Record):
    source: str = Field(min_length=1)
    days: dict[date, Hours | None]


class Instrument(Record):
    model_config = ConfigDict(strict=True)
    symbol: str = Field(min_length=1)
    segment: Literal["cash_equity"]
    tick_paise: PositiveInt
    lot: PositiveInt


class Master(Record):
    effective_date: date
    source: Literal["synthetic"]
    instruments: tuple[Instrument, ...] = Field(min_length=1)


class Quote(Record):
    id: str = Field(min_length=1, strict=True)
    symbol: str
    exchange: AwareDatetime
    received: AwareDatetime
    bid: int = Field(gt=0, strict=True)
    ask: int = Field(gt=0, strict=True)

    @field_validator("exchange", "received")
    @classmethod
    def as_utc(cls, value):
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def check_quote(self) -> Self:
        if self.exchange > self.received or self.ask < self.bid:
            raise ValueError("invalid quote timestamps or crossed market")
        return self
