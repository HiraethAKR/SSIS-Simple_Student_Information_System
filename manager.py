import re
import sqlite3

STUDENT = "students"
PROGRAM = "programs"
COLLEGE = "colleges"

DB = "ssis.db" #SQLite database

def get_connection(): #Opens and returns a connection to the database
    connection = sqlite3.connect(DB) #Connect to the database
    connection.row_factory = sqlite3.Row #Makes rows behave like dictionaries <--- Did this so I wont have to rewrite everything since I used csv for basically all of it
    return connection #Return the connection to use in other functions

STUDENT_FIELDS = ["id", "firstname", "lastname", "program_code", "year", "gender"]
PROGRAM_FIELDS = ["code", "name", "college_code"]
COLLEGE_FIELDS = ["code", "name"]

def init_files(): #Create tables if they dont exist
    connection = get_connection()
    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS colleges (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL
            )
        """) #college
        connection.execute("""
            CREATE TABLE IF NOT EXISTS programs (
                code         TEXT PRIMARY KEY,
                name         TEXT NOT NULL,
                college_code TEXT NOT NULL,
                FOREIGN KEY (college_code) REFERENCES colleges(code)
            )
        """) #program
        connection.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id           TEXT PRIMARY KEY,
                firstname    TEXT NOT NULL,
                lastname     TEXT NOT NULL,
                program_code TEXT NOT NULL,
                year         TEXT NOT NULL,
                gender       TEXT NOT NULL,
                FOREIGN KEY (program_code) REFERENCES programs(code)
            )
        """) #students
        connection.commit() #Save the changes
    finally:
        connection.close() #Always close even if something goes wrong

def fetch_all(table): #Read all records from a table and return as a list of dictionaries
    connection = get_connection()
    rows = connection.execute(f"SELECT * FROM {table}").fetchall() #Fetch all rows from the table
    connection.close()
    data = []
    for row in rows:
        data.append(dict(row)) #Convert each Row object to a dictionary
    return data

def get_students(search, sort_col, reverse, page, page_size): #Fetch one page of students from the database
    connection = get_connection()

    order  = "DESC" if reverse else "ASC" #Ascending or descending
    offset = (page - 1) * page_size       #Calculate how many rows to skip
    like   = f"%{search}%"                #Wrap search term in wildcards

    where = "WHERE s.id LIKE ? OR s.firstname LIKE ? OR s.lastname LIKE ? OR s.program_code LIKE ? OR s.year LIKE ? OR s.gender LIKE ?"
    params = [like, like, like, like, like, like] #One placeholder per WHERE condition

    if sort_col == "college_code": #College isnt on the students table so we need a JOIN to sort by it
        query = f"""
            SELECT s.* FROM students s
            JOIN programs p ON s.program_code = p.code
            {where}
            ORDER BY p.college_code {order}
            LIMIT ? OFFSET ?
        """
    else:
        sort_map = { #Map UI sort names to actual column names
            "id":           "s.id",
            "name":         "s.lastname",
            "program_code": "s.program_code",
            "year":         "s.year",
            "gender":       "s.gender",
        }
        column = sort_map.get(sort_col, "s.id") #Default to id if not found
        query = f"""
            SELECT s.* FROM students s
            {where}
            ORDER BY {column} {order}
            LIMIT ? OFFSET ?
        """

    rows = connection.execute(query, params + [page_size, offset]).fetchall()

    count_query = f"SELECT COUNT(*) FROM students s {where}"
    total_count = connection.execute(count_query, params).fetchone()[0] #Get total matching rows for page calculation

    connection.close()

    data = []
    for row in rows:
        data.append(dict(row)) #Convert to dictionaries
    return data, total_count #Return the page and total count

def get_programs(search, sort_col, reverse, page, page_size): #Fetch one page of programs from the database
    connection = get_connection()

    order    = "DESC" if reverse else "ASC" #Ascending or descending
    sort_map = { #Map UI sort names to actual column names
        "code": "code",
        "name": "name",
    }
    column = sort_map.get(sort_col, "code") #Default to code if not found
    offset = (page - 1) * page_size         #Calculate how many rows to skip

    query = f"""
        SELECT * FROM programs
        WHERE code LIKE ? OR name LIKE ? OR college_code LIKE ?
        ORDER BY {column} {order}
        LIMIT ? OFFSET ?
    """
    like = f"%{search}%" #Wrap search term in wildcards
    rows = connection.execute(query, [like, like, like, page_size, offset]).fetchall()

    count_query = "SELECT COUNT(*) FROM programs WHERE code LIKE ? OR name LIKE ? OR college_code LIKE ?"
    total_count = connection.execute(count_query, [like, like, like]).fetchone()[0] #Get total matching rows for page calculation

    connection.close()

    data = []
    for row in rows:
        data.append(dict(row)) #Convert to dictionaries
    return data, total_count #Return the page and total count


