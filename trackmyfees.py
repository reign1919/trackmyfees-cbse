# ============================================================
#  TrackMyFees -- Fee Tracker
#  Developed by : Akshat R. Chowdhury, Trishaan Saha,
#                 Sashmit Guin  (XII-A)
#  Language     : Python 3.x
#  Database     : MySQL 8.0
#  Interface    : Menu-driven CLI
# ============================================================

import mysql.connector
from mysql.connector import Error
from datetime import date, datetime


# --------------------------------------------------
#  CONFIGURATION  -- change password if needed
# --------------------------------------------------
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "tiger"       # <-- set your MySQL root password here
DB_NAME = "trackmyfees"


# --------------------------------------------------
#  DATABASE CONNECTION
# --------------------------------------------------

def connect():
    """Return a live MySQL connection, or None on failure."""
    try:
        con = mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME
        )
        return con
    except Error as e:
        print(f"\n  [DB ERROR] {e}\n")
        return None


# --------------------------------------------------
#  ONE-TIME SETUP
# --------------------------------------------------

def setup_database():
    """Creates DB and tables if they do not already exist."""
    try:
        con = mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASS
        )
        cur = con.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS trackmyfees")
        cur.execute("USE trackmyfees")

        cur.execute(
            "CREATE TABLE IF NOT EXISTS courses ("
            "  course_id   INT           AUTO_INCREMENT PRIMARY KEY,"
            "  course_name VARCHAR(100)  NOT NULL,"
            "  subject     VARCHAR(100)  NOT NULL,"
            "  tutor_name  VARCHAR(100)  NOT NULL,"
            "  monthly_fee DECIMAL(10,2) NOT NULL"
            ")"
        )

        cur.execute(
            "CREATE TABLE IF NOT EXISTS students ("
            "  student_id INT          AUTO_INCREMENT PRIMARY KEY,"
            "  name       VARCHAR(100) NOT NULL,"
            "  class      VARCHAR(20)  NOT NULL,"
            "  contact    VARCHAR(15)  NOT NULL,"
            "  course_id  INT          NOT NULL,"
            "  join_date  DATE         NOT NULL,"
            "  FOREIGN KEY (course_id) REFERENCES courses(course_id)"
            "    ON DELETE RESTRICT"
            ")"
        )

        cur.execute(
            "CREATE TABLE IF NOT EXISTS payments ("
            "  payment_id   INT           AUTO_INCREMENT PRIMARY KEY,"
            "  student_id   INT           NOT NULL,"
            "  amount_paid  DECIMAL(10,2) NOT NULL,"
            "  payment_date DATE          NOT NULL,"
            "  fee_month    VARCHAR(20)   NOT NULL,"
            "  remarks      VARCHAR(200)  DEFAULT '',"
            "  FOREIGN KEY (student_id) REFERENCES students(student_id)"
            "    ON DELETE CASCADE"
            ")"
        )

        con.commit()
        con.close()
        print("  Database ready.\n")
    except Error as e:
        print(f"\n  [SETUP ERROR] {e}")
        print("  Make sure MySQL is running and credentials are correct.\n")
        exit(1)


# --------------------------------------------------
#  UTILITY HELPERS
# --------------------------------------------------

DIV = "=" * 60

def heading(title):
    print(f"\n{DIV}\n  {title.upper()}\n{DIV}")

def pause():
    input("\n  Press ENTER to return to menu...")

def get_int(prompt, minimum=1):
    while True:
        try:
            val = int(input(prompt))
            if val >= minimum:
                return val
            print(f"  Enter a number >= {minimum}.")
        except ValueError:
            print("  Invalid. Enter a whole number.")

def get_float(prompt, minimum=0.01):
    while True:
        try:
            val = float(input(prompt))
            if val >= minimum:
                return val
            print(f"  Amount must be >= {minimum}.")
        except ValueError:
            print("  Invalid. Enter a number (e.g. 1500 or 1500.50).")

def get_date(prompt):
    while True:
        raw = input(prompt).strip()
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            print("  Format: YYYY-MM-DD  (e.g. 2025-04-01)")


# --------------------------------------------------
#  MODULE 1 -- COURSE / FEE STRUCTURE
# --------------------------------------------------

