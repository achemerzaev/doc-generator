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

The first worksheet must use `employee_full_name` as its first column. Other
column names should match fields in the selected template, for example:

```text
employee_full_name
employee_job_role
department
emp_phone
supervisor_full_name
supervisor_job_role
sup_phone
```

Personal workbooks placed in `catalog/` are ignored by Git. Only
`example_catalog.xlsx`, which contains fictitious data, is committed.

## Running a packaged build

Keep the `DocGenerator` executable and the `_internal` directory together.
The `_internal` directory contains the Python runtime and the bundled public
example files; it is a normal part of a PyInstaller build.

On Linux, unpack `DocGenerator-Linux.tar.gz`, open a terminal in the extracted
`DocGenerator` directory, and run:

```bash
chmod +x DocGenerator
./DocGenerator
```

Generated documents are saved in the `output` directory beside the
executable and are ignored by Git. If startup fails, the application creates
`DocGenerator-error.log` in the same directory with the underlying error.