def get_colleges(search, sort_col, reverse, page, page_size): #Fetch one page of colleges from the database
    connection = get_connection()

    order    = "DESC" if reverse else "ASC" #Ascending or descending
    sort_map = { #Map UI sort names to actual column names
        "code": "code",
        "name": "name",
    }
    column = sort_map.get(sort_col, "code") #Default to code if not found
    offset = (page - 1) * page_size         #Calculate how many rows to skip

    query = f"""
        SELECT * FROM colleges
        WHERE code LIKE ? OR name LIKE ?
        ORDER BY {column} {order}
        LIMIT ? OFFSET ?
    """
    like = f"%{search}%" #Wrap search term in wildcards
    rows = connection.execute(query, [like, like, page_size, offset]).fetchall()

    count_query = "SELECT COUNT(*) FROM colleges WHERE code LIKE ? OR name LIKE ?"
    total_count = connection.execute(count_query, [like, like]).fetchone()[0] #Get total matching rows for page calculation

    connection.close()

    data = []
    for row in rows:
        data.append(dict(row)) #Convert to dictionaries
    return data, total_count #Return the page and total count

def add_record(table, record, fieldnames): #Insert a new record into the table
    connection = get_connection()
    placeholders = ", ".join(["?" for _ in fieldnames]) #Build "?, ?, ?" based on number of fields
    columns      = ", ".join(fieldnames)                #Build "id, firstname, lastname, ..."
    values       = [record[field] for field in fieldnames] #Pull values in the same order as columns
    connection.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)
    connection.commit() #Save
    connection.close() #and close

def update_record(table, pk_field, pk_value, updated_record, fieldnames): #Update a record in the table
    connection = get_connection()
    update_fields = [field for field in fieldnames if field != pk_field] #Dont include the primary key in the SET clause
    set_clause    = ", ".join([f"{field} = ?" for field in update_fields]) #Build "firstname = ?, lastname = ?, ..."
    values        = [updated_record[field] for field in update_fields]     #Pull values in the same order
    values.append(updated_record[pk_field])                                #Add the new pk value at the end for the SET
    values.append(pk_value)                                                #Add the old pk value for the WHERE clause
    connection.execute(f"UPDATE {table} SET {set_clause}, {pk_field} = ? WHERE {pk_field} = ?", values)
    connection.commit() #save
    connection.close() #close

def delete_record(table, pk_field, pk_value): #Delete a record from the table
    connection = get_connection()
    connection.execute(f"DELETE FROM {table} WHERE {pk_field} = ?", [pk_value]) #Delete record with matching pk value
    connection.commit() #save
    connection.close() #close

def pk_check(data, pk_field, pk_value): #Check if primary key already exists/Need this to prevent duplication
    for row in data:
        if row[pk_field].lower() == pk_value.lower(): #Compare pk till a match
            return True 
    return False

def format_check(student_id): #Check if ID follows YYYY-NNNN format
    pattern = r"^\d{4}-\d{4}$" #Check if input: Starts(^), 4 digits(\d{4}), hypen(-), 4 digits(\d{4}), and ends($). All together - "^\d{4}-\d{4}$"
    if re.match(pattern, student_id):
        return True
    return False

def update_college(old_code, new_record): #Cascading update for college
    new_code = new_record["code"]
    update_record(COLLEGE, "code", old_code, new_record, COLLEGE_FIELDS) #Update the college record first

    if old_code.lower() != new_code.lower(): #Only cascade if the code actually changed
        connection = get_connection()
        connection.execute(
            "UPDATE programs SET college_code = ? WHERE college_code = ?",
            [new_code, old_code] #Set new college code for all programs that had the old one
        )
        connection.commit() #save
        connection.close() #close

def update_program(old_code, new_record): #Cascading update for program
    new_code = new_record["code"]
    update_record(PROGRAM, "code", old_code, new_record, PROGRAM_FIELDS) #Update the program record first

    if old_code.lower() != new_code.lower(): #Only cascade if the code actually changed
        connection = get_connection()
        connection.execute(
            "UPDATE students SET program_code = ? WHERE program_code = ?",
            [new_code, old_code] #Set new program code for all students that had the old one
        )
        connection.commit() #save
        connection.close() #close

def delete_college(college_code): #Cascading delete for college
    connection = get_connection()
    connection.execute(
        "DELETE FROM students WHERE program_code IN (SELECT code FROM programs WHERE college_code = ?)",
        [college_code] #Delete all students enrolled in programs under this college
    )
    connection.execute(
        "DELETE FROM programs WHERE college_code = ?",
        [college_code] #Delete all programs under this college
    )
    connection.execute(
        "DELETE FROM colleges WHERE code = ?",
        [college_code] #Delete the college itself
    )
    connection.commit() #Save all three deletions
    connection.close()  #Close

def delete_program(program_code): #Cascading delete for program
    connection = get_connection()
    connection.execute(
        "DELETE FROM students WHERE program_code = ?",
        [program_code] #Delete all students under this program first
    )
    connection.execute(
        "DELETE FROM programs WHERE code = ?",
        [program_code] #Then delete the program itself
    )
    connection.commit() #Save both deletions
    connection.close()  #Close