def add_course():
    heading("Add New Course / Subject")
    con = connect()
    if not con:
        return
    cur = con.cursor()
    name    = input("  Course / Batch name   : ").strip()
    subject = input("  Subject               : ").strip()
    tutor   = input("  Tutor name            : ").strip()
    fee     = get_float("  Monthly fee (Rs.)     : ")
    cur.execute(
        "INSERT INTO courses (course_name, subject, tutor_name, monthly_fee) VALUES (%s,%s,%s,%s)",
        (name, subject, tutor, fee)
    )
    con.commit()
    print(f"\n  Course '{name}' added. ID = {cur.lastrowid}")
    con.close()
    pause()


def view_courses(pause_after=True):
    heading("All Courses")
    con = connect()
    if not con:
        return
    cur = con.cursor()
    cur.execute("SELECT * FROM courses ORDER BY course_id")
    rows = cur.fetchall()
    con.close()
    if not rows:
        print("  No courses found.")
    else:
        print(f"  {'ID':<5} {'Course':<20} {'Subject':<18} {'Tutor':<18} {'Monthly Fee':>12}")
        print("  " + "-" * 60)
        for r in rows:
            print(f"  {r[0]:<5} {r[1]:<20} {r[2]:<18} {r[3]:<18} {float(r[4]):>12.2f}")
    if pause_after:
        pause()


def delete_course():
    heading("Delete Course")
    view_courses(pause_after=False)
    con = connect()
    if not con:
        return
    cur = con.cursor()
    cid = get_int("  Enter Course ID to delete : ")
    cur.execute("SELECT course_name FROM courses WHERE course_id=%s", (cid,))
    row = cur.fetchone()
    if not row:
        print("  Course not found.")
        con.close()
        pause()
        return
    confirm = input(f"  Delete '{row[0]}'? (yes/no) : ").strip().lower()
    if confirm == "yes":
        try:
            cur.execute("DELETE FROM courses WHERE course_id=%s", (cid,))
            con.commit()
            print("  Course deleted.")
        except Error as e:
            print(f"  Cannot delete: {e}")
    else:
        print("  Cancelled.")
    con.close()
    pause()


# --------------------------------------------------
#  MODULE 2 -- STUDENT MANAGEMENT
# --------------------------------------------------

def add_student():
    heading("Register New Student")
    view_courses(pause_after=False)
    con = connect()
    if not con:
        return
    cur = con.cursor()
    name    = input("  Student name          : ").strip()
    cls     = input("  Class (e.g. XI, XII)  : ").strip()
    contact = input("  Contact number        : ").strip()
    cid     = get_int("  Course ID             : ")
    cur.execute("SELECT course_id FROM courses WHERE course_id=%s", (cid,))
    if not cur.fetchone():
        print("  Invalid Course ID.")
        con.close()
        pause()
        return
    jdate = get_date("  Join date (YYYY-MM-DD): ")
    cur.execute(
        "INSERT INTO students (name, class, contact, course_id, join_date) VALUES (%s,%s,%s,%s,%s)",
        (name, cls, contact, cid, jdate)
    )
    con.commit()
    print(f"\n  Student '{name}' registered. ID = {cur.lastrowid}")
    con.close()
    pause()


def view_students(pause_after=True):
    heading("All Students")
    con = connect()
    if not con:
        return
    cur = con.cursor()
    cur.execute(
        "SELECT s.student_id, s.name, s.class, s.contact,"
        "       c.course_name, c.subject, c.tutor_name, c.monthly_fee, s.join_date"
        " FROM students s"
        " JOIN courses c ON s.course_id = c.course_id"
        " ORDER BY s.student_id"
    )
    rows = cur.fetchall()
    con.close()
    if not rows:
        print("  No students registered.")
    else:
        print(f"  {'ID':<5} {'Name':<20} {'Cl':<5} {'Contact':<14}"
              f" {'Course':<15} {'Tutor':<15} {'Monthly Fee':>12}")
        print("  " + "-" * 90)
        for r in rows:
            print(f"  {r[0]:<5} {r[1]:<20} {r[2]:<5} {r[3]:<14}"
                  f" {r[4]:<15} {r[6]:<15} {float(r[7]):>12.2f}")
    if pause_after:
        pause()


