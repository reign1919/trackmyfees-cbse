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
from decimal import Decimal, InvalidOperation
from getpass import getpass
import sys


# --------------------------------------------------
#  CONFIGURATION
# --------------------------------------------------
DB_HOST = "localhost"
DB_USER = "root"
DB_NAME = "trackmyfees"

# Prompt for password instead of hardcoding
DB_PASS = getpass("  Enter MySQL password: ")


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
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cur.execute(f"USE {DB_NAME}")

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
            "  join_date  DATE         NOT NULL"
            ")"
        )

        cur.execute(
            "CREATE TABLE IF NOT EXISTS enrollments ("
            "  enrollment_id   INT AUTO_INCREMENT PRIMARY KEY,"
            "  student_id      INT NOT NULL,"
            "  course_id       INT NOT NULL,"
            "  enrollment_date DATE NOT NULL,"
            "  end_date        DATE DEFAULT NULL,"
            "  UNIQUE (student_id, course_id, enrollment_date),"
            "  FOREIGN KEY (student_id) REFERENCES students(student_id)"
            "    ON DELETE CASCADE,"
            "  FOREIGN KEY (course_id) REFERENCES courses(course_id)"
            "    ON DELETE CASCADE"
            ")"
        )

        cur.execute(
            "CREATE TABLE IF NOT EXISTS payments ("
            "  payment_id   INT           AUTO_INCREMENT PRIMARY KEY,"
            "  student_id   INT           NOT NULL,"
            "  course_id    INT           NOT NULL,"
            "  amount_paid  DECIMAL(10,2) NOT NULL,"
            "  payment_date DATE          NOT NULL,"
            "  fee_month    DATE          NOT NULL,"
            "  remarks      VARCHAR(200)  DEFAULT '',"
            "  UNIQUE (student_id, course_id, fee_month),"
            "  FOREIGN KEY (student_id) REFERENCES students(student_id)"
            "    ON DELETE CASCADE,"
            "  FOREIGN KEY (course_id) REFERENCES courses(course_id)"
            "    ON DELETE RESTRICT"
            ")"
        )

        con.commit()
        con.close()
        print("  Database ready.\n")
    except Error as e:
        print(f"\n  [SETUP ERROR] {e}")
        print("  Make sure MySQL is running and credentials are correct.\n")
        sys.exit(1)


# --------------------------------------------------
#  UTILITY HELPERS
# --------------------------------------------------

DIV = "=" * 60

def heading(title):
    print(f"\n{DIV}\n  {title.upper()}\n{DIV}")

def pause():
    input("\n  Press ENTER to return to menu...")

def get_nonempty(prompt, max_len=None):
    """Get non-empty input, optionally with max length."""
    while True:
        val = input(prompt).strip()
        if not val:
            print("  This field cannot be empty.")
            continue
        if max_len and len(val) > max_len:
            print(f"  Too long. Maximum {max_len} characters.")
            continue
        return val

def get_int(prompt, minimum=1):
    while True:
        try:
            val = int(input(prompt))
            if val >= minimum:
                return val
            print(f"  Enter a number >= {minimum}.")
        except ValueError:
            print("  Invalid. Enter a whole number.")

def get_decimal(prompt, minimum=Decimal("0.01")):
    """Get a Decimal value, rejecting inf/nan and out-of-range."""
    while True:
        raw = input(prompt).strip()
        try:
            val = Decimal(raw)
            if val.is_nan() or val.is_infinite():
                print("  Invalid amount.")
                continue
            if val < minimum:
                print(f"  Amount must be >= {minimum}.")
                continue
            if val > Decimal("99999999.99"):
                print("  Amount too large. Maximum 99,999,999.99.")
                continue
            return val
        except InvalidOperation:
            print("  Invalid. Enter a number (e.g. 1500 or 1500.50).")

def get_date(prompt, allow_future=False):
    while True:
        raw = input(prompt).strip()
        try:
            d = datetime.strptime(raw, "%Y-%m-%d").date()
            if not allow_future and d > date.today():
                print("  Date cannot be in the future.")
                continue
            return d
        except ValueError:
            print("  Format: YYYY-MM-DD  (e.g. 2025-04-01)")

