"""Add clickable sorting to datatable."""
from typing import TypeVar

from rich.text import Text, TextType
from textual import on
from textual.widgets import DataTable
from textual.widgets.data_table import ColumnKey

CellType = TypeVar("CellType")
"""Type used for cells in the DataTable."""


class SortableDataTable(DataTable[CellType]):
    """Just like DataTable except column headers are clickable to sort."""

    sort_column_key: ColumnKey | None = None
    sort_ascending: bool = False

    @on(DataTable.HeaderSelected)
    def header_selected(self, event: DataTable.HeaderSelected) -> None:
        if event.column_key is not None:
            column = self.columns[event.column_key]
            if self.sort_column_key == event.column_key:
                self.sort_ascending = not self.sort_ascending
            else:
                self.sort_ascending = True

            if self.sort_column_key is not None:
                prev = self.columns[self.sort_column_key]
                prev.label = Text(f"{prev.label[:-1]}")
                self.sort_column_key = None

            column.label = column.label + Text(
                "\N{Black Down-Pointing Triangle}"
                if self.sort_ascending
                else "\N{Black Up-Pointing Triangle}"
            )
            self.sort(event.column_key, reverse=self.sort_ascending)
            self.sort_column_key = event.column_key

    def add_column(
        self,
        label: TextType,
        *,
        width: int | None = None,
        key: str | None = None,
        default: CellType | None = None,
    ) -> ColumnKey:
        """Override column labels to leave space for sort arrow."""
        return super().add_column(label + " ", width=width, key=key, default=default)
