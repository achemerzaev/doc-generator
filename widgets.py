import tkinter as tk
from tkinter import ttk
from collections.abc import Iterable
from typing import Optional

from tkcalendar import Calendar


class SearchableCombobox(ttk.Frame):
    """
    Поле ввода с выпадающими подсказками.

    Пользователь может:
    - выбрать значение из списка;
    - ввести произвольное значение;
    - искать по любой части строки.
    """

    def __init__(
        self,
        master,
        values: Iterable[str] = (),
        *,
        textvariable: Optional[tk.StringVar] = None,
        width: int = 40,
        max_visible_rows: int = 8,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        self._values: list[str] = []
        self._filtered_values: list[str] = []
        self._max_visible_rows = max(1, max_visible_rows)
        self._popup_visible = False

        self.variable = textvariable or tk.StringVar(self)

        self.set_values(values)

        # Поле ввода растягивается вместе с компонентом
        self.columnconfigure(0, weight=1)

        self.entry = ttk.Entry(
            self,
            textvariable=self.variable,
            width=width,
        )
        self.entry.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        self.button = ttk.Button(
            self,
            text="▼",
            width=3,
            takefocus=False,
            command=self._toggle_dropdown,
        )
        self.button.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self._create_popup()

        # Обработка ввода
        self.entry.bind("<KeyRelease>", self._on_key_release)

        # Управление клавиатурой
        self.entry.bind("<Down>", self._on_down)
        self.entry.bind("<Up>", self._on_up)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Escape>", self._on_escape)
        self.entry.bind("<Tab>", self._on_tab)

        # Перемещаем список вместе с компонентом
        self.bind(
            "<Configure>",
            lambda _event: self._reposition_popup(),
        )

        # Закрываем список при клике в другом месте окна
        self._toplevel = self.winfo_toplevel()

        self._root_click_binding = self._toplevel.bind(
            "<Button-1>",
            self._on_root_click,
            add="+",
        )

        self._root_configure_binding = self._toplevel.bind(
            "<Configure>",
            lambda _event: self._hide_dropdown(),
            add="+",
        )

    def _create_popup(self) -> None:
        """Создаёт выпадающее окно со списком."""

        self.popup = tk.Toplevel(self)
        self.popup.withdraw()

        # Убирает обычную рамку окна
        self.popup.overrideredirect(True)
        self.popup.transient(self.winfo_toplevel())

        container = ttk.Frame(
            self.popup,
            relief="solid",
            borderwidth=1,
        )
        container.pack(
            fill="both",
            expand=True,
        )

        self.listbox = tk.Listbox(
            container,
            activestyle="none",
            exportselection=False,
            selectmode=tk.SINGLE,
            borderwidth=0,
            highlightthickness=0,
        )
        self.listbox.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar = ttk.Scrollbar(
            container,
            orient="vertical",
            command=self.listbox.yview,
        )
        scrollbar.pack(
            side="right",
            fill="y",
        )

        self.listbox.configure(
            yscrollcommand=scrollbar.set,
        )

        self.listbox.bind(
            "<ButtonRelease-1>",
            self._on_listbox_click,
        )
        self.listbox.bind(
            "<Return>",
            self._on_listbox_enter,
        )
        self.listbox.bind(
            "<Escape>",
            self._on_escape,
        )

    def set_values(self, values: Iterable[str]) -> None:
        """
        Заменяет список доступных подсказок.
        Произвольный ввод при этом всё равно разрешён.
        """

        cleaned_values = []

        for value in values:
            if value is None:
                continue

            text = str(value).strip()

            if text:
                cleaned_values.append(text)

        # Удаляем дубликаты, сохраняя порядок
        self._values = list(dict.fromkeys(cleaned_values))

    def get(self) -> str:
        """
        Возвращает текущий текст.

        Это может быть:
        - выбранное значение;
        - произвольно введённое значение.
        """

        return self.variable.get().strip()

    def set(self, value: str) -> None:
        """Устанавливает текст программно."""

        if value is None:
            value = ""

        self.variable.set(str(value))
        self.entry.icursor(tk.END)
        self._hide_dropdown()

    def clear(self) -> None:
        """Очищает поле."""

        self.set("")

    def focus_set(self) -> None:
        """Устанавливает фокус непосредственно в поле ввода."""

        self.entry.focus_set()

    def _find_matches(self, text: str) -> list[str]:
        """Ищет подходящие подсказки."""

        query = text.strip().casefold()

        if not query:
            return self._values.copy()

        starts_with = []
        word_starts_with = []
        contains = []

        for value in self._values:
            normalized = value.casefold()

            # Сначала ФИО, начинающиеся с введённого текста
            if normalized.startswith(query):
                starts_with.append(value)

            # Затем совпадения по началу имени или отчества
            elif any(
                word.startswith(query)
                for word in normalized.split()
            ):
                word_starts_with.append(value)

            # Затем совпадения в любой части строки
            elif query in normalized:
                contains.append(value)

        return (
            starts_with
            + word_starts_with
            + contains
        )

    def _on_key_release(self, event) -> None:
        """Фильтрует список после ввода символов."""

        ignored_keys = {
            "Up",
            "Down",
            "Return",
            "Escape",
            "Tab",
            "Shift_L",
            "Shift_R",
            "Control_L",
            "Control_R",
            "Alt_L",
            "Alt_R",
        }

        if event.keysym in ignored_keys:
            return

        entered_text = self.variable.get()
        matches = self._find_matches(entered_text)

        if matches:
            self._show_dropdown(matches)
        else:
            # Введённое произвольное ФИО остаётся в поле,
            # просто список подсказок закрывается
            self._hide_dropdown()

    def _toggle_dropdown(self) -> None:
        """Открывает или закрывает список по кнопке."""

        if self._popup_visible:
            self._hide_dropdown()
            self.entry.focus_set()
            return

        matches = self._find_matches(
            self.variable.get()
        )

        if matches:
            self._show_dropdown(matches)

        self.entry.focus_set()
        self.entry.icursor(tk.END)

    def _show_dropdown(
        self,
        values: list[str],
    ) -> None:
        """Показывает выпадающий список."""

        self._filtered_values = values

        self.listbox.delete(0, tk.END)

        for value in values:
            self.listbox.insert(
                tk.END,
                value,
            )

        # Ничего не выбираем автоматически
        self.listbox.selection_clear(
            0,
            tk.END,
        )

        visible_rows = min(
            len(values),
            self._max_visible_rows,
        )

        self.listbox.configure(
            height=visible_rows,
        )

        self.update_idletasks()
        self.popup.update_idletasks()

        x = self.winfo_rootx()
        y = (
            self.winfo_rooty()
            + self.winfo_height()
        )

        width = max(
            self.winfo_width(),
            150,
        )

        height = self.popup.winfo_reqheight()

        self.popup.geometry(
            f"{width}x{height}+{x}+{y}"
        )

        self.popup.deiconify()
        self.popup.lift()

        self._popup_visible = True

    def _hide_dropdown(self) -> None:
        """Закрывает выпадающий список."""

        if (
            hasattr(self, "popup")
            and self.popup.winfo_exists()
        ):
            self.popup.withdraw()

        self._popup_visible = False

    def _reposition_popup(self) -> None:
        """Перемещает список вслед за полем."""

        if not self._popup_visible:
            return

        self.update_idletasks()

        x = self.winfo_rootx()
        y = (
            self.winfo_rooty()
            + self.winfo_height()
        )

        width = max(
            self.winfo_width(),
            150,
        )

        height = self.popup.winfo_height()

        self.popup.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    def _move_selection(
        self,
        step: int,
    ) -> None:
        """Перемещает выделение стрелками."""

        if not self._popup_visible:
            matches = self._find_matches(
                self.variable.get()
            )

            if not matches:
                return

            self._show_dropdown(matches)

        size = self.listbox.size()

        if size == 0:
            return

        selected = self.listbox.curselection()

        if selected:
            current_index = selected[0]
        elif step > 0:
            current_index = -1
        else:
            current_index = size

        new_index = current_index + step

        new_index = max(
            0,
            min(size - 1, new_index),
        )

        self.listbox.selection_clear(
            0,
            tk.END,
        )
        self.listbox.selection_set(
            new_index,
        )
        self.listbox.activate(
            new_index,
        )
        self.listbox.see(
            new_index,
        )

    def _on_down(self, _event):
        self._move_selection(1)
        return "break"

    def _on_up(self, _event):
        self._move_selection(-1)
        return "break"

    def _on_enter(self, _event):
        """
        Выбирает подсказку, только если пользователь
        выделил её стрелками.

        Иначе оставляет произвольный введённый текст.
        """

        if (
            self._popup_visible
            and self.listbox.curselection()
        ):
            self._select_current_item()
        else:
            self._hide_dropdown()

        return "break"

    def _on_escape(self, _event):
        self._hide_dropdown()
        self.entry.focus_set()

        return "break"

    def _on_tab(self, _event):
        self._hide_dropdown()

        # Не возвращаем "break":
        # Tab должен переводить фокус дальше

    def _on_listbox_click(self, _event):
        """Выбирает вариант после клика мышью."""

        if self.listbox.curselection():
            self._select_current_item()

        return "break"

    def _on_listbox_enter(self, _event):
        self._select_current_item()
        return "break"

    def _select_current_item(self) -> None:
        """Переносит выбранное значение в поле ввода."""

        selection = self.listbox.curselection()

        if not selection:
            return

        selected_value = self.listbox.get(
            selection[0]
        )

        self.variable.set(selected_value)
        self.entry.icursor(tk.END)

        self._hide_dropdown()
        self.entry.focus_set()

        # На это событие можно подписаться снаружи
        self.event_generate(
            "<<SearchableComboboxSelected>>"
        )

    def _on_root_click(self, event) -> None:
        """Закрывает список при клике вне компонента."""

        if not self._popup_visible:
            return

        widget_name = str(event.widget)

        # Клик внутри самого компонента
        if widget_name.startswith(str(self)):
            return

        # Клик внутри выпадающего окна
        if widget_name.startswith(str(self.popup)):
            return

        self._hide_dropdown()

    def destroy(self) -> None:
        """Удаляет компонент и его обработчики."""

        try:
            if self._root_click_binding:
                self._toplevel.unbind(
                    "<Button-1>",
                    self._root_click_binding,
                )
        except (tk.TclError, AttributeError):
            pass

        try:
            if self._root_configure_binding:
                self._toplevel.unbind(
                    "<Configure>",
                    self._root_configure_binding,
                )
        except (tk.TclError, AttributeError):
            pass

        try:
            self.popup.destroy()
        except (tk.TclError, AttributeError):
            pass

        super().destroy()

class OptionalDateEntry(ttk.Frame):
    """
    Поле даты, которое может оставаться пустым.

    Формат:
        ДД.ММ.ГГГГ

    Календарь:
        русский язык
    """

    def __init__(
        self,
        master,
        *,
        width: int = 12,
        locale: str = "ru_RU",
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        self._locale = locale
        self._popup = None
        self._calendar = None

        self.variable = tk.StringVar(self)

        self.columnconfigure(0, weight=1)

        self.entry = ttk.Entry(
            self,
            textvariable=self.variable,
            width=width,
        )
        self.entry.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        self.button = ttk.Button(
            self,
            text="📅",
            width=3,
            takefocus=False,
            command=self._open_calendar,
        )
        self.button.grid(
            row=0,
            column=1,
            sticky="ns",
        )

    def get(self) -> str:
        """Возвращает дату как строку ДД.ММ.ГГГГ."""

        return self.variable.get().strip()

    def set(self, value) -> None:
        """Устанавливает дату или очищает поле."""

        self.variable.set(
            "" if value is None else str(value)
        )
        self.entry.icursor(tk.END)

    def clear(self) -> None:
        """Очищает поле."""

        self.variable.set("")

    def delete(self, first, last=None) -> None:
        """
        Совместимость с обычным tk.Entry.

        Позволяет вызывать:
            widget.delete(0, tk.END)
        """

        self.entry.delete(first, last)

    def insert(self, index, value) -> None:
        """
        Совместимость с обычным tk.Entry.

        Позволяет вызывать:
            widget.insert(0, value)
        """

        self.entry.insert(index, value)

    def focus_set(self) -> None:
        self.entry.focus_set()

    def _open_calendar(self) -> None:
        """Открывает отдельное окно с календарём."""

        if (
            self._popup is not None
            and self._popup.winfo_exists()
        ):
            self._popup.lift()
            return

        self._popup = tk.Toplevel(self)
        self._popup.title("Выбор даты")
        self._popup.resizable(False, False)
        self._popup.transient(self.winfo_toplevel())

        self._popup.protocol(
            "WM_DELETE_WINDOW",
            self._close_calendar,
        )

        self._calendar = Calendar(
            self._popup,
            selectmode="day",
            locale=self._locale,
            date_pattern="dd.MM.yyyy",
            firstweekday="monday",
            showweeknumbers=False,
        )
        self._calendar.pack(
            padx=10,
            pady=(10, 5),
        )

        buttons_frame = ttk.Frame(self._popup)
        buttons_frame.pack(
            fill="x",
            padx=10,
            pady=(5, 10),
        )

        ttk.Button(
            buttons_frame,
            text="Выбрать",
            command=self._accept_date,
        ).pack(
            side="left",
            padx=(0, 5),
        )

        ttk.Button(
            buttons_frame,
            text="Очистить",
            command=self._clear_and_close,
        ).pack(
            side="left",
            padx=5,
        )

        ttk.Button(
            buttons_frame,
            text="Отмена",
            command=self._close_calendar,
        ).pack(
            side="right",
            padx=(5, 0),
        )

        # Располагаем календарь под полем
        self.update_idletasks()

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()

        self._popup.geometry(f"+{x}+{y}")

        self._popup.grab_set()
        self._popup.focus_set()

    def _accept_date(self) -> None:
        """Записывает выбранную дату в формате ДД.ММ.ГГГГ."""

        if self._calendar is None:
            return

        selected_date = self._calendar.selection_get()

        if selected_date is not None:
            self.set(
                selected_date.strftime("%d.%m.%Y")
            )

        self._close_calendar()

    def _clear_and_close(self) -> None:
        self.clear()
        self._close_calendar()

    def _close_calendar(self) -> None:
        if (
            self._popup is not None
            and self._popup.winfo_exists()
        ):
            try:
                self._popup.grab_release()
            except tk.TclError:
                pass

            self._popup.destroy()

        self._popup = None
        self._calendar = None