def get_month(prompt):
    """Get a month as YYYY-MM, return as date (1st of month)."""
    while True:
        raw = input(prompt).strip()
        try:
            d = datetime.strptime(raw + "-01", "%Y-%m-%d").date()
            return d
        except ValueError:
            print("  Format: YYYY-MM  (e.g. 2025-04)")

def safe_execute(cur, query, params=None):
    """Execute with error handling. Returns True on success."""
    try:
        cur.execute(query, params or ())
        return True
    except Error as e:
        print(f"  [DB ERROR] {e}")
        return False


# --------------------------------------------------
#  ENROLLMENT HELPERS
# --------------------------------------------------

def get_student_enrollments(cur, sid, active_only=False):
    """Return list of (course_id, course_name, subject, tutor_name, monthly_fee, enrollment_date)."""
    q = (
        "SELECT c.course_id, c.course_name, c.subject, c.tutor_name, c.monthly_fee, e.enrollment_date"
        " FROM enrollments e"
        " JOIN courses c ON e.course_id = c.course_id"
        " WHERE e.student_id = %s"
    )
    if active_only:
        q += " AND e.end_date IS NULL"
    q += " ORDER BY c.course_id"
    cur.execute(q, (sid,))
    return cur.fetchall()


def get_months_between(start_date, end_date):
    """Return list of (year, month) tuples from start to end inclusive."""
    months = []
    y, m = start_date.year, start_date.month
    while (y, m) <= (end_date.year, end_date.month):
        months.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months


def get_paid_months(cur, sid, cid):
    """Return set of (year, month) tuples that have been paid."""
    cur.execute(
        "SELECT fee_month FROM payments WHERE student_id=%s AND course_id=%s",
        (sid, cid)
    )
    return {(r[0].year, r[0].month) for r in cur.fetchall()}


def calculate_dues(cur, sid, cid, enrollment_date, monthly_fee):
    """Calculate dues for a student in a course. Returns (expected, paid, balance, unpaid_months)."""
    today = date.today()
    months = get_months_between(enrollment_date, today)
    expected = monthly_fee * len(months)
    paid_months = get_paid_months(cur, sid, cid)
    cur.execute(
        "SELECT COALESCE(SUM(amount_paid),0) FROM payments WHERE student_id=%s AND course_id=%s",
        (sid, cid)
    )
    paid = cur.fetchone()[0]
    if paid is None:
        paid = Decimal("0")
    balance = expected - paid
    unpaid = [m for m in months if m not in paid_months]
    return expected, paid, balance, unpaid


# --------------------------------------------------
#  MODULE 1 -- COURSE / FEE STRUCTURE
# --------------------------------------------------

def add_course():
    heading("Add New Course / Subject")
    con = connect()
    if not con:
        return
    cur = con.cursor()
    name    = get_nonempty("  Course / Batch name   : ", 100)
    subject = get_nonempty("  Subject               : ", 100)
    tutor   = get_nonempty("  Tutor name            : ", 100)
    fee     = get_decimal("  Monthly fee (Rs.)     : ")
    if safe_execute(cur,
        "INSERT INTO courses (course_name, subject, tutor_name, monthly_fee) VALUES (%s,%s,%s,%s)",
        (name, subject, tutor, fee)
    ):
        con.commit()
        print(f"\n  Course '{name}' added. ID = {cur.lastrowid}")
    else:
        con.rollback()
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
            print(f"  {r[0]:<5} {r[1]:<20} {r[2]:<18} {r[3]:<18} {r[4]:>12.2f}")
    if pause_after:
        pause()


