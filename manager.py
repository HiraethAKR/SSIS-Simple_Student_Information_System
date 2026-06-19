import csv
import os
import re

STUDENT = "students.csv"
PROGRAM = "programs.csv"
COLLEGE = "colleges.csv"

STUDENT_FIELDS = ["id", "firstname", "lastname", "program_code", "year", "gender"]
PROGRAM_FIELDS = ["code", "name", "college_code"]
COLLEGE_FIELDS = ["code", "name"]

def init_files():
    files_to_check = [ #Check if files exists
        (STUDENT, STUDENT_FIELDS),
        (PROGRAM, PROGRAM_FIELDS),
        (COLLEGE, COLLEGE_FIELDS)
    ]

    for filename, fields in files_to_check:
        if not os.path.exists(filename): #Create files if they dont exist
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()

def read_csv(filename):
    data = []
    if os.path.exists(filename): #Reads csv then returns the list
        with open(filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
    return data

def write_csv(filename, data, fieldnames):
    with open(filename, mode='w', newline='', encoding='utf-8') as file: #Overwrite csv file with new list
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def add_record(filename, record, fieldnames): #Add new entry to csv
    data = read_csv(filename)
    data.append(record)
    write_csv(filename, data, fieldnames)

def update_record(filename, pk_field, pk_value, updated_record, fieldnames): 
    data = read_csv(filename)
    success = False #Assume it failed until we find a match

    for i in range(len(data)):
        if data[i][pk_field].lower() == pk_value.lower(): #Case-insensitive check
            data[i] = updated_record
            success = True
            break

    if success:
        write_csv(filename, data, fieldnames)
    return success #Return if it worked or not

def delete_record(filename, pk_field, pk_value, fieldnames): #Deletes a record
    data = read_csv(filename)
    new_data = [] #Create blank list
    for row in data: #Copy data to new_data
        if row[pk_field].lower() != pk_value.lower(): #Only copy data value if the primary key doesnt match with what we're trying to delete
            new_data.append(row)
    write_csv(filename, new_data, fieldnames)

def pk_check(data, pk_field, pk_value): #Check if primary key already exists/Need this to prevent duplication
    for row in data:
        if row[pk_field].lower() == pk_value.lower(): #Compare pk till a match
            return True 
    return False

def format_check(student_id): #Check if ID follows YYYY-NNNN format
    u_input = r"^\d{4}-\d{4}$" #Check if input: Starts(^), 4 digits(\d{4}), hypen(-), 4 digits(\d{4}), and ends($). All together - "^\d{4}-\d{4}$"
    if re.match(u_input, student_id):
        return True
    return False

def search_records(data, query): #Search the fields for a match
    if not query:
        return data # If search bar is empty, return everything
    results = []
    query = query.lower() # Make search case-insensitive
    
    for row in data: 
        for value in row.values(): #Check every value in the current row
            if query in value.lower(): #Lower case data before comparing
                results.append(row)
                break #Move to the next row as soon as we find one match in this one
    return results

def sort_records(data, sort_column, reverse=False): #Sorts based on column
    if not data:
        return data
    
    def get_sort_key(item): #Get Field to be sorted with
        #Sorting by name sorts by last name for students, by name field for programs/colleges
        if sort_column == "name":
            if "lastname" in item:
                return item["lastname"].lower() #Students: sort by last name
            return item["name"].lower() #Programs/Colleges: sort by name field
  
        val = item[sort_column] #ID, Gender, Year, etc.
        if val.isdigit():
             return int(val) #Converts numbers to integer so it sorts properly | This sorts 10 first if not implemented
        return val.lower() #.lower on everything so uppercase coming first than lowercase doesnt happen        
        
    return sorted(data, key=get_sort_key, reverse=reverse) #reverse=reverse controls ascending or descending order

def update_college(old_code, new_record): #Cascading update - relinks programs (and thus their students) to the new college code
    new_code = new_record["code"]

    update_record(COLLEGE, "code", old_code, new_record, COLLEGE_FIELDS) #Update the record in the csv

    if old_code.lower() != new_code.lower(): #Check if college code changed
        programs = read_csv(PROGRAM)
        for p in programs:
            if p["college_code"].lower() == old_code.lower(): #Checks if any program was linked to old college code
                p["college_code"] = new_code #Links program to new college code instead
        write_csv(PROGRAM, programs, PROGRAM_FIELDS) #Updates the new links in the csv

def update_program(old_code, new_record): #Cascading update - relinks students to the new program code
    new_code = new_record["code"]
    update_record(PROGRAM, "code", old_code, new_record, PROGRAM_FIELDS) #Update record in the csv

    if old_code.lower() != new_code.lower(): #check if program code changed
        students = read_csv(STUDENT)
        for s in students:
            if s["program_code"].lower() == old_code.lower(): #Checks if any student is linked to old program code
                s["program_code"] = new_code #Links students to new program code instead
        write_csv(STUDENT, students, STUDENT_FIELDS) #Update the csv with new student to program links

def delete_college(college_code): #No cascading delete - linked programs get college_code set to NULL
    programs = read_csv(PROGRAM)
    colleges = read_csv(COLLEGE)

    for p in programs: #Null out the link instead of deleting linked programs
        if p["college_code"].lower() == college_code.lower():
            p["college_code"] = "NULL"

    new_colleges = [] #Filter out the college itself
    for c in colleges:
        if c["code"].lower() != college_code.lower():
            new_colleges.append(c)

    write_csv(PROGRAM, programs, PROGRAM_FIELDS)
    write_csv(COLLEGE, new_colleges, COLLEGE_FIELDS)

def delete_program(program_code): #No cascading delete - linked students get program_code set to NULL
    students = read_csv(STUDENT)
    programs = read_csv(PROGRAM)

    for s in students: #Null out the link instead of deleting linked students
        if s["program_code"].lower() == program_code.lower():
            s["program_code"] = "NULL"

    new_programs = [] #Filter out the program itself
    for p in programs:
        if p["code"].lower() != program_code.lower():
            new_programs.append(p)

    write_csv(STUDENT, students, STUDENT_FIELDS)
    write_csv(PROGRAM, new_programs, PROGRAM_FIELDS)
