import customtkinter as ctk
from tkinter import filedialog, messagebox
import csv
import json
import random
import os
import shutil
import threading
from queue import Queue, Empty
from datetime import datetime, timedelta
from openpyxl import Workbook
from database import init_db, get_all_members, get_all_clubs, add_club, add_member, get_next_pkf_id, get_next_club_membership_id, delete_fake_data, delete_all_data
from ui_forms import AddMemberFrame, CollapsibleFrame
from ui_alerts import AlertsFrame
from ui_reports import ReportsFrame
from ui_clubs import AddClubFrame

try:
    from faker import Faker
except ImportError:
    Faker = None # Will be handled in the function

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title("PKF - Palestine Karate Federation Database")
        self.geometry("1200x750")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Visual Theme ---
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Queue for background tasks like full export
        self.export_queue = Queue()
        self.after(100, self._process_export_queue)

        # --- Main Title ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(header_frame, text="Palestine Karate Federation", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, sticky="w")

        # Temporary button for testing
        populate_button = ctk.CTkButton(header_frame, text="Add Fake Data (Test)", command=self._populate_with_fake_data, fg_color="#D35400", hover_color="#A94402")
        populate_button.grid(row=0, column=1, padx=(10, 0), sticky="e")
        if not Faker:
            # Instead of disabling, change the command to show an informative message.
            populate_button.configure(
                text="Add Fake Data (Install Faker)",
                command=self._show_faker_install_message,
                fg_color="gray50",
                hover_color="gray30"
            )

        delete_fake_data_button = ctk.CTkButton(header_frame, text="Delete Fake Data", command=self._delete_fake_data, fg_color="#E74C3C", hover_color="#C0392B")
        delete_fake_data_button.grid(row=0, column=2, padx=(10, 0), sticky="e")

        delete_all_data_button = ctk.CTkButton(header_frame, text="Delete All Data", command=self._delete_all_data, fg_color="#9B0000", hover_color="#6D0000")
        delete_all_data_button.grid(row=0, column=3, padx=(10, 0), sticky="e")

        # --- Main Tabbed Interface ---
        self.tab_view = ctk.CTkTabview(self,
                                       fg_color=("#F0F0F0", "#2B2B2B"),
                                       segmented_button_selected_color="#8A2BE2", # Purple
                                       segmented_button_unselected_color=("#E0E0E0", "#3D3D3D")
                                      )
        self.tab_view.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

        self.tab_view.add("Clubs & Organizations")
        self.tab_view.add("Member Registration")
        self.tab_view.add("Expiration Alerts")
        self.tab_view.add("Reports")

        # --- Populate Tabs ---
        # We need to pass a reference to the main App or TabView so frames can communicate
        self.add_club_frame = AddClubFrame(self.tab_view.tab("Clubs & Organizations"))
        self.add_club_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.add_member_frame = AddMemberFrame(self.tab_view.tab("Member Registration"))
        self.add_member_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.alerts_frame = AlertsFrame(self.tab_view.tab("Expiration Alerts"))
        self.alerts_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.reports_frame = ReportsFrame(self.tab_view.tab("Reports"), app_queue=self.export_queue)
        self.reports_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def _process_export_queue(self):
        """Processes results from the background export worker thread."""
        try:
            result_type, data = self.export_queue.get_nowait()
            if result_type == "export_finished":
                filepath = data
                messagebox.showinfo("Success", f"Data exported successfully to:\n{filepath}")
            elif result_type == "export_error":
                error_message = data
                messagebox.showerror("Export Error", f"An error occurred during export: {error_message}")
            elif result_type == "download_finished":
                copied, missing, errors = data
                message = f"Download complete.\n\nSuccessfully copied: {copied} files.\nMissing or failed: {missing} files."
                if errors:
                    print("\n--- Attachment Download Errors ---")
                    for error in errors:
                        print(error)
                    message += "\n\nSome files could not be copied. Check the console for details."
                messagebox.showinfo("Download Complete", message)
            elif result_type == "download_error":
                error_message = data
                messagebox.showerror("Download Error", f"An error occurred during download: {error_message}")
        except Empty:
            pass
        finally:
            # Reschedule the poller
            self.after(100, self._process_export_queue)

    def _show_faker_install_message(self):
        """Shows a message box explaining how to install the Faker library."""
        messagebox.showinfo(
            "Library Required",
            "This feature requires the 'Faker' library, which is currently not installed.\n\n"
            "To enable this feature, please follow these steps:\n\n"
            "1. Open your terminal (Command Prompt, PowerShell, or Terminal).\n"
            "2. Navigate to the project directory.\n"
            "3. Run the command:  `pip install -r requirements.txt`\n\n"
            "After the installation is complete, please restart this application."
        )

    def _delete_all_data(self):
        """Handles the complete deletion of all data in the system with multiple confirmations."""
        
        # First confirmation
        if not messagebox.askyesno("⚠️ DANGER: Confirm Deletion",
                                   "You are about to delete ALL clubs and ALL members from the system.\n\n"
                                   "This action is PERMANENT and CANNOT be undone.\n\n"
                                   "Are you absolutely sure you want to proceed?"):
            return

        # Second, more explicit confirmation
        dialog = ctk.CTkInputDialog(
            text="This is your final warning. This action will wipe the entire database and all associated files.\n\n"
                 "To confirm, please type 'DELETE' in the box below and click OK.",
            title="Final Confirmation"
        )
        confirmation_text = dialog.get_input()

        if confirmation_text != "DELETE":
            messagebox.showinfo("Cancelled", "Deletion cancelled. Your data is safe.")
            return

        try:
            deleted_clubs, deleted_members = delete_all_data()
            messagebox.showinfo("Success",
                                f"All data has been permanently deleted.\n\n"
                                f"Deleted:\n"
                                f"- {deleted_clubs} clubs\n"
                                f"- {deleted_members} member entries")
            
            # Full UI Refresh
            print("--- 🔄 Refreshing entire UI after full data deletion ---")
            self.add_member_frame.clear_form()
            self.add_member_frame.set_next_pkf_id()
            self.add_club_frame._clear_form()
            self.alerts_frame.refresh_lists()
            self.reports_frame.update_club_filter()
            self.reports_frame._perform_search()
            self.reports_frame._perform_club_search()
            print("✅ UI refreshed completely.")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while deleting all data: {e}")

    def _delete_fake_data(self):
        """Handles deletion of all fake data from the database."""
        if not messagebox.askyesno("Confirm Deletion",
                                   "This will permanently delete all fake clubs and members from the database.\n\n"
                                   "Fake data is identified by '[FAKE]' in club names and '[FAKE_DATA]' in member notes.\n\n"
                                   "Are you sure you want to continue?"):
            return

        try:
            deleted_clubs, deleted_members = delete_fake_data()
            messagebox.showinfo("Success",
                                f"Successfully deleted:\n"
                                f"- {deleted_clubs} fake clubs\n"
                                f"- {deleted_members} fake members")
            
            # Refresh UI
            print("--- 🔄 Refreshing UI after deleting fake data ---")
            self.add_member_frame.update_club_list()
            self.add_member_frame.set_next_pkf_id()
            self.alerts_frame.refresh_lists()
            self.reports_frame.update_club_filter()
            self.reports_frame._perform_search()
            print("✅ UI refreshed.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while deleting fake data: {e}")

    def _generate_specific_data(self, role, fake_en):
        """Generates a dictionary of fake role-specific data."""
        data = {}
        if role == "Player":
            kata = random.choice([True, False])
            kumite = random.choice([True, False])
            data = {
                'kata_check': kata,
                'kata_individual': kata and random.choice([True, False]),
                'kata_team': kata and random.choice([True, False]),
                'kumite_check': kumite,
                'kumite_individual': kumite and random.choice([True, False]),
                'kumite_team': kumite and random.choice([True, False]),
                'weight': str(random.randint(50, 90)),
                'nat_rank': str(random.randint(1, 100)),
                'nat_rank_points': str(random.randint(0, 1000)),
                'int_rank': str(random.randint(1, 500)),
                'int_rank_points': str(random.randint(0, 5000)),
                'additional_details': fake_en.sentence()
            }
        elif role == "Coach":
            data = {
                # National Level
                'coach_national_degree': f"Dan {random.randint(1, 5)}",
                'coach_national_place': fake_en.city(),
                'coach_national_date': fake_en.date_between(start_date='-5y', end_date='-3y').strftime('%Y-%m-%d'),
                'coach_national_points': str(random.randint(10, 100)),
                # Asian Level (optional)
                'coach_asian_degree': random.choice(["C", "B", "A"]),
                'coach_asian_place': fake_en.city(),
                'coach_asian_date': fake_en.date_between(start_date='-3y', end_date='-1y').strftime('%Y-%m-%d'),
                'coach_asian_points': str(random.randint(50, 200)),
                # International Level (optional)
                'coach_international_degree': random.choice(["WKF Accredited", "Level 1"]),
                'coach_international_place': fake_en.city(),
                'coach_international_date': fake_en.date_between(start_date='-1y', end_date='today').strftime('%Y-%m-%d'),
                'coach_international_points': str(random.randint(100, 500)),
                'additional_details': fake_en.sentence(),
            }
        elif role == "Referee":
            data = {
                # Kata - National
                'ref_kata_national_degree': random.choice(['Judge B', 'Judge A']),
                'ref_kata_national_place': fake_en.city(),
                'ref_kata_national_date': fake_en.date_between(start_date='-5y', end_date='-4y').strftime('%Y-%m-%d'),
                'ref_kata_national_points': str(random.randint(10, 50)),
                # Kata - Asian
                'ref_kata_asian_degree': random.choice(['Judge A']),
                'ref_kata_asian_place': fake_en.city(),
                'ref_kata_asian_date': fake_en.date_between(start_date='-3y', end_date='-2y').strftime('%Y-%m-%d'),
                'ref_kata_asian_points': str(random.randint(20, 100)),
                # Kata - International
                'ref_kata_international_degree': random.choice(['WKF Judge A']),
                'ref_kata_international_place': fake_en.city(),
                'ref_kata_international_date': fake_en.date_between(start_date='-1y', end_date='today').strftime('%Y-%m-%d'),
                'ref_kata_international_points': str(random.randint(50, 200)),
                
                # Kumite - National
                'ref_kumite_national_degree': random.choice(['Judge B', 'Judge A', 'Referee B', 'Referee A']),
                'ref_kumite_national_place': fake_en.city(),
                'ref_kumite_national_date': fake_en.date_between(start_date='-5y', end_date='-4y').strftime('%Y-%m-%d'),
                'ref_kumite_national_points': str(random.randint(10, 50)),
                # Kumite - Asian
                'ref_kumite_asian_degree': random.choice(['Judge A', 'Referee A']),
                'ref_kumite_asian_place': fake_en.city(),
                'ref_kumite_asian_date': fake_en.date_between(start_date='-3y', end_date='-2y').strftime('%Y-%m-%d'),
                'ref_kumite_asian_points': str(random.randint(20, 100)),
                # Kumite - International
                'ref_kumite_international_degree': random.choice(['WKF Referee A']),
                'ref_kumite_international_place': fake_en.city(),
                'ref_kumite_international_date': fake_en.date_between(start_date='-1y', end_date='today').strftime('%Y-%m-%d'),
                'ref_kumite_international_points': str(random.randint(50, 200)),

                'refereeing_achievements': fake_en.sentence()
            }
        elif role == "Admin":
            # The 'admin_title' is handled as a top-level field in the database.
            data['admin_title'] = random.choice(['Board Member', 'Secretary', 'Treasurer'])

        return data

    def _populate_with_fake_data(self):
        """Temporary function to populate the database with fake data for testing."""
        if not Faker:
            messagebox.showerror("Missing Library", "The 'Faker' library is required for this feature. Please install it using:\n\npip install Faker")
            return

        # Using a more descriptive message
        if not messagebox.askyesno("Confirm Action",
                                   "This will add fake data to the database for testing:\n\n"
                                   "• 5 Arabic-named clubs\n"
                                   "• 100 member entries (for ~80 unique people)\n"
                                   "• Some members will have multiple roles (e.g., Player & Coach)\n"
                                   "• All data fields will be filled.\n\n"
                                   "This data can be removed later using the 'Delete Fake Data' button.\n\n"
                                   "Are you sure you want to continue?"):
            return

        print("--- 🚀 Populating database with fake data... ---")
        
        fake_ar = Faker('ar_SA')
        fake_en = Faker()

        # --- 1. Create Fake Clubs (Arabic) ---
        try:
            print("Creating 5 fake Arabic clubs...")
            for i in range(5):
                club_data = {
                    'club_membership_id': get_next_club_membership_id(),
                    'name': f"[FAKE] نادي {fake_ar.company_suffix()} الرياضي", # Arabic name with marker
                    'representative_name': fake_ar.name(),
                    'address': fake_ar.address().replace('\n', ', '),
                    'email': fake_en.email(),
                    'phone': fake_en.phone_number(),
                    'classification': random.choice(['A', 'B', 'C']),
                    'affiliation_date': fake_en.date_this_decade().strftime('%Y-%m-%d'),
                    'subscription_expiry_date': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
                    'representative_gender': random.choice(['Male', 'Female']),
                    'club_subscription_fee': round(random.uniform(100, 500), 2),
                    'admin_subscription_fee': round(random.uniform(50, 200), 2),
                    'points': random.randint(0, 1000),
                    'attachments_data': {} # Ensure this is present
                }
                add_club(club_data)
            print("✅ Fake clubs created.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create fake clubs: {e}")
            return

        # --- 2. Get Club IDs ---
        all_clubs = get_all_clubs()
        if not all_clubs:
            messagebox.showerror("Error", "Could not retrieve clubs to assign members.")
            return
        club_ids = [club['id'] for club in all_clubs]

        # --- 3. Create Fake Members (with multiple roles) ---
        try:
            print("Creating 100 fake member entries for ~80 people...")
            
            unique_people = []
            NUM_UNIQUE_PEOPLE = 80
            
            # First, generate the core data for unique individuals
            for i in range(NUM_UNIQUE_PEOPLE):
                person = {
                    'pkf_id': get_next_pkf_id(),
                    'full_name': fake_en.name(),
                    'full_name_ar': fake_ar.name(),
                    'id_number': str(random.randint(100000000, 999999999)),
                    'dob': fake_en.date_of_birth(minimum_age=18, maximum_age=50).strftime('%Y-%m-%d'),
                    'gender': random.choice(['Male', 'Female']),
                    'passport_number': fake_en.swift(),
                    'passport_expiry_date': (datetime.now() + timedelta(days=random.randint(30, 1825))).strftime('%Y-%m-%d'),
                }
                unique_people.append(person)

            all_member_roles_to_create = []
            
            # Assign a primary role to each unique person
            for person in unique_people:
                person_with_role = person.copy()
                person_with_role['role'] = random.choice(["Player", "Coach", "Referee", "Admin"])
                all_member_roles_to_create.append(person_with_role)

            # Now, add 20 additional roles to random existing people
            NUM_ADDITIONAL_ROLES = 20
            for i in range(NUM_ADDITIONAL_ROLES):
                person_to_duplicate = random.choice(unique_people)
                
                # Get existing roles for this person to avoid duplicates
                existing_roles = [p['role'] for p in all_member_roles_to_create if p['pkf_id'] == person_to_duplicate['pkf_id']]
                
                # Find a new role that the person doesn't have yet
                possible_roles = ["Player", "Coach", "Referee", "Admin"]
                new_role = None
                random.shuffle(possible_roles) # Shuffle to try roles in random order
                for r in possible_roles:
                    if r not in existing_roles:
                        new_role = r
                        break
                
                if new_role: # If a unique new role was found
                    person_with_new_role = person_to_duplicate.copy()
                    person_with_new_role['role'] = new_role
                    all_member_roles_to_create.append(person_with_new_role)

            # Finally, generate the full member data for each role entry and add to DB
            for member_role_data in all_member_roles_to_create:
                role = member_role_data['role']
                specific_data = self._generate_specific_data(role, fake_en)
                
                member_data = {
                    **member_role_data, # Unpack the core person data (pkf_id, name, etc.)
                    'photo_path': '',
                    'expiry_date': (datetime.now() + timedelta(days=random.randint(-60, 365))).strftime('%Y-%m-%d'),
                    'current_belt': random.choice(['White', 'Yellow', 'Orange', 'Green', 'Blue', 'Brown', 'Black 1st Dan', 'Black 2nd Dan', 'Black 3rd Dan']),
                    'phone': fake_en.phone_number(),
                    'email': fake_en.email(),
                    'notes': f"[FAKE_DATA] {fake_en.sentence()}", # Add marker to notes
                    'club_id': random.choice(club_ids),
                    'specific_data': specific_data,
                    'admin_title': specific_data.get('admin_title') if role == 'Admin' else None
                }
                add_member(member_data)

            print(f"✅ {len(all_member_roles_to_create)} fake member entries created.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create fake members: {e}")
            # It's good practice to print the traceback for debugging
            import traceback
            traceback.print_exc()
            return
        
        # --- 4. Refresh UI ---
        print("--- 🔄 Refreshing UI ---")
        self.add_member_frame.update_club_list()
        self.add_member_frame.set_next_pkf_id()
        self.alerts_frame.refresh_lists()
        self.reports_frame.update_club_filter()
        self.reports_frame._perform_search()
        print("✅ UI refreshed.")

        messagebox.showinfo("Success", f"Successfully added {len(all_clubs)} fake clubs and {len(all_member_roles_to_create)} fake member entries.")

    def _flatten_dict(self, d: dict, parent_key: str = '', sep: str = '_') -> dict:
        """
        Flattens a nested dictionary for CSV/Excel export.
        Example: {'a': 1, 'c': {'a': 2, 'b': {'x': 5}}} -> {'a': 1, 'c_a': 2, 'c_b_x': 5}
        """
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, dict) and v:
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def _export_data_worker(self, filepath):
        """Worker function to handle the data processing and file saving in the background."""
        try:
            self._process_and_save_data(filepath)
            self.export_queue.put(("export_finished", filepath))
        except Exception as e:
            self.export_queue.put(("export_error", str(e)))

    def _export_data(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel file", "*.xlsx"), ("CSV file", "*.csv")]
        )
        if not filepath:
            return

        messagebox.showinfo("Exporting", "The full data export is running in the background. You will be notified upon completion.")
        
        # Run the heavy lifting in a separate thread
        thread = threading.Thread(target=self._export_data_worker, args=(filepath,), daemon=True)
        thread.start()

    def _process_and_save_data(self, filepath):
        """The actual logic for processing and saving the data, to be called by the worker."""
        members = get_all_members()
        if not members:
            raise ValueError("There is no data to export.")

        # Flatten the data
        processed_data = []
        for member in members:
            try:
                specific_data = json.loads(member.get('specific_data', '{}'))
                flat_specific_data = self._flatten_dict(specific_data)
                member.update(flat_specific_data)
            except (json.JSONDecodeError, AttributeError):
                pass # Ignore if specific_data is not valid JSON
            if 'specific_data' in member:
                del member['specific_data'] # Remove the original JSON field
            processed_data.append(member)

        # --- Define headers dynamically ---
        preferred_order = [
            'pkf_id', 'full_name', 'full_name_ar', 'id_number', 'role', 'club_name', 
            'admin_title', 'dob', 'expiry_date', 'current_belt', 'phone', 'email', 'notes', 'club_id',
            'passport_number', 'passport_expiry_date'
        ]

        all_available_headers = set()
        for member in processed_data:
            all_available_headers.update(member.keys())

        headers = []
        for h in preferred_order:
            if h in all_available_headers:
                headers.append(h)
        headers.extend(sorted([h for h in all_available_headers if h not in headers]))

        if filepath.endswith('.xlsx'):
            # Export to Excel
            wb = Workbook()
            ws = wb.active
            ws.title = "PKF Members"
            ws.append(headers)
            for member in processed_data:
                row = [member.get(h, "") for h in headers]
                ws.append(row)
            wb.save(filepath)

        elif filepath.endswith('.csv'):
            # Export to CSV
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                for member in processed_data:
                    filtered_member = {k: member.get(k, "") for k in headers}
                    writer.writerow(filtered_member)
        else:
            raise ValueError("Unsupported file format. Please use .xlsx or .csv.")


