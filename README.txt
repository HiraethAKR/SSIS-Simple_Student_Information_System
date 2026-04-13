Student Information System (SSIS)
CCC151 Project

A desktop student information system for managing students, programs, and colleges.
Built with Python, customtkinter, and SQLite.

----------------------------------------------------------------------------

HOW TO RUN

Install the required dependency first:
    pip install customtkinter

Then you can run the application by either:

Double-click:
    run.bat

Or manually in the terminal:
    python main.py

-----------------------------------------------------------------------------------------------------

PROJECT FILES

_____________________________________________________________________________________________________

main.py       — Entry point. Initializes the database and launches the UI  
manager.py    — All database logic (SQLite). CRUD, search, sort, pagination, cascade  
importer.py   — CSV import logic with row-by-row validation for all three tables  
ui.py         — Full desktop GUI built with customtkinter and tkinter's ttk.Treeview  
ssis.db       — SQLite database file (pre-populated with 5000 students, 30 programs, and 7 colleges)  
run.bat       — Windows shortcut to launch the app  
_____________________________________________________________________________________________________

-----------------------------------------------------------------------------------------------------

FEATURES

Students
- Add, edit, delete individual students via popup forms
- Search across all fields (ID, name, program, college, year, gender)
- Sort by ID, Name, Program, College, Year, or Gender (ascending/descending)
- Paginated table (50 records per page) with Prev / Next / Go-to controls
- Import multiple students at once from a CSV file

Programs
- Add, edit, delete programs
- Search by code, name, or college
- Sort by Code or Name
- Paginated table with same controls as students
- Editing a program code automatically updates all linked students (cascade)
- Deleting a program also deletes all students enrolled in it
- Import through CSV file

Colleges
- Add, edit, delete colleges
- Search by code or name
- Paginated table
- Editing a college code automatically updates all linked programs (cascade)
- Deleting a college also deletes all its programs and their students
- Import through CSV file

Header bar shows live counts of total students, programs, and colleges

-----------------------------------------------------------------------------------------------------

HOW THE CSV IMPORT WORKS

Import order matters — colleges first, then programs, then students.
Importing students before programs, or programs before colleges, will not work.

Each import shows a summary of how many records were added and which rows were skipped and why.

Colleges CSV (columns: code, name)
CCS, College of Computer Studies
CED, College of Education

Programs CSV (columns: code, name, college_code)
BSCS, Bachelor of Science in Computer Science, CCS
BSED, Bachelor of Secondary Education, CED

Students CSV (columns: id, firstname, lastname, program_code, year, gender)
2023-0001, Juan, Dela Cruz, BSCS, 1, Male
2022-0042, Maria, Santos, BSED, 3, Female

Rows are skipped (not added) if:
- Required fields are empty
- Student ID does not follow YYYY-NNNN format
- Year level is not a number from 1 to 10
- Gender is not Male, Female, or Other
- The referenced program or college does not exist
- The record already exists in the database

-----------------------------------------------------------------------------------------------------

DATA RULES

_____________________________________________________________________________________________________

- Student ID must follow YYYY-NNNN format (e.g. 2023-0001)  
- Year level must be a whole number from 1 to 10  
- Gender must be Male, Female, or Other  
- Program code must already exist before adding students  
- College code must already exist before adding programs  
_____________________________________________________________________________________________________

-----------------------------------------------------------------------------------------------------

DATABASE

The database file ssis.db is SQLite and is created automatically on first run if missing.
It comes pre-populated with 5000 students, 30 programs, and 7 colleges.

Tables:
colleges  — code (PK), name
programs  — code (PK), name, college_code (FK → colleges)
students  — id (PK), firstname, lastname, program_code (FK → programs), year, gender
