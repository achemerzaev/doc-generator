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
today and `end_date` to two years from today only if those columns are absent.
Excel values, including empty cells, override these defaults; Excel dates
are formatted as `DD.MM.YYYY`. Switching rows clears previous field values.
Templates without `employee_full_name` can also generate documents.

Personal workbooks placed in `catalog/` are ignored by Git. Only
`example_catalog.xlsx`, which contains fictitious data, is committed.

## Running a packaged build

Keep the `DocGenerator` executable and the `_internal` directory together.
The `_internal` directory contains the Python runtime and the bundled public
example files; it is a normal part of a PyInstaller build.

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
