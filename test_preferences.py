from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from docx import Document

import main
from test_catalog import Entry


class PreferencesTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)

    def test_initial_form_and_blank_catalog_start_date_default_to_today(self):
        entries = {"begin_date": Entry(), "employee_full_name": Entry()}
        main.fill_frame(None, {}, entries)
        self.assertEqual(entries["begin_date"].get(), date.today().strftime("%d.%m.%Y"))
        main.fill_frame(Entry("A"), {"A": {"begin_date": None}}, entries)
        self.assertEqual(entries["begin_date"].get(), date.today().strftime("%d.%m.%Y"))
        entries["begin_date"].delete(0)
        entries["begin_date"].insert(0, "01.01.2027")
        self.assertEqual(entries["begin_date"].get(), "01.01.2027")

    def test_filename_uses_template_first_two_names_and_current_year(self):
        for title in ("Шаблон УЗ создание", "УЗ_создание_шаблон", "УЗ создание ШАБЛОН"):
            self.assertEqual(
                main.make_output_filename({"employee_full_name": "Иванов Иван Иванович"}, title),
                f"УЗ создание Иванов Иван {date.today().year}.docx",
            )

    def test_custom_filename_is_used_and_cannot_escape_output_directory(self):
        template = self.path / "template.docx"
        document = Document()
        document.add_paragraph("{{ employee_full_name }}")
        document.save(template)
        output_dir = self.path / "output"
        output = main.doc_render(template, "Template", {"employee_full_name": "Иван"},
                                 output_dir, "../Мой файл.docx")
        self.assertEqual(output.parent, output_dir)
        self.assertEqual(output.suffix, ".docx")
        self.assertEqual(Document(output).paragraphs[0].text, "Иван")
        with self.assertRaises(ValueError):
            main.doc_render(template, "Template", {}, output_dir, "  ")

    def test_suggestion_uses_selected_record_even_without_name_in_form(self):
        records = {
            "Иванов Иван (строка 2)": {"department": "ИТ", "employee_full_name": "Иванов Иван Петрович"},
            "Иванов Иван (строка 3)": {"employee_full_name": "Иванов Иван Сергеевич"},
            "Петров Пётр": {"employee_full_name": "Петров Пётр Иванович"},
        }
        self.assertEqual(
            main.suggest_output_name("Иванов Иван (строка 2)", records, "Шаблон УЗ создание"),
            f"УЗ создание Иванов Иван {date.today().year}",
        )
        self.assertEqual(
            main.suggest_output_name("Петров Пётр", records, "УЗ создание"),
            f"УЗ создание Петров Пётр {date.today().year}",
        )
        for selection in (None, "", "Введено вручную"):
            self.assertEqual(main.suggest_output_name(selection, records, "УЗ создание"), "")
        self.assertEqual(main.suggest_output_name("A", {"A": {"employee_full_name": None}}, "УЗ"), "")

    def test_form_rejects_empty_filename_before_rendering(self):
        template = {"test": {"title": "Тест", "file": self.path / "test.docx", "fields": {}}}
        with patch.object(main, "TEMPLATES", template), \
                patch.object(main, "doc_render") as render, \
                patch.object(main.messagebox, "showerror") as showerror:
            for filename in (None, "", "   ", ".docx"):
                main.handle_button_click({}, Entry("Тест"), {"Тест": "test"}, filename)
            render.assert_not_called()
            self.assertEqual(showerror.call_count, 4)
            self.assertIn("название выходного файла", showerror.call_args.args[1])

    def test_settings_survive_restart_and_missing_catalog_falls_back(self):
        catalog = self.path / "catalog.xlsx"
        catalog.touch()
        with patch.object(main, "SETTINGS_PATH", self.path / "settings.yaml"):
            settings = {"template_id": "my_template", "catalog_path": str(catalog)}
            main.save_settings(settings)
            self.assertEqual(main.load_settings(), settings)
            self.assertEqual(main.get_default_catalog_path(), catalog)
            catalog.unlink()
            self.assertNotEqual(main.get_default_catalog_path(), catalog)

    def test_refresh_imported_source_updates_content_and_fields(self):
        source = self.path / "source.docx"
        document = Document()
        document.add_paragraph("Updated {{ employee_full_name }} {{ begin_date }}")
        document.save(source)
        template_dir = self.path / "templates" / "imported"
        template_dir.mkdir(parents=True)
        working_copy = template_dir / "copy.docx"
        Document().save(working_copy)
        config = {
            "id": "imported", "title": "Импорт", "file": working_copy,
            "source_path": str(source), "config_path": template_dir / "config.yaml",
            "fields": {
                "employee_full_name": {"label": "Сотрудник", "required": True},
                "removed": {"label": "Удалено", "required": False},
            },
        }
        main.save_template_config(config)
        main.refresh_template_files(main.load_templates(self.path / "templates"))
        updated = main.load_templates(self.path / "templates")["imported"]
        self.assertEqual(set(updated["fields"]), {"employee_full_name", "begin_date"})
        self.assertEqual(updated["fields"]["employee_full_name"]["label"], "Сотрудник")
        self.assertEqual(updated["fields"]["begin_date"]["type"], "date")
        self.assertEqual(Document(working_copy).paragraphs[0].text,
                         "Updated {{ employee_full_name }} {{ begin_date }}")


if __name__ == "__main__":
    unittest.main()
