import customtkinter as ctk
from tkinter import messagebox, filedialog
import manager
import importer

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

NAVY   = "#1a1a2e" #Navy
DANGER = "#e63946" #Red
ODD    = "#f8f9fa" #Light
EVEN   = "#ffffff" #White

FONT_TITLE  = ("Segoe UI", 22, "bold") #Popup form title, app title in the header bar
FONT_HEADER = ("Segoe UI", 11, "bold") #Column header row and popup field labels
FONT_BODY   = ("Segoe UI", 11)         #Table row data, toolbar buttons, search bar, dropdowns
FONT_BOLD   = ("Segoe UI", 12, "bold") #Student ID and Name 
FONT_SMALL  = ("Segoe UI", 10, "bold") #Edit and Delete buttons


class PopupForm(ctk.CTkToplevel): #Popup window used for add/edit forms
    def __init__(self, parent, title, fields, on_submit, initial=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False) #Prevent resizing
        self.grab_set() #Lock to this popup until its closed or saved
        self.on_submit = on_submit #Callback function when user clicks Save
        self.input_widgets = {} #Store input widget for when form is submitted

        ctk.CTkLabel(self, text=title, font=FONT_TITLE).pack(pady=(20, 10), padx=30) #Title
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(padx=30, pady=5, fill="x")

        for field_label, field_key, widget_type, dropdown_options in fields: #Go through each field then build the right widget
            ctk.CTkLabel(form_frame, text=field_label, font=FONT_HEADER, anchor="w").pack(fill="x", pady=(8, 2))
            if widget_type == "entry":
                text_entry = ctk.CTkEntry(form_frame, font=FONT_BODY, height=36)
                if initial and field_key in initial: #Pre-fill if editing
                    text_entry.insert(0, initial[field_key])
                text_entry.pack(fill="x")
                self.input_widgets[field_key] = text_entry #Store entry widget to read value later
            elif widget_type == "dropdown":
                default_value = initial[field_key] if initial and field_key in initial else dropdown_options[0] #Use existing value if editing
                selected_value = ctk.StringVar(value=default_value)
                ctk.CTkOptionMenu(form_frame, values=dropdown_options, variable=selected_value,
                                  font=FONT_BODY, height=36,
                                  fg_color=NAVY, button_color=NAVY, button_hover_color="#2d2d4e").pack(fill="x")
                self.input_widgets[field_key] = selected_value #Save the StringVar not the dropdown

        button_row = ctk.CTkFrame(self, fg_color="transparent") #Buttons Save/Cancel
        button_row.pack(pady=20, padx=30, fill="x")
        ctk.CTkButton(button_row, text="Cancel", fg_color="#dee2e6", text_color="#212529",
                      hover_color="#ced4da", font=FONT_BODY,
                      command=self.destroy).pack(side="left", expand=True, padx=(0, 5))
        ctk.CTkButton(button_row, text="Save", fg_color=NAVY, font=FONT_BODY,
                      command=self._submit).pack(side="left", expand=True, padx=(5, 0))

    def _submit(self): #Read all values from the form and pass them to on_submit
        form_values = {}
        for field_key, input_widget in self.input_widgets.items(): #StringVar for dropdowns, Entry for text fields
            form_values[field_key] = input_widget.get() if isinstance(input_widget, ctk.StringVar) else input_widget.get().strip() 
        self.on_submit(form_values) #Call the callback function with all form values


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SSIS — Student Information System")
        self.geometry("1150x720")
        self.minsize(900, 600)
        self.student_sort_reverse = False #Track sort direction per tab 
        self.program_sort_reverse = False #False means ascending
        self.college_sort_reverse = False #True means descending

        #Load everything into memory once at startup
        #Search, sort, and refresh all read from these instead of the CSV every time
        self.all_students = manager.read_csv(manager.STUDENT)
        self.all_programs = manager.read_csv(manager.PROGRAM)
        self.all_colleges = manager.read_csv(manager.COLLEGE)

        #Students dont store college directly so look it up through dictionary that maps program_code -> college_codes
        self.program_to_college = {}
        for p in self.all_programs:
            self.program_to_college[p["code"]] = p["college_code"]

        self._build_header()
        self._build_tabs()
        self._update_counters()

    def _reload_data(self): #read the csv and update our in-memory variables after add/delete/edit
        self.all_students = manager.read_csv(manager.STUDENT)
        self.all_programs = manager.read_csv(manager.PROGRAM)
        self.all_colleges = manager.read_csv(manager.COLLEGE)
        self.program_to_college = {} #Rebuild the lookup too
        for p in self.all_programs:
            self.program_to_college[p["code"]] = p["college_code"]

    def _build_header(self):
        header_bar = ctk.CTkFrame(self, fg_color=NAVY, corner_radius=0, height=70) #Header
        header_bar.pack(fill="x")
        header_bar.pack_propagate(False) #Prevent frame from shrinking to fit contents
        ctk.CTkLabel(header_bar, text="SSIS — Student Information System", #App title
                     font=FONT_TITLE, text_color="white").pack(side="left", padx=24)

        counter_frame = ctk.CTkFrame(header_bar, fg_color="transparent") #For student, program, and college counts
        counter_frame.pack(side="right", padx=24)
        self.student_count_label = self._counter(counter_frame, "Students", "#4cc9f0") #Cyan for students
        self.program_count_label = self._counter(counter_frame, "Programs", "#4ade80") #Green for programs
        self.college_count_label = self._counter(counter_frame, "Colleges", "#f9c74f") #Yellow for colleges

    def _counter(self, parent, label, color): #Build counter block
        counter_block = ctk.CTkFrame(parent, fg_color="transparent") #Counter block
        counter_block.pack(side="left", padx=12)
        count_label = ctk.CTkLabel(counter_block, text="0", font=("Segoe UI", 22, "bold"), text_color=color) #Number counter
        count_label.pack()
        ctk.CTkLabel(counter_block, text=label, font=FONT_SMALL, text_color="#adb5bd").pack() #Counter label students/programs/colleges
        return count_label #Return label to update the number

    def _update_counters(self): #Count records in csv and update the header numbers
        self.student_count_label.configure(text=str(len(self.all_students))) #Update student count
        self.program_count_label.configure(text=str(len(self.all_programs))) #Update program count
        self.college_count_label.configure(text=str(len(self.all_colleges))) #Update college count

    def _build_tabs(self):
        tab_view = ctk.CTkTabview(self, anchor="nw",
                                  segmented_button_selected_color=NAVY, #Navy for selected tab
                                  segmented_button_selected_hover_color="#2d2d4e", #Darker navy if hovering selected tab
                                  segmented_button_unselected_hover_color="#ced4da") #Light gray if hovering unselected tab
        tab_view.pack(fill="both", expand=True, padx=16, pady=16)
        tab_view.add("Students") #Add the student/program/college tabs
        tab_view.add("Programs")
        tab_view.add("Colleges")
        self._build_student_tab(tab_view.tab("Students")) #Build the student/program/college tabs' contents
        self._build_program_tab(tab_view.tab("Programs"))
        self._build_college_tab(tab_view.tab("Colleges")) 

    def _table_header(self, parent, columns): #Build the column header row
        header_row = ctk.CTkFrame(parent, fg_color=NAVY, corner_radius=6, height=36)
        header_row.pack(fill="x", pady=(0, 2))
        header_row.pack_propagate(False) #Keep fixed height
        for column_label, column_width in columns:
            ctk.CTkLabel(header_row, text=column_label, font=FONT_HEADER, text_color="white", #Column header label
                         width=column_width, anchor="w").pack(side="left", padx=8) #Each column header with specified width

    def _make_cmd(self, func, row_data): #Wrapper so each button gets its own copy of row data
        def command():
            func(row_data) #Call the function with this specific row's data
        return command #Return the command function so button can use it

    def _show_import_summary(self, total_added, skipped_reasons): #Show popup with results of the import
        summary_message = f"{total_added} record(s) added successfully.\n"

        if len(skipped_reasons) == 0: #No skipped records
            summary_message = summary_message + "No records were skipped."
        else: #List each skipped row and why it was skipped
            summary_message = summary_message + f"\n{len(skipped_reasons)} record(s) skipped:\n"
            for skip_reason in skipped_reasons:
                summary_message = summary_message + f"  - {skip_reason}\n" #Add each skipped row and reason

        messagebox.showinfo("Import Summary", summary_message) #Display summary in a popup

    def _import_students(self):
        messagebox.showinfo("Import Format — Students", #Show format reminder before opening file dialog
            "Your CSV file must have these columns in this order:\n\n"  #Dialogue box start
            "  id, firstname, lastname, program_code, year, gender\n\n"
            "Example row:\n"
            "  2023-0001, Juan, Dela Cruz, BSCS, 1, Male\n\n"
            "Notes:\n"
            "  - ID must follow YYYY-NNNN format\n"
            "  - program_code must already exist in the system\n"
            "  - Import colleges and programs first before students"  #Dialogue box end
        )
        csv_file_path = filedialog.askopenfilename(title="Select Student CSV", filetypes=[("CSV Files", "*.csv")])
        if not csv_file_path: #User cancelled
            return #end
        try:
            total_added, skipped_reasons = importer.import_students(csv_file_path) #Import students
            self._reload_data()
            self._refresh_students() #Update the student table display
            self._update_counters() #Update the counters
            self._show_import_summary(total_added, skipped_reasons) #Display results
        except Exception as error:
            messagebox.showerror("Import Failed", f"Something went wrong:\n{error}") #Show error if import fails

    def _import_programs(self):
        messagebox.showinfo("Import Format — Programs", #Show format reminder before opening file dialog
            "Your CSV file must have these columns in this order:\n\n" #Dialogue box start
            "  code, name, college_code\n\n"
            "Example row:\n"
            "  BSCS, Bachelor of Science in Computer Science, CCS\n\n"
            "Notes:\n"
            "  - college_code must already exist in the system\n"
            "  - Import colleges first before programs"                 #Dialogue box end
        )
        csv_file_path = filedialog.askopenfilename(title="Select Program CSV", filetypes=[("CSV Files", "*.csv")])
        if not csv_file_path: #User cancelled
            return #end
        try:
            total_added, skipped_reasons = importer.import_programs(csv_file_path) #Import programs from csv
            self._reload_data()
            self._refresh_programs() #Update the program table display
            self._update_counters() #Update the counters
            self._show_import_summary(total_added, skipped_reasons) #Display results
        except Exception as error:
            messagebox.showerror("Import Failed", f"Something went wrong:\n{error}") #Show error if import fails

    def _import_colleges(self):
        messagebox.showinfo("Import Format — Colleges",                 #Dialogue box start
            "Your CSV file must have these columns in this order:\n\n"
            "  code, name\n\n"
            "Example row:\n"
            "  CCS, College of Computer Studies"                        #Dialogue box end
        )
        csv_file_path = filedialog.askopenfilename(title="Select College CSV", filetypes=[("CSV Files", "*.csv")])
        if not csv_file_path: #User cancelled
            return #exit
        try:
            total_added, skipped_reasons = importer.import_colleges(csv_file_path) #Import colleges from csv
            self._reload_data()
            self._refresh_colleges() #Update the college table display
            self._update_counters() #Update the counters
            self._show_import_summary(total_added, skipped_reasons) #Display results
        except Exception as error:
            messagebox.showerror("Import Failed", f"Something went wrong:\n{error}") #Show error if import fails

    # ── Students ──────────────────────────────────────────────
    def _build_student_tab(self, parent):
        self.student_search_var = ctk.StringVar()
        self.student_sort_var   = ctk.StringVar(value="ID")

        student_toolbar = ctk.CTkFrame(parent, fg_color="transparent") #Build search/sort bar and order toggle
        student_toolbar.pack(fill="x", pady=(0, 10))

        search_entry = ctk.CTkEntry(student_toolbar, textvariable=self.student_search_var,
                                    placeholder_text="Search...", font=FONT_BODY, height=36, width=260) #Searchbar
        search_entry.pack(side="left", padx=(0, 8))
        search_entry.bind("<KeyRelease>", lambda event: self._refresh_students()) #Refresh on every keypress

        ctk.CTkOptionMenu(student_toolbar, values=["ID", "Name", "Program", "College", "Year", "Gender"], #Sort bar
                          variable=self.student_sort_var, font=FONT_BODY, height=36, width=150,
                          fg_color=NAVY, button_color=NAVY, button_hover_color="#2d2d4e", #Change color when hovering
                          command=lambda selected: self._refresh_students()).pack(side="left", padx=(0, 8)) #Dropdown to choose sort column

        self.student_order_button = ctk.CTkButton(student_toolbar, text="⤊ Asc", width=80, height=36,#Order toggle
                                                  fg_color=NAVY, font=FONT_BODY,
                                                  command=self._toggle_student_order)
        self.student_order_button.pack(side="left", padx=(0, 8))

        ctk.CTkButton(student_toolbar, text="+ Add Student", height=36, fg_color=NAVY, #Add new student button
                      font=FONT_BODY, command=self._add_student).pack(side="right", padx=(4, 0))
        ctk.CTkButton(student_toolbar, text="⬆ Import", height=36, fg_color=NAVY,
                      font=FONT_BODY, command=self._import_students).pack(side="right") #Import students button

        self._table_header(parent, [
            ("ID", 120), ("Name", 190), ("Program", 100),
            ("College", 90), ("Year", 50), ("Gender", 90), ("Actions", 160)
        ])

        self.student_list_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent") #Scrolling bar
        self.student_list_frame.pack(fill="both", expand=True)
        self._refresh_students() #Load and display all students

    def _toggle_student_order(self): #Order toggle
        self.student_sort_reverse = not self.student_sort_reverse #Toggle ascending/descending
        self.student_order_button.configure(text="⤋ Desc" if self.student_sort_reverse else "⤊ Asc") #Update button text
        self._refresh_students() #Refresh table with new sort order

    def _refresh_students(self):
        for existing_row in self.student_list_frame.winfo_children(): #Clear existing rows
            existing_row.destroy()

        sort_column_map = {
            "ID":      "id",
            "Name":    "name",
            "Program": "program_code",
            "Year":    "year",
            "Gender":  "gender",
            "College": "program_code"
        }
        sort_column   = sort_column_map[self.student_sort_var.get()] #Get actual column name from display name
        student_list  = manager.search_records(self.all_students, self.student_search_var.get()) #filter list based on search

        if self.student_sort_var.get() == "College": #College needs a lookup since students only store program_code
            student_list = sorted(student_list,
                                  key=lambda student: self.program_to_college.get(student["program_code"], "").lower(), #Sort by college code via program lookup
                                  reverse=self.student_sort_reverse)
        else:
            student_list = manager.sort_records(student_list, sort_column, self.student_sort_reverse) #Use sorting in manager file

        for row_index, student in enumerate(student_list):
            row_color = ODD if row_index % 2 == 0 else EVEN #Alternate row colors
            table_row = ctk.CTkFrame(self.student_list_frame, fg_color=row_color, corner_radius=4, height=40)
            table_row.pack(fill="x", pady=1)
            table_row.pack_propagate(False)

            display_name = student["lastname"] + ", " + student["firstname"] #Format name as Lastname, Firstname
            college_code = self.program_to_college.get(student["program_code"], "N/A") #Look up the college through the program
            ctk.CTkLabel(table_row, text=student["id"],           font=FONT_BOLD, width=120, anchor="w").pack(side="left", padx=8) #Student ID
            ctk.CTkLabel(table_row, text=display_name,            font=FONT_BOLD, width=190, anchor="w").pack(side="left", padx=8) #Student name
            ctk.CTkLabel(table_row, text=student["program_code"], font=FONT_BODY, width=100, anchor="w").pack(side="left", padx=8) #Program code
            ctk.CTkLabel(table_row, text=college_code,            font=FONT_BODY, width=90,  anchor="w").pack(side="left", padx=8) #College code
            ctk.CTkLabel(table_row, text=student["year"],         font=FONT_BODY, width=50,  anchor="w").pack(side="left", padx=8) #Year level
            ctk.CTkLabel(table_row, text=student["gender"],       font=FONT_BODY, width=90,  anchor="w").pack(side="left", padx=8) #Gender

            action_button_frame = ctk.CTkFrame(table_row, fg_color="transparent")
            action_button_frame.pack(side="left", padx=4)
            ctk.CTkButton(action_button_frame, text="Edit",   width=64, height=28, fg_color=NAVY,   font=FONT_SMALL,
                          command=self._make_cmd(self._edit_student, student)).pack(side="left", padx=2) #Student edit button
            ctk.CTkButton(action_button_frame, text="Delete", width=64, height=28, fg_color=DANGER, font=FONT_SMALL,
                          command=self._make_cmd(self._delete_student, student)).pack(side="left", padx=2) #Student delete button

    def _student_fields(self, initial=None):
        available_programs = [program["code"] for program in self.all_programs] or ["(No programs yet)"] #Get list of all program codes
        year_options       = [str(year_number) for year_number in range(1, 11)] #Max year is 10
        return [
            ("Student ID  (YYYY-NNNN)", "id",           "entry",    []), #Text entry for ID/FirstName/LastName
            ("First Name",              "firstname",     "entry",    []),
            ("Last Name",               "lastname",      "entry",    []),
            ("Program",                 "program_code",  "dropdown", available_programs), #Dropdown for program/year/gender
            ("Year Level",              "year",          "dropdown", year_options),
            ("Gender",                  "gender",        "dropdown", ["Male", "Female", "Other"]),
        ]

    def _add_student(self):
        def save(form_values):
            if not manager.format_check(form_values["id"]): #Check YYYY-NNNN format
                messagebox.showerror("Invalid ID", "ID must follow YYYY-NNNN format."); return
            if manager.pk_check(self.all_students, "id", form_values["id"]): #Check for duplicate ID
                messagebox.showerror("Duplicate", "This ID already exsists."); return
            manager.add_record(manager.STUDENT, form_values, manager.STUDENT_FIELDS) #Record new student
            self._reload_data()
            add_student_popup.destroy(); self._refresh_students(); self._update_counters() #Close popup, refresh table and counters
        add_student_popup = PopupForm(self, "Add Student", self._student_fields(), save) #Create and show the popup form

    def _edit_student(self, student):
        def save(form_values):
            if not manager.format_check(form_values["id"]): #Check YYYY-NNNN format
                messagebox.showerror("Invalid ID", "ID must follow YYYY-NNNN format."); return
            id_was_changed = form_values["id"].lower() != student["id"].lower() #Check if user changed ID
            if id_was_changed and manager.pk_check(self.all_students, "id", form_values["id"]): #Only check duplicate if ID changed
                messagebox.showerror("Duplicate", "This ID already exists."); return
            manager.update_record(manager.STUDENT, "id", student["id"], form_values, manager.STUDENT_FIELDS) #Update student record
            self._reload_data()
            edit_student_popup.destroy(); self._refresh_students() #Close popup and refresh table
        edit_student_popup = PopupForm(self, "Edit Student", self._student_fields(student), save, initial=student) #Create popup with student data

    def _delete_student(self, student):
        full_name = student["firstname"] + " " + student["lastname"] #Format for confirmation message
        if messagebox.askyesno("Delete", f"Delete {full_name}?"): #Ask user to confirm deletion
            manager.delete_record(manager.STUDENT, "id", student["id"], manager.STUDENT_FIELDS) #Delete student record
            self._reload_data()
            self._refresh_students(); self._update_counters() #Refresh table and update counters

    # ── Programs ──────────────────────────────────────────────
    def _build_program_tab(self, parent):
        program_toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        program_toolbar.pack(fill="x", pady=(0, 10))

        self.program_order_button = ctk.CTkButton(program_toolbar, text="⤊ Asc", width=80, height=36,
                                                  fg_color=NAVY, font=FONT_BODY,
                                                  command=self._toggle_program_order) #Order toggle
        self.program_order_button.pack(side="left", padx=(0, 8))

        ctk.CTkButton(program_toolbar, text="+ Add Program", height=36, fg_color=NAVY,
                      font=FONT_BODY, command=self._add_program).pack(side="right", padx=(4, 0)) #Add program button
        ctk.CTkButton(program_toolbar, text="⬆ Import", height=36, fg_color=NAVY,
                      font=FONT_BODY, command=self._import_programs).pack(side="right") #Import program button

        self._table_header(parent, [("Code", 120), ("Name", 360), ("College", 120), ("Actions", 160)])

        self.program_list_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent") #Scrolling bar for program rows
        self.program_list_frame.pack(fill="both", expand=True)
        self._refresh_programs() #Load and display all programs

    def _toggle_program_order(self):
        self.program_sort_reverse = not self.program_sort_reverse #Order toggle
        self.program_order_button.configure(text="⤋ Desc" if self.program_sort_reverse else "⤊ Asc") #Update button text
        self._refresh_programs() #Refresh table with new sort order

    def _refresh_programs(self):
        for existing_row in self.program_list_frame.winfo_children(): #Clear existing rows
            existing_row.destroy()
        program_list = manager.sort_records(self.all_programs, "code", self.program_sort_reverse) #Always sort by code
        for row_index, program in enumerate(program_list):
            row_color = ODD if row_index % 2 == 0 else EVEN #Alternate row colors
            table_row = ctk.CTkFrame(self.program_list_frame, fg_color=row_color, corner_radius=4, height=40)
            table_row.pack(fill="x", pady=1)
            table_row.pack_propagate(False) #Keep fixed height
            ctk.CTkLabel(table_row, text=program["code"],         font=FONT_BODY, width=120, anchor="w").pack(side="left", padx=8) #Program code
            ctk.CTkLabel(table_row, text=program["name"],         font=FONT_BODY, width=360, anchor="w").pack(side="left", padx=8) #Program name
            ctk.CTkLabel(table_row, text=program["college_code"], font=FONT_BODY, width=120, anchor="w").pack(side="left", padx=8) #College code
            action_button_frame = ctk.CTkFrame(table_row, fg_color="transparent")
            action_button_frame.pack(side="left", padx=4)
            ctk.CTkButton(action_button_frame, text="Edit",   width=64, height=28, fg_color=NAVY,   font=FONT_SMALL,
                          command=self._make_cmd(self._edit_program, program)).pack(side="left", padx=2) #Edit program button
            ctk.CTkButton(action_button_frame, text="Delete", width=64, height=28, fg_color=DANGER, font=FONT_SMALL,
                          command=self._make_cmd(self._delete_program, program)).pack(side="left", padx=2) #Delete program button

    def _program_fields(self, initial=None):
        available_colleges = [college["code"] for college in self.all_colleges] or ["(No colleges yet)"] #Get list of all college codes
        return [
            ("Program Code  (e.g. BSCS)", "code",         "entry",    []), #Text entry for program code/name
            ("Program Name",               "name",         "entry",    []),
            ("College",                    "college_code", "dropdown", available_colleges), #Dropdown for college code
        ]

    def _add_program(self):
        def save(form_values):
            if not form_values["code"] or not form_values["name"]: #Check if required fields are empty
                messagebox.showerror("Missing Fields", "Code and Name are required."); return
            if manager.pk_check(self.all_programs, "code", form_values["code"]): #Check for duplicate program code
                messagebox.showerror("Duplicate", "This program code already exists."); return
            manager.add_record(manager.PROGRAM, form_values, manager.PROGRAM_FIELDS) #Add the new program record
            self._reload_data()
            add_program_popup.destroy(); self._refresh_programs(); self._update_counters() #Close popup, refresh table and counters
        add_program_popup = PopupForm(self, "Add Program", self._program_fields(), save) #Create and show the popup form

    def _edit_program(self, program):
        def save(form_values):
            if not form_values["code"] or not form_values["name"]: #Check if required fields are empty
                messagebox.showerror("Missing Fields", "Code and Name are required."); return
            code_was_changed = form_values["code"].lower() != program["code"].lower() #Check if user changed the code
            if code_was_changed and manager.pk_check(self.all_programs, "code", form_values["code"]): #Only check duplicate if code changed
                messagebox.showerror("Duplicate", "This program code already exists."); return
            manager.update_program(program["code"], form_values) #Update the program record
            self._reload_data()
            edit_program_popup.destroy(); self._refresh_programs(); self._refresh_students() #Refresh students too since they link to programs
        edit_program_popup = PopupForm(self, "Edit Program", self._program_fields(program), save, initial=program) #Create popup with existing program data

    def _delete_program(self, program):
        if messagebox.askyesno("Delete", f"Delete '{program['code']}'?\nAll enrolled students will also be deleted."): #Ask user to confirm deletion
            manager.delete_program(program["code"]) #Delete the program
            self._reload_data()
            self._refresh_programs(); self._refresh_students(); self._update_counters() #Refresh both tables and update counters

    # ── Colleges ──────────────────────────────────────────────
    def _build_college_tab(self, parent):
        college_toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        college_toolbar.pack(fill="x", pady=(0, 10))

        self.college_order_button = ctk.CTkButton(college_toolbar, text="⤊ Asc", width=80, height=36,
                                                  fg_color=NAVY, font=FONT_BODY,
                                                  command=self._toggle_college_order) #Order toggle
        self.college_order_button.pack(side="left", padx=(0, 8))

        ctk.CTkButton(college_toolbar, text="+ Add College", height=36, fg_color=NAVY,
                      font=FONT_BODY, command=self._add_college).pack(side="right", padx=(4, 0)) #Add college button
        ctk.CTkButton(college_toolbar, text="⬆ Import", height=36, fg_color=NAVY,
                      font=FONT_BODY, command=self._import_colleges).pack(side="right") #import college button

        self._table_header(parent, [("Code", 120), ("Name", 480), ("Actions", 160)])

        self.college_list_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent") #Scrolling bar
        self.college_list_frame.pack(fill="both", expand=True)
        self._refresh_colleges() #Display colleges

    def _toggle_college_order(self):
        self.college_sort_reverse = not self.college_sort_reverse #Order toggle
        self.college_order_button.configure(text="⤋ Desc" if self.college_sort_reverse else "⤊ Asc") #Update button text
        self._refresh_colleges() #Refresh table with new sort order

    def _refresh_colleges(self):
        for existing_row in self.college_list_frame.winfo_children(): #Clear existing rows
            existing_row.destroy()
        college_list = manager.sort_records(self.all_colleges, "code", self.college_sort_reverse) #Sort by code
        for row_index, college in enumerate(college_list):
            row_color = ODD if row_index % 2 == 0 else EVEN #Alternate row colors for readability
            table_row = ctk.CTkFrame(self.college_list_frame, fg_color=row_color, corner_radius=4, height=40)
            table_row.pack(fill="x", pady=1)
            table_row.pack_propagate(False) #Keep fixed height
            ctk.CTkLabel(table_row, text=college["code"], font=FONT_BODY, width=120, anchor="w").pack(side="left", padx=8) #College code
            ctk.CTkLabel(table_row, text=college["name"], font=FONT_BODY, width=480, anchor="w").pack(side="left", padx=8) #College name
            action_button_frame = ctk.CTkFrame(table_row, fg_color="transparent")
            action_button_frame.pack(side="left", padx=4)
            ctk.CTkButton(action_button_frame, text="Edit",   width=64, height=28, fg_color=NAVY,   font=FONT_SMALL,
                          command=self._make_cmd(self._edit_college, college)).pack(side="left", padx=2) #Edit college button
            ctk.CTkButton(action_button_frame, text="Delete", width=64, height=28, fg_color=DANGER, font=FONT_SMALL,
                          command=self._make_cmd(self._delete_college, college)).pack(side="left", padx=2) #Delete college button

    def _college_fields(self):
        return [
            ("College Code  (e.g. CCS)", "code", "entry", []), #Text entry for college code/name
            ("College Name",              "name", "entry", []),
        ]

    def _add_college(self):
        def save(form_values):
            if not form_values["code"] or not form_values["name"]: #Check if required fields are empty
                messagebox.showerror("Missing Fields", "Code and Name are required."); return
            if manager.pk_check(self.all_colleges, "code", form_values["code"]): #Check for duplicate college code
                messagebox.showerror("Duplicate", "This college code already exists."); return
            manager.add_record(manager.COLLEGE, form_values, manager.COLLEGE_FIELDS) #Add the new college record
            self._reload_data()
            add_college_popup.destroy(); self._refresh_colleges(); self._update_counters() #Close popup, refresh table and counters
        add_college_popup = PopupForm(self, "Add College", self._college_fields(), save) #Create and show the popup form

    def _edit_college(self, college):
        def save(form_values):
            if not form_values["code"] or not form_values["name"]: #Check if required fields are empty
                messagebox.showerror("Missing Fields", "Code and Name are required."); return
            code_was_changed = form_values["code"].lower() != college["code"].lower() #Check if user changed the code
            if code_was_changed and manager.pk_check(self.all_colleges, "code", form_values["code"]): #Only check duplicate if code changed
                messagebox.showerror("Duplicate", "This college code already exists."); return
            manager.update_college(college["code"], form_values) #Update the college record
            self._reload_data()
            edit_college_popup.destroy(); self._refresh_colleges(); self._refresh_programs(); self._update_counters() #Refresh programs too since they link to colleges
        edit_college_popup = PopupForm(self, "Edit College", self._college_fields(), save, initial=college) #Create popup existing college data

    def _delete_college(self, college):
        if messagebox.askyesno("Delete", f"Delete '{college['code']}'?\nAll programs and students under it will also be deleted."): #Confirmation
            manager.delete_college(college["code"]) #Delete the college
            self._reload_data()
            self._refresh_colleges(); self._refresh_programs(); self._refresh_students(); self._update_counters() #Refresh all tables and update counters