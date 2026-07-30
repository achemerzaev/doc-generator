from datetime import date
from pathlib import Path
import sys
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

import openpyxl
import yaml
from docxtpl import DocxTemplate

from widgets import (
    SearchableCombobox,
    OptionalDateEntry,
)


def get_app_dir():
    """Return the writable directory containing the source or executable."""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


def get_bundle_dir():
    """Return the directory containing PyInstaller's bundled resources."""

    bundle_dir = getattr(sys, "_MEIPASS", None)
    return Path(bundle_dir).resolve() if bundle_dir else get_app_dir()


def unique_paths(*paths):
    result = []

    for path in paths:
        resolved = Path(path).resolve()
        if resolved not in result:
            result.append(resolved)

    return tuple(result)


def load_templates(template_dirs):
    if isinstance(template_dirs, (str, Path)):
        template_dirs = (Path(template_dirs),)

    templates = {}

    for templates_dir in template_dirs:
        if not templates_dir.is_dir():
            continue

        for config_path in sorted(templates_dir.glob("*/config.yaml")):
            with config_path.open("r", encoding="UTF-8") as file:
                config = yaml.safe_load(file)

            if not isinstance(config, dict):
                raise ValueError(f"пустая конфигурация шаблона: {config_path}")

            for required_key in ("id", "title", "file", "fields"):
                if required_key not in config:
                    raise ValueError(
                        f"в {config_path} отсутствует поле {required_key}"
                    )

            template_id = config.pop("id")
            template_path = config_path.parent / config["file"]

            if not template_path.is_file():
                raise FileNotFoundError(
                    f"шаблон не найден: {template_path}"
                )

            config["file"] = template_path
            templates[template_id] = config

    return templates


APP_DIR = get_app_dir()
BUNDLE_DIR = get_bundle_dir()

TEMPLATE_DIRS = unique_paths(
    BUNDLE_DIR / "templates",
    APP_DIR / "templates",
)
CATALOG_DIRS = unique_paths(
    APP_DIR / "catalog",
    BUNDLE_DIR / "catalog",
)

CATALOG_DIR = APP_DIR / "catalog"
OUTPUT_DIR = APP_DIR / "output"
PRIVATE_CATALOG_PATH = CATALOG_DIR / "catalog.xlsx"
EXAMPLE_CATALOG_PATHS = tuple(
    catalog_dir / "example_catalog.xlsx"
    for catalog_dir in CATALOG_DIRS
)

TEMPLATES = {}


def make_output_filename(context, template_name):
    splitted_name = context["employee_full_name"].split()
    output_name = template_name + "_"
    for x in splitted_name:
        output_name = output_name + x + "_"
    output_name = output_name + "2026.docx"
    return output_name


def doc_render(template_path, template_name, context, output_path):
    if not template_path.is_file():
        raise FileNotFoundError(f"шаблон не найден: {template_path}")

    if not (template_path.suffix.lower() == ".docx"):
        raise ValueError(f"Расширение шаблона должно быть .docx: {template_path}")


    doc = DocxTemplate(template_path)
    doc.render(context)
    output_name = make_output_filename(context, template_name)
    output_filename = output_path / output_name

    output_filename.parent.mkdir(parents = True, exist_ok = True)
    doc.save(output_filename)
    return output_filename

def validate(context, fields_config):
    for field_name, field_config in fields_config.items():
        if not field_config["required"]:
            continue
        value = context.get(field_name, "")
        if not value:
            raise ValueError(f"обязательное поле {field_config['label']} не заполнено")


