import customtkinter as ctk
from tkinter.ttk import Treeview, Style
from tkinter import filedialog, messagebox
import json
import os
import shutil
import sys
import subprocess
import threading
from queue import Queue, Empty
from database import search_members_advanced, get_unique_clubs, search_clubs_advanced, get_club_by_id, delete_member, delete_club
from PIL import Image # New
from openpyxl import Workbook
from ui_forms import CollapsibleFrame
from ui_clubs import AddClubFrame
# A forward-import for type hinting, will be properly imported inside methods
from ui_forms import AddMemberFrame
from utils import bind_mouse_wheel, DateEntry
from bilingual_labels import MEMBER_LABELS_EN, MEMBER_LABELS_AR, SPECIFIC_LABELS_EN, SPECIFIC_LABELS_AR, ATTACHMENT_LABELS_EN, ATTACHMENT_LABELS_AR, CLUB_LABELS_EN, CLUB_LABELS_AR
from doc_generator import generate_bilingual_profile_doc
# استدعاء دالة التوليد من الملف الذي أنشأناه
from id_generator import generate_word_card

class MemberInfoWindow(ctk.CTkToplevel):
    """A pop-up window to display detailed member information."""
    def __init__(self, master, member_data, **kwargs):
        super().__init__(master, **kwargs)
        self.title(f"Details for {member_data.get('full_name', 'Member')}")
        self.geometry("950x700")
        self.transient(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Store data and a reference to the main reports frame for callbacks
        self.member_data = member_data
        # The master is the ReportsFrame, which has the _perform_search method
        self.reports_frame = master

        self.result_queue = Queue()
        self.after(100, self._process_queue)
        
        # --- Display Photo ---
        photo_frame = ctk.CTkFrame(self, fg_color="transparent")
        photo_frame.grid(row=0, column=0, pady=10, sticky="ew")
        photo_frame.grid_columnconfigure(0, weight=1)
        photo_path = member_data.get('photo_path')
        if photo_path and os.path.exists(photo_path):
            try:
                pil_image = Image.open(photo_path)
                pil_image.thumbnail((150, 150))
                ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=pil_image.size)
                photo_label = ctk.CTkLabel(photo_frame, image=ctk_image, text="")
                photo_label.pack()
            except Exception as e:
                ctk.CTkLabel(photo_frame, text=f"Error loading image: {e}").pack()
        else:
            ctk.CTkLabel(photo_frame, text="No Photo Available").pack()

        # --- Main content area for bilingual details ---
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        content_frame.grid_columnconfigure((0, 2), weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # --- Left side (English) ---
        en_scroll_frame = ctk.CTkScrollableFrame(content_frame, label_text="Details (English)")
        en_scroll_frame.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="nsew")
        en_scroll_frame.grid_columnconfigure(1, weight=1)
        bind_mouse_wheel(en_scroll_frame)

        # --- Separator ---
        separator = ctk.CTkFrame(content_frame, width=2, fg_color="gray50")
        separator.grid(row=0, column=1, sticky="ns", pady=5)

        # --- Right side (Arabic) ---
        ar_scroll_frame = ctk.CTkScrollableFrame(content_frame, label_text="التفاصيل (العربية)")
        ar_scroll_frame.grid(row=0, column=2, padx=(5, 0), pady=5, sticky="nsew")
        ar_scroll_frame.grid_columnconfigure(0, weight=1)
        bind_mouse_wheel(ar_scroll_frame)

        self._populate_details(en_scroll_frame, ar_scroll_frame, member_data)

        # --- Action Buttons ---
        action_frame = ctk.CTkFrame(self)
        action_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        action_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        edit_button = ctk.CTkButton(action_frame, text="Edit Member Information", command=self._open_edit_window)
        edit_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        delete_button = ctk.CTkButton(action_frame, text="Delete Member", command=self._delete_member, fg_color="#D32F2F", hover_color="#B71C1C")
        delete_button.grid(row=0, column=1, padx=(5, 5), sticky="ew")

        export_button = ctk.CTkButton(action_frame, text="Export to Word", command=self._export_to_word, fg_color="#1E88E5", hover_color="#1565C0")
        export_button.grid(row=0, column=2, padx=(5, 5), sticky="ew")

        print_card_button = ctk.CTkButton(action_frame, text="طباعة البطاقة (Word)", command=self._print_card, fg_color="#27AE60", hover_color="#1E8449")
        print_card_button.grid(row=0, column=3, padx=(5, 0), sticky="ew")

    def _open_edit_window(self):
        """يفتح نافذة جديدة لتعديل بيانات العضو."""

        edit_window = ctk.CTkToplevel(self)
        edit_window.title(f"Edit Member: {self.member_data.get('full_name')}")
        edit_window.geometry("900x700")
        edit_window.transient(self) # تبقى فوق نافذة التفاصيل
        
        # إنشاء إطار التعديل وتمرير بيانات العضو ودالة التحديث
        edit_frame = AddMemberFrame(
            edit_window,
            member_data=self.member_data,
            on_save_callback=lambda: (self.reports_frame._perform_search(), self.destroy())
        )
        edit_frame.pack(fill="both", expand=True, padx=10, pady=10)
        edit_window.protocol("WM_DELETE_WINDOW", lambda: (self.reports_frame._perform_search(), self.destroy(), edit_window.destroy()))

    def _delete_member(self):
        """Handles the deletion of the current member."""
        pkf_id = self.member_data.get('pkf_id')
        full_name = self.member_data.get('full_name')
        if not messagebox.askyesno("Confirm Deletion", f"Are you sure you want to permanently delete member '{full_name}' (ID: {pkf_id})?\n\nThis will also delete all associated files and cannot be undone."):
            return
        try:
            delete_member(pkf_id)
            messagebox.showinfo("Success", f"Member '{full_name}' has been deleted.")
            self.reports_frame._perform_search() # Refresh the list in the main window
            self.destroy() # Close this info window
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete member: {e}")

    def _print_card(self):
        """Generates and opens the member's ID card."""
        messagebox.showinfo("جاري إصدار البطاقة", "سيتم الآن توليد بطاقة العضو وفتحها تلقائياً. الرجاء الانتظار.")
        try:
            # The generation process is usually fast, so we run it in the main thread.
            # If it becomes slow, it should be moved to a background thread.
            success, message = generate_word_card(self.member_data)
            if not success:
                messagebox.showerror("خطأ في الطباعة", message)
            # If successful, the file opens automatically, so no extra message is needed.
        except Exception as e:
            messagebox.showerror("خطأ غير متوقع", f"An unexpected error occurred: {e}")

    def _process_queue(self):
        """Processes results from the worker thread in the main UI thread."""
        try:
            result_type, data = self.result_queue.get_nowait()

            if result_type == "word_export_finished":
                temp_path = data
                if not temp_path:
                    messagebox.showerror("Error", "Failed to generate Word document.")
                    return

                save_path = filedialog.asksaveasfilename(
                    defaultextension=".docx",
                    filetypes=[("Word Document", "*.docx")],
                    initialfile=os.path.basename(temp_path)
                )

                if save_path:
                    shutil.copy(temp_path, save_path)
                    messagebox.showinfo("Success", f"Profile exported successfully to:\n{save_path}")
            
            elif result_type == "word_export_error":
                error_message = data
                messagebox.showerror("Export Error", f"An error occurred during export: {error_message}")

        except Empty:
            pass
        finally:
            self.after(100, self._process_queue)

    def _export_to_word_worker(self):
        """Worker function to generate the Word doc in the background."""
        try:
            temp_path = generate_bilingual_profile_doc(
                self.member_data, MEMBER_LABELS_EN, MEMBER_LABELS_AR,
                ATTACHMENT_LABELS_EN, ATTACHMENT_LABELS_AR,
                SPECIFIC_LABELS_EN, SPECIFIC_LABELS_AR, 'member'
            )
            self.result_queue.put(("word_export_finished", temp_path))
        except Exception as e:
            self.result_queue.put(("word_export_error", str(e)))

    def _export_to_word(self):
        """Kicks off the Word document generation in a background thread."""
        messagebox.showinfo("Exporting", "The Word document is being generated. You will be prompted to save it when it's ready.")
        thread = threading.Thread(target=self._export_to_word_worker)
        thread.daemon = True
        thread.start()

    def _populate_details(self, en_parent, ar_parent, data):
        """Populates the English and Arabic frames with member details."""
        # --- Basic Information ---
        self._add_section_header(en_parent, ar_parent, "Basic Information", "المعلومات الأساسية")
        self._add_info_rows(en_parent, ar_parent, data, MEMBER_LABELS_EN, MEMBER_LABELS_AR)

        # --- Specific Data ---
        try:
            specific_data = json.loads(data.get('specific_data', '{}'))
            non_attachment_keys = {k: v for k, v in specific_data.items() if not k.endswith(('_docs', '_certs', '_receipts'))}
            if non_attachment_keys:
                self._add_section_header(en_parent, ar_parent, "Specialization Details", "تفاصيل التخصص")
                self._add_info_rows(en_parent, ar_parent, specific_data, SPECIFIC_LABELS_EN, SPECIFIC_LABELS_AR)

            # --- Attachments ---
            attachment_keys = {k: v for k, v in specific_data.items() if k.endswith(('_docs', '_certs', '_receipts'))}
            if attachment_keys:
                self._add_section_header(en_parent, ar_parent, "Attached Files", "الملفات المرفقة")
                self._add_attachments_section(en_parent, ar_parent, attachment_keys, ATTACHMENT_LABELS_EN, ATTACHMENT_LABELS_AR)

        except (json.JSONDecodeError, TypeError):
            pass

    def _add_section_header(self, en_parent, ar_parent, en_text, ar_text):
        """Adds a bold header to both parent frames."""
        en_header = ctk.CTkLabel(en_parent, text=en_text, font=ctk.CTkFont(weight="bold", size=14))
        en_header.pack(fill="x", pady=(15, 5), padx=10)

        ar_header = ctk.CTkLabel(ar_parent, text=ar_text, font=ctk.CTkFont(weight="bold", size=14))
        ar_header.pack(fill="x", pady=(15, 5), padx=10)

    def _add_info_rows(self, en_parent, ar_parent, data, labels_en, labels_ar):
        """Adds key-value data rows to both parent frames."""
        for key, label_en in labels_en.items():
            value = data.get(key)

            # Format list values nicely, otherwise use 'N/A'
            if isinstance(value, list):
                value = ", ".join(map(str, value)) if value else 'N/A'
            elif not value:
                value = 'N/A'

            # --- English Row (Left) ---
            en_row = ctk.CTkFrame(en_parent, fg_color="transparent")
            en_row.pack(fill="x", padx=10, pady=2)
            en_row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(en_row, text=f"{label_en}:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(en_row, text=str(value), wraplength=250, justify="left").grid(row=0, column=1, sticky="w", padx=5)

            # --- Arabic Row (Right) ---
            label_ar = labels_ar.get(key, label_en)
            ar_row = ctk.CTkFrame(ar_parent, fg_color="transparent")
            ar_row.pack(fill="x", padx=10, pady=2)
            ar_row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(ar_row, text=f":{label_ar}", font=ctk.CTkFont(weight="bold"), justify="right").grid(row=0, column=1, sticky="e")
            ctk.CTkLabel(ar_row, text=str(value), wraplength=250, justify="right").grid(row=0, column=0, sticky="e", padx=5)

    def _add_attachments_section(self, en_parent, ar_parent, attachment_data, labels_en, labels_ar):
        for key, file_paths in attachment_data.items():
            if not file_paths: continue

            en_label = labels_en.get(key, key.replace('_', ' ').title())
            ar_label = labels_ar.get(key, en_label)

            ctk.CTkLabel(en_parent, text=en_label, font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))
            ctk.CTkLabel(ar_parent, text=ar_label, font=ctk.CTkFont(weight="bold")).pack(anchor="e", padx=10, pady=(10, 0))

            for path in file_paths:
                filename = os.path.basename(path)
                # English
                en_file_label = ctk.CTkLabel(en_parent, text=filename, text_color="#6495ED", cursor="hand2")
                en_file_label.pack(anchor="w", padx=20)
                en_file_label.bind("<Button-1>", lambda e, p=path: self._open_file(p))
                # Arabic
                ar_file_label = ctk.CTkLabel(ar_parent, text=filename, text_color="#6495ED", cursor="hand2")
                ar_file_label.pack(anchor="e", padx=20)
                ar_file_label.bind("<Button-1>", lambda e, p=path: self._open_file(p))

    def _open_file(self, path):
        try:
            if not os.path.exists(path):
                messagebox.showerror("Error", f"File not found:\n{path}")
                return
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")


