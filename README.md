# doc-generator
Util for generation documents from docx + yaml templates

## Trying the application

Install the dependencies and run the application:

```bash
pip install -r requirements.txt
python main.py
```

In a fresh checkout, the application automatically loads
`catalog/example_catalog.xlsx`. Use the **Выбрать…** button next to the catalog
path to load another `.xlsx` file.

The first row of the first worksheet contains column names. Each name must
match a DOCX placeholder exactly: the column `department` fills
`{{ department }}`. The order of columns is arbitrary; no specific columns
are required. Names are case-sensitive, surrounding whitespace is trimmed,
and empty or duplicate column names are rejected. For example:

```text
employee_full_name
employee_job_role
department
emp_phone
supervisor_full_name
supervisor_job_role
sup_phone
```

Select a row in the searchable list to fill the selected template. The list
uses `employee_full_name` when present, otherwise the first column. Duplicate
or empty selection values include the Excel row number, so every record can
be selected. The selection column also fills its matching placeholder.

Only columns matching template fields are used. Missing fields remain empty
and can be entered manually. For existing templates, `begin_date` defaults to
today and `end_date` to two years from today when the form opens.
Excel values override these defaults, except that a blank `begin_date` also
defaults to today. A blank `end_date` stays empty. Excel dates
are formatted as `DD.MM.YYYY`. Switching rows clears previous field values.
Templates without `employee_full_name` can also generate documents.

The editable **Название выходного файла** field suggests a name such as
`УЗ создание Иванов Иван 2026`: template title without the word `шаблон`,
the first two parts of the selected catalog record's `employee_full_name`, and
the current year. Selecting another employee replaces the suggestion. Manual
form entry does not generate a filename: enter it yourself in the required
filename field, without an extension. The `.docx` extension is added automatically.

Use **По умолчанию** beside the template or Excel catalog to remember that
choice for the next launch. Preferences are saved in `settings.yaml` beside
the executable (or source file). If a saved resource disappears, the app
falls back to an available template or catalog.

**Обновить информацию** reloads the current Excel catalog and template files,
including added or removed placeholders. Existing field labels are preserved.
Newly imported templates remember their source DOCX path; refresh copies
changes from that file when it is available. For templates imported by older
versions, edit the application's stored DOCX or import the template again.
Refresh rebuilds the form from the selected catalog record, so manually
entered field values should be saved in a document first.

Personal workbooks placed in `catalog/` are ignored by Git. Only
`example_catalog.xlsx`, which contains fictitious data, is committed.

## Running a packaged build

The build includes `INSTRUCTION.txt` beside the executable: an offline Russian
guide for nontechnical users covering startup, Word templates, Excel employee
catalogs, generated documents, backups, and troubleshooting. Its source is
[INSTRUCTION.txt](./INSTRUCTION.txt). Every PyInstaller build appends the actual
Python and dependency versions, build platform, timestamp, and Git revision
for future vulnerability checks. The broader build-environment package list
is labelled separately from the application dependencies.

Keep the `DocGenerator` executable and the `_internal` directory together.
The `_internal` directory contains the Python runtime and the bundled public
example files; it is a normal part of a PyInstaller build.
The build includes only Russian and English Babel locales and Tcl/Tk message
translations; runtime encodings and timezone resources are retained.
Test files, test runners (`unittest`, `doctest`, `pytest`) and the standard-library
test suite are excluded from production builds. Jinja2's `tests` module is kept
because it implements template conditions such as `is defined`.

Imported templates are saved in `_internal/templates/`, alongside the bundled
example template. Previously added templates in `templates/` beside the
executable are still loaded.

On Linux, unpack `DocGenerator-Linux.tar.gz`, open a terminal in the extracted
`DocGenerator` directory, and run:

```bash
chmod +x DocGenerator
./DocGenerator
```

Generated documents are saved in the `output` directory beside the
executable and are ignored by Git. If startup fails, the application creates
`DocGenerator-error.log` in the same directory with the underlying error.