def handle_button_click(entries, selected_template, title_to_key):
    selected_title = selected_template.get()
    template_key = title_to_key[selected_title]
    template_config = TEMPLATES[template_key]
    fields_config = template_config["fields"]
    template_name = template_config["title"]

    template_path =  template_config["file"]
    output_path = OUTPUT_DIR

    context = {}

    try:
        for entry in entries:
            context[entry] = entries[entry].get().strip()

        validate(context, fields_config)
        out = doc_render(template_path, template_name, context, output_path)

    except ValueError as error:
        messagebox.showerror("Ошибка e", f"ошибка e {error}")
    except FileNotFoundError as error:
        messagebox.showerror("Ошибка", f"ошибка df {error}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"ошибка sew {e}")
    else:
        messagebox.showinfo("Документ создан", f"Путь: {out}")

def render_frame(template_combobox, title_to_key, frame, entries):
    selection = template_combobox.get()
    fields = TEMPLATES[title_to_key[selection]]["fields"]

    entries.clear()
    for widget in frame.winfo_children():
        widget.destroy()
    
    for row, (field_name, field_config) in enumerate(
    fields.items(),
    ):
        label = tk.Label(frame, text=field_config["label"])
        label.grid(
            row=row, 
            column=0,
            padx=(5, 10),
            pady=4,
            sticky="w",
        )

        if field_config.get("type") == "date":
            entry = OptionalDateEntry(
                    frame,
                    locale="ru_RU",
                    width=12
                )
        else:
            entry = tk.Entry(frame)

        entry.grid(
            row=row,
            column=1,
            padx=(0, 5),
            pady=4,
            sticky="ew",
        )

        entries[field_name] = entry

def fill_frame(name_combobox, data_dict, entries):
    selection = name_combobox.get().strip()
    employee_data = data_dict.get(selection, {})

    today = date.today()
    try:
        future_date = today.replace(year=today.year + 2)
    except ValueError:
        # 29 February becomes 28 February in a non-leap target year.
        future_date = today.replace(
            year=today.year + 2,
            month=2,
            day=28,
        )

    def set_entry_value(field_name, value):
        entry = entries.get(field_name)

        if entry is None:
            return
        
        entry.delete(0, tk.END)

        if value is not None:
            entry.insert(0, str(value))

    
    # ФИО записываем независимо от того,
    # есть ли человек в Excel
    set_entry_value(
        "employee_full_name",
        selection,
    )

    # Начальная дата — сегодня.
    set_entry_value(
        "begin_date",
        today.strftime("%d.%m.%Y"),
    )

    # Конечная дата — через два года.
    set_entry_value(
        "end_date",
        future_date.strftime("%d.%m.%Y"),
    )

    # Дату приказа специально не заполняем.
    # Поле order_date останется пустым.

    # Подставляем остальные сведения из Excel.
    for field_name, value in employee_data.items():
        # Эти значения уже установлены выше и не должны
        # случайно перезаписываться данными из таблицы.
        if field_name in {
            "employee_full_name",
            "begin_date",
            "end_date",
            "order_date",
        }:
            continue

        set_entry_value(
            field_name,
            value,
        )


def change_template(
    template_combobox,
    title_to_key,
    frame,
    entries,
    name_combobox,
    data_dict,
):
    # Сначала создаём поля нового шаблона
    render_frame(
        template_combobox,
        title_to_key,
        frame,
        entries,
    )

    # Затем снова заполняем ФИО, данные сотрудника
    # и начальную/конечную даты
    if name_combobox.get().strip():
        fill_frame(
            name_combobox,
            data_dict,
            entries,
        )

def get_default_catalog_path():
    """Prefer the private catalog and fall back to the public example."""

    for catalog_path in (
        PRIVATE_CATALOG_PATH,
        *EXAMPLE_CATALOG_PATHS,
    ):
        if catalog_path.is_file():
            return catalog_path

    return None


def read_catalog(catalog_file):
    catalog_file = Path(catalog_file)

    if not catalog_file.is_file():
        raise FileNotFoundError(f"каталог не найден: {catalog_file}")

    if catalog_file.suffix.lower() != ".xlsx":
        raise ValueError("каталог должен быть файлом .xlsx")

    try:
        workbook = openpyxl.load_workbook(
            catalog_file,
            read_only=True,
            data_only=True,
        )
    except Exception as error:
        raise ValueError(
            f"не удалось прочитать каталог {catalog_file}: {error}"
        ) from error

    try:
        sheet = workbook.active
        headers = [
            str(cell.value).strip() if cell.value is not None else ""
            for cell in sheet[1]
        ]

        if not headers or headers[0] != "employee_full_name":
            raise ValueError(
                "первый столбец каталога должен называться "
                "employee_full_name"
            )

        if any(not header for header in headers):
            raise ValueError("названия столбцов каталога не могут быть пустыми")

        if len(headers) != len(set(headers)):
            raise ValueError("названия столбцов каталога не должны повторяться")

        data_dict = {}

        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not row or row[0] is None:
                continue

            full_name = str(row[0]).strip()

            if not full_name:
                continue

            data_dict[full_name] = dict(zip(headers[1:], row[1:]))

        return data_dict
    finally:
        workbook.close()


def choose_catalog(
    root,
    catalog_path_var,
    name_combobox,
    data_dict,
    entries,
):
    current_value = catalog_path_var.get().strip()
    current_path = Path(current_value) if current_value else None
    existing_catalog_dir = next(
        (
            catalog_dir
            for catalog_dir in CATALOG_DIRS
            if catalog_dir.is_dir()
        ),
        APP_DIR,
    )
    initial_dir = (
        current_path.parent
        if current_path and current_path.parent.is_dir()
        else existing_catalog_dir
    )

    selected_path = filedialog.askopenfilename(
        parent=root,
        title="Выберите каталог сотрудников",
        initialdir=initial_dir,
        filetypes=[
            ("Книги Excel", "*.xlsx"),
            ("Все файлы", "*.*"),
        ],
    )

    if not selected_path:
        return

    try:
        selected_data = read_catalog(selected_path)
    except (OSError, ValueError) as error:
        messagebox.showerror(
            "Не удалось открыть каталог",
            str(error),
            parent=root,
        )
        return

    data_dict.clear()
    data_dict.update(selected_data)
    name_combobox.set_values(data_dict.keys())
    name_combobox.clear()

    for entry in entries.values():
        entry.delete(0, tk.END)

    catalog_path_var.set(str(Path(selected_path)))
    messagebox.showinfo(
        "Каталог загружен",
        f"Записей: {len(data_dict)}",
        parent=root,
    )


def main():
    global TEMPLATES

    TEMPLATES = load_templates(TEMPLATE_DIRS)

    if not TEMPLATES:
        searched_paths = ", ".join(str(path) for path in TEMPLATE_DIRS)
        raise RuntimeError(
            f"не найдены шаблоны документов; проверены: {searched_paths}"
        )

    root = tk.Tk()

    root.title("Генератор заявок")
    root.geometry("800x600")
    root.columnconfigure(0, weight=1)
    entries = {}

    default_catalog_path = get_default_catalog_path()
    startup_catalog_error = None

    try:
        data_dict = (
            read_catalog(default_catalog_path)
            if default_catalog_path
            else {}
        )
    except (OSError, ValueError) as error:
        data_dict = {}
        startup_catalog_error = str(error)

    title_to_key = {
        template_config["title"]: template_key
        for template_key, template_config in TEMPLATES.items()
    }

    selected_template = tk.StringVar()
    template_combobox = ttk.Combobox(
        root,
        textvariable=selected_template,
        values=list(title_to_key.keys()),
        state="readonly",
    )

    template_combobox.grid(row=0, column=0, columnspan=2, sticky="ew")
    template_combobox.current(0)

    catalog_frame = ttk.Frame(root)
    catalog_frame.grid(
        row=1,
        column=0,
        columnspan=2,
        padx=5,
        pady=5,
        sticky="ew",
    )
    catalog_frame.columnconfigure(1, weight=1)

    ttk.Label(
        catalog_frame,
        text="Каталог сотрудников:",
    ).grid(
        row=0,
        column=0,
        padx=(0, 8),
        sticky="w",
    )

    catalog_path_var = tk.StringVar(
        value=str(default_catalog_path) if default_catalog_path else ""
    )
    ttk.Entry(
        catalog_frame,
        textvariable=catalog_path_var,
        state="readonly",
    ).grid(
        row=0,
        column=1,
        sticky="ew",
    )

    name_combobox = SearchableCombobox(
        root,
        values=list(data_dict.keys()),
        width=55,
        max_visible_rows=6,
    )

    ttk.Button(
        catalog_frame,
        text="Выбрать…",
        command=lambda: choose_catalog(
            root,
            catalog_path_var,
            name_combobox,
            data_dict,
            entries,
        ),
    ).grid(
        row=0,
        column=2,
        padx=(8, 0),
    )

    name_combobox.grid(row=2, column=0, columnspan=2, sticky="ew")

    frame = tk.Frame(root)
    frame.grid(row=3, column=0, columnspan=2, sticky="ew")
    frame.columnconfigure(1, weight=1)

    render_frame(template_combobox, title_to_key, frame, entries)

    template_combobox.bind("<<ComboboxSelected>>", 
    lambda event: change_template(
        template_combobox,
        title_to_key,
        frame,
        entries,
        name_combobox,
        data_dict,
        ),
    )

    name_combobox.bind("<<SearchableComboboxSelected>>", 
    lambda event: fill_frame(
        name_combobox, 
        data_dict,
        entries
    ))

    submit_button = tk.Button(root, text='Сгенерировать', 
                              command=lambda: handle_button_click(
                                  entries, selected_template, title_to_key))
    submit_button.grid(row=4, 
                       column=0,
                       columnspan=2,
                       pady=10,
    )

    if startup_catalog_error:
        root.after_idle(
            lambda: messagebox.showerror(
                "Не удалось открыть каталог",
                startup_catalog_error,
                parent=root,
            )
        )

    root.mainloop()


def write_startup_error(error):
    details = "".join(
        traceback.format_exception(
            type(error),
            error,
            error.__traceback__,
        )
    )

    if sys.stderr is not None:
        sys.stderr.write(details)

    for directory in unique_paths(APP_DIR, Path.cwd()):
        try:
            log_path = directory / "DocGenerator-error.log"
            log_path.write_text(details, encoding="UTF-8")
            return log_path
        except OSError:
            continue

    return None


def show_startup_error(error, log_path):
    try:
        error_root = tk.Tk()
        error_root.withdraw()

        message = f"Приложение не удалось запустить:\n\n{error}"
        if log_path:
            message += f"\n\nПодробности записаны в:\n{log_path}"

        messagebox.showerror(
            "Ошибка запуска DocGenerator",
            message,
            parent=error_root,
        )
        error_root.destroy()
    except Exception:
        pass


def run():
    try:
        main()
    except Exception as error:
        log_path = write_startup_error(error)
        show_startup_error(error, log_path)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(run())
