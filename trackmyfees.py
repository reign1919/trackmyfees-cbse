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
            "  join_date  DATE         NOT NULL"
            ")"
        )

        cur.execute(
            "CREATE TABLE IF NOT EXISTS enrollments ("
            "  student_id      INT NOT NULL,"
            "  course_id       INT NOT NULL,"
            "  enrollment_date DATE NOT NULL,"
            "  PRIMARY KEY (student_id, course_id),"
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
            "  fee_month    VARCHAR(20)   NOT NULL,"
            "  remarks      VARCHAR(200)  DEFAULT '',"
            "  FOREIGN KEY (student_id) REFERENCES students(student_id)"
            "    ON DELETE CASCADE,"
            "  FOREIGN KEY (course_id) REFERENCES courses(course_id)"
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
#  ENROLLMENT HELPERS
# --------------------------------------------------

def get_student_enrollments(cur, sid):
    """Return list of (course_id, course_name, subject, tutor_name, monthly_fee) for a student."""
    cur.execute(
        "SELECT c.course_id, c.course_name, c.subject, c.tutor_name, c.monthly_fee"
        " FROM enrollments e"
        " JOIN courses c ON e.course_id = c.course_id"
        " WHERE e.student_id = %s"
        " ORDER BY c.course_id",
        (sid,)
    )
    return cur.fetchall()


def enroll_student_in_course(cur, sid, cid, enroll_date=None):
    """Enroll a student in a course. Returns True if newly enrolled, False if already."""
    cur.execute(
        "SELECT 1 FROM enrollments WHERE student_id=%s AND course_id=%s",
        (sid, cid)
    )
    if cur.fetchone():
        return False
    if enroll_date is None:
        enroll_date = date.today()
    cur.execute(
        "INSERT INTO enrollments (student_id, course_id, enrollment_date) VALUES (%s,%s,%s)",
        (sid, cid, enroll_date)
    )
    return True


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
    con = connect()
    if not con:
        return
    cur = con.cursor()
    name    = input("  Student name          : ").strip()
    cls     = input("  Class (e.g. XI, XII)  : ").strip()
    contact = input("  Contact number        : ").strip()
    jdate   = get_date("  Join date (YYYY-MM-DD): ")

    cur.execute(
        "INSERT INTO students (name, class, contact, join_date) VALUES (%s,%s,%s,%s)",
        (name, cls, contact, jdate)
    )
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
        if enroll_student_in_course(cur, sid, cid, jdate):
            print(f"  Enrolled in '{row[0]}'.")
        else:
            print(f"  Already enrolled in '{row[0]}'.")
        con.commit()

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
    con.close()
    if not students:
        print("  No students registered.")
    else:
        for s in students:
            sid, name, cls, contact, jdate = s
            print(f"\n  ID: {sid}  |  {name}  |  Class: {cls}  |  Contact: {contact}  |  Joined: {jdate}")
            # Show enrollments
            con = connect()
            if con:
                cur = con.cursor()
                enrolls = get_student_enrollments(cur, sid)
                con.close()
                if enrolls:
                    for e in enrolls:
                        print(f"      -> {e[1]} ({e[2]}) — Tutor: {e[3]} — Rs. {float(e[4]):.2f}/month")
                else:
                    print("      -> No enrollments")
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
            "SELECT s.student_id, s.name, s.class, s.contact, s.join_date"
            " FROM students s"
            " WHERE s.student_id=%s", (int(keyword),)
        )
    else:
        like = f"%{keyword}%"
        cur.execute(
            "SELECT DISTINCT s.student_id, s.name, s.class, s.contact, s.join_date"
            " FROM students s"
            " LEFT JOIN enrollments e ON s.student_id = e.student_id"
            " LEFT JOIN courses c ON e.course_id = c.course_id"
            " WHERE s.name LIKE %s OR c.course_name LIKE %s OR c.subject LIKE %s",
            (like, like, like)
        )
    students = cur.fetchall()
    con.close()
    if not students:
        print("  No records found.")
    else:
        for s in students:
            sid, name, cls, contact, jdate = s
            print(f"\n  ID: {sid}  |  {name}  |  Class: {cls}  |  Contact: {contact}  |  Joined: {jdate}")
            con = connect()
            if con:
                cur = con.cursor()
                enrolls = get_student_enrollments(cur, sid)
                con.close()
                if enrolls:
                    for e in enrolls:
                        print(f"      -> {e[1]} ({e[2]}) — Tutor: {e[3]} — Rs. {float(e[4]):.2f}/month")
                else:
                    print("      -> No enrollments")
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

    # Manage enrollments
    while True:
        print("\n  Current enrollments:")
        enrolls = get_student_enrollments(cur, sid)
        if enrolls:
            for e in enrolls:
                print(f"      {e[0]}: {e[1]} ({e[2]}) — Tutor: {e[3]}")
        else:
            print("      None")

        print("\n  1. Add enrollment")
        print("  2. Remove enrollment")
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
            if enroll_student_in_course(cur, sid, cid):
                con.commit()
                print(f"  Enrolled in '{crow[0]}'.")
            else:
                print(f"  Already enrolled in '{crow[0]}'.")
        elif choice == "2":
            cid = get_int("  Enter Course ID to remove : ")
            cur.execute(
                "DELETE FROM enrollments WHERE student_id=%s AND course_id=%s",
                (sid, cid)
            )
            con.commit()
            print("  Enrollment removed.")
        elif choice == "0":
            break

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
    cur.execute("SELECT name FROM students WHERE student_id=%s", (sid,))
    srow = cur.fetchone()
    if not srow:
        print("  Student not found.")
        con.close()
        pause()
        return

    # Show enrolled courses for selection
    enrolls = get_student_enrollments(cur, sid)
    if not enrolls:
        print("  Student is not enrolled in any course.")
        con.close()
        pause()
        return

    print(f"\n  Student: {srow[0]}")
    print("  Enrolled courses:")
    for e in enrolls:
        print(f"      {e[0]}: {e[1]} ({e[2]}) — Tutor: {e[3]} — Rs. {float(e[4]):.2f}/month")

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
    print(f"  Monthly Fee : Rs. {float(selected[4]):.2f}")
    amount  = get_float("  Amount paid (Rs.)         : ")
    pdate   = get_date( "  Payment date (YYYY-MM-DD)  : ")
    month   = input(    "  Fee month (e.g. April 2025): ").strip()
    remarks = input(    "  Remarks (optional)         : ").strip()
    cur.execute(
        "INSERT INTO payments (student_id, course_id, amount_paid, payment_date, fee_month, remarks)"
        " VALUES (%s,%s,%s,%s,%s,%s)",
        (sid, cid, amount, pdate, month, remarks)
    )
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
    cur.execute("SELECT name FROM students WHERE student_id=%s", (sid,))
    srow = cur.fetchone()
    if not srow:
        print("  Student not found.")
        con.close()
        pause()
        return

    # Show all payments across all courses
    cur.execute(
        "SELECT p.payment_id, c.course_name, c.tutor_name, p.fee_month,"
        "       p.amount_paid, p.payment_date, p.remarks"
        " FROM payments p"
        " JOIN courses c ON p.course_id = c.course_id"
        " WHERE p.student_id = %s"
        " ORDER BY p.payment_date",
        (sid,)
    )
    rows = cur.fetchall()
    con.close()

    print(f"\n  Student: {srow[0]}")
    if not rows:
        print("  No payment records found.")
    else:
        total = 0.0
        print(f"  {'Rec#':<6} {'Course':<18} {'Tutor':<15} {'Month':<14} {'Amount':>10} {'Date':<12} Remarks")
        print("  " + "-" * 90)
        for r in rows:
            total += float(r[4])
            print(f"  {r[0]:<6} {r[1]:<18} {r[2]:<15} {r[3]:<14} {float(r[4]):>10.2f} {str(r[5]):<12} {r[6]}")
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
        print(f"  {r[0]:<6} {r[1]:<18} {r[2]:<14} {float(r[3]):>10.2f} {r[4]}")
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
    g_exp = g_paid = 0.0
    for s in students:
        sid, name = s
        enrolls = get_student_enrollments(cur, sid)
        for e in enrolls:
            cid, cname, subj, tutor, mfee = e
            # Use enrollment date for months calculation
            cur.execute("SELECT enrollment_date FROM enrollments WHERE student_id=%s AND course_id=%s", (sid, cid))
            edate = cur.fetchone()[0]
            months = (today.year - edate.year) * 12 + (today.month - edate.month) + 1
            expected = float(mfee) * months
            cur.execute(
                "SELECT COALESCE(SUM(amount_paid),0) FROM payments WHERE student_id=%s AND course_id=%s",
                (sid, cid)
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
    cur.execute("SELECT student_id, name, class, contact FROM students")
    students = cur.fetchall()
    defaulters = []
    for s in students:
        sid, name, cls, contact = s
        enrolls = get_student_enrollments(cur, sid)
        total_bal = 0.0
        tutor_names = []
        for e in enrolls:
            cid, cname, subj, tutor, mfee = e
            cur.execute("SELECT enrollment_date FROM enrollments WHERE student_id=%s AND course_id=%s", (sid, cid))
            edate = cur.fetchone()[0]
            months = (today.year - edate.year) * 12 + (today.month - edate.month) + 1
            expected = float(mfee) * months
            cur.execute(
                "SELECT COALESCE(SUM(amount_paid),0) FROM payments WHERE student_id=%s AND course_id=%s",
                (sid, cid)
            )
            paid = float(cur.fetchone()[0])
            bal = expected - paid
            if bal > 0:
                total_bal += bal
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
        " JOIN courses  c ON p.course_id=c.course_id"
        f" {where}"
        " GROUP BY p.student_id, p.course_id ORDER BY SUM(p.amount_paid) DESC",
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
