import customtkinter as ctk
from datetime import datetime, timedelta
import calendar
from tkinter import Toplevel

def bind_mouse_wheel(widget):
    """
    Binds mouse wheel scrolling for cross-platform compatibility (Windows, macOS, Linux).
    This function handles the different event deltas and bindings for both
    standard Tkinter widgets (like Treeview) and CustomTkinter scrollable frames.
    """
    
    # Determine the actual scrollable target
    scrollable_target = widget
    if isinstance(widget, ctk.CTkScrollableFrame):
        scrollable_target = widget._parent_canvas

    def _on_mouse_wheel(event):
        # For Windows and macOS with mouse wheel
        if event.delta:
            # On Windows, delta is a multiple of 120. On macOS trackpad, it's a small integer.
            # We normalize the scrolling speed.
            scroll_speed = int(-1 * (event.delta / 120)) if abs(event.delta) >= 120 else -event.delta
            scrollable_target.yview_scroll(scroll_speed, "units")
        # For Linux and some macOS setups
        elif event.num == 4: # Scroll up
            scrollable_target.yview_scroll(-1, "units")
        elif event.num == 5: # Scroll down
            scrollable_target.yview_scroll(1, "units")

    widget.bind("<MouseWheel>", _on_mouse_wheel)
    widget.bind("<Button-4>", _on_mouse_wheel) # For Linux scroll up
    widget.bind("<Button-5>", _on_mouse_wheel) # For Linux scroll down

def calculate_age(dob_str):
    """Calculates age based on date of birth string (YYYY-MM-DD)."""
    if not dob_str:
        print("DEBUG: calculate_age received empty dob_str.")
        return None
    try:
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except ValueError:
        print(f"DEBUG: calculate_age failed to parse dob_str='{dob_str}'.")
        return None

def get_eligible_categories(dob_str, gender, weight_kg):
    """
    Determines eligible Kumite and Kata categories based on DOB, gender, and weight.
    
    Args:
        dob_str (str): Date of birth in YYYY-MM-DD format.
        gender (str): "Male" or "Female".
        weight_kg (float): Player's weight in kilograms.
        
    Returns:
        tuple: (list of eligible kumite categories, list of eligible kata categories)
    """
    print(f"DEBUG: get_eligible_categories called with dob='{dob_str}', gender='{gender}', weight={weight_kg}")
    from competition_categories import KUMITE_CATEGORIES, KATA_CATEGORIES, AGE_RANGES

    age = calculate_age(dob_str)
    print(f"DEBUG: Calculated age: {age}")
    if age is None or gender not in ["Male", "Female"]:
        print("DEBUG: Age is None or gender is invalid. Returning empty lists.")
        return [], []

    eligible_kumite = []
    eligible_kata = []
    
    age_category_keys = []
    for min_age, max_age, key in AGE_RANGES:
        if min_age <= age <= max_age:
            age_category_keys.append(key)
    print(f"DEBUG: Age category keys: {age_category_keys}")

    if age_category_keys:
        for age_category_key in age_category_keys:
            # Kumite Categories
            if age_category_key in KUMITE_CATEGORIES and gender in KUMITE_CATEGORIES[age_category_key]:
                weight_classes = KUMITE_CATEGORIES[age_category_key][gender]
                for wc in weight_classes:
                    is_eligible = True
                    if wc["min_weight"] is not None and weight_kg < wc["min_weight"]:
                        is_eligible = False
                    if wc["max_weight"] is not None and weight_kg > wc["max_weight"]:
                        is_eligible = False
                    
                    if is_eligible:
                        eligible_kumite.append(wc["label"])
            
            # Kata Categories
            if age_category_key in KATA_CATEGORIES and gender in KATA_CATEGORIES[age_category_key]:
                eligible_kata.extend(KATA_CATEGORIES[age_category_key][gender])
        print(f"DEBUG: Kumite categories found: {eligible_kumite}")
        print(f"DEBUG: Kata categories found: {eligible_kata}")

    return eligible_kumite, eligible_kata

