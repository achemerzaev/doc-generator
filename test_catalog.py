from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from docx import Document
from openpyxl import Workbook

from main import doc_render, fill_frame, read_catalog


class Entry:
    """Minimal entry interface for checking form filling without a display."""

    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def delete(self, *_):
        self.value = ""

    def insert(self, _, value):
        self.value = value


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)

    def catalog(self, rows, other_active_sheet=False):
        workbook = Workbook()
        for row in rows:
            workbook.active.append(row)
        if other_active_sheet:
            workbook.create_sheet("Other")
            workbook.active = 1
        path = self.path / "data.xlsx"
        workbook.save(path)
        workbook.close()
        return read_catalog(path)

    def test_arbitrary_headers_fill_and_render_docx(self):
        data = self.catalog([
            [" contract_id ", "amount", "order_date", "extra"],
            ["Contract/42", 0, datetime(2026, 11, 5), "unused"],
        ], other_active_sheet=True)
        entries = {name: Entry() for name in ("contract_id", "amount", "order_date")}
        fill_frame(Entry("Contract/42"), data, entries)
        context = {name: entry.get() for name, entry in entries.items()}
        self.assertEqual(context, {
            "contract_id": "Contract/42", "amount": "0", "order_date": "05.11.2026",
        })
        template = self.path / "template.docx"
        document = Document()
        document.add_paragraph("{{ contract_id }}: {{ amount }} / {{ order_date }}")
        document.save(template)
        output = doc_render(template, "Contract", context, self.path / "output")
        self.assertEqual(output.parent, self.path / "output")
        self.assertEqual(Document(output).paragraphs[0].text, "Contract/42: 0 / 05.11.2026")

    def test_employee_column_can_be_anywhere(self):
        data = self.catalog([
            ["department", "employee_full_name", "emp_phone"],
            ["IT", "Иванов Иван", "123"],
        ])
        self.assertEqual(data["Иванов Иван"], {
            "department": "IT", "employee_full_name": "Иванов Иван", "emp_phone": "123",
        })

    def test_duplicates_empty_selectors_and_label_collisions_preserve_rows(self):
        data = self.catalog([
            ["item", "amount"],
            ["A", 1],
            ["A", 2],
            ["A (строка 2)", 3],
            [None, 4],
            [None, None],
        ])
        self.assertEqual(len(data), 4)
        self.assertEqual([record["amount"] for record in data.values()], [1, 2, 3, 4])
        self.assertEqual(data["A (строка 2)"]["amount"], 3)

    def test_empty_and_duplicate_headers_rejected(self):
        for headers in ([], ["item", None], ["item", " item "]):
            with self.subTest(headers=headers), self.assertRaises(ValueError):
                self.catalog([headers])

    def test_excel_dates_and_blank_cells_override_defaults(self):
        data = self.catalog([
            ["item", "begin_date", "end_date", "order_date"],
            ["A", datetime(2020, 1, 2), None, datetime(2021, 3, 4)],
        ])
        entries = {
            name: Entry("old value")
            for name in ("item", "begin_date", "end_date", "order_date", "missing")
        }
        fill_frame(Entry("A"), data, entries)
        self.assertEqual(entries["begin_date"].get(), "02.01.2020")
        self.assertEqual(entries["end_date"].get(), "")
        self.assertEqual(entries["order_date"].get(), "04.03.2021")
        self.assertEqual(entries["missing"].get(), "")

    def test_defaults_and_manual_employee_entry_still_work(self):
        entries = {name: Entry() for name in ("employee_full_name", "begin_date")}
        fill_frame(Entry("Иванов Иван"), {}, entries)
        self.assertEqual(entries["employee_full_name"].get(), "Иванов Иван")
        self.assertEqual(entries["begin_date"].get(), date.today().strftime("%d.%m.%Y"))

    def test_switching_rows_clears_empty_values(self):
        data = self.catalog([
            ["item", "amount"], ["A", 100], ["B", None],
        ])
        entries = {name: Entry() for name in ("item", "amount")}
        fill_frame(Entry("A"), data, entries)
        self.assertEqual(entries["amount"].get(), "100")
        fill_frame(Entry("B"), data, entries)
        self.assertEqual(entries["item"].get(), "B")
        self.assertEqual(entries["amount"].get(), "")

    def test_example_catalog_remains_compatible(self):
        data = read_catalog(Path(__file__).parent / "catalog" / "example_catalog.xlsx")
        self.assertTrue(data)
        for label, record in data.items():
            self.assertEqual(label, record["employee_full_name"])


if __name__ == "__main__":
    unittest.main()
