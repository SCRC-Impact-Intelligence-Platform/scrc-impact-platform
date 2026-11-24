"""Reporting periods: an inclusive range of calendar months.

A quarter, a calendar year (Jan - Dec) and a UC fiscal year (Jul - Jun) are all
month ranges, so reports only need a start and an end month.
"""

from dataclasses import dataclass

_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


@dataclass(frozen=True)
class MonthRange:
    start_year: int
    start_month: int
    end_year: int
    end_month: int

    @classmethod
    def parse(cls, start: str, end: str) -> "MonthRange":
        """From two valid "YYYY-MM" strings. Raises ValueError if end is before start."""
        period = cls(int(start[:4]), int(start[5:]), int(end[:4]), int(end[5:]))
        if period.end_index < period.start_index:
            raise ValueError("end month is before start month")
        return period

    @property
    def start_index(self) -> int:
        """Months since year 0, so a range check is one comparison."""
        return self.start_year * 12 + self.start_month - 1

    @property
    def end_index(self) -> int:
        return self.end_year * 12 + self.end_month - 1

    @property
    def start(self) -> str:
        return f"{self.start_year:04d}-{self.start_month:02d}"

    @property
    def end(self) -> str:
        return f"{self.end_year:04d}-{self.end_month:02d}"

    def touched_years(self) -> list[int]:
        """Calendar years with at least one month in the range."""
        return list(range(self.start_year, self.end_year + 1))

    def full_years(self) -> list[int]:
        """Calendar years whose twelve months are all in the range."""
        return [
            y for y in self.touched_years()
            if (y > self.start_year or self.start_month == 1) and (y < self.end_year or self.end_month == 12)
        ]

    def label(self) -> str:
        """e.g. "Mar 2026", "Jan – Mar 2026", "Jul 2025 – Jun 2026"."""
        sm, em = _MONTHS[self.start_month - 1], _MONTHS[self.end_month - 1]
        if self.start_index == self.end_index:
            return f"{sm} {self.start_year}"
        if self.start_year == self.end_year:
            return f"{sm} – {em} {self.start_year}"
        return f"{sm} {self.start_year} – {em} {self.end_year}"

    def slug(self) -> str:
        """For file names, e.g. "2026-01_to_2026-03"."""
        return f"{self.start}_to_{self.end}"