class DateEntry(ctk.CTkFrame):
    """
    A custom widget that combines a CTkEntry with a button to open a calendar
    for date selection.
    """
    def __init__(self, master, placeholder_text="", initial_date=None, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0) # Button column

        self.command = command

        self.date_var = ctk.StringVar()
        self.entry = ctk.CTkEntry(self, textvariable=self.date_var, placeholder_text=placeholder_text)
        self.entry.grid(row=0, column=0, sticky="ew")

        self.calendar_button = ctk.CTkButton(self, text="📅", width=30, command=self._open_calendar)
        self.calendar_button.grid(row=0, column=1, padx=(5,0))

        self.selected_date = None
        if initial_date:
            self.set(initial_date)

    def _open_calendar(self):
        self.calendar_window = ctk.CTkToplevel(self)
        self.calendar_window.title("Select Date")
        self.calendar_window.transient(self.master) # Keep on top of parent
        self.calendar_window.grab_set() # Make it modal
        self.calendar_window.resizable(False, False)

        # Center the calendar window relative to the main window
        self.calendar_window.update_idletasks()
        # Get current position of the DateEntry widget
        x_widget = self.winfo_rootx()
        y_widget = self.winfo_rooty()
        width_widget = self.winfo_width()
        height_widget = self.winfo_height()

        # Calculate position for calendar window (e.g., below the DateEntry)
        x = x_widget
        y = y_widget + height_widget + 5 # 5 pixels below the widget
        self.calendar_window.geometry(f"+{x}+{y}")

        self.current_year = self.selected_date.year if self.selected_date else datetime.now().year
        self.current_month = self.selected_date.month if self.selected_date else datetime.now().month

        self._draw_calendar()

    def _draw_calendar(self):
        for widget in self.calendar_window.winfo_children():
            widget.destroy()

        # Month and Year navigation
        nav_frame = ctk.CTkFrame(self.calendar_window)
        nav_frame.pack(pady=5)

        # Year selection
        years = [str(y) for y in range(1910, 2101)]
        self.year_combobox = ctk.CTkComboBox(nav_frame, values=years, command=self._on_year_selected, width=80)
        self.year_combobox.set(str(self.current_year))
        self.year_combobox.pack(side="left", padx=5)

        # Month selection
        months = [calendar.month_name[i] for i in range(1, 13)]
        self.month_combobox = ctk.CTkComboBox(nav_frame, values=months, command=self._on_month_selected, width=100)
        self.month_combobox.set(calendar.month_name[self.current_month])
        self.month_combobox.pack(side="left", padx=5)

        # Previous/Next Month buttons (optional, but good for fine-tuning)
        ctk.CTkButton(nav_frame, text="<", width=30, command=lambda: self._change_month_by_button(-1)).pack(side="left", padx=2)
        ctk.CTkButton(nav_frame, text=">", width=30, command=lambda: self._change_month_by_button(1)).pack(side="left", padx=2)

        # Weekday headers
        weekdays_frame = ctk.CTkFrame(self.calendar_window)
        weekdays_frame.pack()
        for i, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            ctk.CTkLabel(weekdays_frame, text=day, width=40, height=30, font=ctk.CTkFont(weight="bold")).grid(row=0, column=i)

        # Days grid
        days_frame = ctk.CTkFrame(self.calendar_window)
        days_frame.pack()

        cal = calendar.Calendar()
        month_days = cal.monthdayscalendar(self.current_year, self.current_month)

        for week_idx, week in enumerate(month_days):
            for day_idx, day_num in enumerate(week):
                if day_num != 0:
                    day_button = ctk.CTkButton(days_frame, text=str(day_num), width=40, height=30,
                                               command=lambda d=day_num: self._select_date(d))
                    day_button.grid(row=week_idx, column=day_idx, padx=1, pady=1)
                    
                    # Highlight selected date
                    if self.selected_date and self.selected_date.year == self.current_year and \
                       self.selected_date.month == self.current_month and self.selected_date.day == day_num:
                        day_button.configure(fg_color="#8A2BE2") # Highlight color
                else:
                    ctk.CTkLabel(days_frame, text="", width=40, height=30).grid(row=week_idx, column=day_idx, padx=1, pady=1)
        
        # "Today" button
        today_button = ctk.CTkButton(self.calendar_window, text="Today", command=self._select_today)
        today_button.pack(pady=5)

    def _change_month_by_button(self, delta):
        self.current_month += delta
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        elif self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.year_combobox.set(str(self.current_year)) # Update combobox
        self.month_combobox.set(calendar.month_name[self.current_month]) # Update combobox
        self._draw_calendar()

    def _on_year_selected(self, selected_year):
        self.current_year = int(selected_year)
        self._draw_calendar()

    def _on_month_selected(self, selected_month_name):
        # Convert month name back to number
        self.current_month = list(calendar.month_name).index(selected_month_name)
        self._draw_calendar()

    def _select_date(self, day):
        self.selected_date = datetime(self.current_year, self.current_month, day).date()
        self.date_var.set(self.selected_date.strftime('%Y-%m-%d'))
        self.calendar_window.destroy()
        if self.command:
            self.command()

    def _select_today(self):
        today = datetime.now().date()
        self.selected_date = today
        self.date_var.set(today.strftime('%Y-%m-%d'))
        self.calendar_window.destroy()
        if self.command:
            self.command()

    def get(self):
        return self.date_var.get()

    def set(self, date_str):
        self.date_var.set(date_str)
        try:
            self.selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            self.selected_date = None

    def delete(self, start_index, end_index):
        self.entry.delete(start_index, end_index)
        self.selected_date = None

    def insert(self, index, text):
        self.entry.insert(index, text)
        try:
            self.selected_date = datetime.strptime(self.entry.get(), '%Y-%m-%d').date()
        except ValueError:
            self.selected_date = None

    def bind(self, event, command):
        """Allows binding to the internal CTkEntry widget."""
        self.entry.bind(event, command)

    def configure(self, **kwargs):
        # Pass configuration to the internal entry widget
        if 'placeholder_text' in kwargs:
            self.entry.configure(placeholder_text=kwargs.pop('placeholder_text'))
        self.entry.configure(**kwargs) # Pass remaining kwargs to entry