def update_course():
    heading("Edit Course")
    view_courses(pause_after=False)
    con = connect()
    if not con:
        return
    cur = con.cursor()
    cid = get_int("  Enter Course ID to edit : ")
    cur.execute("SELECT course_name, subject, tutor_name, monthly_fee FROM courses WHERE course_id=%s", (cid,))
    row = cur.fetchone()
    if not row:
        print("  Course not found.")
        con.close()
        pause()
        return
    print(f"\n  Current Name    : {row[0]}")
    print(f"  Current Subject : {row[1]}")
    print(f"  Current Tutor   : {row[2]}")
    print(f"  Current Fee     : Rs. {row[3]:.2f}")
    print("  (Press ENTER to keep existing value)")
    name    = input("  New name    : ").strip() or row[0]
    subject = input("  New subject : ").strip() or row[1]
    tutor   = input("  New tutor   : ").strip() or row[2]
    fee_raw = input("  New fee     : ").strip()
    if fee_raw:
        try:
            fee = Decimal(fee_raw)
        except InvalidOperation:
            print("  Invalid fee. Keeping existing value.")
            fee = row[3]
    else:
        fee = row[3]
    if safe_execute(cur,
        "UPDATE courses SET course_name=%s, subject=%s, tutor_name=%s, monthly_fee=%s WHERE course_id=%s",
        (name, subject, tutor, fee, cid)
    ):
        con.commit()
        print("  Course updated.")
    else:
        con.rollback()
    con.close()
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
    # Check for payments
    cur.execute("SELECT COUNT(*) FROM payments WHERE course_id=%s", (cid,))
    pay_count = cur.fetchone()[0]
    if pay_count > 0:
        print(f"\n  WARNING: This course has {pay_count} payment record(s).")
        print("  Deleting it will fail because payments are protected (ON DELETE RESTRICT).")
        print("  You must delete the payment records first.")
        con.close()
        pause()
        return
    confirm = input(f"  Delete '{row[0]}'? (yes/no) : ").strip().lower()
    if confirm == "yes":
        if safe_execute(cur, "DELETE FROM courses WHERE course_id=%s", (cid,)):
            con.commit()
            print("  Course deleted.")
        else:
            con.rollback()
    else:
        print("  Cancelled.")
    con.close()
    pause()


# --------------------------------------------------
#  MODULE 2 -- STUDENT MANAGEMENT
# --------------------------------------------------

def add_student():
    heading("Register New Student")
    con = connect()
    if not con:
        return
    cur = con.cursor()
    name    = get_nonempty("  Student name          : ", 100)
    cls     = get_nonempty("  Class (e.g. XI, XII)  : ", 20)
    contact = get_nonempty("  Contact number        : ", 15)
    jdate   = get_date("  Join date (YYYY-MM-DD): ")

    if not safe_execute(cur,
        "INSERT INTO students (name, class, contact, join_date) VALUES (%s,%s,%s,%s)",
        (name, cls, contact, jdate)
    ):
        con.rollback()
        con.close()
        pause()
        return
    sid = cur.lastrowid
    con.commit()

    # Enroll in one or more courses
    while True:
        print(f"\n  Enrolling student ID = {sid}")
        view_courses(pause_after=False)
        cid = get_int("  Enter Course ID to enroll (0 to finish) : ", minimum=0)
        if cid == 0:
            break
        cur.execute("SELECT course_name FROM courses WHERE course_id=%s", (cid,))
        row = cur.fetchone()
        if not row:
            print("  Invalid Course ID.")
            continue
        # Check if already actively enrolled
        cur.execute(
            "SELECT 1 FROM enrollments WHERE student_id=%s AND course_id=%s AND end_date IS NULL",
            (sid, cid)
        )
        if cur.fetchone():
            print(f"  Already actively enrolled in '{row[0]}'.")
            continue
        if safe_execute(cur,
            "INSERT INTO enrollments (student_id, course_id, enrollment_date) VALUES (%s,%s,%s)",
            (sid, cid, jdate)
        ):
            con.commit()
            print(f"  Enrolled in '{row[0]}'.")
        else:
            con.rollback()

    print(f"\n  Student '{name}' registered. ID = {sid}")
    con.close()
    pause()


