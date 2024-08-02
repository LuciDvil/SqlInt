import sqlite3
import streamlit as st
import pandas as pd

# Database interaction functions
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('employee.db')
    except sqlite3.Error as e:
        st.error(f"Error connecting to database: {e}")
    return conn

def create_table(conn):
    try:
        sql_create_employees_table = """ CREATE TABLE IF NOT EXISTS employees (
                                            id integer PRIMARY KEY,
                                            name text NOT NULL,
                                            department text NOT NULL,
                                            salary real
                                        ); """
        conn.execute(sql_create_employees_table)
    except sqlite3.Error as e:
        st.error(f"Error creating table: {e}")

def insert_employee(conn, employee):
    columns = ', '.join(employee.keys())
    placeholders = ', '.join('?' * len(employee))
    sql = f'INSERT INTO employees ({columns}) VALUES ({placeholders})'
    cur = conn.cursor()
    cur.execute(sql, tuple(employee.values()))
    conn.commit()
    return cur.lastrowid

def update_employee(conn, employee, employee_id):
    columns = ', '.join(f'{col} = ?' for col in employee.keys())
    sql = f'UPDATE employees SET {columns} WHERE id = ?'
    cur = conn.cursor()
    cur.execute(sql, tuple(employee.values()) + (employee_id,))
    conn.commit()

def delete_employee(conn, id):
    sql = 'DELETE FROM employees WHERE id=?'
    cur = conn.cursor()
    cur.execute(sql, (id,))
    conn.commit()

def select_all_employees(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees")
    rows = cur.fetchall()
    return rows

def select_employee_by_id(conn, id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees WHERE id=?", (id,))
    row = cur.fetchone()
    return row

def select_employees_filtered(conn, department=None, min_salary=None, max_salary=None):
    cur = conn.cursor()
    query = "SELECT * FROM employees WHERE 1=1"
    params = []
    
    if department:
        query += " AND department=?"
        params.append(department)
    
    if min_salary:
        query += " AND salary>=?"
        params.append(min_salary)
    
    if max_salary:
        query += " AND salary<=?"
        params.append(max_salary)
    
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    return rows

def add_extra_columns(conn, columns):
    cur = conn.cursor()
    for column in columns:
        cur.execute(f"ALTER TABLE employees ADD COLUMN {column} TEXT")
    conn.commit()

def get_columns(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(employees)")
    columns_info = cur.fetchall()
    columns = [info[1] for info in columns_info if info[1] != 'id']
    return columns

# Streamlit user interface
def main():
    st.title("Employee Management System")
    
    # Database connection
    conn = create_connection()
    if conn is not None:
        create_table(conn)
    else:
        st.error("Error! Cannot create the database connection.")
        return
    
    menu = ["Add", "Update", "Delete", "View"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if choice == "Add":
        st.subheader("Add Employee")
        with st.form(key='add_employee'):
            columns = get_columns(conn)
            employee = {}
            for column in columns:
                if column == 'salary':
                    employee[column] = st.number_input(column.capitalize(), min_value=0.0, step=0.1)
                else:
                    employee[column] = st.text_input(column.capitalize())
            submit_button = st.form_submit_button(label='Add Employee')
        
        if submit_button:
            if all(employee.values()):
                insert_employee(conn, employee)
                st.success("Employee added successfully!")
            else:
                st.warning("Please fill out all fields.")

    elif choice == "Update":
        st.subheader("Update Employee")
        employee_id = st.number_input("Employee ID", min_value=1, step=1)
        employee = select_employee_by_id(conn, employee_id)
        
        if employee:
            columns = get_columns(conn)
            st.write(f"Selected Employee - ID: {employee[0]}")
            with st.form(key='update_employee'):
                updated_employee = {}
                for idx, column in enumerate(columns, start=1):
                    if column == 'salary':
                        updated_employee[column] = st.number_input(column.capitalize(), min_value=0.0, step=0.1, value=employee[idx])
                    else:
                        updated_employee[column] = st.text_input(column.capitalize(), value=employee[idx])
                submit_button = st.form_submit_button(label='Update Employee')
            
            if submit_button:
                if all(updated_employee.values()):
                    update_employee(conn, updated_employee, employee_id)
                    st.success("Employee updated successfully!")
                else:
                    st.warning("Please fill out all fields.")
        else:
            st.warning("Employee ID not found.")

    elif choice == "Delete":
        st.subheader("Delete Employee")
        employee_id = st.number_input("Employee ID", min_value=1, step=1)
        if st.button("Delete"):
            delete_employee(conn, employee_id)
            st.success("Employee deleted successfully!")

    elif choice == "View":
        st.subheader("View All Employees")
        
        with st.expander("Add Filters"):
            department_filter = st.text_input("Department")
            min_salary_filter = st.number_input("Minimum Salary", min_value=0.0, step=0.1)
            max_salary_filter = st.number_input("Maximum Salary", min_value=0.0, step=0.1)
            apply_filters = st.button("Apply Filters")
        
        with st.expander("Add Extra Columns"):
            extra_columns = st.text_input("Extra Columns (comma-separated)")
            add_columns = st.button("Add Columns")
        
        if add_columns and extra_columns:
            extra_columns_list = [column.strip() for column in extra_columns.split(',')]
            add_extra_columns(conn, extra_columns_list)
            st.success("Columns added successfully!")
        
        if apply_filters:
            employees = select_employees_filtered(conn, department_filter, min_salary_filter, max_salary_filter)
        else:
            employees = select_all_employees(conn)
        
        if employees:
            columns = ['id'] + get_columns(conn)
            df = pd.DataFrame(employees, columns=columns)
            st.table(df)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name='employees.csv',
                mime='text/csv',
            )
        else:
            st.warning("No employees found.")

if __name__ == '__main__':
    main()
