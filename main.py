from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QWidget, QComboBox, QHeaderView
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets 
import csv
import re
from dialogs import AddStudentDialog, UpdateStudentDialog, AddCourseDialog, UpdateCourseDialog
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QAbstractItemView, QLineEdit, QComboBox, QMessageBox, QToolBar, QStatusBar
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, pyqtSignal
import mysql.connector



# Database connection parameters
HOST = 'localhost'
USER = 'root'
PASSWORD = '7h!ns=cY96NF'
DATABASE = 'ssis'

try:
    # Establish connection
    connection = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DATABASE
        
    )

    # Create cursor
    cursor = connection.cursor()

    # Close cursor and connection
    # cursor.close()
    # connection.close()

except mysql.connector.Error as error:
    print("Error:", error)
# Constants for student fields and database files

STUDENT_FIELDS = ['First Name', 'Middle Initial', 'Last Name', 'ID', 'Year Level', 'Gender', 'Course Code']

COURSE_FIELDS = ['Course Code', 'Course Name']


def get_course_data(cursor):
    """Retrieve course data from the MySQL database."""
    course_data = []
    cursor.execute("SELECT * FROM courses")
    for row in cursor.fetchall():
        course_data.append(row)
    return course_data


class Signal(QObject):
    course_added = pyqtSignal()

class StudentManagementApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("University Student Management System")
        self.setGeometry(100, 100, 800, 600)

        # Database connection setup
        self.connection = mysql.connector.connect(
            host=HOST,
            user=USER,
            password=PASSWORD,
            database=DATABASE
        )
        self.cursor = self.connection.cursor()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Get course data
        self.course_data = get_course_data(cursor)
        self.signal = Signal()

        self.init_ui()

        # Reload course data into the table
        self.course_data = get_course_data(cursor)
        self.populate_course_table(self.course_data)  # Refresh course table

        # Refresh student data in the table
        self.load_student_data()  # Refresh student table     
        self.scroll_position = 0  

        # Create cursor
        self.cursor = connection.cursor()
        self.connection = connection


    def init_ui(self):
        # Create buttons
        self.toggle_button = QPushButton("Switch to Courses")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)  # By default, show student data
        self.toggle_button.toggled.connect(self.toggle_data)
        self.layout.addWidget(self.toggle_button)

        self.add_button = QPushButton("Add New Student")
        self.add_button.clicked.connect(self.add_student_dialog)  # Initially set to add student
        self.quit_button = QPushButton("Quit")

        # Add buttons to layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.quit_button)
        self.layout.addLayout(button_layout)

        # Connect button signals to slots
        self.quit_button.clicked.connect(self.close)

        # Initialize student table
        self.student_table = QTableWidget()
        self.student_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layout.addWidget(self.student_table)
        self.load_student_data()  # Corrected line

        # Add search components
        self.search_line_edit = QLineEdit()
        self.search_line_edit.setPlaceholderText("Search...")
        self.search_line_edit.returnPressed.connect(self.search_students)
        self.search_criteria_combo = QComboBox()
        self.search_criteria_combo.addItems(STUDENT_FIELDS)
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_students)

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_line_edit)
        search_layout.addWidget(self.search_criteria_combo)
        search_layout.addWidget(self.search_button)
        self.layout.addLayout(search_layout)

        # Connect signal to slot
        self.signal.course_added.connect(self.load_course_data)  # Connect signal to reload course data

        # Initially hide the course management buttons
        if hasattr(self, 'student_table'):
            self.hide_course_table_buttons(True)
        
        # Apply styles
        self.apply_styles()
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 8px 12px;
            font-size: 14px;
            margin: 1px;
            border-radius: 12px;
            min-width: 80px; /* Ensures button width adjusts to text */
            min-height: 15px; /* Ensures enough height for the text */
            font-family: Arial, sans-serif; /* Consistent font */
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3e8e41; /* Darker shade when pressed */
        }
            QLineEdit, QComboBox {
                padding: 10px;
                margin: 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #ddd;
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)


    def create_connection(self):
        try:
            connection = mysql.connector.connect(
                host=HOST,
                user=USER,
                password=PASSWORD,
                database=DATABASE
            )
            if connection.is_connected():
                return connection
        except Exception as e:
            print(f"Error: {e}")
        return None
    
    def reconnect(self):
        self.connection = self.create_connection()
        if self.connection:
            self.cursor = self.connection.cursor()

    def closeEvent(self, event):
        """Override close event to ensure proper closing of database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        event.accept()
        
    def search_courses(self):
        """Search for courses based on the selected criteria."""
        query = self.search_line_edit.text().strip().lower()
        criteria = self.search_criteria_combo.currentText()

        if not query:
            self.load_course_data()  # Reload all course data if query is empty
            return

        filtered_courses = []
        sql_query = ""

        if criteria == 'Course Code':
            sql_query = "SELECT * FROM courses WHERE LOWER(course_code) LIKE %s"
        elif criteria == 'Course Name':
            sql_query = "SELECT * FROM courses WHERE LOWER(course_name) LIKE %s"

        try:
            self.cursor.execute(sql_query, ('%' + query + '%',))
            filtered_courses = self.cursor.fetchall()
            
            if not filtered_courses:
                QMessageBox.information(self, "No Results", "No courses found matching the search criteria.")
            else:
                self.populate_course_table(filtered_courses)  # Update table with filtered results
        except mysql.connector.Error as e:
            # Show error message in the UI
            QMessageBox.critical(self, "Error", "An error occurred while searching courses: " + str(e))

    def search_students(self):
        """Search for students based on the selected criteria."""
        query = self.search_line_edit.text().strip().upper()  # Convert query to uppercase
        criteria = self.search_criteria_combo.currentText()

        if not query:
            self.load_student_data()  # Reload all student data if query is empty
            return

        sql_query = ""

        if criteria == 'First Name':
            sql_query = "SELECT * FROM students WHERE first_name LIKE %s"
        elif criteria == 'Middle Initial':
            sql_query = "SELECT * FROM students WHERE middle_initial LIKE %s"
        elif criteria == 'Last Name':
            sql_query = "SELECT * FROM students WHERE last_name LIKE %s"
        elif criteria == 'ID':
            sql_query = "SELECT * FROM students WHERE id_value LIKE %s"
        elif criteria == 'Year Level':
            sql_query = "SELECT * FROM students WHERE year_level LIKE %s"
        elif criteria == 'Gender':
            gender_query = 'Male' if query in ['M', 'MALE'] else 'Female' if query in ['F', 'FEMALE'] else query
            sql_query = "SELECT * FROM students WHERE gender = %s"

        try:
            if criteria != 'Gender':
                wildcard_query = f"%{query}%"
                self.cursor.execute(sql_query, (wildcard_query,))
            else:
                self.cursor.execute(sql_query, (gender_query,))  # For gender search, use the mapped value

            rows = self.cursor.fetchall()

            if not rows:
                QMessageBox.information(self, "No Results", "No students found matching the search criteria.")

            self.populate_student_table(rows)  # Update table with filtered results

        except mysql.connector.errors.ProgrammingError as e:
            if e.errno == 2055:  # Cursor is not connected
                self.reconnect()
                if criteria != 'Gender':
                    wildcard_query = f"%{query}%"
                    self.cursor.execute(sql_query, (wildcard_query,))
                else:
                    self.cursor.execute(sql_query, (gender_query,))  # For gender search, use the mapped value

                rows = self.cursor.fetchall()

                if not rows:
                    QMessageBox.information(self, "No Results", "No students found matching the search criteria.")
                else:
                    self.populate_student_table(rows)  # Update table with filtered results
            else:
                raise


    def matches_search_criteria(self, student_data, criteria, query):
        """Check if a student matches the search criteria."""
        data_value = student_data[self.get_field_index(criteria)].lower()

        if criteria == 'ID':
            # Check if query is an exact match or substring of the ID (case-insensitive)
            return query.lower() in data_value
        elif criteria == 'Name':
            # Check if query is a substring of any part of the name (Last Name, First Name, Middle Initial)
            name_parts = [part.strip().lower() for part in student_data[0].split(',')]
            return any(query.lower() in part for part in name_parts)
        elif criteria == 'Gender':
            # Check if the query matches the gender (case-insensitive)
            return query.lower() == data_value
        else:
            # Check if query is a substring of the specified criteria (case-insensitive)
            return query.lower() in data_value


    def get_field_index(self, criteria):
        """Get the index of the field based on the criteria."""
        fields = ['First Name', 'Middle Initial', 'Last Name', 'ID', 'Year Level', 'Gender', 'Course Code']
        return fields.index(criteria)

    def populate_student_table(self, students_data):
        self.student_table.clear()  # Clear existing data
        num_columns = len(STUDENT_FIELDS) + 3  # Additional columns for 'Status', 'Update', and 'Delete'
        self.student_table.setColumnCount(num_columns)
        self.student_table.setRowCount(len(students_data))

        headers = STUDENT_FIELDS + ["Status", "Action", "Action"]
        self.student_table.setHorizontalHeaderLabels(headers)

        for i, row_data in enumerate(students_data):
            for j, cell in enumerate(row_data):
                item = QTableWidgetItem(str(cell))  # Ensure cell content is converted to string
                self.student_table.setItem(i, j, item)

            # Compute status based on course code (index 6 is the course code column)
            course_code = row_data[6]
            if course_code is not None and course_code.strip().lower() != "none":
                status = "Enrolled"
            else:
                status = "Unenrolled"

            # Add status item to the 'Status' column
            status_item = QTableWidgetItem(status)
            self.student_table.setItem(i, len(STUDENT_FIELDS), status_item)

            # Add update button
            update_button = QPushButton("Update")
            update_button.clicked.connect(lambda _, row=i: self.update_student_dialog(row))
            self.student_table.setCellWidget(i, len(STUDENT_FIELDS) + 1, update_button)

            # Add delete button
            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda _, row=i: self.confirm_delete_student(row))
            self.student_table.setCellWidget(i, len(STUDENT_FIELDS) + 2, delete_button)

        # Hide update and delete buttons for course entries
        self.update_delete_buttons_visibility(False)

        
    def update_delete_buttons_visibility(self, course_view):
        """Hide or show the update and delete buttons based on the view."""
        if hasattr(self, 'student_table'):
            num_cols = self.student_table.columnCount()
            for i in range(self.student_table.rowCount()):
                update_button = self.student_table.cellWidget(i, num_cols - 2)
                delete_button = self.student_table.cellWidget(i, num_cols - 1)
                if course_view:
                    # Show course update and delete buttons
                    if update_button:
                        update_button.setVisible(True)
                    if delete_button:
                        delete_button.setVisible(True)
                else:
                    # Hide course update and delete buttons
                    if update_button:
                        update_button.setVisible(False)
                    if delete_button:
                        delete_button.setVisible(False)


    def load_student_data(self):
        """Load student data into the table with 'Status' column."""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.reconnect()

            with self.connection.cursor() as cursor:
                cursor.execute("SELECT first_name, middle_initial, last_name, id_value, year_level, gender, course_code FROM students")
                data = cursor.fetchall()
                students_data = self.compute_student_status(data, self.course_data)
                self.populate_student_table(students_data)
        except mysql.connector.Error as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load student data: {str(e)}")



    def compute_student_status(self, data, course_data):
        """Compute the 'Status' (Enrolled/Unenrolled) based on the course."""
        students_data = []
        valid_course_codes = [course[0] for course in course_data]
        for row in data:
            if len(row) >= 7:
                first_name, middle_initial, last_name, id_value, year_level, gender, course_code = row
                if course_code is not None and course_code.strip().lower() != "none":
                    status = "Enrolled"
                else:
                    status = "Unenrolled"
                students_data.append([first_name, middle_initial, last_name, id_value, year_level, gender, course_code, status])
            else:
                print(f"Skipping row due to insufficient data: {row}")
        return students_data

    def populate_course_table(self, course_data):
        """Populate the course table with data and dynamically resize columns."""
        num_rows = len(course_data)
        num_cols = len(COURSE_FIELDS) + 2  # Additional columns for 'Update' and 'Delete'

        self.student_table.clear()  # Clear existing data
        self.student_table.setRowCount(num_rows)
        self.student_table.setColumnCount(num_cols)
        headers = COURSE_FIELDS + ["Update", "Delete"]
        self.student_table.setHorizontalHeaderLabels(headers)

        # Populate table data and determine initial column widths
        column_widths = [0] * num_cols
        for i, row in enumerate(course_data):
            for j, cell in enumerate(row):
                item = QTableWidgetItem(str(cell))  # Ensure cell content is converted to string
                self.student_table.setItem(i, j, item)

                # Update column width based on content length
                column_widths[j] = max(column_widths[j], len(str(cell)) * 10)  # Adjust multiplier as needed

            # Add 'Update' button
            update_button = QPushButton("Update")
            update_button.clicked.connect(lambda _, idx=i: self.update_course_dialog(idx))
            self.student_table.setCellWidget(i, num_cols - 2, update_button)

            # Add 'Delete' button
            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda _, idx=i: self.confirm_delete_course(idx))
            self.student_table.setCellWidget(i, num_cols - 1, delete_button)

        # Set column widths based on calculated maximums
        for col in range(num_cols):
            self.student_table.setColumnWidth(col, column_widths[col])

        # Set horizontal header resize mode to stretch last section
        header = self.student_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Resize columns to fit content
        self.resize_columns_to_fit()


    def toggle_data(self, checked):
        """Toggle between student data and course data."""
        if checked:
            self.toggle_button.setText("Switch to Students")
            self.load_course_data()
            self.add_button.setText("Add New Course")
            self.add_button.clicked.disconnect(self.add_student_dialog)
            self.add_button.clicked.connect(self.add_course_dialog)
            if hasattr(self, 'student_table'):
                self.hide_student_table_buttons(True)  # Hide student table buttons
                self.hide_course_table_buttons(False)  # Show course table buttons

                # Ensure course table is populated and visible
                self.load_course_data()  # Load data when switching to course view
                self.student_table.show()
                self.student_table.setVisible(True)

            # Change search criteria for course view
            self.search_criteria_combo.clear()
            self.search_criteria_combo.addItems(COURSE_FIELDS)
            self.search_button.clicked.disconnect(self.search_students)
            self.search_button.clicked.connect(self.search_courses)
        else:
            self.toggle_button.setText("Switch to Courses")
            self.load_student_data()
            self.add_button.setText("Add New Student")
            self.add_button.clicked.disconnect(self.add_course_dialog)
            self.add_button.clicked.connect(self.add_student_dialog)
            if hasattr(self, 'student_table'):
                self.hide_student_table_buttons(False)  # Show student table buttons
                self.hide_course_table_buttons(True)  # Hide course table buttons

            # Change search criteria for student view
            self.search_criteria_combo.clear()
            self.search_criteria_combo.addItems(STUDENT_FIELDS)
            self.search_button.clicked.disconnect(self.search_courses)
            self.search_button.clicked.connect(self.search_students)



    def resize_columns_to_fit(self):
        """Resize each column in the table to fit its content."""
        header = self.student_table.horizontalHeader()
        for col in range(self.student_table.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
    
    def hide_student_table_buttons(self, hide):
        """Hide or show the update and delete buttons in the student data table."""
        if hasattr(self, 'student_table'):
            num_columns = self.student_table.columnCount()
            for i in range(self.student_table.rowCount()):
                for j in range(num_columns - 2, num_columns):
                    item = self.student_table.cellWidget(i, j)
                    if item:
                        item.setVisible(not hide)

    def hide_course_table_buttons(self, hide):
        """Hide or show the update and delete buttons in the course data table."""
        if hasattr(self, 'student_table'):
            num_columns = self.student_table.columnCount()
            for i in range(self.student_table.rowCount()):
                update_button = self.student_table.cellWidget(i, num_columns - 2)
                delete_button = self.student_table.cellWidget(i, num_columns - 1)
                if update_button:
                    update_button.setVisible(not hide)
                if delete_button:
                    delete_button.setVisible(not hide)

    def load_course_data(self):
        """Retrieve course data from the MySQL database."""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.reconnect()

            with self.connection.cursor() as cursor:
                cursor.execute("SELECT course_code, course_name FROM courses")
                self.course_data = cursor.fetchall()
                self.populate_course_table(self.course_data)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load course data: {str(e)}")


    def add_student_dialog(self):
        """Open dialog to add a new student."""
        dialog = AddStudentDialog(parent=self, course_data=self.course_data, connection=self.connection)
        if dialog.exec_():
            student_data = dialog.get_student_data()
            if self.confirm_action("Add Student"):
                try:
                    # Reconnect if necessary
                    self.connection.ping(reconnect=True)
                    # Insert student data into the database
                    self.cursor.execute("""
                        INSERT INTO students (first_name, middle_initial, last_name, id_value, year_level, gender, course_code)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, student_data)
                    self.connection.commit()
                    # Reload student data into the table
                    self.load_student_data()
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Error", f"Failed to add student: {str(e)}")

    def add_course_dialog(self):
        """Open dialog to add a new course."""
        if self.connection is None or not self.connection.is_connected():
            self.reconnect()
        dialog = AddCourseDialog(parent=self, connection=self.connection)
        if dialog.exec_():
            course_data = dialog.get_course_data()
            try:
                # Reconnect if necessary
                self.connection.ping(reconnect=True)
                self.cursor = self.connection.cursor()  # Ensure cursor is re-created after reconnecting
                # Insert course data into the database
                self.cursor.execute("""
                    INSERT INTO courses (course_code, course_name)
                    VALUES (%s, %s)
                """, course_data)
                self.connection.commit()
                # Reload course data into the table
                self.load_course_data()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to add course: {str(e)}")


    def update_course_dialog(self, row):
        """Open dialog to update course information."""
        if self.connection is None or not self.connection.is_connected():
            self.reconnect()

        dialog = UpdateCourseDialog(parent=self, row=row, connection=self.connection)
        if dialog.exec_():
            updated_course_data = dialog.get_updated_course_data()
            old_course_code = self.course_data[row][0]
            new_course_code = updated_course_data[0]
            new_course_name = updated_course_data[1]

            try:
                with self.connection.cursor() as cursor:
                    # Check if the new course code already exists in the courses table
                    cursor.execute("SELECT * FROM courses WHERE course_code = %s", (new_course_code,))
                    if cursor.fetchone():
                        raise ValueError(f"Course code '{new_course_code}' already exists in the courses table.")

                    # Check if there's an ongoing transaction
                    cursor.execute("SELECT @@autocommit")
                    autocommit_status = cursor.fetchone()[0]
                    if autocommit_status == 1:
                        # Start a transaction only if not in autocommit mode
                        self.connection.start_transaction()

                    # Update course code and course name in the courses table first
                    cursor.execute("""
                        UPDATE courses
                        SET course_code = %s, course_name = %s
                        WHERE course_code = %s
                    """, (new_course_code, new_course_name, old_course_code))
                    print(f"Updated courses table with new course_code {new_course_code} and new course_name {new_course_name}.")

                    # Update course code in the students table
                    cursor.execute("""
                        UPDATE students
                        SET course_code = %s
                        WHERE course_code = %s
                    """, (new_course_code, old_course_code))
                    print(f"Updated students table with new course_code {new_course_code}.")

                    # Commit the transaction if it was started in this block
                    if autocommit_status == 1:
                        self.connection.commit()
                        print("Transaction committed.")

                    self.load_course_data()
                    QtWidgets.QMessageBox.information(self, "Success", "Course updated successfully.")
            except mysql.connector.Error as e:
                self.connection.rollback()
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to update course: {str(e)}")
                print(f"Error: {str(e)}")
            except ValueError as ve:
                self.connection.rollback()
                QtWidgets.QMessageBox.warning(self, "Warning", str(ve))
                print(f"Warning: {str(ve)}")
            except Exception as ex:
                self.connection.rollback()
                QtWidgets.QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(ex)}")
                print(f"Unexpected Error: {str(ex)}")
            finally:
                cursor.close()


    def update_student_dialog(self, row):
        """Open dialog to update student information."""
        dialog = UpdateStudentDialog(parent=self, row=row, course_data=self.course_data, connection=self.connection)
        if dialog.exec_():
            updated_student_data = dialog.get_updated_student_data()
            try:
                # Reconnect if necessary
                self.connection.ping(reconnect=True)
                # Update student data in the database
                self.cursor.execute("""
                    UPDATE students
                    SET first_name = %s, middle_initial = %s, last_name = %s, id_value = %s,
                        year_level = %s, gender = %s, course_code = %s
                    WHERE id_value = %s
                """, updated_student_data + (self.student_table.item(row, 3).text(),))
                self.connection.commit()
                # Reload student data into the table
                self.load_student_data()
                # Show confirmation pop-up
                QtWidgets.QMessageBox.information(self, "Success", "Student updated successfully!")
            except mysql.connector.Error as e:
                if e.errno in (mysql.connector.errorcode.ER_ROW_IS_REFERENCED_2, mysql.connector.errorcode.ER_NO_REFERENCED_ROW_2):
                    # Suppress specific foreign key constraint error message
                    print("Suppressed error message: Foreign key constraint issue.")
                else:
                    QtWidgets.QMessageBox.critical(self, "Error", f"Failed to update student: {str(e)}")

    def confirm_action(self, action_name):
        """Confirm an action before proceeding."""
        self.load_student_data()  # Reload student data after adding a student
        return False

    def confirm_delete_student(self, row):
        """Confirm deletion of a student."""
        reply = QMessageBox.question(self, 'Delete Student', 'Are you sure you want to delete this student?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.delete_student(row)

    def delete_student(self, row):
        """Delete a student from the database."""
        student_id = self.student_table.item(row, 3).text()  # Assuming ID is in the 4th column

        try:
            connection = self.connection
            cursor = connection.cursor()
            cursor.execute("DELETE FROM students WHERE id_value = %s", (student_id,))
            connection.commit()  # Commit the transaction
            self.load_student_data()  # Reload student data
            QMessageBox.information(self, "Success", "Student successfully deleted.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to delete student: {str(e)}")
        finally:
            cursor.close()  # Close the cursor

    def confirm_delete_course(self, row):
        """Confirm deletion of a course."""
        reply = QMessageBox.question(self, 'Delete Course', 'Are you sure you want to delete this course?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.delete_course(row)

    def delete_course(self, row):
        """Delete a course from the database."""
        try:
            course_code = self.course_data[row][0]  # Assuming Course Code is in the 1st column
            self.connection.ping(reconnect=True)

            with self.connection.cursor() as cursor:
                # Update the course_code in students table to NULL for the course being deleted
                cursor.execute("UPDATE students SET course_code = NULL WHERE course_code = %s", (course_code,))

                # Delete the course from courses table
                cursor.execute("DELETE FROM courses WHERE course_code = %s", (course_code,))

            # Commit the transaction
            self.connection.commit()

            # Reload course data to reflect the deletion
            self.load_course_data()

            # Refresh student data in the background without switching view
            #self.load_student_data()

            QMessageBox.information(self, "Success", "Course successfully deleted.")
        except Exception as e:
            self.connection.rollback()  # Rollback the transaction in case of error
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to delete course: {str(e)}")


def main():
    app = QApplication([])
    window = StudentManagementApp()
    window.show()
    app.exec_()

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = StudentManagementApp()
    window.show()
    sys.exit(app.exec_())
    