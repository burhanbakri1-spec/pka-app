import customtkinter as ctk
import threading
from database import get_expiring_members, get_expiring_passports
from queue import Queue, Empty
from utils import bind_mouse_wheel

class AlertsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Header and Filters ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header_frame, text="Show items expiring within:").grid(row=0, column=0, padx=(0, 5))
        self.days_filter = ctk.CTkOptionMenu(header_frame, values=["30 days", "60 days", "90 days", "180 days"], command=self.refresh_lists)
        self.days_filter.grid(row=0, column=1, padx=5, sticky="w")

        refresh_button = ctk.CTkButton(header_frame, text="Refresh", command=self.refresh_lists)
        refresh_button.grid(row=0, column=2, padx=5, sticky="e")

        # --- Tab View for different alerts ---
        self.alerts_tab_view = ctk.CTkTabview(self, fg_color="transparent")
        self.alerts_tab_view.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.alerts_tab_view.add("Membership Expiry")
        self.alerts_tab_view.add("Passport Expiry")

        # --- Membership Expiry Tab ---
        membership_tab = self.alerts_tab_view.tab("Membership Expiry")
        membership_tab.grid_columnconfigure(0, weight=1)
        membership_tab.grid_rowconfigure(0, weight=1)
        self.membership_results_frame = ctk.CTkScrollableFrame(membership_tab)
        self.membership_results_frame.grid(row=0, column=0, sticky="nsew")
        bind_mouse_wheel(self.membership_results_frame)
        self.membership_results_frame.grid_columnconfigure(0, weight=1)
        self.membership_widgets = []

        # --- Passport Expiry Tab ---
        passport_tab = self.alerts_tab_view.tab("Passport Expiry")
        passport_tab.grid_columnconfigure(0, weight=1)
        passport_tab.grid_rowconfigure(0, weight=1)
        self.passport_results_frame = ctk.CTkScrollableFrame(passport_tab)
        self.passport_results_frame.grid(row=0, column=0, sticky="nsew")
        bind_mouse_wheel(self.passport_results_frame)
        self.passport_results_frame.grid_columnconfigure(0, weight=1)
        self.passport_widgets = []

        self.refresh_lists() # Initial load
        
        # Queue for background loading of alerts
        self.alerts_queue = Queue()
        self.after(100, self._process_alerts_queue)

        self.refresh_lists() # Initial load

    def _process_alerts_queue(self):
        """Processes results from the background worker threads."""
        try:
            result_type, data = self.alerts_queue.get_nowait()
            if result_type == "membership_results":
                self._populate_membership_list(data)
            elif result_type == "passport_results":
                self._populate_passport_list(data)
        except Empty:
            pass # No items in queue
        finally:
            self.after(100, self._process_alerts_queue)

    def refresh_lists(self, filter_value=None):
        """Kicks off the data loading in background threads."""
        # Clear current lists and show a "Loading..." message immediately
        for widget in self.membership_widgets: widget.destroy()
        self.membership_widgets.clear()
        loading_label_mem = ctk.CTkLabel(self.membership_results_frame, text="Loading...", text_color="gray")
        loading_label_mem.pack(pady=20)
        self.membership_widgets.append(loading_label_mem)

        for widget in self.passport_widgets: widget.destroy()
        self.passport_widgets.clear()
        loading_label_pass = ctk.CTkLabel(self.passport_results_frame, text="Loading...", text_color="gray")
        loading_label_pass.pack(pady=20)
        self.passport_widgets.append(loading_label_pass)

        days = int(self.days_filter.get().split()[0])
        
        # Start worker threads to fetch data
        threading.Thread(target=self._fetch_expiring_members_worker, args=(days,), daemon=True).start()
        threading.Thread(target=self._fetch_expiring_passports_worker, args=(days,), daemon=True).start()

    def _fetch_expiring_members_worker(self, days):
        """Worker thread to get expiring members from DB."""
        results = get_expiring_members(days)
        self.alerts_queue.put(("membership_results", results))

    def _fetch_expiring_passports_worker(self, days):
        """Worker thread to get expiring passports from DB."""
        results = get_expiring_passports(days)
        self.alerts_queue.put(("passport_results", results))

    def _populate_membership_list(self, expiring_members):
        """Populates the UI with membership results from the queue."""
        for widget in self.membership_widgets:
            widget.destroy()
        self.membership_widgets.clear()

        if not expiring_members:
            no_results_label = ctk.CTkLabel(self.membership_results_frame, text="No memberships are expiring in this period.", text_color="gray")
            no_results_label.pack(pady=20)
            self.membership_widgets.append(no_results_label)
            return

        for member in expiring_members:
            row_frame = ctk.CTkFrame(self.membership_results_frame, fg_color=("gray85", "gray20"))
            row_frame.pack(fill="x", pady=3, padx=3)
            row_frame.grid_columnconfigure((0, 1, 2), weight=1)

            ctk.CTkLabel(row_frame, text=member.get('full_name', 'N/A'), anchor="w").grid(row=0, column=0, padx=5, sticky="ew")
            ctk.CTkLabel(row_frame, text=member.get('club_name', 'N/A'), anchor="w").grid(row=0, column=1, padx=5, sticky="ew")
            ctk.CTkLabel(row_frame, text=f"Expires on: {member.get('expiry_date', 'N/A')}", anchor="e", text_color="#E57373").grid(row=0, column=2, padx=5, sticky="ew")
            self.membership_widgets.append(row_frame)

    def _populate_passport_list(self, expiring_passports):
        """Populates the UI with passport results from the queue."""
        for widget in self.passport_widgets:
            widget.destroy()
        self.passport_widgets.clear()

        if not expiring_passports:
            no_results_label = ctk.CTkLabel(self.passport_results_frame, text="No passports are expiring in this period.", text_color="gray")
            no_results_label.pack(pady=20)
            self.passport_widgets.append(no_results_label)
            return

        for member in expiring_passports:
            row_frame = ctk.CTkFrame(self.passport_results_frame, fg_color=("gray85", "gray20"))
            row_frame.pack(fill="x", pady=3, padx=3)
            row_frame.grid_columnconfigure((0, 1, 2), weight=1)

            ctk.CTkLabel(row_frame, text=member.get('full_name', 'N/A'), anchor="w").grid(row=0, column=0, padx=5, sticky="ew")
            ctk.CTkLabel(row_frame, text=f"Passport: {member.get('passport_number', 'N/A')}", anchor="w").grid(row=0, column=1, padx=5, sticky="ew")
            ctk.CTkLabel(row_frame, text=f"Expires on: {member.get('passport_expiry_date', 'N/A')}", anchor="e", text_color="#E57373").grid(row=0, column=2, padx=5, sticky="ew")
            self.passport_widgets.append(row_frame)