class ClubInfoWindow(ctk.CTkToplevel):
    """A pop-up window to display detailed club information."""
    def __init__(self, master, club_data, **kwargs):
        super().__init__(master, **kwargs)
        self.title(f"Details for {club_data.get('name', 'Club')}")
        self.geometry("950x700")
        self.transient(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.club_data = club_data
        self.reports_frame = master # The master is the ReportsFrame

        self.result_queue = Queue()
        self.after(100, self._process_queue)

        # --- Main content area for bilingual details ---
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        content_frame.grid_columnconfigure((0, 2), weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        en_scroll_frame = ctk.CTkScrollableFrame(content_frame, label_text="Details (English)")
        en_scroll_frame.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="nsew")
        en_scroll_frame.grid_columnconfigure(1, weight=1)
        bind_mouse_wheel(en_scroll_frame)

        separator = ctk.CTkFrame(content_frame, width=2, fg_color="gray50")
        separator.grid(row=0, column=1, sticky="ns", pady=5)

        ar_scroll_frame = ctk.CTkScrollableFrame(content_frame, label_text="التفاصيل (العربية)")
        ar_scroll_frame.grid(row=0, column=2, padx=(5, 0), pady=5, sticky="nsew")
        ar_scroll_frame.grid_columnconfigure(0, weight=1)
        bind_mouse_wheel(ar_scroll_frame)

        self._populate_details(en_scroll_frame, ar_scroll_frame, club_data)

        # --- Action Buttons ---
        action_frame = ctk.CTkFrame(self)
        action_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        action_frame.grid_columnconfigure((0, 1, 2), weight=1)

        edit_button = ctk.CTkButton(action_frame, text="Edit Club Information", command=self._open_edit_window)
        edit_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        delete_button = ctk.CTkButton(action_frame, text="Delete Club", command=self._delete_club, fg_color="#D32F2F", hover_color="#B71C1C")
        delete_button.grid(row=0, column=1, padx=5, sticky="ew")
        export_button = ctk.CTkButton(action_frame, text="Export to Word", command=self._export_to_word, fg_color="#1E88E5", hover_color="#1565C0")
        export_button.grid(row=0, column=2, padx=(5, 0), sticky="ew")

    def _open_edit_window(self):
        edit_window = ctk.CTkToplevel(self)
        edit_window.title(f"Edit Club: {self.club_data.get('name')}")
        edit_window.geometry("800x600")
        edit_window.transient(self)
        edit_window.grab_set()

        edit_frame = AddClubFrame(
            edit_window,
            club_data=self.club_data,
            on_save_callback=lambda: (self.reports_frame._perform_club_search(), self.destroy())
        )
        edit_frame.pack(fill="both", expand=True, padx=10, pady=10)
        edit_window.protocol("WM_DELETE_WINDOW", lambda: (self.reports_frame._perform_club_search(), self.destroy(), edit_window.destroy()))

    def _delete_club(self):
        """Handles the deletion of the current club."""
        club_id = self.club_data.get('id')
        club_name = self.club_data.get('name')
        if not messagebox.askyesno("Confirm Deletion", f"Are you sure you want to permanently delete club '{club_name}'?\n\nMembers of this club will become unaffiliated. This will also delete all associated files and cannot be undone."):
            return
        try:
            delete_club(club_id)
            messagebox.showinfo("Success", f"Club '{club_name}' has been deleted.")
            self.reports_frame._perform_club_search() # Refresh the list
            self.reports_frame.update_club_filter() # Refresh dropdowns in other tabs
            self.destroy() # Close this info window
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete club: {e}")

    def _process_queue(self):
        """Processes results from the worker thread in the main UI thread."""
        try:
            result_type, data = self.result_queue.get_nowait()
            if result_type == "word_export_finished":
                temp_path = data
                if not temp_path:
                    messagebox.showerror("Error", "Failed to generate Word document.")
                    return
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".docx",
                    filetypes=[("Word Document", "*.docx")],
                    initialfile=os.path.basename(temp_path)
                )
                if save_path:
                    shutil.copy(temp_path, save_path)
                    messagebox.showinfo("Success", f"Profile exported successfully to:\n{save_path}")
            elif result_type == "word_export_error":
                error_message = data
                messagebox.showerror("Export Error", f"An error occurred during export: {error_message}")
        except Empty:
            pass
        finally:
            self.after(100, self._process_queue)

    def _export_to_word_worker(self):
        """Worker function to generate the Word doc in the background."""
        try:
            temp_path = generate_bilingual_profile_doc(
                self.club_data, CLUB_LABELS_EN, CLUB_LABELS_AR,
                ATTACHMENT_LABELS_EN, ATTACHMENT_LABELS_AR,
                {}, {}, 'club' # No specific labels for clubs
            )
            self.result_queue.put(("word_export_finished", temp_path))
        except Exception as e:
            self.result_queue.put(("word_export_error", str(e)))

    def _export_to_word(self):
        messagebox.showinfo("Exporting", "The Word document is being generated. You will be prompted to save it when it's ready.")
        thread = threading.Thread(target=self._export_to_word_worker)
        thread.daemon = True
        thread.start()

    def _populate_details(self, en_parent, ar_parent, data):
        self._add_section_header(en_parent, ar_parent, "Club Information", "معلومات النادي")
        self._add_info_rows(en_parent, ar_parent, data, CLUB_LABELS_EN, CLUB_LABELS_AR)

        try:
            attachments = data.get('attachments_data', '{}')
            if isinstance(attachments, str):
                attachments = json.loads(attachments)
            if attachments:
                self._add_section_header(en_parent, ar_parent, "Attached Files", "الملفات المرفقة")
                self._add_attachments_section(en_parent, ar_parent, attachments, ATTACHMENT_LABELS_EN, ATTACHMENT_LABELS_AR)
        except (json.JSONDecodeError, TypeError):
            pass

    def _add_section_header(self, en_parent, ar_parent, en_text, ar_text):
        en_header = ctk.CTkLabel(en_parent, text=en_text, font=ctk.CTkFont(weight="bold", size=14))
        en_header.pack(fill="x", pady=(15, 5), padx=10)
        ar_header = ctk.CTkLabel(ar_parent, text=ar_text, font=ctk.CTkFont(weight="bold", size=14))
        ar_header.pack(fill="x", pady=(15, 5), padx=10)

    def _add_info_rows(self, en_parent, ar_parent, data, labels_en, labels_ar):
        for key, label_en in labels_en.items():
            value = data.get(key)
            if not value: value = 'N/A'
            en_row = ctk.CTkFrame(en_parent, fg_color="transparent")
            en_row.pack(fill="x", padx=10, pady=2)
            en_row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(en_row, text=f"{label_en}:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(en_row, text=str(value), wraplength=250, justify="left").grid(row=0, column=1, sticky="w", padx=5)
            label_ar = labels_ar.get(key, label_en)
            ar_row = ctk.CTkFrame(ar_parent, fg_color="transparent")
            ar_row.pack(fill="x", padx=10, pady=2)
            ar_row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(ar_row, text=f":{label_ar}", font=ctk.CTkFont(weight="bold"), justify="right").grid(row=0, column=1, sticky="e")
            ctk.CTkLabel(ar_row, text=str(value), wraplength=250, justify="right").grid(row=0, column=0, sticky="e", padx=5)

    def _add_attachments_section(self, en_parent, ar_parent, attachment_data, labels_en, labels_ar):
        for key, file_paths in attachment_data.items():
            if not file_paths: continue
            en_label = labels_en.get(key, key.replace('_', ' ').title())
            ar_label = labels_ar.get(key, en_label)
            ctk.CTkLabel(en_parent, text=en_label, font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))
            ctk.CTkLabel(ar_parent, text=ar_label, font=ctk.CTkFont(weight="bold")).pack(anchor="e", padx=10, pady=(10, 0))
            for path in file_paths:
                filename = os.path.basename(path)
                en_file_label = ctk.CTkLabel(en_parent, text=filename, text_color="#6495ED", cursor="hand2")
                en_file_label.pack(anchor="w", padx=20)
                en_file_label.bind("<Button-1>", lambda e, p=path: self._open_file(p))
                ar_file_label = ctk.CTkLabel(ar_parent, text=filename, text_color="#6495ED", cursor="hand2")
                ar_file_label.pack(anchor="e", padx=20)
                ar_file_label.bind("<Button-1>", lambda e, p=path: self._open_file(p))

    def _open_file(self, path):
        try:
            if not os.path.exists(path):
                messagebox.showerror("Error", f"File not found:\n{path}")
                return
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")