def search_student():
    heading("Search Student")
    keyword = input("  Enter name, ID, or subject/course keyword : ").strip()
    con = connect()
    if not con:
        return
    cur = con.cursor()
    if keyword.isdigit():
        cur.execute(
            "SELECT s.student_id, s.name, s.class, s.contact,"
            "       c.course_name, c.subject, c.tutor_name, c.monthly_fee, s.join_date"
            " FROM students s JOIN courses c ON s.course_id=c.course_id"
            " WHERE s.student_id=%s", (int(keyword),)
        )
    else:
        like = f"%{keyword}%"
        cur.execute(
            "SELECT s.student_id, s.name, s.class, s.contact,"
            "       c.course_name, c.subject, c.tutor_name, c.monthly_fee, s.join_date"
            " FROM students s JOIN courses c ON s.course_id=c.course_id"
            " WHERE s.name LIKE %s OR c.course_name LIKE %s OR c.subject LIKE %s",
            (like, like, like)
        )
    rows = cur.fetchall()
    con.close()
    if not rows:
        print("  No records found.")
    else:
        print(f"  {'ID':<5} {'Name':<20} {'Cl':<5} {'Contact':<14}"
              f" {'Course':<15} {'Tutor':<15} {'Monthly Fee':>12}")
        print("  " + "-" * 90)
        for r in rows:
            print(f"  {r[0]:<5} {r[1]:<20} {r[2]:<5} {r[3]:<14}"
                  f" {r[4]:<15} {r[6]:<15} {float(r[7]):>12.2f}")
    pause()


def update_student():
    heading("Update Student Record")
    view_students(pause_after=False)
    con = connect()
    if not con:
        return
    cur = con.cursor()
    sid = get_int("  Enter Student ID to update : ")
    cur.execute("SELECT student_id, name, class, contact FROM students WHERE student_id=%s", (sid,))
    row = cur.fetchone()
    if not row:
        print("  Student not found.")
        con.close()
        pause()
        return
    print(f"\n  Current Name    : {row[1]}")
    print(f"  Current Class   : {row[2]}")
    print(f"  Current Contact : {row[3]}")
    print("  (Press ENTER to keep existing value)")
    name    = input("  New name    : ").strip() or row[1]
    cls     = input("  New class   : ").strip() or row[2]
    contact = input("  New contact : ").strip() or row[3]
    cur.execute(
        "UPDATE students SET name=%s, class=%s, contact=%s WHERE student_id=%s",
        (name, cls, contact, sid)
    )
    con.commit()
    print("  Record updated.")
    con.close()
    pause()


def delete_student():
    heading("Delete Student")
    view_students(pause_after=False)
    con = connect()
    if not con:
        return
    cur = con.cursor()
    sid = get_int("  Enter Student ID to delete : ")
    cur.execute("SELECT name FROM students WHERE student_id=%s", (sid,))
    row = cur.fetchone()
    if not row:
        print("  Student not found.")
        con.close()
        pause()
        return
    confirm = input(
        f"  Delete '{row[0]}' and ALL their payment records? (yes/no) : "
    ).strip().lower()
    if confirm == "yes":
        cur.execute("DELETE FROM students WHERE student_id=%s", (sid,))
        con.commit()
        print("  Student deleted.")
    else:
        print("  Cancelled.")
    con.close()
    pause()


# --------------------------------------------------
#  MODULE 3 -- PAYMENTS
# --------------------------------------------------

def record_payment():
    heading("Record Fee Payment")
    view_students(pause_after=False)
    con = connect()
    if not con:
        return
    cur = con.cursor()
    sid = get_int("  Enter Student ID : ")
    cur.execute(
        "SELECT s.name, c.monthly_fee FROM students s"
        " JOIN courses c ON s.course_id=c.course_id WHERE s.student_id=%s", (sid,)
    )
    row = cur.fetchone()
    if not row:
        print("  Student not found.")
        con.close()
        pause()
        return
    print(f"\n  Student     : {row[0]}")
    print(f"  Monthly Fee : Rs. {float(row[1]):.2f}")
    amount  = get_float("  Amount paid (Rs.)         : ")
    pdate   = get_date( "  Payment date (YYYY-MM-DD)  : ")
    month   = input(    "  Fee month (e.g. April 2025): ").strip()
    remarks = input(    "  Remarks (optional)         : ").strip()
    cur.execute(
        "INSERT INTO payments (student_id, amount_paid, payment_date, fee_month, remarks)"
        " VALUES (%s,%s,%s,%s,%s)",
        (sid, amount, pdate, month, remarks)
    )
    con.commit()
    pid = cur.lastrowid
    con.close()
    # Receipt
    print(f"\n  {'-'*48}")
    print("           PAYMENT RECEIPT")
    print(f"  {'-'*48}")
    print(f"  Receipt No.  : {pid}")
    print(f"  Student      : {row[0]}")
    print(f"  Fee Month    : {month}")
    print(f"  Amount Paid  : Rs. {amount:.2f}")
    print(f"  Payment Date : {pdate}")
    if remarks:
        print(f"  Remarks      : {remarks}")
    print(f"  {'-'*48}")
    pause()


