Student Information System (SSIS)

This is my CCC151 project. Its a student information system where you can manage students, programs, and colleges. Data is saved using csv files.

------------------------------------------------------------------------

HOW TO RUN

make sure you have customtkinter installed first:
    pip install customtkinter

just run: 
	run.bat

if that doesnt work try running this in the terminal:
    python main.py

-----------------------------------------------------------------------

WHAT IT DOES

- You can add, edit, search, sort, and delete students, programs, and colleges
- Theres an import feature if you want to add multiple records at once using a csv file
- Deleting a college or program also deletes everything under it

-------------------------------------------------------------------------

HOW THE IMPORT WORKS

Your csv file needs to have the correct columns otherwise it wont work

colleges:
    code, name
    CCS, College of Computer Studies

programs:
    code, name, college_code
    BSCS, Bachelor of Science in Computer Science, CCS

students:
    id, firstname, lastname, program_code, year, gender
    2023-0001, Juan, Dela Cruz, BSCS, 1, Male

You have to import colleges first then programs then students
Importing students before program and program before college will not work.

-----------------------------------------------------------------------

NOTES

- student id has to be in YYYY-NNNN format (ex. 2023-0001)
- the csv files are created automatically so you dont need to make them