class ReportsFrame(ctk.CTkFrame):
    def __init__(self, master, app_queue, **kwargs):
        super().__init__(master, **kwargs)
        self.app_queue = app_queue
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main tab view for different report types
        self.report_tab_view = ctk.CTkTabview(self, fg_color="transparent")
        self.report_tab_view.pack(fill="both", expand=True, padx=5, pady=5)
        self.report_tab_view.add("Member Reports")
        self.report_tab_view.add("Club Reports")
        self.report_tab_view.add("Attachments Report")

        # --- Populate Member Reports Tab ---
        self.member_tab = self.report_tab_view.tab("Member Reports")
        self.member_tab.grid_columnconfigure(0, weight=1)
        self.member_tab.grid_rowconfigure(1, weight=1)
        self.members_data = {}
        self._create_member_report_widgets(self.member_tab)
        
        # --- Populate Club Reports Tab ---
        self.club_tab = self.report_tab_view.tab("Club Reports")
        self.club_tab.grid_columnconfigure(0, weight=1)
        self.club_tab.grid_rowconfigure(1, weight=1)
        self.clubs_data = {}
        self._create_club_report_widgets(self.club_tab)

        # --- Populate Attachments Report Tab ---
        self.attachment_tab = self.report_tab_view.tab("Attachments Report")
        self.attachment_tab.grid_columnconfigure(0, weight=1)
        self.attachment_tab.grid_rowconfigure(1, weight=1)
        self.selected_attachment_entity = None
        self.attachment_type_checkboxes = {}
        self._create_attachment_report_widgets(self.attachment_tab)

        self.search_queue = Queue()
        self.after(100, self._process_search_queue)

        self.excel_export_queue = Queue()
        self.after(100, self._process_excel_queue)

        # Initial data load
        self.update_club_filter()
        # Do not perform search on startup to improve performance.
        # User will click "Apply Filters" to load data.

        self.results_tree.insert("", "end", iid="members_prompt", values=("", "Press 'Apply Filters' to load data", "", "", ""))
        self.club_results_tree.insert("", "end", iid="clubs_prompt", values=("", "Press 'Apply Filters' to load data", "", "", ""))
    def _create_member_report_widgets(self, tab):
        """Creates and places all widgets for the member reports tab."""
        filters_scroll_frame = ctk.CTkScrollableFrame(tab, height=250)
        filters_scroll_frame.grid(row=0, column=0, padx=10, pady=(0, 10), sticky="ew")
        bind_mouse_wheel(filters_scroll_frame)
        filters_scroll_frame.grid_columnconfigure(0, weight=1)
        general_filters_frame = CollapsibleFrame(filters_scroll_frame, text="General Filters")
        general_filters_frame.pack(fill="x", padx=5, pady=5)
        gf_content = general_filters_frame.content_frame
        gf_content.grid_columnconfigure(1, weight=1)
        gf_content.grid_columnconfigure(3, weight=1)

        self.search_entry = ctk.CTkEntry(gf_content, placeholder_text="Search by Name or ID...")
        self.search_entry.grid(row=0, column=0, columnspan=4, padx=10, pady=5, sticky="ew")
        self.search_entry.bind("<Return>", self._perform_search)

        ctk.CTkLabel(gf_content, text="Role:").grid(row=1, column=0, padx=(10,5), pady=5, sticky="w")
        self.role_filter = ctk.CTkOptionMenu(gf_content, values=["All Roles", "Player", "Coach", "Referee", "Admin"])
        self.role_filter.grid(row=1, column=1, padx=(0,10), pady=5, sticky="ew")

        ctk.CTkLabel(gf_content, text="Club:").grid(row=1, column=2, padx=(10,5), pady=5, sticky="w")
        self.club_filter = ctk.CTkOptionMenu(gf_content, values=["All Clubs"])
        self.club_filter.grid(row=1, column=3, padx=(0,10), pady=5, sticky="ew")

        ctk.CTkLabel(gf_content, text="Current Belt:").grid(row=2, column=0, padx=(10,5), pady=5, sticky="w")
        self.belt_filter = ctk.CTkEntry(gf_content, placeholder_text="e.g., Black")
        self.belt_filter.grid(row=2, column=1, padx=(0,10), pady=5, sticky="ew")

        ctk.CTkLabel(gf_content, text="Profession:").grid(row=2, column=2, padx=(10,5), pady=5, sticky="w")
        self.profession_filter = ctk.CTkEntry(gf_content, placeholder_text="e.g., Engineer")
        self.profession_filter.grid(row=2, column=3, padx=(0,10), pady=5, sticky="ew")

        date_filters_frame = CollapsibleFrame(filters_scroll_frame, text="Date Filters")
        date_filters_frame.pack(fill="x", padx=5, pady=5)
        df_content = date_filters_frame.content_frame
        df_content.grid_columnconfigure(1, weight=1)
        df_content.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(df_content, text="Expiry Date:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.expiry_from = DateEntry(df_content, placeholder_text="From Date")
        self.expiry_from.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.expiry_to = DateEntry(df_content, placeholder_text="To Date")
        self.expiry_to.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(df_content, text="Date of Birth:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.dob_from = DateEntry(df_content, placeholder_text="From Date")
        self.dob_from.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.dob_to = DateEntry(df_content, placeholder_text="To Date")
        self.dob_to.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        player_filters_frame = CollapsibleFrame(filters_scroll_frame, text="Player Filters")
        player_filters_frame.pack(fill="x", padx=5, pady=5)
        pf_content = player_filters_frame.content_frame
        pf_content.grid_columnconfigure(1, weight=1)
        pf_content.grid_columnconfigure(3, weight=1)

        self.kata_filter = ctk.CTkCheckBox(pf_content, text="Participates in Kata")
        self.kata_filter.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        self.kumite_filter = ctk.CTkCheckBox(pf_content, text="Participates in Kumite")
        self.kumite_filter.grid(row=0, column=2, columnspan=2, padx=10, pady=5, sticky="w")

        coach_filters_frame = CollapsibleFrame(filters_scroll_frame, text="Coach Filters")
        coach_filters_frame.pack(fill="x", padx=5, pady=5)
        cf_content = coach_filters_frame.content_frame
        cf_content.grid_columnconfigure(1, weight=1)
        cf_content.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(cf_content, text="National Degree:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.coach_nat_rank = ctk.CTkEntry(cf_content, placeholder_text="e.g., Dan 1")
        self.coach_nat_rank.grid(row=0, column=1, columnspan=3, padx=10, pady=5, sticky="ew")

        action_frame = ctk.CTkFrame(filters_scroll_frame, fg_color="transparent")
        action_frame.pack(fill="x", padx=5, pady=10)
        search_button = ctk.CTkButton(action_frame, text="Apply Filters", command=self._perform_search)
        search_button.pack(side="left", padx=10)
        
        export_button = ctk.CTkButton(action_frame, text="Export to Excel", command=self._export_to_excel)
        export_button.pack(side="left", padx=10)

        clear_button = ctk.CTkButton(action_frame, text="Clear Filters", command=self._clear_filters, fg_color="gray")
        clear_button.pack(side="left", padx=10)

        tree_frame = ctk.CTkFrame(tab)
        tree_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        style = Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2B2B2B", foreground="white", fieldbackground="#2B2B2B", borderwidth=0, rowheight=25)
        style.map('Treeview', background=[('selected', '#8A2BE2')])
        style.configure("Treeview.Heading", background="#565B5E", foreground="white", relief="flat", font=('Calibri', 12, 'bold'))
        style.map("Treeview.Heading", background=[('active', '#343638')])

        self.results_tree = Treeview(tree_frame, columns=("Name (EN)", "Name (AR)", "PKF ID", "Club", "Role"), show="headings")
        self.results_tree.heading("Name (EN)", text="Name (English)")
        self.results_tree.heading("Name (AR)", text="Name (Arabic)")
        self.results_tree.heading("PKF ID", text="Membership No.")
        self.results_tree.heading("Club", text="Club")
        self.results_tree.heading("Role", text="Role")

        self.results_tree.column("Name (EN)", width=200)
        self.results_tree.column("Name (AR)", width=200)
        self.results_tree.column("PKF ID", width=150)
        self.results_tree.column("Club", width=200)
        self.results_tree.column("Role", width=100)

        self.results_tree.grid(row=0, column=0, sticky="nsew")
        self.results_tree.bind("<Double-1>", self._on_double_click)

        scrollbar = ctk.CTkScrollbar(tree_frame, command=self.results_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        bind_mouse_wheel(self.results_tree)
        self.results_tree.configure(yscrollcommand=scrollbar.set)

    def _create_club_report_widgets(self, tab):
        """Creates and places all widgets for the club reports tab."""
        # --- Filters Frame ---
        club_filters_frame = ctk.CTkFrame(tab, fg_color="transparent")
        club_filters_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        club_filters_frame.grid_columnconfigure(1, weight=1)
        club_filters_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(club_filters_frame, text="Membership ID:").grid(row=0, column=0, padx=(10,5), pady=5, sticky="w")
        self.club_id_filter = ctk.CTkEntry(club_filters_frame, placeholder_text="Search by Club ID...")
        self.club_id_filter.grid(row=0, column=1, columnspan=3, padx=(0,10), pady=5, sticky="ew")
        self.club_id_filter.bind("<Return>", self._perform_club_search)

        ctk.CTkLabel(club_filters_frame, text="Classification:").grid(row=1, column=0, padx=(10,5), pady=5, sticky="w")
        self.club_class_filter = ctk.CTkOptionMenu(club_filters_frame, values=["All Classifications", "A", "B", "C"])
        self.club_class_filter.grid(row=1, column=1, padx=(0,10), pady=5, sticky="ew")

        ctk.CTkLabel(club_filters_frame, text="Affiliation Date:").grid(row=2, column=0, padx=(10,5), pady=5, sticky="w")
        self.club_aff_from = DateEntry(club_filters_frame, placeholder_text="From Date")
        self.club_aff_from.grid(row=2, column=1, padx=(0,10), pady=5, sticky="ew")
        self.club_aff_to = DateEntry(club_filters_frame, placeholder_text="To Date")
        self.club_aff_to.grid(row=2, column=2, columnspan=2, padx=(0,10), pady=5, sticky="ew")

        ctk.CTkLabel(club_filters_frame, text="Points (Min):").grid(row=3, column=0, padx=(10,5), pady=5, sticky="w")
        self.club_points_filter = ctk.CTkEntry(club_filters_frame, placeholder_text="Minimum Points")
        self.club_points_filter.grid(row=3, column=1, padx=(0,10), pady=5, sticky="ew")

        self.club_expired_filter = ctk.CTkCheckBox(club_filters_frame, text="Show only clubs with expired subscriptions")
        self.club_expired_filter.grid(row=4, column=0, columnspan=4, padx=10, pady=5, sticky="w")

        club_action_frame = ctk.CTkFrame(club_filters_frame, fg_color="transparent")
        club_action_frame.grid(row=5, column=0, columnspan=4, pady=10)
        club_search_button = ctk.CTkButton(club_action_frame, text="Apply Filters", command=self._perform_club_search)
        club_search_button.pack(side="left", padx=10)

        export_clubs_button = ctk.CTkButton(club_action_frame, text="Export to Excel", command=self._export_clubs_to_excel)
        export_clubs_button.pack(side="left", padx=10)

        club_clear_button = ctk.CTkButton(club_action_frame, text="Clear Filters", command=self._clear_club_filters, fg_color="gray")
        club_clear_button.pack(side="left", padx=10)

        # --- Results Treeview for Clubs ---
        club_tree_frame = ctk.CTkFrame(tab)
        club_tree_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        club_tree_frame.grid_rowconfigure(0, weight=1)
        club_tree_frame.grid_columnconfigure(0, weight=1)

        style = Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2B2B2B", foreground="white", fieldbackground="#2B2B2B", borderwidth=0, rowheight=25)
        style.map('Treeview', background=[('selected', '#8A2BE2')])
        style.configure("Treeview.Heading", background="#565B5E", foreground="white", relief="flat", font=('Calibri', 12, 'bold'))
        style.map("Treeview.Heading", background=[('active', '#343638')])

        self.club_results_tree = Treeview(club_tree_frame, columns=("ID", "Name", "Classification", "Affiliation", "Expiry"), show="headings")
        self.club_results_tree.heading("ID", text="Membership ID")
        self.club_results_tree.heading("Name", text="Club Name")
        self.club_results_tree.heading("Classification", text="Classification")
        self.club_results_tree.heading("Affiliation", text="Affiliation Date")
        self.club_results_tree.heading("Expiry", text="Expiry Date")
        self.club_results_tree.grid(row=0, column=0, sticky="nsew")
        self.club_results_tree.bind("<Double-1>", self._on_club_double_click)

        club_scrollbar = ctk.CTkScrollbar(club_tree_frame, command=self.club_results_tree.yview)
        club_scrollbar.grid(row=0, column=1, sticky="ns")
        bind_mouse_wheel(self.club_results_tree)
        self.club_results_tree.configure(yscrollcommand=club_scrollbar.set)

    def _create_attachment_report_widgets(self, tab):
        """Creates and places all widgets for the attachment reports tab."""
        # --- Top Search Frame ---
        search_frame = ctk.CTkFrame(tab)
        search_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        search_frame.grid_columnconfigure(0, weight=1)

        self.attachment_search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search by Member or Club Name/ID...")
        self.attachment_search_entry.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="ew")
        self.attachment_search_entry.bind("<Return>", lambda e: self._perform_attachment_search())

        search_button = ctk.CTkButton(search_frame, text="Search", command=self._perform_attachment_search)
        search_button.grid(row=0, column=1, pady=5, sticky="e")

        # --- Middle Content Frame ---
        content_frame = ctk.CTkFrame(tab, fg_color="transparent")
        content_frame.grid(row=1, column=0, padx=10, pady=0, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # --- Search Results (Left) ---
        self.attachment_search_results_frame = ctk.CTkScrollableFrame(content_frame, label_text="Search Results")
        self.attachment_search_results_frame.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
        bind_mouse_wheel(self.attachment_search_results_frame)
        ctk.CTkLabel(self.attachment_search_results_frame, text="Enter a search term above.").pack(pady=20)

        # --- Attachment Types (Right) ---
        self.attachment_type_selection_frame = ctk.CTkScrollableFrame(content_frame, label_text="Available Attachments")
        self.attachment_type_selection_frame.grid(row=0, column=1, padx=(5, 0), sticky="nsew")
        bind_mouse_wheel(self.attachment_type_selection_frame)
        ctk.CTkLabel(self.attachment_type_selection_frame, text="Select an entity from the results.").pack(pady=20)

        # --- Bottom Action Frame ---
        action_frame = ctk.CTkFrame(tab)
        action_frame.grid(row=2, column=0, padx=10, pady=(10, 10), sticky="ew")
        
        self.download_button = ctk.CTkButton(action_frame, text="Download Selected Attachments", command=self._download_selected_attachments, height=40, fg_color="#008CBA", hover_color="#007B9E", state="disabled")
        self.download_button.pack(fill="x", padx=10, pady=10)

    def _perform_attachment_search(self):
        query = self.attachment_search_entry.get()
        if not query.strip():
            messagebox.showwarning("Input Needed", "Please enter a name or ID to search for.")
            return

        for widget in self.attachment_search_results_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.attachment_search_results_frame, text="Searching...").pack(pady=20)

        for widget in self.attachment_type_selection_frame.winfo_children():
            widget.destroy()
        self.attachment_type_checkboxes.clear()
        self.selected_attachment_entity = None
        self.download_button.configure(state="disabled")

        thread = threading.Thread(target=self._perform_attachment_search_worker, args=(query,), daemon=True)
        thread.start()

    def _perform_attachment_search_worker(self, query):
        try:
            member_results = search_members_advanced(query=query)
            club_results = search_clubs_advanced(membership_id=query, name=query)

            combined_results = []
            for member in member_results:
                combined_results.append({'type': 'member', 'data': member})
            for club in club_results:
                combined_results.append({'type': 'club', 'data': club})
            
            self.search_queue.put(("attachment_entity_search_results", combined_results))
        except Exception as e:
            self.search_queue.put(("search_error", f"Failed to search for entities: {e}"))

    def _on_entity_selected(self, entity):
        self.selected_attachment_entity = entity

        for widget in self.attachment_type_selection_frame.winfo_children():
            widget.destroy()
        self.attachment_type_checkboxes.clear()

        attachment_data = {}
        if entity['type'] == 'member':
            try:
                specific_data = json.loads(entity['data'].get('specific_data', '{}'))
                attachment_data = {k: v for k, v in specific_data.items() if k.endswith(('_docs', '_certs', '_receipts')) and v}
            except json.JSONDecodeError: pass
        elif entity['type'] == 'club':
            try:
                attachment_data = json.loads(entity['data'].get('attachments_data', '{}'))
                attachment_data = {k: v for k, v in attachment_data.items() if v}
            except json.JSONDecodeError: pass

        if not attachment_data:
            ctk.CTkLabel(self.attachment_type_selection_frame, text="No attachments found for this entity.").pack(pady=10)
            self.download_button.configure(state="disabled")
            return

        for key in sorted(attachment_data.keys()):
            label = ATTACHMENT_LABELS_EN.get(key, key.replace('_', ' ').title())
            chk = ctk.CTkCheckBox(self.attachment_type_selection_frame, text=label)
            chk.pack(anchor="w", padx=10, pady=2)
            self.attachment_type_checkboxes[key] = chk
        
        self.download_button.configure(state="normal")

    def _download_selected_attachments(self):
        if not self.selected_attachment_entity:
            messagebox.showwarning("No Selection", "Please search for and select a member or club first.")
            return

        selected_types = [type_key for type_key, chk in self.attachment_type_checkboxes.items() if chk.get() == 1]

        if not selected_types:
            messagebox.showwarning("No Selection", "Please select at least one attachment type.")
            return

        destination_folder = filedialog.askdirectory(title="Select Folder to Save Attachments")
        if not destination_folder: return

        messagebox.showinfo("Download Started", "Downloading selected attachments in the background. You will be notified upon completion.")

        thread = threading.Thread(target=self._download_attachments_worker, args=(destination_folder, self.selected_attachment_entity, selected_types), daemon=True)
        thread.start()

    def _download_attachments_worker(self, destination_folder, entity, selected_types):
        copied_count, missing_count, error_list = 0, 0, []

        def copy_file(source_path, dest_folder):
            nonlocal copied_count, missing_count
            if os.path.exists(source_path):
                try:
                    os.makedirs(dest_folder, exist_ok=True)
                    shutil.copy2(source_path, dest_folder) # copy2 preserves metadata
                    copied_count += 1
                except Exception as e:
                    missing_count += 1
                    error_list.append(f"Could not copy '{source_path}': {e}")
            else:
                missing_count += 1
                error_list.append(f"File not found: '{source_path}'")

        try:
            entity_data = entity['data']
            
            if entity['type'] == 'member':
                name = entity_data.get('full_name', 'Unknown_Member')
                id_str = entity_data.get('pkf_id', 'NO_ID')
                attachment_source = json.loads(entity_data.get('specific_data', '{}'))
            else: # club
                name = entity_data.get('name', 'Unknown_Club')
                id_str = entity_data.get('club_membership_id', 'NO_ID')
                attachment_source = json.loads(entity_data.get('attachments_data', '{}'))

            safe_name = "".join(c for c in f"{name} {id_str}" if c.isalnum() or c in (' ', '_', '-')).rstrip()
            entity_folder_path = os.path.join(destination_folder, safe_name)

            for type_key in selected_types:
                if type_key in attachment_source:
                    paths = attachment_source[type_key]
                    if isinstance(paths, list):
                        for path in paths: copy_file(path, entity_folder_path)
                    elif isinstance(paths, str) and paths:
                        copy_file(paths, entity_folder_path)

            self.app_queue.put(("download_finished", (copied_count, missing_count, error_list)))
        except Exception as e:
            self.app_queue.put(("download_error", str(e)))
    def _perform_search(self, event=None):
        filters = { "query": self.search_entry.get(), "role": self.role_filter.get(), "club": self.club_filter.get(), "current_belt": self.belt_filter.get(), "profession": self.profession_filter.get(), "expiry_from": self.expiry_from.get(), "expiry_to": self.expiry_to.get(), "dob_from": self.dob_from.get(), "dob_to": self.dob_to.get(), "has_kata": self.kata_filter.get() == 1, "has_kumite": self.kumite_filter.get() == 1, "coach_nat_rank": self.coach_nat_rank.get(), }
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.results_tree.insert("", "end", iid="searching", values=("", "Searching, please wait...", "", "", ""))
        self.update_idletasks()
        thread = threading.Thread(target=self._perform_search_worker, args=(filters,), daemon=True)
        thread.start()

    def _on_double_click(self, event):
        """Handles double-click event on the results tree."""
        item_id = self.results_tree.focus()
        if not item_id or item_id in ["members_prompt", "searching", "no_results"]:
            return

        member_data = self.members_data.get(int(item_id))
        if member_data:
            MemberInfoWindow(self, member_data)

    def _process_excel_queue(self):
        """Processes results from the Excel export worker thread."""
        try:
            result_type, data = self.excel_export_queue.get_nowait()
            if result_type == "excel_export_finished":
                filepath = data
                messagebox.showinfo("Success", f"Report exported successfully to:\n{filepath}")
            elif result_type == "excel_export_error":
                error_message = data
                messagebox.showerror("Export Error", f"An error occurred during export: {error_message}")
        except Empty:
            pass
        finally:
            self.after(100, self._process_excel_queue)

    def _process_search_queue(self):
        """Processes results from the background search worker threads."""
        try:
            result_type, data = self.search_queue.get_nowait()

            if result_type == "member_search_results":
                for item in self.results_tree.get_children(): self.results_tree.delete(item)
                self.members_data.clear()
                results = data
                if not results:
                    self.results_tree.insert("", "end", iid="no_results", values=("", "No members found for the selected criteria.", "", "", ""))
                    return
                for member_data in results:
                    db_id = member_data['id']
                    self.members_data[db_id] = member_data
                    self.results_tree.insert("", "end", iid=db_id, values=(member_data.get('full_name', 'N/A'), member_data.get('full_name_ar', 'N/A'), member_data.get('pkf_id', 'N/A'), member_data.get('club_name', 'N/A'), member_data.get('role', 'N/A')))

            elif result_type == "club_search_results":
                for item in self.club_results_tree.get_children(): self.club_results_tree.delete(item)
                self.clubs_data.clear()
                results = data
                if not results:
                    self.club_results_tree.insert("", "end", iid="no_results", values=("", "No clubs found for the selected criteria.", "", "", ""))
                    return
                for club_data in results:
                    club_id = club_data['id']
                    self.clubs_data[club_id] = club_data
                    self.club_results_tree.insert("", "end", iid=club_id, values=(club_data.get('club_membership_id', 'N/A'), club_data.get('name', 'N/A'), club_data.get('classification', 'N/A'), club_data.get('affiliation_date', 'N/A'), club_data.get('subscription_expiry_date', 'N/A')))

            elif result_type == "club_list_for_filter":
                clubs = data
                self.club_filter.configure(values=["All Clubs"] + clubs, state="normal")

            elif result_type == "attachment_entity_search_results":
                results = data
                for widget in self.attachment_search_results_frame.winfo_children():
                    widget.destroy()
                if not results:
                    ctk.CTkLabel(self.attachment_search_results_frame, text="No members or clubs found.").pack(pady=20)
                else:
                    for entity in results:
                        if entity['type'] == 'member':
                            label = f"Member: {entity['data']['full_name']}\n(ID: {entity['data']['pkf_id']})"
                        else: # club
                            label = f"Club: {entity['data']['name']}\n(ID: {entity['data'].get('club_membership_id', 'N/A')})"
                        
                        btn = ctk.CTkButton(self.attachment_search_results_frame, text=label, command=lambda e=entity: self._on_entity_selected(e), anchor="w")
                        btn.pack(fill="x", padx=5, pady=3)

            elif result_type == "search_error":
                error_message = data
                messagebox.showerror("Search Error", f"An error occurred during search: {error_message}")
                for item in self.results_tree.get_children(): self.results_tree.delete(item)
                for item in self.club_results_tree.get_children(): self.club_results_tree.delete(item)
        except Empty:
            pass
        finally:
            self.after(100, self._process_search_queue)

    def _export_to_excel(self):
        """Exports the currently displayed search results to an Excel file."""
        member_ids = self.results_tree.get_children()
        
        # Filter out non-numeric iids like 'searching' or 'no_results'
        valid_member_ids = []
        for mid in member_ids:
            try:
                valid_member_ids.append(int(mid))
            except ValueError:
                continue # Skip non-integer iids

        if not valid_member_ids:
            messagebox.showinfo("Info", "There are no results to export.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel file", "*.xlsx")],
            initialfile="pkf_report.xlsx"
        )
        if not filepath:
            return

        # Get the full data for the filtered members
        members_to_export = [self.members_data[mid] for mid in valid_member_ids if mid in self.members_data]

        messagebox.showinfo("Exporting", "The Excel report is being generated in the background. You will be notified upon completion.")

        # Run the heavy lifting in a separate thread
        thread = threading.Thread(target=self._export_to_excel_worker, args=(filepath, members_to_export))
        thread.daemon = True
        thread.start()

    def _export_to_excel_worker(self, filepath, members_to_export):
        """Worker function to handle the creation and saving of the Excel file."""
        try:
            # This block contains the time-consuming logic
            all_specific_keys = set()
            processed_data = []
            for member in members_to_export:
                member_copy = member.copy()
                try:
                    specific_data = json.loads(member_copy.get('specific_data', '{}'))
                    member_copy.update(specific_data)
                    all_specific_keys.update(specific_data.keys())
                except (json.JSONDecodeError, AttributeError):
                    pass
                if 'specific_data' in member_copy:
                    del member_copy['specific_data']
                processed_data.append(member_copy)

            main_headers = [key for key in members_to_export[0].keys() if key != 'specific_data']
            headers = main_headers + sorted(list(all_specific_keys))

            wb = Workbook()
            ws = wb.active
            ws.title = "Filtered Members Report"
            ws.append(headers)

            for member in processed_data:
                row = [member.get(h, "") for h in headers]
                ws.append(row)
            
            wb.save(filepath)
            self.excel_export_queue.put(("excel_export_finished", filepath))
        except Exception as e:
            self.excel_export_queue.put(("excel_export_error", str(e)))

    def _export_clubs_to_excel(self):
        """Exports the currently displayed club search results to an Excel file."""
        club_ids = self.club_results_tree.get_children()

        # Filter out non-numeric iids like 'searching' or 'no_results'
        valid_club_ids = []
        for cid in club_ids:
            try:
                valid_club_ids.append(int(cid))
            except ValueError:
                continue # Skip non-integer iids

        if not valid_club_ids:
            messagebox.showinfo("Info", "There are no club results to export.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel file", "*.xlsx")],
            initialfile="pkf_clubs_report.xlsx"
        )
        if not filepath:
            return

        # Get the full data for the filtered clubs
        clubs_to_export = [self.clubs_data[cid] for cid in valid_club_ids if cid in self.clubs_data]

        messagebox.showinfo("Exporting", "The Excel report for clubs is being generated in the background. You will be notified upon completion.")

        # Run the heavy lifting in a separate thread
        thread = threading.Thread(target=self._export_clubs_to_excel_worker, args=(filepath, clubs_to_export))
        thread.daemon = True
        thread.start()

    def _export_clubs_to_excel_worker(self, filepath, clubs_to_export):
        """Worker function to handle the creation and saving of the club Excel file."""
        try:
            if not clubs_to_export:
                raise ValueError("No club data to export.")

            preferred_order = [
                "club_membership_id", "name", "classification", "points",
                "representative_name", "representative_gender", "address", "phone", "email",
                "affiliation_date", "subscription_expiry_date",
                "club_subscription_fee", "admin_subscription_fee"
            ]
            
            all_keys = set(clubs_to_export[0].keys())
            headers = [h for h in preferred_order if h in all_keys]
            headers.extend(sorted([h for h in all_keys if h not in headers and h != 'attachments_data']))

            wb = Workbook()
            ws = wb.active
            ws.title = "Filtered Clubs Report"
            ws.append(headers)

            for club in clubs_to_export:
                row = [club.get(h, "") for h in headers]
                ws.append(row)
            
            wb.save(filepath)
            self.excel_export_queue.put(("excel_export_finished", filepath))
        except Exception as e:
            self.excel_export_queue.put(("excel_export_error", str(e)))

    def _clear_filters(self):
        self.search_entry.delete(0, 'end')
        self.role_filter.set("All Roles")
        self.club_filter.set("All Clubs")
        self.belt_filter.delete(0, 'end')
        self.profession_filter.delete(0, 'end')
        self.expiry_from.delete(0, 'end') # Use delete for DateEntry
        self.expiry_to.delete(0, 'end')   # Use delete for DateEntry
        self.dob_from.delete(0, 'end')    # Use delete for DateEntry
        self.dob_to.delete(0, 'end')      # Use delete for DateEntry
        self.kata_filter.deselect()
        self.kumite_filter.deselect()
        self.coach_nat_rank.delete(0, 'end')
        self._perform_search() # Perform search with cleared filters
    
    def _perform_search_worker(self, filters):
        """Worker thread for member search."""
        try:
            results = search_members_advanced(**filters)
            self.search_queue.put(("member_search_results", results))
        except Exception as e:
            self.search_queue.put(("search_error", str(e)))

    def update_club_filter(self):
        """Asynchronously updates the club filter dropdown."""
        def worker():
            try:
                clubs = get_unique_clubs()
                self.search_queue.put(("club_list_for_filter", clubs))
            except Exception as e:
                print(f"Error fetching clubs for filter: {e}")
        
        self.club_filter.configure(values=["Loading..."], state="disabled")
        threading.Thread(target=worker, daemon=True).start()

    def _perform_club_search_worker(self, filters):
        """Worker thread for club search."""
        try:
            results = search_clubs_advanced(**filters)
            self.search_queue.put(("club_search_results", results))
        except Exception as e:
            self.search_queue.put(("search_error", str(e)))

    def _perform_club_search(self, event=None):
        """Gathers filter criteria and populates the club results tree asynchronously."""
        filters = { "membership_id": self.club_id_filter.get(), "name": self.club_id_filter.get(), "classification": self.club_class_filter.get(), "affiliation_from": self.club_aff_from.get(), "affiliation_to": self.club_aff_to.get(), "subscription_expired": self.club_expired_filter.get() == 1, "min_points": self.club_points_filter.get() }
        if filters["min_points"]:
            try:
                filters["min_points"] = int(filters["min_points"])
            except ValueError:
                messagebox.showwarning("Invalid Input", "Points filter must be a number.")
                return
        for item in self.club_results_tree.get_children(): self.club_results_tree.delete(item)
        self.club_results_tree.insert("", "end", iid="searching", values=("", "Searching, please wait...", "", "", ""))
        self.update_idletasks()
        thread = threading.Thread(target=self._perform_club_search_worker, args=(filters,), daemon=True)
        thread.start()

    def _clear_club_filters(self):
        """Clears all filter fields for the club report and refreshes the search."""
        self.club_id_filter.delete(0, 'end')
        self.club_class_filter.set("All Classifications")
        self.club_aff_from.delete(0, 'end') # Use delete for DateEntry
        self.club_aff_to.delete(0, 'end')   # Use delete for DateEntry
        self.club_expired_filter.deselect()
        self.club_points_filter.delete(0, 'end')
        self._perform_club_search()

    def _on_club_double_click(self, event):
        """Handles double-click on the club results tree to open an edit window."""
        item_id = self.club_results_tree.focus() # Get selected item's IID
        if not item_id or item_id in ["clubs_prompt", "searching", "no_results"]:
            return

        club_data = self.clubs_data.get(int(item_id)) # IID from treeview is a string, key is int
        if club_data:
            ClubInfoWindow(self, club_data)