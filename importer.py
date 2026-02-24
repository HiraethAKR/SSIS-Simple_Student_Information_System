import csv
import manager

def import_students(csv_file_path): #Read a csv file and add each row as a student
    total_added = 0
    skipped_reasons = [] #Rows that didnt get added and why

    existing_students = manager.read_csv(manager.STUDENT) #Load once before the loop instead of reading the file every row
    existing_programs = manager.read_csv(manager.PROGRAM) 

    with open(csv_file_path, mode='r', newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file) #Read CSV file with headers

        for current_row in csv_reader:
            student_id   = current_row.get("id",           "").strip() #Get student ID and remove whitespace
            first_name   = current_row.get("firstname",    "").strip() #Get first name and remove whitespace
            last_name    = current_row.get("lastname",     "").strip() #Get last name and remove whitespace
            program_code = current_row.get("program_code", "").strip() #Get program code and remove whitespace
            year_level   = current_row.get("year",         "").strip() #Get year level and remove whitespace
            gender       = current_row.get("gender",       "").strip() #Get gender and remove whitespace

            if not student_id or not first_name or not last_name: #Skip if required fields are empty
                skipped_reasons.append(f"Row with id '{student_id}' — missing required fields (id, firstname, lastname)")
                continue

            if not manager.format_check(student_id): #Skip if ID doesnt follow YYYY-NNNN format
                skipped_reasons.append(f"'{student_id}' — invalid ID format, must be YYYY-NNNN")
                continue

            if not manager.pk_check(existing_programs, "code", program_code): #Skip if program doesnt exist in system
                skipped_reasons.append(f"'{student_id}' — program '{program_code}' does not exist")
                continue

            if manager.pk_check(existing_students, "id", student_id): #Skip if student already exists
                skipped_reasons.append(f"'{student_id}' — already exists")
                continue

            new_student_record = {
                "id":           student_id,
                "firstname":    first_name,
                "lastname":     last_name,
                "program_code": program_code,
                "year":         year_level,
                "gender":       gender
            }
            manager.add_record(manager.STUDENT, new_student_record, manager.STUDENT_FIELDS) #Add the valid student record
            existing_students.append(new_student_record) #Update our local list so duplicate checks work within the same import
            total_added = total_added + 1 #Increment counter

    return total_added, skipped_reasons #Return both so the UI can show the summary


def import_programs(csv_file_path): #Read a csv file and add each row as a program
    total_added = 0
    skipped_reasons = [] #Rows that didnt get added and why

    existing_programs = manager.read_csv(manager.PROGRAM) #Load once before the loop instead of reading the file every row
    existing_colleges = manager.read_csv(manager.COLLEGE) #Same here

    with open(csv_file_path, mode='r', newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file) #Read CSV file with headers

        for current_row in csv_reader:
            program_code = current_row.get("code",         "").strip() #Get program code and remove whitespace
            program_name = current_row.get("name",         "").strip() #Get program name and remove whitespace
            college_code = current_row.get("college_code", "").strip() #Get college code and remove whitespace

            if not program_code or not program_name: #Skip if required fields are empty
                skipped_reasons.append(f"Row with code '{program_code}' — missing required fields (code, name)")
                continue

            if not manager.pk_check(existing_colleges, "code", college_code): #Skip if college doesnt exist in system
                skipped_reasons.append(f"'{program_code}' — college '{college_code}' does not exist")
                continue

            if manager.pk_check(existing_programs, "code", program_code): #Skip if program already exists
                skipped_reasons.append(f"'{program_code}' — already exists")
                continue

            new_program_record = {"code": program_code, "name": program_name, "college_code": college_code}
            manager.add_record(manager.PROGRAM, new_program_record, manager.PROGRAM_FIELDS) #Add the valid program record
            existing_programs.append(new_program_record) #Update our local list so duplicate checks work within the same import
            total_added = total_added + 1 #Increment counter

    return total_added, skipped_reasons #Return both so the UI can show the summary


def import_colleges(csv_file_path): #Read a csv file and add each row as a college
    total_added = 0
    skipped_reasons = [] #Rows that didnt get added and why

    existing_colleges = manager.read_csv(manager.COLLEGE) #Load once before the loop instead of reading the file every row

    with open(csv_file_path, mode='r', newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file) #Read CSV file with headers

        for current_row in csv_reader:
            college_code = current_row.get("code", "").strip() #Get college code and remove whitespace
            college_name = current_row.get("name", "").strip() #Get college name and remove whitespace

            if not college_code or not college_name: #Skip if required fields are empty
                skipped_reasons.append(f"Row with code '{college_code}' — missing required fields (code, name)")
                continue

            if manager.pk_check(existing_colleges, "code", college_code): #Skip if college already exsists
                skipped_reasons.append(f"'{college_code}' — already exists")
                continue

            new_college_record = {"code": college_code, "name": college_name}
            manager.add_record(manager.COLLEGE, new_college_record, manager.COLLEGE_FIELDS) #Add the valid college record
            existing_colleges.append(new_college_record) #Update our local list so duplicate checks work within the same import
            total_added = total_added + 1 #Increment counter

    return total_added, skipped_reasons #Return both so the UI can show the summary