def view_payment_history():
    heading("Payment History")
    view_students(pause_after=False)
    con = connect()
    if not con:
        return
    cur = con.cursor()
    sid = get_int("  Enter Student ID : ")
    cur.execute(
        "SELECT s.name, c.course_name, c.subject, c.tutor_name, c.monthly_fee"
        " FROM students s JOIN courses c ON s.course_id=c.course_id"
        " WHERE s.student_id=%s", (sid,)
    )
    info = cur.fetchone()
    if not info:
        print("  Student not found.")
        con.close()
        pause()
        return
    cur.execute(
        "SELECT payment_id, fee_month, amount_paid, payment_date, remarks"
        " FROM payments WHERE student_id=%s ORDER BY payment_date", (sid,)
    )
    rows = cur.fetchall()
    con.close()
    print(f"\n  Student    : {info[0]}")
    print(f"  Course     : {info[1]}  ({info[2]})  |  Tutor: {info[3]}")
    print(f"  Monthly Fee: Rs. {float(info[4]):.2f}\n")
    if not rows:
        print("  No payment records found.")
    else:
        total = 0.0
        print(f"  {'Rec#':<6} {'Month':<18} {'Amount':>10} {'Date':<14} Remarks")
        print("  " + "-" * 68)
        for r in rows:
            total += float(r[2])
            print(f"  {r[0]:<6} {r[1]:<18} {float(r[2]):>10.2f} {str(r[3]):<14} {r[4]}")
        print("  " + "-" * 68)
        print(f"  {'TOTAL PAID':>35} : Rs. {total:.2f}")
    pause()


def delete_payment():
    heading("Delete Payment Record")
    con = connect()
    if not con:
        return
    cur = con.cursor()
    sid = get_int("  Enter Student ID : ")
    cur.execute(
        "SELECT payment_id, fee_month, amount_paid, payment_date FROM payments"
        " WHERE student_id=%s ORDER BY payment_date", (sid,)
    )
    rows = cur.fetchall()
    if not rows:
        print("  No payment records for this student.")
        con.close()
        pause()
        return
    print(f"\n  {'Rec#':<6} {'Month':<18} {'Amount':>10} {'Date'}")
    print("  " + "-" * 50)
    for r in rows:
        print(f"  {r[0]:<6} {r[1]:<18} {float(r[2]):>10.2f} {r[3]}")
    pid = get_int("  Enter Receipt # to delete : ")
    cur.execute(
        "SELECT payment_id FROM payments WHERE payment_id=%s AND student_id=%s", (pid, sid)
    )
    if not cur.fetchone():
        print("  Record not found.")
        con.close()
        pause()
        return
    confirm = input("  Confirm delete? (yes/no) : ").strip().lower()
    if confirm == "yes":
        cur.execute("DELETE FROM payments WHERE payment_id=%s", (pid,))
        con.commit()
        print("  Payment deleted.")
    else:
        print("  Cancelled.")
    con.close()
    pause()


def reprint_receipt():
    heading("Reprint Receipt")
    pid = get_int("  Enter Receipt # : ")
    con = connect()
    if not con:
        return
    cur = con.cursor()
    cur.execute(
        "SELECT p.payment_id, s.name, c.course_name, c.subject,"
        "       c.tutor_name, p.fee_month, p.amount_paid, p.payment_date, p.remarks"
        " FROM payments p"
        " JOIN students s ON p.student_id=s.student_id"
        " JOIN courses  c ON s.course_id=c.course_id"
        " WHERE p.payment_id=%s", (pid,)
    )
    r = cur.fetchone()
    con.close()
    if not r:
        print("  Receipt not found.")
    else:
        print(f"\n  {'-'*48}")
        print("           PAYMENT RECEIPT")
        print(f"  {'-'*48}")
        print(f"  Receipt No.  : {r[0]}")
        print(f"  Student      : {r[1]}")
        print(f"  Course       : {r[2]}  ({r[3]})")
        print(f"  Tutor        : {r[4]}")
        print(f"  Fee Month    : {r[5]}")
        print(f"  Amount Paid  : Rs. {float(r[6]):.2f}")
        print(f"  Payment Date : {r[7]}")
        if r[8]:
            print(f"  Remarks      : {r[8]}")
        print(f"  {'-'*48}")
    pause()


