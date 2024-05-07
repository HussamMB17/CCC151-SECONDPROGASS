from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QWidget, QComboBox, QHeaderView
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox
from PyQt5.QtCore import pyqtSignal
import csv
import re
import mysql.connector
from mysql.connector import Error

# MySQL database credentials
HOST = 'localhost'
USER = 'root'
PASSWORD = '7h!ns=cY96NF'
DATABASE = 'ssis'

STUDENT_FIELDS = ['Name', 'ID', 'Year Level', 'Gender', 'Course Code', 'Course Name']
COURSE_FIELDS = ['Course Code', 'Course Name']

def create_connection(host, user, password, database):
    """Create a connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        if connection.is_connected():
            print("Connected to MySQL database")
            return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

class AddStudentDialog(QDialog):
    def __init__(self, parent=None, course_data=None):
        super().__init__(parent)
        self.setWindowTitle("Add Student")
        self.setGeometry(200, 200, 400, 350)

        self.course_data = course_data
        self.original_scroll_position = None  # Variable to store the scroll position

        layout = QVBoxLayout(self)

        self.first_name_edit = QLineEdit()
        self.middle_initial_edit = QLineEdit()
        self.last_name_edit = QLineEdit()
        self.id_edit = QLineEdit()

        layout.addWidget(QLabel("First Name (Ex. John/Johnny Depp):"))
        layout.addWidget(self.first_name_edit)
        layout.addWidget(QLabel("Middle Initial (Ex. A.):"))
        layout.addWidget(self.middle_initial_edit)
        layout.addWidget(QLabel("Last Name (Ex. Doe):"))
        layout.addWidget(self.last_name_edit)
        layout.addWidget(QLabel("ID (Ex. 2022-0101):"))
        layout.addWidget(self.id_edit)

        self.year_level_combo = QComboBox()
        self.year_level_combo.addItems(['1', '2', '3', '4'])
        layout.addWidget(QLabel("Year Level:"))
        layout.addWidget(self.year_level_combo)

        self.gender_combo = QComboBox()
        self.gender_combo.addItems(['Male', 'Female'])
        layout.addWidget(QLabel("Gender:"))
        layout.addWidget(self.gender_combo)

        self.course_combo = QComboBox()
        self.course_combo.addItem('None')
        for course_code, course_name in self.course_data:
            self.course_combo.addItem(course_code)
        layout.addWidget(QLabel("Course Code:"))
        layout.addWidget(self.course_combo)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_data)
        layout.addWidget(self.submit_button)

        # Capture the current scroll position before showing the dialog
        if parent and hasattr(parent, 'student_table'):
            self.original_scroll_position = parent.student_table.verticalScrollBar().value()

    def submit_data(self):
        """Submit student data to the MySQL database."""
        id_value = self.id_edit.text()  # Get ID from QLineEdit widget
        first_name = self.first_name_edit.text()
        middle_initial = self.middle_initial_edit.text()
        last_name = self.last_name_edit.text()
        year_level = self.year_level_combo.currentText()
        gender = self.gender_combo.currentText()
        course_code = self.course_combo.currentText()

        # Prepare student data in the correct order for MySQL insertion
        student_data = (first_name, middle_initial, last_name, id_value, year_level, gender, course_code)

        # Validate student data
        if self.validate_student_data(student_data):
            # Check if ID is already used
            if self.is_duplicate_id(id_value):
                QMessageBox.warning(self, "Error", "ID already exists. Please enter a unique ID.")
                return

            # Establish connection to the MySQL database
            connection = create_connection(HOST, USER, PASSWORD, DATABASE)
            if connection:
                try:
                    cursor = connection.cursor()
                    # Insert student data into the database
                    insert_query = """
                        INSERT INTO students (first_name, middle_initial, last_name, id_value, year_level, gender, course_code)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, student_data)
                    connection.commit()
                    QMessageBox.information(self, "Success", "Student added successfully.")
                    # Close the dialog
                    self.accept()
                except Error as e:
                    QMessageBox.warning(self, "Error", f"Error occurred: {str(e)}")
                finally:
                    # Close the database connection
                    if connection.is_connected():
                        cursor.close()
                        connection.close()
        else:
            QMessageBox.warning(self, "Error", "Please enter valid data.")

    def validate_student_data(self, student_data):
        """Validate student data."""
        first_name, middle_initial, last_name, id_value, year_level, gender, course_code = student_data

        # Check if required fields are not empty
        if not first_name or not middle_initial or not last_name or not id_value:
            return False

        # Validate first name format
        if not self.validate_name_format(first_name):
            return False

        # Validate last name format
        if not self.validate_name_format(last_name):
            return False

        # Validate middle initial format: One uppercase letter followed by a period
        if len(middle_initial) != 2 or not middle_initial[0].isupper() or middle_initial[1] != '.':
            return False

        # Validate ID format: XXXX-XXXX where X is a digit (0-9)
        if not re.match(r'^\d{4}-\d{4}$', id_value):
            return False

        return True

    def validate_name_format(self, name):
        """Validate name format: Each part starts with an uppercase letter followed by lowercase letters."""
        parts = name.split()
        for part in parts:
            if len(part) < 1 or not part[0].isupper() or not part[1:].islower():
                return False
        return True

    def is_duplicate_id(self, id_value):
        """Check if the ID already exists in the student database."""
        try:
            connection = create_connection(HOST, USER, PASSWORD, DATABASE)
            if connection:
                cursor = connection.cursor()
                # Execute a SELECT query to check for the existence of the ID
                select_query = "SELECT id_value FROM students WHERE id_value = %s"
                cursor.execute(select_query, (id_value,))
                result = cursor.fetchone()
                if result:
                    return True  # ID already exists
        except Error as e:
            print(f"Error checking for duplicate ID: {e}")
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
        return False  # ID does not exist or an error occurred
    
    def get_student_data(self):
        """Get student data from the dialog."""
        first_name = self.first_name_edit.text()
        middle_initial = self.middle_initial_edit.text()
        last_name = self.last_name_edit.text()
        id_value = self.id_edit.text()
        year_level = self.year_level_combo.currentText()
        gender = self.gender_combo.currentText()
        course_code = self.course_combo.currentText()

        return first_name, middle_initial, last_name, id_value, year_level, gender, course_code


class AddCourseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Course")
        self.setGeometry(200, 200, 400, 200)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.fields = []
        for field in COURSE_FIELDS:
            label = QLabel(field)
            edit = QLineEdit()
            layout.addWidget(label)
            layout.addWidget(edit)
            self.fields.append(edit)

        self.submit_button = QPushButton("Submit")
        layout.addWidget(self.submit_button)
        self.submit_button.clicked.connect(self.submit_data)

    def submit_data(self):
        """Submit course data."""
        course_data = [field.text() for field in self.fields]

        # Validate course data
        if self.validate_course_data(course_data):
            try:
                connection = create_connection(HOST, USER, PASSWORD, DATABASE)
                if connection:
                    cursor = connection.cursor()
                    # Insert course data into the database
                    insert_query = """
                        INSERT INTO courses (course_code, course_name)
                        VALUES (%s, %s)
                    """
                    cursor.execute(insert_query, course_data)
                    connection.commit()
                    QMessageBox.information(self, "Success", "Course added successfully.")
                    if self.parent():
                        if hasattr(self.parent(), 'signal'):
                            self.parent().signal.course_added.emit()  # Emit signal after adding a course
                    self.close()
            except Error as e:
                QMessageBox.warning(self, "Error", f"Error occurred: {str(e)}")
            finally:
                if connection and connection.is_connected():
                    cursor.close()
                    connection.close()
        else:
            QMessageBox.warning(self, "Error", "Please enter valid data.")

    def validate_course_data(self, course_data):
        """Validate course data."""
        # You can add your validation logic here
        return True


