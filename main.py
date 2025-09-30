import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd 

# --- 1. Database Manager Class ---
class DatabaseManager:
    """Handles all SQLite database operations for grade records."""
    def __init__(self, db_name='performance_tracker.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        """Creates the 'grades' table with necessary fields, including new student info."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                email TEXT,
                class TEXT,
                division TEXT,
                roll_number TEXT,
                subject TEXT NOT NULL,
                score REAL NOT NULL
            )
        """)
        self.conn.commit()

    def add_grade(self, student_name, email, student_class, division, roll_number, subject, score):
        """Inserts a new grade record with all associated student details."""
        try:
            self.cursor.execute(
                "INSERT INTO grades (student_name, email, class, division, roll_number, subject, score) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (student_name, email, student_class, division, roll_number, subject, score)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Database error while adding grade: {e}")
            return False

    def get_all_grades(self):
        """Retrieves all grade records, including all student details."""
        self.cursor.execute("SELECT id, student_name, email, class, division, roll_number, subject, score FROM grades ORDER BY id DESC")
        return self.cursor.fetchall()

    def get_filtered_grades(self, search_term):
        """Retrieves grades filtered by student name (case-insensitive)."""
        search_pattern = f"%{search_term}%"
        self.cursor.execute("SELECT id, student_name, email, class, division, roll_number, subject, score FROM grades WHERE student_name LIKE ? ORDER BY id DESC", (search_pattern,))
        return self.cursor.fetchall()

    def get_average_grades_by_subject(self):
        """Calculates and returns the average score for each subject."""
        self.cursor.execute("SELECT subject, AVG(score) FROM grades GROUP BY subject")
        return self.cursor.fetchall()

    def get_summary_stats(self):
        """Calculates and returns total grades entered, overall average score, and unique students."""
        self.cursor.execute("SELECT COUNT(id), AVG(score) FROM grades")
        count, avg = self.cursor.fetchone()
        
        self.cursor.execute("SELECT COUNT(DISTINCT student_name) FROM grades")
        unique_students = self.cursor.fetchone()[0]
        
        return count or 0, avg or 0.0, unique_students or 0

    def close(self):
        """Closes the database connection safely."""
        self.conn.close()

# --- 2. Tkinter GUI Application Class ---
class PerformanceTrackerApp(tk.Tk):
    """Main application window using Tkinter for performance tracking and visualization."""
    def __init__(self):
        super().__init__()
        self.title("Student Performance Tracker | Modern Dashboard")
        self.geometry("1200x800")
        self.db = DatabaseManager()
        self.configure(bg='#f0f8ff') # Light background color

        # Configure grid for a responsive two-panel layout
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=3) 
        self.grid_rowconfigure(0, weight=1)

        # Initialize tracking variables for KPIs
        self.total_records_var = tk.StringVar(value='0')
        self.overall_avg_var = tk.StringVar(value='0.0 %')
        self.unique_students_var = tk.StringVar(value='0')
        self.search_term_var = tk.StringVar()
        self.search_term_var.trace_add("write", lambda name, index, mode: self.load_grades(self.search_term_var.get()))

        self._create_styles()
        self._create_widgets()
        self.load_grades() 

    def _create_styles(self):
        """Custom styles for Treeview and other components."""
        style = ttk.Style(self)
        style.theme_use('clam') 

        # Style for the Treeview headings
        style.configure("Treeview.Heading", 
                        font=('Arial', 11, 'bold'), 
                        background='#0056b3', # Primary accent color (Darker Blue)
                        foreground='white', 
                        relief="flat")
        
        # Style for the Treeview rows
        style.configure("Treeview", 
                        font=('Arial', 10),
                        rowheight=30,
                        fieldbackground='#ffffff')
        
        # Style for selected row
        style.map('Treeview', 
                  background=[('selected', '#007bff')],
                  foreground=[('selected', 'white')])
        
        # Style for input fields
        style.configure('TEntry', fieldbackground='#f8f9fa')
        style.map('TEntry', fieldbackground=[('focus', '#e9ecef')])


    def _create_widgets(self):
        """Initializes and places all GUI elements."""
        
        # --- Left Panel: Grade Input (Clean) ---
        input_frame = tk.Frame(self, padx=25, pady=25, bg='#ffffff', bd=0, relief=tk.FLAT)
        input_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_columnconfigure(1, weight=2)

        tk.Label(input_frame, 
                 text="New Performance Record", 
                 font=('Arial', 16, 'bold'), 
                 bg='#ffffff', 
                 fg='#343a40').grid(row=0, column=0, columnspan=2, pady=(0, 25))

        # Helper function for input rows
        def create_input_row(parent, label_text, row):
            tk.Label(parent, text=label_text, font=('Arial', 11), bg='#ffffff', fg='#555555', anchor='w').grid(
                row=row, column=0, sticky='w', pady=(8, 2), padx=(5, 10))
            entry = tk.Entry(parent, width=30, bd=1, relief=tk.SOLID, font=('Arial', 11), fg='#343a40', highlightthickness=1, highlightcolor='#ced4da')
            entry.grid(row=row, column=1, pady=(8, 2), padx=5, sticky='ew')
            return entry

        # --- Student Details Group ---
        student_group = tk.LabelFrame(input_frame, text="Student Details", font=('Arial', 12, 'bold'), bg='#ffffff', fg='#007bff', padx=10, pady=10, bd=1, relief=tk.SOLID)
        student_group.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(5, 15))
        student_group.grid_columnconfigure(0, weight=1)
        student_group.grid_columnconfigure(1, weight=2)

        self.name_entry = create_input_row(student_group, "Student Name:", 0)
        self.email_entry = create_input_row(student_group, "Email ID:", 1)
        self.class_entry = create_input_row(student_group, "Class:", 2)
        self.division_entry = create_input_row(student_group, "Division:", 3)
        self.roll_entry = create_input_row(student_group, "Roll Number:", 4)
        
        # --- Subject Details Group ---
        subject_group = tk.LabelFrame(input_frame, text="Subject & Score", font=('Arial', 12, 'bold'), bg='#ffffff', fg='#20c997', padx=10, pady=10, bd=1, relief=tk.SOLID)
        subject_group.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(15, 15))
        subject_group.grid_columnconfigure(0, weight=1)
        subject_group.grid_columnconfigure(1, weight=2)

        self.subject_entry = create_input_row(subject_group, "Subject:", 0)
        self.score_entry = create_input_row(subject_group, "Score (0-100):", 1)


        # Add Grade Button (Primary Action)
        tk.Button(input_frame, text="SAVE GRADE RECORD", command=self.add_grade, 
                  bg='#007bff', fg='white', font=('Arial', 12, 'bold'), 
                  activebackground='#0056b3', relief=tk.FLAT, bd=0, padx=15, pady=10).grid(
                      row=3, column=0, columnspan=2, pady=(25, 10), sticky='ew', padx=10
                  )

        # Generate Chart Button (Secondary Action)
        tk.Button(input_frame, text="VISUALIZE SUBJECT AVERAGES", command=self.generate_chart,
                  bg='#20c997', fg='white', font=('Arial', 12, 'bold'), 
                  activebackground='#17a2b8', relief=tk.FLAT, bd=0, padx=15, pady=10).grid(
                      row=4, column=0, columnspan=2, pady=10, sticky='ew', padx=10
                  )


        # --- Right Panel: Data View and Chart (Dashboard View) ---
        data_viz_frame = tk.Frame(self, bg='#e9ecef', bd=0, relief=tk.FLAT)
        data_viz_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        data_viz_frame.grid_rowconfigure(2, weight=1) # Treeview/Chart row
        data_viz_frame.grid_columnconfigure(0, weight=1)

        # 2a. KPI Cards Frame
        kpi_frame = tk.Frame(data_viz_frame, bg='#e9ecef', padx=5, pady=10)
        kpi_frame.grid(row=0, column=0, sticky='ew', columnspan=2)
        kpi_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        def create_kpi_card(parent, title, var, bg_color, col):
            card = tk.Frame(parent, bg=bg_color, padx=15, pady=15, bd=1, relief=tk.FLAT)
            card.grid(row=0, column=col, sticky='ew', padx=10)
            tk.Label(card, text=title, font=('Arial', 10), fg='white', bg=bg_color).pack(pady=(0, 5))
            tk.Label(card, textvariable=var, font=('Arial', 20, 'bold'), fg='white', bg=bg_color).pack()
        
        create_kpi_card(kpi_frame, "Total Records", self.total_records_var, '#17a2b8', 0)
        create_kpi_card(kpi_frame, "Overall Avg Score", self.overall_avg_var, '#20c997', 1)
        create_kpi_card(kpi_frame, "Unique Students", self.unique_students_var, '#ffc107', 2)

        # 2b. Search and Title
        header_frame = tk.Frame(data_viz_frame, bg='#e9ecef', pady=10)
        header_frame.grid(row=1, column=0, sticky='ew')
        header_frame.grid_columnconfigure(0, weight=1)
        
        tk.Label(header_frame, text="Student Data & Recent Grades", 
                 font=('Arial', 14, 'bold'), 
                 bg='#e9ecef', fg='#2c3e50').grid(row=0, column=0, sticky='w')
        
        tk.Entry(header_frame, textvariable=self.search_term_var, font=('Arial', 10), 
                 relief=tk.SOLID, bd=1, width=30, highlightthickness=1, 
                 highlightcolor='#ced4da', fg='#343a40').grid(row=0, column=1, sticky='e', padx=(10, 5))
        tk.Label(header_frame, text="Search by Name:", font=('Arial', 10), bg='#e9ecef', fg='#555555').grid(row=0, column=1, sticky='w', padx=(0, 200)) # Placeholder for better positioning


        # 2c. Data Table and Chart Container
        table_chart_frame = tk.Frame(data_viz_frame, bg='#ffffff', bd=1, relief=tk.SOLID)
        table_chart_frame.grid(row=2, column=0, sticky='nsew', padx=10, pady=10)
        table_chart_frame.grid_columnconfigure(0, weight=1)
        table_chart_frame.grid_columnconfigure(1, weight=1)
        table_chart_frame.grid_rowconfigure(0, weight=1)

        # Treeview setup 
        tree_container = tk.Frame(table_chart_frame, bg='#ffffff')
        tree_container.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        tree_container.grid_columnconfigure(0, weight=1)
        tree_container.grid_rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_container, columns=('ID', 'Student', 'Email', 'Class', 'Div', 'Roll', 'Subject', 'Score'), show='headings')
        
        # Column headings and widths
        for col in ['ID', 'Student', 'Email', 'Class', 'Div', 'Roll', 'Subject', 'Score']:
            self.tree.heading(col, text=col.replace("Div", "Div.").replace("Roll", "Roll No.").replace("Score", "Score %"), anchor=tk.CENTER if col in ['ID', 'Class', 'Div', 'Roll', 'Score'] else tk.W)

        self.tree.column('ID', width=30, anchor=tk.CENTER, stretch=tk.NO)
        self.tree.column('Student', width=120, stretch=tk.YES)
        self.tree.column('Email', width=180, stretch=tk.YES)
        self.tree.column('Class', width=60, anchor=tk.CENTER, stretch=tk.NO)
        self.tree.column('Div', width=50, anchor=tk.CENTER, stretch=tk.NO)
        self.tree.column('Roll', width=70, anchor=tk.CENTER, stretch=tk.NO)
        self.tree.column('Subject', width=100, stretch=tk.YES)
        self.tree.column('Score', width=70, anchor=tk.CENTER, stretch=tk.NO)

        self.tree.grid(row=0, column=0, sticky='nsew')
        
        # Scrollbar for Treeview
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Matplotlib Chart Area Container
        self.chart_frame = tk.Frame(table_chart_frame, bg='#ffffff', bd=0, relief=tk.FLAT)
        self.chart_frame.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)
        self.chart_frame.grid_columnconfigure(0, weight=1)
        self.chart_frame.grid_rowconfigure(0, weight=1)
        
        self.chart_canvas = None
        self.generate_chart(placeholder=True)

    # --- 3. Application Logic Methods ---
    
    def update_kpi_cards(self):
        """Fetches and updates the Key Performance Indicator (KPI) values."""
        total_records, overall_avg, unique_students = self.db.get_summary_stats()
        
        self.total_records_var.set(f'{total_records}')
        
        if overall_avg > 0:
            self.overall_avg_var.set(f'{overall_avg:.1f} %')
        else:
            self.overall_avg_var.set('0.0 %')
            
        self.unique_students_var.set(f'{unique_students}')

    def add_grade(self):
        """Validates input and inserts a new grade record into the database."""
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        student_class = self.class_entry.get().strip()
        division = self.division_entry.get().strip()
        roll_number = self.roll_entry.get().strip()

        subject = self.subject_entry.get().strip()
        score_str = self.score_entry.get().strip()

        if not name or not student_class or not division or not subject or not score_str:
            messagebox.showerror("Input Error", "Name, Class, Division, Subject, and Score are required fields.")
            return

        try:
            score = float(score_str)
            if not (0 <= score <= 100):
                messagebox.showerror("Input Error", "Score must be a numerical value between 0 and 100.")
                return
        except ValueError:
            messagebox.showerror("Input Error", "Score must be a valid number.")
            return

        if self.db.add_grade(name, email, student_class, division, roll_number, subject, score):
            messagebox.showinfo("Success", f"Record for {name} added.")
            
            # Clear fields and refresh data
            self.name_entry.delete(0, tk.END)
            self.email_entry.delete(0, tk.END)
            self.roll_entry.delete(0, tk.END)
            self.subject_entry.delete(0, tk.END)
            self.score_entry.delete(0, tk.END)
            self.name_entry.focus()
            
            self.load_grades()
            self.generate_chart() 
        else:
            messagebox.showerror("Database Error", "Failed to save record.")

    def load_grades(self, search_term=""):
        """Clears and reloads all grade data into the TreeView table, with optional filtering."""
        
        # Update KPIs first
        self.update_kpi_cards()
        
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if search_term:
            grades = self.db.get_filtered_grades(search_term)
        else:
            grades = self.db.get_all_grades()
            
        for grade in grades:
            if len(grade) == 8:
                formatted_score = f"{grade[7]:.1f}"
                formatted_grade = grade[:7] + (formatted_score,)
                self.tree.insert('', tk.END, values=formatted_grade)

    def generate_chart(self, placeholder=False):
        """Generates a Matplotlib bar chart of subject averages and embeds it in Tkinter."""
        
        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()
            plt.close('all') 

        plt.style.use('ggplot') 
        fig, ax = plt.subplots(figsize=(6, 5))

        if placeholder:
            ax.text(0.5, 0.5, "Press 'VISUALIZE SUBJECT AVERAGES'\n to view performance chart.", 
                    ha='center', va='center', fontsize=12, color='#7f8c8d')
            ax.set_title("Performance Visualization Area")
            ax.axis('off')
            fig.patch.set_facecolor('#ffffff')
        else:
            avg_grades = self.db.get_average_grades_by_subject()
            if not avg_grades:
                messagebox.showinfo("Chart Info", "Not enough data. Add some grades first!")
                self.generate_chart(placeholder=True) 
                return
            
            subjects = [item[0] for item in avg_grades]
            averages = [item[1] for item in avg_grades]

            colors = plt.cm.tab10(range(len(subjects)))
            
            bars = ax.bar(subjects, averages, color=colors)
            
            ax.set_title('Subject Average Scores (%)', fontsize=16, color='#343a40')
            ax.set_ylabel('Average Score', fontsize=12, color='#555555')
            ax.set_ylim(0, 100) 
            ax.tick_params(axis='x', rotation=30)
            ax.tick_params(axis='both', which='major', labelsize=10)

            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., 
                        height + 2,
                        f'{height:.1f}',
                        ha='center', 
                        va='bottom',
                        fontsize=10, 
                        fontweight='bold',
                        color='#343a40')
            
            fig.tight_layout() 

        # Embed the Matplotlib figure into the Tkinter frame
        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def on_closing(self):
        """Handles cleanup (closing the DB connection) when the app is closed."""
        try:
            self.db.close()
        except Exception as e:
            print(f"Error during database closure: {e}")
        self.destroy()

# --- 4. Application Execution ---
if __name__ == "__main__":
    app = PerformanceTrackerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing) 
    app.mainloop()