# --------------------------------------------------
#  MODULE 4 -- REPORTS
# --------------------------------------------------

def pending_dues():
    heading("Pending Dues -- All Students")
    con = connect()
    if not con:
        return
    cur = con.cursor()
    today = date.today()
    cur.execute(
        "SELECT s.student_id, s.name, c.tutor_name, c.monthly_fee, s.join_date"
        " FROM students s JOIN courses c ON s.course_id=c.course_id ORDER BY s.student_id"
    )
    students = cur.fetchall()
    if not students:
        print("  No students found.")
        con.close()
        pause()
        return
    print(f"\n  {'ID':<5} {'Name':<20} {'Tutor':<15}"
          f" {'Expected':>10} {'Paid':>10} {'Balance':>10}")
    print("  " + "-" * 74)
    g_exp = g_paid = 0.0
    for s in students:
        sid, name, tutor, mfee, jdate = s
        months = (today.year - jdate.year) * 12 + (today.month - jdate.month) + 1
        expected = float(mfee) * months
        cur.execute(
            "SELECT COALESCE(SUM(amount_paid),0) FROM payments WHERE student_id=%s", (sid,)
        )
        paid = float(cur.fetchone()[0])
        bal  = expected - paid
        g_exp  += expected
        g_paid += paid
        flag = "  *** DUES ***" if bal > 0 else ""
        print(f"  {sid:<5} {name:<20} {tutor:<15}"
              f" {expected:>10.2f} {paid:>10.2f} {bal:>10.2f}{flag}")
    print("  " + "-" * 74)
    print(f"  {'TOTAL':<41} {g_exp:>10.2f} {g_paid:>10.2f} {g_exp-g_paid:>10.2f}")
    con.close()
    pause()


def defaulter_list():
    heading("Defaulter List")
    threshold = get_float("  Show defaulters with dues above Rs. : ", minimum=0)
    con = connect()
    if not con:
        return
    cur = con.cursor()
    today = date.today()
    cur.execute(
        "SELECT s.student_id, s.name, s.class, s.contact,"
        "       c.tutor_name, c.monthly_fee, s.join_date"
        " FROM students s JOIN courses c ON s.course_id=c.course_id"
    )
    students = cur.fetchall()
    defaulters = []
    for s in students:
        sid, name, cls, contact, tutor, mfee, jdate = s
        months   = (today.year - jdate.year)*12 + (today.month - jdate.month) + 1
        expected = float(mfee) * months
        cur.execute(
            "SELECT COALESCE(SUM(amount_paid),0) FROM payments WHERE student_id=%s", (sid,)
        )
        paid = float(cur.fetchone()[0])
        bal  = expected - paid
        if bal > threshold:
            defaulters.append((sid, name, cls, contact, tutor, bal))
    con.close()
    if not defaulters:
        print(f"\n  No defaulters with dues above Rs. {threshold:.2f}")
    else:
        print(f"\n  Defaulters with dues > Rs. {threshold:.2f}\n")
        print(f"  {'ID':<5} {'Name':<20} {'Cl':<5} {'Contact':<14} {'Tutor':<15} {'Balance':>10}")
        print("  " + "-" * 73)
        for d in defaulters:
            print(f"  {d[0]:<5} {d[1]:<20} {d[2]:<5} {d[3]:<14} {d[4]:<15} {d[5]:>10.2f}")
        print(f"\n  Total defaulters : {len(defaulters)}")
    pause()