def view_students(pause_after=True):
    heading("All Students")
    con = connect()
    if not con:
        return
    cur = con.cursor()
    cur.execute("SELECT student_id, name, class, contact, join_date FROM students ORDER BY student_id")
    students = cur.fetchall()
    if not students:
        print("  No students registered.")
    else:
        for s in students:
            sid, name, cls, contact, jdate = s
            print(f"\n  ID: {sid}  |  {name}  |  Class: {cls}  |  Contact: {contact}  |  Joined: {jdate}")
            enrolls = get_student_enrollments(cur, sid)
            if enrolls:
                for e in enrolls:
                    print(f"      -> {e[1]} ({e[2]}) — Tutor: {e[3]} — Rs. {e[4]:.2f}/month — From: {e[5]}")
            else:
                print("      -> No enrollments")
    con.close()
    if pause_after:
        pause()


def search_student():
    heading("Search Student")
    keyword = input("  Enter name, ID, or subject/course keyword : ").strip()
    if not keyword:
        print("  Search term cannot be empty.")
        pause()
        return
    con = connect()
    if not con:
        return
    cur = con.cursor()
    # Escape LIKE wildcards
    escaped = keyword.replace("%", "\\%").replace("_", "\\_")
    like = f"%{escaped}%"
    if keyword.isdigit():
        # Search by student ID AND also by course name/subject containing the number
        cur.execute(
            "SELECT DISTINCT s.student_id, s.name, s.class, s.contact, s.join_date"
            " FROM students s"
            " LEFT JOIN enrollments e ON s.student_id = e.student_id"
            " LEFT JOIN courses c ON e.course_id = c.course_id"
            " WHERE s.student_id=%s"
            " OR c.course_name LIKE %s ESCAPE '\\\\'"
            " OR c.subject LIKE %s ESCAPE '\\\\'",
            (int(keyword), like, like)
        )
    else:
        cur.execute(
            "SELECT DISTINCT s.student_id, s.name, s.class, s.contact, s.join_date"
            " FROM students s"
            " LEFT JOIN enrollments e ON s.student_id = e.student_id"
            " LEFT JOIN courses c ON e.course_id = c.course_id"
            " WHERE s.name LIKE %s ESCAPE '\\\\'"
            " OR c.course_name LIKE %s ESCAPE '\\\\'"
            " OR c.subject LIKE %s ESCAPE '\\\\'",
            (like, like, like)
        )
    students = cur.fetchall()
    if not students:
        print("  No records found.")
    else:
        for s in students:
            sid, name, cls, contact, jdate = s
            print(f"\n  ID: {sid}  |  {name}  |  Class: {cls}  |  Contact: {contact}  |  Joined: {jdate}")
            enrolls = get_student_enrollments(cur, sid)
            if enrolls:
                for e in enrolls:
                    print(f"      -> {e[1]} ({e[2]}) — Tutor: {e[3]} — Rs. {e[4]:.2f}/month — From: {e[5]}")
            else:
                print("      -> No enrollments")
    con.close()
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
    if safe_execute(cur,
        "UPDATE students SET name=%s, class=%s, contact=%s WHERE student_id=%s",
        (name, cls, contact, sid)
    ):
        con.commit()
    else:
        con.rollback()

    # Manage enrollments
    while True:
        print("\n  Current enrollments:")
        enrolls = get_student_enrollments(cur, sid)
        if enrolls:
            for e in enrolls:
                print(f"      {e[0]}: {e[1]} ({e[2]}) — Tutor: {e[3]} — From: {e[5]}")
        else:
            print("      None")

        print("\n  1. Add enrollment")
        print("  2. End enrollment")
        print("  0. Done")
        choice = input("  Choice : ").strip()
        if choice == "1":
            view_courses(pause_after=False)
            cid = get_int("  Enter Course ID to enroll : ")
            cur.execute("SELECT course_name FROM courses WHERE course_id=%s", (cid,))
            crow = cur.fetchone()
            if not crow:
                print("  Invalid Course ID.")
                continue
            cur.execute(
                "SELECT 1 FROM enrollments WHERE student_id=%s AND course_id=%s AND end_date IS NULL",
                (sid, cid)
            )
            if cur.fetchone():
                print(f"  Already actively enrolled in '{crow[0]}'.")
                continue
            if safe_execute(cur,
                "INSERT INTO enrollments (student_id, course_id, enrollment_date) VALUES (%s,%s,%s)",
                (sid, cid, date.today())
            ):
                con.commit()
                print(f"  Enrolled in '{crow[0]}'.")
            else:
                con.rollback()
        elif choice == "2":
            cid = get_int("  Enter Course ID to end enrollment : ")
            cur.execute(
                "SELECT 1 FROM enrollments WHERE student_id=%s AND course_id=%s AND end_date IS NULL",
                (sid, cid)
            )
            if not cur.fetchone():
                print("  No active enrollment found for that course.")
                continue
            if safe_execute(cur,
                "UPDATE enrollments SET end_date=%s WHERE student_id=%s AND course_id=%s AND end_date IS NULL",
                (date.today(), sid, cid)
            ):
                con.commit()
                print("  Enrollment ended.")
            else:
                con.rollback()
        elif choice == "0":
            break
        else:
            print("  Invalid choice.")

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
        if safe_execute(cur, "DELETE FROM students WHERE student_id=%s", (sid,)):
            con.commit()
            print("  Student deleted.")
        else:
            con.rollback()
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
    cur.execute("SELECT name FROM students WHERE student_id=%s", (sid,))
    srow = cur.fetchone()
    if not srow:
        print("  Student not found.")
        con.close()
        pause()
        return

    enrolls = get_student_enrollments(cur, sid, active_only=True)
    if not enrolls:
        print("  Student is not actively enrolled in any course.")
        con.close()
        pause()
        return

    print(f"\n  Student: {srow[0]}")
    print("  Active enrollments:")
    for e in enrolls:
        print(f"      {e[0]}: {e[1]} ({e[2]}) — Tutor: {e[3]} — Rs. {e[4]:.2f}/month")

    cid = get_int("  Enter Course ID for payment : ")
    selected = None
    for e in enrolls:
        if e[0] == cid:
            selected = e
            break
    if not selected:
        print("  Invalid Course ID.")
        con.close()
        pause()
        return

    print(f"\n  Course      : {selected[1]}")
    print(f"  Tutor       : {selected[3]}")
    print(f"  Monthly Fee : Rs. {selected[4]:.2f}")
    amount  = get_decimal("  Amount paid (Rs.)         : ")
    pdate   = get_date( "  Payment date (YYYY-MM-DD)  : ")
    month   = get_month("  Fee month (YYYY-MM)        : ")
    remarks = input(    "  Remarks (optional)         : ").strip()

    if not safe_execute(cur,
        "INSERT INTO payments (student_id, course_id, amount_paid, payment_date, fee_month, remarks)"
        " VALUES (%s,%s,%s,%s,%s,%s)",
        (sid, cid, amount, pdate, month, remarks)
    ):
        con.rollback()
        con.close()
        pause()
        return
    con.commit()
    pid = cur.lastrowid
    con.close()
    # Receipt
    print(f"\n  {'-'*48}")
    print("           PAYMENT RECEIPT")
    print(f"  {'-'*48}")
    print(f"  Receipt No.  : {pid}")
    print(f"  Student      : {srow[0]}")
    print(f"  Course       : {selected[1]}")
    print(f"  Tutor        : {selected[3]}")
    print(f"  Fee Month    : {month.strftime('%B %Y')}")
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
    cur.execute("SELECT name FROM students WHERE student_id=%s", (sid,))
    srow = cur.fetchone()
    if not srow:
        print("  Student not found.")
        con.close()
        pause()
        return

    cur.execute(
        "SELECT p.payment_id, c.course_name, c.tutor_name, p.fee_month,"
        "       p.amount_paid, p.payment_date, p.remarks"
        " FROM payments p"
        " JOIN courses c ON p.course_id = c.course_id"
        " WHERE p.student_id = %s"
        " ORDER BY p.payment_date, p.payment_id",
        (sid,)
    )
    rows = cur.fetchall()
    con.close()

    print(f"\n  Student: {srow[0]}")
    if not rows:
        print("  No payment records found.")
    else:
        total = Decimal("0")
        print(f"  {'Rec#':<6} {'Course':<18} {'Tutor':<15} {'Month':<14} {'Amount':>10} {'Date':<12} Remarks")
        print("  " + "-" * 90)
        for r in rows:
            total += r[4]
            print(f"  {r[0]:<6} {r[1]:<18} {r[2]:<15} {r[3].strftime('%b %Y'):<14} {r[4]:>10.2f} {str(r[5]):<12} {r[6]}")
        print("  " + "-" * 90)
        print(f"  {'TOTAL PAID':>60} : Rs. {total:.2f}")
    pause()