class UpdateStudentDialog(QDialog):
    def __init__(self, parent=None, row=None, course_data=None):
        super().__init__(parent)
        self.setWindowTitle("Update Student")
        self.setGeometry(200, 200, 400, 350)

        self.row = row
        self.course_data = course_data
        self.original_scroll_position = None  # Variable to store the scroll position

        layout = QVBoxLayout(self)

        # Add fields for ID, first name, middle initial, last name
        self.first_name_edit = QLineEdit()
        self.middle_initial_edit = QLineEdit()
        self.last_name_edit = QLineEdit()
        self.id_edit = QLineEdit()

        layout.addWidget(QLabel("First Name (Ex. John/Johnny Depp):"))
        layout.addWidget(self.first_name_edit)
        layout.addWidget(QLabel("Middle Initial (Ex. A.):"))
        layout.addWidget(self.middle_initial_edit)
        layout.addWidget(QLabel("Last Name (Ex. Doe):"))
        layout.addWidget(self.last_name_edit)
        layout.addWidget(QLabel("ID:"))
        layout.addWidget(self.id_edit)

        # Add existing student fields (Year Level, Gender, Course)
        self.fields = []
        for field in ["Year Level", "Gender", "Course Code"]:
            label = QLabel(field)
            combo_box = QComboBox()
            if field == "Year Level":
                combo_box.addItems(['1', '2', '3', '4'])  # Restrict options to 1, 2, 3, 4
            elif field == "Gender":
                combo_box.addItems(['Male', 'Female'])  # Restrict options to Male and Female
            elif field == "Course Code":
                combo_box.addItem('None')
                for course_code in self.course_data:
                    combo_box.addItem(course_code[0])  # Add course name
            layout.addWidget(label)
            layout.addWidget(combo_box)
            self.fields.append(combo_box)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_data)
        layout.addWidget(self.submit_button)

        # Pre-fill the dialog with existing student data
        self.populate_fields()

        # Capture the current scroll position before showing the dialog
        if parent and hasattr(parent, 'student_table'):
            self.original_scroll_position = parent.student_table.verticalScrollBar().value()

    def populate_fields(self):
        """Populate dialog fields with existing student data."""
        if self.row is not None:
            # Get data from the main window's student table
            first_name = self.parent().student_table.item(self.row, 0).text()  # First Name
            middle_initial = self.parent().student_table.item(self.row, 1).text()  # Middle Initial
            last_name = self.parent().student_table.item(self.row, 2).text()  # Last Name
            id_value = self.parent().student_table.item(self.row, 3).text()  # ID
            year_level = self.parent().student_table.item(self.row, 4).text()  # Year Level
            gender = self.parent().student_table.item(self.row, 5).text()  # Gender
            course_code = self.parent().student_table.item(self.row, 6).text()  # Course Code

            # Populate the dialog fields
            self.first_name_edit.setText(first_name)
            self.middle_initial_edit.setText(middle_initial)
            self.last_name_edit.setText(last_name)
            self.id_edit.setText(id_value)

            # Disable editing for the ID field
            self.id_edit.setEnabled(False)

            year_level_index = self.fields[0].findText(year_level)  # Year Level
            if year_level_index != -1:
                self.fields[0].setCurrentIndex(year_level_index)

            gender_index = self.fields[1].findText(gender)  # Gender
            if gender_index != -1:
                self.fields[1].setCurrentIndex(gender_index)

            course_index = self.fields[2].findText(course_code)  # Course Code
            if course_index != -1:
                self.fields[2].setCurrentIndex(course_index)

    def validate_student_data(self, student_data):
        """Validate updated student data."""
        first_name, middle_initial, last_name, id_value, year_level, gender, course_code = student_data

        # Check if required fields are not empty
        if not first_name or not middle_initial or not last_name:
            return False

        # Validate first name format
        if not self.validate_name_format(first_name):
            return False

        # Validate last name format
        if not self.validate_name_format(last_name):
            return False

        # Validate middle initial format: One uppercase letter followed by a period
        if len(middle_initial) != 2 or not middle_initial[0].isupper() or middle_initial[1] != '.':
            return False

        # Add more validation rules as needed...

        return True

    def validate_name_format(self, name):
        """Validate name format: Each part starts with an uppercase letter followed by lowercase letters."""
        parts = name.split()
        for part in parts:
            if len(part) < 1 or not part[0].isupper() or not part[1:].islower():
                return False
        return True

    def submit_data(self):
        """Submit updated student data."""
        id_value = self.id_edit.text()  # Get ID from QLineEdit widget
        first_name = self.first_name_edit.text()
        middle_initial = self.middle_initial_edit.text()
        last_name = self.last_name_edit.text()
        year_level = self.fields[0].currentText()
        gender = self.fields[1].currentText()
        course_code = self.fields[2].currentText()

        # Prepare updated student data in the correct order for CSV writing
        updated_student_data = [first_name, middle_initial, last_name, id_value, year_level, gender, course_code]

        # Validate all updated student data
        if self.validate_student_data(updated_student_data):
            try:
                connection = create_connection(HOST, USER, PASSWORD, DATABASE)
                if connection:
                    cursor = connection.cursor()
                    # Update student data in the database
                    update_query = """
                        UPDATE students
                        SET first_name = %s,
                            middle_initial = %s,
                            last_name = %s,
                            year_level = %s,
                            gender = %s,
                            course_code = %s
                        WHERE id = %s
                    """
                    cursor.execute(update_query, (first_name, middle_initial, last_name, year_level, gender, course_code, id_value))
                    connection.commit()
                    QMessageBox.information(self, "Success", "Student updated successfully.")
                    self.accept()  # Close the dialog after successful update

                    # Restore the scroll position after closing the dialog
                    if self.parent() and hasattr(self.parent(), 'student_table'):
                        self.parent().student_table.verticalScrollBar().setValue(self.original_scroll_position)
            except Error as e:
                QMessageBox.warning(self, "Error", f"Error occurred: {str(e)}")
            finally:
                if connection and connection.is_connected():
                    cursor.close()
                    connection.close()
        else:
            QMessageBox.warning(self, "Error", "Please enter valid data.")