import sqlite3

def migrate_db():
    """
    Ensures the 'members' and 'clubs' tables have all the required columns.
    If columns are missing, it rebuilds the table to the correct schema while preserving data.
    """
    conn = None
    try:
        conn = sqlite3.connect("pkf_database.db")
        cursor = conn.cursor()

        # --- 1. Migrate 'members' table ---
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='members'")
        if cursor.fetchone() is not None:
            cursor.execute("PRAGMA table_info(members)")
            existing_cols_info = cursor.fetchall()
            existing_columns = [col[1] for col in existing_cols_info]
            
            required_columns = {
                "id": "INTEGER", "pkf_id": "TEXT", "id_number": "TEXT", "full_name": "TEXT", 
                "full_name_ar": "TEXT", "dob": "TEXT", "gender": "TEXT", "photo_path": "TEXT", 
                "phone": "TEXT", "email": "TEXT", "role": "TEXT", "expiry_date": "TEXT", 
                "current_belt": "TEXT", "specific_data": "TEXT", "notes": "TEXT", "club_id": "INTEGER", 
                "admin_title": "TEXT", "passport_number": "TEXT", "passport_expiry_date": "TEXT"
            }

            # Check if any required column is missing
            missing_columns = [col for col in required_columns if col not in existing_columns]

            if missing_columns:
                print(f"Schema migration needed for 'members' table. Missing: {missing_columns}")
                try:
                    cursor.execute("PRAGMA foreign_keys=off;")
                    cursor.execute("BEGIN TRANSACTION;")
                    cursor.execute("ALTER TABLE members RENAME TO members_old;")
                    
                    # Create new table with the correct schema from database.py
                    cursor.execute("""
                        CREATE TABLE members (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            pkf_id TEXT NOT NULL,
                            id_number TEXT,
                            full_name TEXT NOT NULL,
                            full_name_ar TEXT,
                            dob TEXT,
                            gender TEXT,
                            photo_path TEXT,
                            phone TEXT,
                            email TEXT,
                            role TEXT NOT NULL,
                            expiry_date TEXT,
                            current_belt TEXT,
                            specific_data TEXT,
                            notes TEXT,
                            club_id INTEGER,
                            admin_title TEXT,
                            passport_number TEXT,
                            passport_expiry_date TEXT,
                            FOREIGN KEY (club_id) REFERENCES clubs (id) ON DELETE SET NULL
                        )
                    """)
                    
                    # Copy data from the old table to the new one, only for columns that exist in both
                    cursor.execute("PRAGMA table_info(members_old)")
                    old_columns = [col[1] for col in cursor.fetchall()]
                    
                    # Find common columns
                    common_columns = [col for col in old_columns if col in required_columns]
                    common_cols_str = ", ".join(f'"{col}"' for col in common_columns)

                    cursor.execute(f"INSERT INTO members ({common_cols_str}) SELECT {common_cols_str} FROM members_old;")
                    
                    cursor.execute("DROP TABLE members_old;")
                    cursor.execute("COMMIT;")
                    cursor.execute("PRAGMA foreign_keys=on;")
                    print("✅ 'members' table migration completed successfully.")
                except sqlite3.Error as e:
                    print(f"FATAL: 'members' table migration failed: {e}. Rolling back.")
                    cursor.execute("ROLLBACK;")
                    # Try to restore if rename was successful
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='members_old'")
                    if cursor.fetchone():
                        cursor.execute("DROP TABLE IF EXISTS members;")
                        cursor.execute("ALTER TABLE members_old RENAME TO members;")
                    return

        # --- 2. Migrate 'clubs' table ---
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clubs'")
        if cursor.fetchone() is not None:
            cursor.execute("PRAGMA table_info(clubs)")
            existing_club_columns = [column[1] for column in cursor.fetchall()]
            required_club_columns = {
                "id": "INTEGER", "club_membership_id": "TEXT", "name": "TEXT", "representative_name": "TEXT",
                "address": "TEXT", "email": "TEXT", "points": "INTEGER", "phone": "TEXT",
                "classification": "TEXT", "club_subscription_fee": "REAL",
                "admin_subscription_fee": "REAL", "subscription_expiry_date": "TEXT",
                "affiliation_date": "TEXT", "representative_gender": "TEXT",
                "attachments_data": "TEXT"
            }

            missing_club_columns = [col for col in required_club_columns if col not in existing_club_columns]

            if missing_club_columns:
                print(f"Schema migration needed for 'clubs' table. Missing: {missing_club_columns}")
                # Just add columns for clubs, as it's less complex
                for col_name in missing_club_columns:
                    col_type = required_club_columns[col_name]
                    print(f"Adding '{col_name}' column to 'clubs' table...")
                    cursor.execute(f"ALTER TABLE clubs ADD COLUMN {col_name} {col_type.split()[0]}")
                    print(f"'{col_name}' column added successfully.")


        # --- 3. Migrate or Create 'club_points_history' table ---
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='club_points_history'")
        table_exists = cursor.fetchone() is not None
        recreate_table = False
        if table_exists:
            cursor.execute("PRAGMA table_info(club_points_history)")
            cols = [col[1] for col in cursor.fetchall()]
            # If it has the old 'year' column, it needs migration
            if 'year' in cols:
                recreate_table = True
                print("Schema migration needed for 'club_points_history' table (old schema found).")
                cursor.execute("DROP TABLE club_points_history;")

        if not table_exists or recreate_table:
            print("Creating 'club_points_history' table with new schema...")
            cursor.execute("""
                CREATE TABLE club_points_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    club_id INTEGER NOT NULL,
                    date TEXT,
                    description TEXT,
                    points INTEGER DEFAULT 0,
                    FOREIGN KEY (club_id) REFERENCES clubs (id) ON DELETE CASCADE
                )
            """)
            print("'club_points_history' table is ready.")

        conn.commit()
    except sqlite3.Error as e:
        print(f"Database migration check error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    migrate_db() # Ensure the schema is up-to-date
    init_db()  # Ensure the database and table are created before the app runs
    app = App()
    app.mainloop()