def delete_payment():
    heading("Delete Payment Record")
    con = connect()
    if not con:
        return
    cur = con.cursor()
    sid = get_int("  Enter Student ID : ")
    cur.execute(
        "SELECT p.payment_id, c.course_name, p.fee_month, p.amount_paid, p.payment_date"
        " FROM payments p"
        " JOIN courses c ON p.course_id = c.course_id"
        " WHERE p.student_id=%s ORDER BY p.payment_date",
        (sid,)
    )
    rows = cur.fetchall()
    if not rows:
        print("  No payment records for this student.")
        con.close()
        pause()
        return
    print(f"\n  {'Rec#':<6} {'Course':<18} {'Month':<14} {'Amount':>10} {'Date'}")
    print("  " + "-" * 60)
    for r in rows:
        print(f"  {r[0]:<6} {r[1]:<18} {r[2].strftime('%b %Y'):<14} {r[3]:>10.2f} {r[4]}")
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
        if safe_execute(cur, "DELETE FROM payments WHERE payment_id=%s", (pid,)):
            con.commit()
            print("  Payment deleted.")
        else:
            con.rollback()
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
        " JOIN courses  c ON p.course_id=c.course_id"
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
        print(f"  Fee Month    : {r[5].strftime('%B %Y')}")
        print(f"  Amount Paid  : Rs. {r[6]:.2f}")
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
    cur.execute("SELECT student_id, name FROM students ORDER BY student_id")
    students = cur.fetchall()
    if not students:
        print("  No students found.")
        con.close()
        pause()
        return
    print(f"\n  {'ID':<5} {'Name':<20} {'Tutor':<15}"
          f" {'Expected':>10} {'Paid':>10} {'Balance':>10}")
    print("  " + "-" * 74)
    g_exp = Decimal("0")
    g_paid = Decimal("0")
    for s in students:
        sid, name = s
        enrolls = get_student_enrollments(cur, sid, active_only=True)
        for e in enrolls:
            cid, cname, subj, tutor, mfee, edate = e
            expected, paid, balance, unpaid = calculate_dues(cur, sid, cid, edate, mfee)
            g_exp  += expected
            g_paid += paid
            flag = "  *** DUES ***" if balance > 0 else ""
            print(f"  {sid:<5} {name:<20} {tutor:<15}"
                  f" {expected:>10.2f} {paid:>10.2f} {balance:>10.2f}{flag}")
    print("  " + "-" * 74)
    print(f"  {'TOTAL':<42} {g_exp:>10.2f} {g_paid:>10.2f} {g_exp-g_paid:>10.2f}")
    con.close()
    pause()