def fee_summary():
    heading("Fee Collection Summary")
    print("  Leave blank to show ALL records.")
    raw_from = input("  From date (YYYY-MM-DD) : ").strip()
    raw_to   = input("  To   date (YYYY-MM-DD) : ").strip()
    con = connect()
    if not con:
        return
    cur = con.cursor()
    params = []
    where  = ""
    if raw_from and raw_to:
        where, params = "WHERE p.payment_date BETWEEN %s AND %s", [raw_from, raw_to]
    elif raw_from:
        where, params = "WHERE p.payment_date >= %s", [raw_from]
    elif raw_to:
        where, params = "WHERE p.payment_date <= %s", [raw_to]
    cur.execute(
        "SELECT s.name, c.tutor_name, c.subject,"
        "       COUNT(p.payment_id), SUM(p.amount_paid)"
        " FROM payments p"
        " JOIN students s ON p.student_id=s.student_id"
        " JOIN courses  c ON s.course_id=c.course_id"
        f" {where}"
        " GROUP BY p.student_id ORDER BY SUM(p.amount_paid) DESC",
        params
    )
    rows = cur.fetchall()
    cur.execute(
        f"SELECT COALESCE(SUM(amount_paid),0) FROM payments p {where}", params
    )
    grand = float(cur.fetchone()[0])
    con.close()
    if not rows:
        print("  No payment records in this period.")
    else:
        print(f"\n  {'Student':<20} {'Tutor':<15} {'Subject':<15} {'#Payments':>9} {'Total':>12}")
        print("  " + "-" * 74)
        for r in rows:
            print(f"  {r[0]:<20} {r[1]:<15} {r[2]:<15} {r[3]:>9} {float(r[4]):>12.2f}")
        print("  " + "-" * 74)
        print(f"  {'GRAND TOTAL COLLECTED':>55} : Rs. {grand:.2f}")
    pause()


# --------------------------------------------------
#  MENUS
# --------------------------------------------------

def course_menu():
    while True:
        heading("Course / Fee Structure")
        print("  1. Add new course")
        print("  2. View all courses")
        print("  3. Delete a course")
        print("  0. Back")
        c = input("\n  Choice : ").strip()
        if   c == "1": add_course()
        elif c == "2": view_courses()
        elif c == "3": delete_course()
        elif c == "0": break
        else: print("  Invalid choice.")

def student_menu():
    while True:
        heading("Student Management")
        print("  1. Register new student")
        print("  2. View all students")
        print("  3. Search student")
        print("  4. Update student record")
        print("  5. Delete student")
        print("  0. Back")
        c = input("\n  Choice : ").strip()
        if   c == "1": add_student()
        elif c == "2": view_students()
        elif c == "3": search_student()
        elif c == "4": update_student()
        elif c == "5": delete_student()
        elif c == "0": break
        else: print("  Invalid choice.")

def payment_menu():
    while True:
        heading("Payments")
        print("  1. Record a payment")
        print("  2. View payment history")
        print("  3. Delete a payment record")
        print("  4. Reprint a receipt")
        print("  0. Back")
        c = input("\n  Choice : ").strip()
        if   c == "1": record_payment()
        elif c == "2": view_payment_history()
        elif c == "3": delete_payment()
        elif c == "4": reprint_receipt()
        elif c == "0": break
        else: print("  Invalid choice.")

def reports_menu():
    while True:
        heading("Reports & Dues")
        print("  1. Pending dues -- all students")
        print("  2. Defaulter list")
        print("  3. Fee collection summary")
        print("  0. Back")
        c = input("\n  Choice : ").strip()
        if   c == "1": pending_dues()
        elif c == "2": defaulter_list()
        elif c == "3": fee_summary()
        elif c == "0": break
        else: print("  Invalid choice.")

def main_menu():
    while True:
        print(f"\n{DIV}")
        print("        TRACKMYFEES -- FEE TRACKER")
        print(f"{DIV}")
        print("  1. Course / Fee Structure")
        print("  2. Student Management")
        print("  3. Payments")
        print("  4. Reports & Dues")
        print("  0. Exit")
        print(DIV)
        c = input("  Choice : ").strip()
        if   c == "1": course_menu()
        elif c == "2": student_menu()
        elif c == "3": payment_menu()
        elif c == "4": reports_menu()
        elif c == "0":
            print("\n  Goodbye!\n")
            break
        else: print("  Invalid choice. Try again.")

# --------------------------------------------------
#  ENTRY POINT
# --------------------------------------------------
if __name__ == "__main__":
    print(f"\n{DIV}")
    print("  TrackMyFees  --  Starting up...")
    print(DIV)
    setup_database()
    main_menu()
