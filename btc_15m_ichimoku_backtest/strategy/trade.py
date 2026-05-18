from dataclasses import dataclass
from datetime import datetime


@dataclass
class Trade:
    """Represents a completed trade with entry and exit information."""

    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float

    @property
    def return_pct(self) -> float:
        """Calculate return percentage of the trade."""
        return ((self.exit_price - self.entry_price) / self.entry_price) * 100

    @property
    def entry_date(self):
        return self.entry_time

    @property
    def exit_date(self):
        return self.exit_time

    @property
    def days_in_trade(self):
        return (self.exit_time - self.entry_time).total_seconds() / (24 * 3600)

    @property
    def duration_days(self):
        return (self.exit_time - self.entry_time).total_seconds() / (24 * 3600)

    def to_dict(self) -> dict:
        """Convert to dictionary for backward compatibility."""
        return {
            "entry_time": self.entry_time,
            "entry_price": self.entry_price,
            "exit_time": self.exit_time,
            "exit_price": self.exit_price,
            "return_pct": self.return_pct,
        }