def defaulter_list():
    heading("Defaulter List")
    threshold = get_decimal("  Show defaulters with dues above Rs. : ", minimum=Decimal("0"))
    con = connect()
    if not con:
        return
    cur = con.cursor()
    today = date.today()
    cur.execute("SELECT student_id, name, class, contact FROM students")
    students = cur.fetchall()
    defaulters = []
    for s in students:
        sid, name, cls, contact = s
        enrolls = get_student_enrollments(cur, sid, active_only=True)
        total_bal = Decimal("0")
        tutor_names = []
        for e in enrolls:
            cid, cname, subj, tutor, mfee, edate = e
            expected, paid, balance, unpaid = calculate_dues(cur, sid, cid, edate, mfee)
            if balance > 0:
                total_bal += balance
                tutor_names.append(tutor)
        if total_bal > threshold:
            tutors_str = ", ".join(tutor_names) if tutor_names else "N/A"
            defaulters.append((sid, name, cls, contact, tutors_str, total_bal))
    con.close()
    if not defaulters:
        print(f"\n  No defaulters with dues above Rs. {threshold:.2f}")
    else:
        print(f"\n  Defaulters with dues > Rs. {threshold:.2f}\n")
        print(f"  {'ID':<5} {'Name':<20} {'Cl':<5} {'Contact':<14} {'Tutor(s)':<20} {'Balance':>10}")
        print("  " + "-" * 80)
        for d in defaulters:
            print(f"  {d[0]:<5} {d[1]:<20} {d[2]:<5} {d[3]:<14} {d[4]:<20} {d[5]:>10.2f}")
        print(f"\n  Total defaulters : {len(defaulters)}")
    pause()


