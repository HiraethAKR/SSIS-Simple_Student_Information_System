import customtkinter as ctk
from tkinter import messagebox, filedialog, ttk
import manager
import importer

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

NAVY   = "#1a1a2e" #Navy
DANGER = "#e63946" #Red

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
        self.program_search_var = ctk.StringVar() #Search var for programs
        self.program_sort_var   = ctk.StringVar(value="Code") #Sort var for programs
        self.college_search_var = ctk.StringVar() #Search var for colleges
        self.college_sort_var   = ctk.StringVar(value="Code") #Sort var for colleges

        self.student_page = 1 #Page number per tab for students
        self.program_page = 1 #for programs
        self.college_page = 1 #for colleges
        self.page_size = 50 #number of records per page
        self._student_search_after_id = None #track the delayed refresh call
        self._program_search_after_id = None
        self._college_search_after_id = None

        #Load everything into memory once at startup
        self.all_students = manager.fetch_all(manager.STUDENT)
        self.all_programs = manager.fetch_all(manager.PROGRAM)
        self.all_colleges = manager.fetch_all(manager.COLLEGE)

        #Students dont store college directly so look it up through dictionary that maps program_code -> college_codes
        self.program_to_college = {}
        for p in self.all_programs:
            self.program_to_college[p["code"]] = p["college_code"]

        self._build_header()
        self._build_tabs()
        self._update_counters()

    def _reload_data(self): #read the database and update our in-memory variables after add/delete/edit
        self.all_students = manager.fetch_all(manager.STUDENT) #Reload students
        self.all_programs = manager.fetch_all(manager.PROGRAM) #Reload programs
        self.all_colleges = manager.fetch_all(manager.COLLEGE) #Reload colleges
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

    def _update_counters(self): #Count records and update the header numbers
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

    def _style_treeview(self, tree_name): #Apply consistent styling to a treeview
        style = ttk.Style()
        style.theme_use("clam") #Use clam theme as base so we can override colors
        style.configure(f"{tree_name}.Treeview",
                        font=FONT_BODY, rowheight=36,
                        background="#ffffff", fieldbackground="#ffffff",
                        borderwidth=0) #Row styling
        style.configure(f"{tree_name}.Treeview.Heading",
                        font=FONT_HEADER, background=NAVY,
                        foreground="white", relief="flat") #Header styling
        style.map(f"{tree_name}.Treeview",
                  background=[("selected", "#2d2d4e")], #Selected row color
                  foreground=[("selected", "white")])    #Selected row text color

    def _make_cmd(self, func, row_data): #Wrapper so each button gets its own copy of row data
        def command():
            func(row_data) #Call the function with this specific row's data
        return command #Return the command function so button can use it

    def _on_student_search(self): #Delay student table refresh until user stops typing
        if self._student_search_after_id is not None: #If there's already a pending refresh
            self.after_cancel(self._student_search_after_id) #Cancel it so we dont refresh mid-typing
        self._student_search_after_id = self.after(300, lambda: self._refresh_students(reset_page=True)) #Wait 300ms then refresh

    def _on_program_search(self): #Delay program table refresh until user stops typing
        if self._program_search_after_id is not None: #If there's already a pending refresh
            self.after_cancel(self._program_search_after_id) #Cancel it so we dont refresh mid-typing
        self._program_search_after_id = self.after(300, lambda: self._refresh_programs(reset_page=True)) #Wait 300ms then refresh

    def _on_college_search(self): #Delay college table refresh until user stops typing
        if self._college_search_after_id is not None: #If there's already a pending refresh
            self.after_cancel(self._college_search_after_id) #Cancel it so we dont refresh mid-typing
        self._college_search_after_id = self.after(300, lambda: self._refresh_colleges(reset_page=True)) #Wait 300ms then refresh

    def _build_page_controls(self, parent, prev_cmd, next_cmd, jump_cmd): #Reusable page bar for all 3 tabs
        page_bar = ctk.CTkFrame(parent, fg_color="transparent") #Page bar frame
        page_bar.pack(fill="x", pady=(6, 0)) #Pack the page bar frame
        ctk.CTkButton(page_bar, text="← Prev", width=80, height=30, fg_color=NAVY, #Previous button
                      font=FONT_BODY, command=prev_cmd).pack(side="left", padx=(0, 6))
        page_label = ctk.CTkLabel(page_bar, text="Page 1 of 1", font=FONT_BODY) #Page number label
        page_label.pack(side="left", padx=6) #Pack the page number label
        ctk.CTkButton(page_bar, text="Next →", width=80, height=30, fg_color=NAVY, #Next button
                      font=FONT_BODY, command=next_cmd).pack(side="left", padx=(6, 0)) #Pack the next button
        ctk.CTkLabel(page_bar, text="Go to:", font=FONT_BODY).pack(side="left", padx=(16, 4)) #Go to page label
        page_entry = ctk.CTkEntry(page_bar, width=50, height=30, font=FONT_BODY) #Page number input
        page_entry.pack(side="left", padx=(0, 4))
        ctk.CTkButton(page_bar, text="Go", width=40, height=30, fg_color=NAVY, #Go button
                      font=FONT_BODY, command=lambda: jump_cmd(page_entry.get())).pack(side="left")
        return page_label #Return so each tab can store it and update the page number

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
            "Your CSV file must have these columns in this order:\n\n"
            "  id, firstname, lastname, program_code, year, gender\n\n"
            "Example row:\n"
            "  2023-0001, Juan, Dela Cruz, BSCS, 1, Male\n\n"
            "Notes:\n"
            "  - ID must follow YYYY-NNNN format\n"
            "  - program_code must already exist in the system\n"
            "  - Import colleges and programs first before students"
        )
        csv_file_path = filedialog.askopenfilename(title="Select Student CSV", filetypes=[("CSV Files", "*.csv")])
        if not csv_file_path: #User cancelled
            return
        try:
            total_added, skipped_reasons = importer.import_students(csv_file_path) #Import students
            self._reload_data()
            self._refresh_students() #Update the student table display
            self._update_counters() #Update the counters
            self._show_import_summary(total_added, skipped_reasons) #Display results
        except Exception as error:
            messagebox.showerror("Import Failed", f"Something went wrong:\n{error}")

    def _import_programs(self):
        messagebox.showinfo("Import Format — Programs",
            "Your CSV file must have these columns in this order:\n\n"
            "  code, name, college_code\n\n"
            "Example row:\n"
            "  BSCS, Bachelor of Science in Computer Science, CCS\n\n"
            "Notes:\n"
            "  - college_code must already exist in the system\n"
            "  - Import colleges first before programs"
        )
        csv_file_path = filedialog.askopenfilename(title="Select Program CSV", filetypes=[("CSV Files", "*.csv")])
        if not csv_file_path: #User cancelled
            return
        try:
            total_added, skipped_reasons = importer.import_programs(csv_file_path) #Import programs from csv
            self._reload_data()
            self._refresh_programs() #Update the program table display
            self._update_counters() #Update the counters
            self._show_import_summary(total_added, skipped_reasons) #Display results
        except Exception as error:
            messagebox.showerror("Import Failed", f"Something went wrong:\n{error}")

    def _import_colleges(self):
        messagebox.showinfo("Import Format — Colleges",
            "Your CSV file must have these columns in this order:\n\n"
            "  code, name\n\n"
            "Example row:\n"
            "  CCS, College of Computer Studies"
        )
        csv_file_path = filedialog.askopenfilename(title="Select College CSV", filetypes=[("CSV Files", "*.csv")])
        if not csv_file_path: #User cancelled
            return
        try:
            total_added, skipped_reasons = importer.import_colleges(csv_file_path) #Import colleges from csv
            self._reload_data()
            self._refresh_colleges() #Update the college table display
            self._update_counters() #Update the counters
            self._show_import_summary(total_added, skipped_reasons) #Display results
        except Exception as error:
            messagebox.showerror("Import Failed", f"Something went wrong:\n{error}")

    # ── Students ──────────────────────────────────────────────
    def _build_student_tab(self, parent):
        self.student_search_var = ctk.StringVar()
        self.student_sort_var   = ctk.StringVar(value="ID")

        student_toolbar = ctk.CTkFrame(parent, fg_color="transparent") #Toolbar with search, sort, and action buttons
        student_toolbar.pack(fill="x", pady=(0, 10))

        search_entry = ctk.CTkEntry(student_toolbar, textvariable=self.student_search_var,
                                    placeholder_text="Search...", font=FONT_BODY, height=36, width=260) #Searchbar
        search_entry.pack(side="left", padx=(0, 8))
        search_entry.bind("<KeyRelease>", lambda event: self._on_student_search()) #Delay refresh until user stops typing

        ctk.CTkOptionMenu(student_toolbar, values=["ID", "Name", "Program", "College", "Year", "Gender"], #Sort dropdown
                          variable=self.student_sort_var, font=FONT_BODY, height=36, width=150,
                          fg_color=NAVY, button_color=NAVY, button_hover_color="#2d2d4e",
                          command=lambda selected: self._refresh_students(reset_page=True)).pack(side="left", padx=(0, 8))

        self.student_order_button = ctk.CTkButton(student_toolbar, text="⤊ Asc", width=80, height=36, #Order toggle
                                                  fg_color=NAVY, font=FONT_BODY,
                                                  command=self._toggle_student_order)
        self.student_order_button.pack(side="left", padx=(0, 8))

        ctk.CTkButton(student_toolbar, text="+ Add Student", height=36, fg_color=NAVY, #Add new student button
                      font=FONT_BODY, command=self._add_student).pack(side="right", padx=(4, 0))
        ctk.CTkButton(student_toolbar, text="⬆ Import", height=36, fg_color=NAVY,
                      font=FONT_BODY, command=self._import_students).pack(side="right") #Import students button

        action_bar = ctk.CTkFrame(parent, fg_color="transparent") #Edit and delete buttons for selected row
        action_bar.pack(fill="x", pady=(0, 6))
        ctk.CTkButton(action_bar, text="Edit Selected", height=32, fg_color=NAVY,
                      font=FONT_SMALL, command=self._edit_selected_student).pack(side="left", padx=(0, 6)) #Edit selected student
        ctk.CTkButton(action_bar, text="Delete Selected", height=32, fg_color="#e63946",
                      font=FONT_SMALL, command=self._delete_selected_student).pack(side="left") #Delete selected student

        self._style_treeview("Student") #Apply styling to the student treeview
        self.student_tree = ttk.Treeview(parent, style="Student.Treeview",
                                         columns=("id", "name", "program", "college", "year", "gender"),
                                         show="headings", selectmode="browse") #One row selectable at a time
        self.student_tree.heading("id",      text="ID") #Column headers
        self.student_tree.heading("name",    text="Name")
        self.student_tree.heading("program", text="Program")
        self.student_tree.heading("college", text="College")
        self.student_tree.heading("year",    text="Year")
        self.student_tree.heading("gender",  text="Gender")
        self.student_tree.column("id",      width=130, anchor="w") #Column widths
        self.student_tree.column("name",    width=200, anchor="w")
        self.student_tree.column("program", width=110, anchor="w")
        self.student_tree.column("college", width=100, anchor="w")
        self.student_tree.column("year",    width=60,  anchor="w")
        self.student_tree.column("gender",  width=100, anchor="w")
        self.student_tree.pack(fill="both", expand=True)
        self.student_tree.tag_configure("odd",  background="#f8f9fa") #Alternating row colors
        self.student_tree.tag_configure("even", background="#ffffff")

        self.student_page_label = self._build_page_controls(parent, self._student_prev_page, self._student_next_page, self._student_jump_page) #Page controls
        self._refresh_students(reset_page=True) #Load and display all students

    def _toggle_student_order(self): #Order toggle
        self.student_sort_reverse = not self.student_sort_reverse #Toggle ascending/descending
        self.student_order_button.configure(text="⤋ Desc" if self.student_sort_reverse else "⤊ Asc") #Update button text
        self._refresh_students(reset_page=True) #Refresh table with new sort order

    def _refresh_students(self, reset_page=False):
        if reset_page:
            self.student_page = 1 #Reset page number to 1 if reset_page is True

        for row in self.student_tree.get_children(): #Clear existing rows from the treeview
            self.student_tree.delete(row)

        sort_column_map = {
            "ID":      "id",
            "Name":    "name",
            "Program": "program_code",
            "Year":    "year",
            "Gender":  "gender",
            "College": "college_code" #college_code triggers a JOIN in get_students since the column lives on programs, not students
        }
        sort_column = sort_column_map[self.student_sort_var.get()] #Get actual column name from display name

        page_of_students, total_count = manager.get_students( #Let the database handle search, sort, and pagination
            search    = self.student_search_var.get(),
            sort_col  = sort_column,
            reverse   = self.student_sort_reverse,
            page      = self.student_page,
            page_size = self.page_size
        )

        total_pages = (total_count + self.page_size - 1) // self.page_size #Ceiling division without importing math
        if total_pages == 0:
            total_pages = 1 #If no records, set to 1 page
        if self.student_page > total_pages: #Clamp page if search narrowed down the results
            self.student_page = total_pages #Set page number to the last page
        self.student_page_label.configure(text=f"Page {self.student_page} of {total_pages}") #Update page number label

        for row_index, student in enumerate(page_of_students): #Insert each student as a treeview row
            display_name = student["lastname"] + ", " + student["firstname"] #Format name as Lastname, Firstname
            college_code = self.program_to_college.get(student["program_code"], "N/A") #Look up the college through the program
            tag = "odd" if row_index % 2 == 0 else "even" #Alternate row colors
            self.student_tree.insert("", "end", iid=student["id"], tags=(tag,), #Use student ID as the row identifier
                                     values=(student["id"], display_name, student["program_code"],
                                             college_code, student["year"], student["gender"]))

    def _get_selected_student(self): #Get the full student record for the selected treeview row
        selected = self.student_tree.selection() #Get selected row ID
        if not selected: #No row selected
            messagebox.showwarning("No Selection", "Please select a student first.")
            return None
        student_id = selected[0] #Row iid is the student ID
        self.all_students = manager.fetch_all(manager.STUDENT) #Reload to get latest data
        for student in self.all_students: #Find the matching student record
            if student["id"].lower() == student_id.lower():
                return student
        return None

    def _edit_selected_student(self): #Edit the currently selected student
        student = self._get_selected_student()
        if student:
            self._edit_student(student) #Open edit popup with student data

    def _delete_selected_student(self): #Delete the currently selected student
        student = self._get_selected_student()
        if student:
            self._delete_student(student) #Run the delete flow

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
            self.all_students = manager.fetch_all(manager.STUDENT) #Reload before pk_check to catch latest records
            if not manager.format_check(form_values["id"]): #Check YYYY-NNNN format
                messagebox.showerror("Invalid ID", "ID must follow YYYY-NNNN format."); return
            if manager.pk_check(self.all_students, "id", form_values["id"]): #Check for duplicate ID
                messagebox.showerror("Duplicate", "This ID already exists."); return
            manager.add_record(manager.STUDENT, form_values, manager.STUDENT_FIELDS) #Record new student
            self._reload_data()
            add_student_popup.destroy(); self._refresh_students(); self._update_counters() #Close popup, refresh table and counters
        add_student_popup = PopupForm(self, "Add Student", self._student_fields(), save) #Create and show the popup form

    def _edit_student(self, student):
        def save(form_values):
            self.all_students = manager.fetch_all(manager.STUDENT) #Reload before pk_check to catch latest records
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
            manager.delete_record(manager.STUDENT, "id", student["id"]) #Delete student record
            self._reload_data()
            self._refresh_students(); self._update_counters() #Refresh table and update counters

    def _student_prev_page(self):
        if self.student_page > 1: #If not on the first page
            self.student_page -= 1 #Go to the previous page
            self._refresh_students() #Refresh table

    def _student_next_page(self):
        self.student_page += 1 #Go to the next page
        self._refresh_students() #Refresh will clamp if out of range

    def _student_jump_page(self, value): #Jump to a specific page number
        if value.isdigit(): #Only jump if the input is a valid number
            self.student_page = int(value)
            self._refresh_students() #Refresh will clamp if out of range

    # ── Programs ──────────────────────────────────────────────
    def _build_program_tab(self, parent):
        program_toolbar = ctk.CTkFrame(parent, fg_color="transparent") #Toolbar
        program_toolbar.pack(fill="x", pady=(0, 10))

        program_search_entry = ctk.CTkEntry(program_toolbar, textvariable=self.program_search_var,
                                            placeholder_text="Search...", font=FONT_BODY, height=36, width=260) #Searchbar
        program_search_entry.pack(side="left", padx=(0, 8))
        program_search_entry.bind("<KeyRelease>", lambda event: self._on_program_search()) #Delay refresh until user stops typing

        ctk.CTkOptionMenu(program_toolbar, values=["Code", "Name"], #Sort dropdown
                          variable=self.program_sort_var, font=FONT_BODY, height=36, width=120,
                          fg_color=NAVY, button_color=NAVY, button_hover_color="#2d2d4e",
                          command=lambda selected: self._refresh_programs(reset_page=True)).pack(side="left", padx=(0, 8))

        self.program_order_button = ctk.CTkButton(program_toolbar, text="⤊ Asc", width=80, height=36,
                                                  fg_color=NAVY, font=FONT_BODY,
                                                  command=self._toggle_program_order) #Order toggle
        self.program_order_button.pack(side="left", padx=(0, 8))

        ctk.CTkButton(program_toolbar, text="+ Add Program", height=36, fg_color=NAVY,
                      font=FONT_BODY, command=self._add_program).pack(side="right", padx=(4, 0)) #Add program button
        ctk.CTkButton(program_toolbar, text="⬆ Import", height=36, fg_color=NAVY,
                      font=FONT_BODY, command=self._import_programs).pack(side="right") #Import program button

        action_bar = ctk.CTkFrame(parent, fg_color="transparent") #Edit and delete buttons for selected row
        action_bar.pack(fill="x", pady=(0, 6))
        ctk.CTkButton(action_bar, text="Edit Selected", height=32, fg_color=NAVY,
                      font=FONT_SMALL, command=self._edit_selected_program).pack(side="left", padx=(0, 6)) #Edit selected program
        ctk.CTkButton(action_bar, text="Delete Selected", height=32, fg_color="#e63946",
                      font=FONT_SMALL, command=self._delete_selected_program).pack(side="left") #Delete selected program

        self._style_treeview("Program") #Apply styling to the program treeview
        self.program_tree = ttk.Treeview(parent, style="Program.Treeview",
                                         columns=("code", "name", "college"),
                                         show="headings", selectmode="browse") #One row selectable at a time
        self.program_tree.heading("code",    text="Code") #Column headers
        self.program_tree.heading("name",    text="Name")
        self.program_tree.heading("college", text="College")
        self.program_tree.column("code",    width=120, anchor="w") #Column widths
        self.program_tree.column("name",    width=400, anchor="w")
        self.program_tree.column("college", width=130, anchor="w")
        self.program_tree.pack(fill="both", expand=True)
        self.program_tree.tag_configure("odd",  background="#f8f9fa") #Alternating row colors
        self.program_tree.tag_configure("even", background="#ffffff")

        self.program_page_label = self._build_page_controls(parent, self._program_prev_page, self._program_next_page, self._program_jump_page) #Page controls
        self._refresh_programs(reset_page=True) #Load and display all programs

    def _toggle_program_order(self):
        self.program_sort_reverse = not self.program_sort_reverse #Order toggle
        self.program_order_button.configure(text="⤋ Desc" if self.program_sort_reverse else "⤊ Asc") #Update button text
        self._refresh_programs(reset_page=True) #Refresh table with new sort order

    def _refresh_programs(self, reset_page=False):
        if reset_page:
            self.program_page = 1 #Reset page number to 1 if reset_page is True

        for row in self.program_tree.get_children(): #Clear existing rows from the treeview
            self.program_tree.delete(row)

        sort_column_map = {"Code": "code", "Name": "name"} #Map display name to field name
        sort_column = sort_column_map[self.program_sort_var.get()] #Get actual column name

        page_of_programs, total_count = manager.get_programs( #Let the database handle search, sort, and pagination
            search    = self.program_search_var.get(),
            sort_col  = sort_column,
            reverse   = self.program_sort_reverse,
            page      = self.program_page,
            page_size = self.page_size
        )

        total_pages = (total_count + self.page_size - 1) // self.page_size #Ceiling division without importing math
        if total_pages == 0:
            total_pages = 1 #If no records, set to 1 page
        if self.program_page > total_pages: #Clamp page if search narrowed down the results
            self.program_page = total_pages #Set page number to the last page
        self.program_page_label.configure(text=f"Page {self.program_page} of {total_pages}") #Update page number label

        for row_index, program in enumerate(page_of_programs): #Insert each program as a treeview row
            tag = "odd" if row_index % 2 == 0 else "even" #Alternate row colors
            self.program_tree.insert("", "end", iid=program["code"], tags=(tag,), #Use program code as the row identifier
                                     values=(program["code"], program["name"], program["college_code"]))

    def _get_selected_program(self): #Get the full program record for the selected treeview row
        selected = self.program_tree.selection() #Get selected row ID
        if not selected: #No row selected
            messagebox.showwarning("No Selection", "Please select a program first.")
            return None
        program_code = selected[0] #Row iid is the program code
        self.all_programs = manager.fetch_all(manager.PROGRAM) #Reload to get latest data
        for program in self.all_programs: #Find the matching program record
            if program["code"].lower() == program_code.lower():
                return program
        return None

    def _edit_selected_program(self): #Edit the currently selected program
        program = self._get_selected_program()
        if program:
            self._edit_program(program) #Open edit popup with program data

    def _delete_selected_program(self): #Delete the currently selected program
        program = self._get_selected_program()
        if program:
            self._delete_program(program) #Run the delete flow

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

    def _program_prev_page(self):
        if self.program_page > 1: #If not on the first page
            self.program_page -= 1 #Go to the previous page
            self._refresh_programs() #Refresh table

    def _program_next_page(self):
        self.program_page += 1 #Go to the next page
        self._refresh_programs() #Refresh will clamp if out of range

    def _program_jump_page(self, value): #Jump to a specific page number
        if value.isdigit(): #Only jump if the input is a valid number
            self.program_page = int(value)
            self._refresh_programs() #Refresh will clamp if out of range

    # ── Colleges ──────────────────────────────────────────────
    def _build_college_tab(self, parent):
        college_toolbar = ctk.CTkFrame(parent, fg_color="transparent") #Toolbar
        college_toolbar.pack(fill="x", pady=(0, 10))

        college_search_entry = ctk.CTkEntry(college_toolbar, textvariable=self.college_search_var,
                                            placeholder_text="Search...", font=FONT_BODY, height=36, width=260) #Searchbar
        college_search_entry.pack(side="left", padx=(0, 8))
        college_search_entry.bind("<KeyRelease>", lambda event: self._on_college_search()) #Delay refresh until user stops typing

        ctk.CTkOptionMenu(college_toolbar, values=["Code", "Name"], #Sort dropdown
                          variable=self.college_sort_var, font=FONT_BODY, height=36, width=120,
                          fg_color=NAVY, button_color=NAVY, button_hover_color="#2d2d4e",
                          command=lambda selected: self._refresh_colleges(reset_page=True)).pack(side="left", padx=(0, 8))

        self.college_order_button = ctk.CTkButton(college_toolbar, text="⤊ Asc", width=80, height=36,
                                                  fg_color=NAVY, font=FONT_BODY,
                                                  command=self._toggle_college_order) #Order toggle
        self.college_order_button.pack(side="left", padx=(0, 8))

        ctk.CTkButton(college_toolbar, text="+ Add College", height=36, fg_color=NAVY,
                      font=FONT_BODY, command=self._add_college).pack(side="right", padx=(4, 0)) #Add college button
        ctk.CTkButton(college_toolbar, text="⬆ Import", height=36, fg_color=NAVY,
                      font=FONT_BODY, command=self._import_colleges).pack(side="right") #Import college button

        action_bar = ctk.CTkFrame(parent, fg_color="transparent") #Edit and delete buttons for selected row
        action_bar.pack(fill="x", pady=(0, 6))
        ctk.CTkButton(action_bar, text="Edit Selected", height=32, fg_color=NAVY,
                      font=FONT_SMALL, command=self._edit_selected_college).pack(side="left", padx=(0, 6)) #Edit selected college
        ctk.CTkButton(action_bar, text="Delete Selected", height=32, fg_color="#e63946",
                      font=FONT_SMALL, command=self._delete_selected_college).pack(side="left") #Delete selected college

        self._style_treeview("College") #Apply styling to the college treeview
        self.college_tree = ttk.Treeview(parent, style="College.Treeview",
                                         columns=("code", "name"),
                                         show="headings", selectmode="browse") #One row selectable at a time
        self.college_tree.heading("code", text="Code") #Column headers
        self.college_tree.heading("name", text="Name")
        self.college_tree.column("code", width=150, anchor="w") #Column widths
        self.college_tree.column("name", width=550, anchor="w")
        self.college_tree.pack(fill="both", expand=True)
        self.college_tree.tag_configure("odd",  background="#f8f9fa") #Alternating row colors
        self.college_tree.tag_configure("even", background="#ffffff")

        self.college_page_label = self._build_page_controls(parent, self._college_prev_page, self._college_next_page, self._college_jump_page) #Page controls
        self._refresh_colleges(reset_page=True) #Display colleges

    def _toggle_college_order(self):
        self.college_sort_reverse = not self.college_sort_reverse #Order toggle
        self.college_order_button.configure(text="⤋ Desc" if self.college_sort_reverse else "⤊ Asc") #Update button text
        self._refresh_colleges(reset_page=True) #Refresh table with new sort order

    def _refresh_colleges(self, reset_page=False):
        if reset_page:
            self.college_page = 1 #Reset page number to 1 if reset_page is True

        for row in self.college_tree.get_children(): #Clear existing rows from the treeview
            self.college_tree.delete(row)

        sort_column_map = {"Code": "code", "Name": "name"} #Map display name to field name
        sort_column = sort_column_map[self.college_sort_var.get()] #Get actual column name

        page_of_colleges, total_count = manager.get_colleges( #Let the database handle search, sort, and pagination
            search    = self.college_search_var.get(),
            sort_col  = sort_column,
            reverse   = self.college_sort_reverse,
            page      = self.college_page,
            page_size = self.page_size
        )

        total_pages = (total_count + self.page_size - 1) // self.page_size #Ceiling division without importing math
        if total_pages == 0:
            total_pages = 1 #If no records, set to 1 page
        if self.college_page > total_pages: #Clamp page if search narrowed down the results
            self.college_page = total_pages #Set page number to the last page
        self.college_page_label.configure(text=f"Page {self.college_page} of {total_pages}") #Update page number label

        for row_index, college in enumerate(page_of_colleges): #Insert each college as a treeview row
            tag = "odd" if row_index % 2 == 0 else "even" #Alternate row colors
            self.college_tree.insert("", "end", iid=college["code"], tags=(tag,), #Use college code as the row identifier
                                     values=(college["code"], college["name"]))

    def _get_selected_college(self): #Get the full college record for the selected treeview row
        selected = self.college_tree.selection() #Get selected row ID
        if not selected: #No row selected
            messagebox.showwarning("No Selection", "Please select a college first.")
            return None
        college_code = selected[0] #Row iid is the college code
        self.all_colleges = manager.fetch_all(manager.COLLEGE) #Reload to get latest data
        for college in self.all_colleges: #Find the matching college record
            if college["code"].lower() == college_code.lower():
                return college
        return None

    def _edit_selected_college(self): #Edit the currently selected college
        college = self._get_selected_college()
        if college:
            self._edit_college(college) #Open edit popup with college data

    def _delete_selected_college(self): #Delete the currently selected college
        college = self._get_selected_college()
        if college:
            self._delete_college(college) #Run the delete flow

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
        edit_college_popup = PopupForm(self, "Edit College", self._college_fields(), save, initial=college) #Create popup with existing college data

    def _delete_college(self, college):
        if messagebox.askyesno("Delete", f"Delete '{college['code']}'?\nAll programs and students under it will also be deleted."): #Confirmation
            manager.delete_college(college["code"]) #Delete the college
            self._reload_data()
            self._refresh_colleges(); self._refresh_programs(); self._refresh_students(); self._update_counters() #Refresh all tables and update counters

    def _college_prev_page(self):
        if self.college_page > 1: #If not on the first page
            self.college_page -= 1 #Go to the previous page
            self._refresh_colleges() #Refresh table

    def _college_next_page(self):
        self.college_page += 1 #Go to the next page
        self._refresh_colleges() #Refresh will clamp if out of range

    def _college_jump_page(self, value): #Jump to a specific page number
        if value.isdigit(): #Only jump if the input is a valid number
            self.college_page = int(value)
            self._refresh_colleges() #Refresh will clamp if out of range