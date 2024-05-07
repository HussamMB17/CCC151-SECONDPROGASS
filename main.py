from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QWidget, QComboBox, QHeaderView
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtCore import Qt
import csv
import re
from dialogs import AddStudentDialog, UpdateStudentDialog, AddCourseDialog, UpdateCourseDialog
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
        self.signal.course_added.connect(self.load_course_data)

        # Initially hide the course management buttons
        if hasattr(self, 'student_table'):
            self.hide_course_table_buttons(True)

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
            sql_query = "SELECT * FROM courses WHERE course_code LIKE %s"
        elif criteria == 'Course Name':
            sql_query = "SELECT * FROM courses WHERE course_name LIKE %s"

        cursor.execute(sql_query, ('%' + query + '%',))
        for row in cursor.fetchall():
            filtered_courses.append(row)

        self.populate_course_table(filtered_courses)  # Update table with filtered results


    def search_students(self):
        """Search for students based on the selected criteria."""
        query = self.search_line_edit.text().strip().upper()  # Convert query to uppercase
        criteria = self.search_criteria_combo.currentText()

        if not query:
            self.load_student_data()  # Reload all student data if query is empty
            return

        filtered_students = []
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
            # Special case for gender search
            if query in ['M', 'MALE']:
                gender_query = 'Male'
            elif query in ['F', 'FEMALE']:
                gender_query = 'Female'
            else:
                gender_query = query  # Assume it's already Male or Female
            sql_query = "SELECT * FROM students WHERE gender = %s"

        if criteria != 'Gender':
            wildcard_query = f"%{query}%"
            cursor.execute(sql_query, (wildcard_query,))
        else:
            cursor.execute(sql_query, (gender_query,))  # For gender search, use the mapped value

        rows = cursor.fetchall()

        self.populate_student_table(rows)  # Update table with filtered results

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
        """Populate the student table with data including the 'Status' column."""
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
            course_code = row_data[6].strip().lower()
            if course_code != "none":
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
        cursor.execute("SELECT first_name, middle_initial, last_name, id_value, year_level, gender, course_code FROM students")
        data = cursor.fetchall()
        students_data = self.compute_student_status(data, self.course_data)
        self.populate_student_table(students_data)


    def compute_student_status(self, data, course_data):
        """Compute the 'Status' (Enrolled/Unenrolled) based on the course."""
        students_data = []
        valid_course_codes = [course[0] for course in course_data]
        for row in data:
            if len(row) >= 7:
                first_name, middle_initial, last_name, id_value, year_level, gender, course_code = row
                if course_code.strip().lower() != "none":
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
                self.populate_course_table(self.course_data)
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
        self.course_data = get_course_data(cursor)

    def add_student_dialog(self):
        """Open dialog to add a new student."""
        dialog = AddStudentDialog(self, self.course_data)
        if dialog.exec_():
            # Get student data from the dialog
            student_data = dialog.get_student_data()

            # Insert student data into the database
            self.cursor.execute("""
                INSERT INTO students (first_name, middle_initial, last_name, id_value, year_level, gender, course_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, student_data)
            self.connection.commit()

            # Reload student data into the table
            self.load_student_data()

    def add_course_dialog(self):
        """Open dialog to add a new course."""
        dialog = AddCourseDialog(self)
        if dialog.exec_():
            # Get course data from the dialog
            course_data = dialog.get_course_data()

            # Insert course data into the database
            self.cursor.execute("""
                INSERT INTO courses (course_code, course_name)
                VALUES (%s, %s)
            """, course_data)
            self.connection.commit()

            # Reload course data into the table
            self.load_course_data()

    def update_course_dialog(self, row):
        """Open dialog to update course information."""
        dialog = UpdateCourseDialog(self, row)
        if dialog.exec_():
            # Get updated course data from the dialog
            updated_course_data = dialog.get_updated_course_data()

            # Update course data in the database
            self.db_cursor.execute("""
                UPDATE courses
                SET course_code = %s, course_name = %s
                WHERE course_code = %s
            """, updated_course_data + (self.course_data[row][0],))
            self.connection.commit()

            # Reload course data into the table
            self.load_course_data()

    def update_student_dialog(self, row):
        """Open dialog to update student information."""
        dialog = UpdateStudentDialog(self, row, self.course_data)
        if dialog.exec_():
            # Get updated student data from the dialog
            updated_student_data = dialog.get_updated_student_data()

            # Update student data in the database
            self.cursor.execute("""
                UPDATE students
                SET first_name = %s, middle_initial = %s, last_name = %s,
                    id_value = %s, year_level = %s, gender = %s, course_code = %s
                WHERE id_value = %s
            """, updated_student_data + (self.student_table.item(row, 3).text(),))
            self.connection.commit()

            # Reload student data into the table
            self.load_student_data()

    def confirm_delete_student(self, row):
        """Confirm deletion of a student."""
        reply = QMessageBox.question(self, 'Delete Student', 'Are you sure you want to delete this student?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.delete_student(row)

    def delete_student(self, row):
        """Delete a student from the database."""
        student_id = self.student_table.item(row, 3).text()  # Assuming ID is in the 4th column
        cursor.execute("DELETE FROM students WHERE id_value = %s", (student_id,))
        connection.commit()  # Commit the transaction
        self.load_student_data()  # Reload student data

    def confirm_delete_course(self, row):
        """Confirm deletion of a course."""
        reply = QMessageBox.question(self, 'Delete Course', 'Are you sure you want to delete this course?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.delete_course(row)

    def delete_course(self, row):
        """Delete a course from the database."""
        course_code = self.student_table.item(row, 0).text()  # Assuming Course Code is in the 1st column
        cursor.execute("DELETE FROM courses WHERE course_code = %s", (course_code,))
        connection.commit()  # Commit the transaction
        self.load_course_data()  # Reload course data

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
    