def fee_summary():
    heading("Fee Collection Summary")
    print("  Leave blank to show ALL records.")
    raw_from = input("  From date (YYYY-MM-DD) : ").strip()
    raw_to   = input("  To   date (YYYY-MM-DD) : ").strip()

    # Validate dates
    from_date = None
    to_date = None
    if raw_from:
        try:
            from_date = datetime.strptime(raw_from, "%Y-%m-%d").date()
        except ValueError:
            print("  Invalid 'from' date. Use YYYY-MM-DD.")
            pause()
            return
    if raw_to:
        try:
            to_date = datetime.strptime(raw_to, "%Y-%m-%d").date()
        except ValueError:
            print("  Invalid 'to' date. Use YYYY-MM-DD.")
            pause()
            return
    if from_date and to_date and from_date > to_date:
        print("  'From' date cannot be after 'to' date.")
        pause()
        return

    con = connect()
    if not con:
        return
    cur = con.cursor()
    params = []
    where  = ""
    if from_date and to_date:
        where, params = "WHERE p.payment_date BETWEEN %s AND %s", [from_date, to_date]
    elif from_date:
        where, params = "WHERE p.payment_date >= %s", [from_date]
    elif to_date:
        where, params = "WHERE p.payment_date <= %s", [to_date]
    cur.execute(
        "SELECT s.name, c.tutor_name, c.subject,"
        "       COUNT(p.payment_id), SUM(p.amount_paid)"
        " FROM payments p"
        " JOIN students s ON p.student_id=s.student_id"
        " JOIN courses  c ON p.course_id=c.course_id"
        f" {where}"
        " GROUP BY p.student_id, p.course_id ORDER BY SUM(p.amount_paid) DESC",
        params
    )
    rows = cur.fetchall()
    cur.execute(
        f"SELECT COALESCE(SUM(amount_paid),0) FROM payments p {where}", params
    )
    grand = cur.fetchone()[0]
    if grand is None:
        grand = Decimal("0")

    # Calculate total dues outstanding
    cur.execute("SELECT student_id, name FROM students")
    students = cur.fetchall()
    total_dues = Decimal("0")
    today = date.today()
    for s in students:
        sid, name = s
        enrolls = get_student_enrollments(cur, sid, active_only=True)
        for e in enrolls:
            cid, cname, subj, tutor, mfee, edate = e
            expected, paid, balance, unpaid = calculate_dues(cur, sid, cid, edate, mfee)
            if balance > 0:
                total_dues += balance

    con.close()
    if not rows:
        print("  No payment records in this period.")
    else:
        print(f"\n  {'Student':<20} {'Tutor':<15} {'Subject':<15} {'#Payments':>9} {'Total':>12}")
        print("  " + "-" * 74)
        for r in rows:
            print(f"  {r[0]:<20} {r[1]:<15} {r[2]:<15} {r[3]:>9} {r[4]:>12.2f}")
        print("  " + "-" * 74)
        print(f"  {'GRAND TOTAL COLLECTED':>55} : Rs. {grand:.2f}")
        print(f"  {'TOTAL DUES OUTSTANDING':>55} : Rs. {total_dues:.2f}")
    pause()


# --------------------------------------------------
#  MENUS
# --------------------------------------------------

def course_menu():
    while True:
        heading("Course / Fee Structure")
        print("  1. Add new course")
        print("  2. View all courses")
        print("  3. Edit a course")
        print("  4. Delete a course")
        print("  0. Back")
        c = input("\n  Choice : ").strip()
        if   c == "1": add_course()
        elif c == "2": view_courses()
        elif c == "3": update_course()
        elif c == "4": delete_course()
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