class UpdateCourseDialog(QDialog):
    def __init__(self, parent=None, row=None):
        super().__init__(parent)
        self.setWindowTitle("Update Course")
        self.setGeometry(200, 200, 400, 200)

        self.row = row

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.fields = []
        for i, field in enumerate(COURSE_FIELDS):
            label = QLabel(field)
            edit = QLineEdit()
            layout.addWidget(label)
            layout.addWidget(edit)
            self.fields.append(edit)
            edit.setText(parent.student_table.item(self.row, i).text())

        self.submit_button = QPushButton("Submit")
        layout.addWidget(self.submit_button)
        self.submit_button.clicked.connect(self.submit_data)

    def submit_data(self):
        """Submit updated course data."""
        updated_data = [field.text() for field in self.fields]

        # Validate updated data
        if self.validate_course_data(updated_data):
            try:
                connection = create_connection(HOST, USER, PASSWORD, DATABASE)
                if connection:
                    cursor = connection.cursor()
                    # Update course data in the database
                    update_query = """
                        UPDATE courses
                        SET course_name = %s
                        WHERE course_code = %s
                    """
                    cursor.execute(update_query, (updated_data[1], updated_data[0]))
                    connection.commit()
                    QMessageBox.information(self, "Success", "Course updated successfully.")
                    self.parent().load_course_data()  # Reload data in main window
                    self.close()
            except Error as e:
                QMessageBox.warning(self, "Error", f"Error occurred: {str(e)}")
            finally:
                if connection and connection.is_connected():
                    cursor.close()
                    connection.close()
        else:
            QMessageBox.warning(self, "Error", "Please enter valid data.")

    def validate_course_data(self, course_data):
        """Validate updated course data."""
        # You can add your validation logic here
        return True