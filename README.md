# TrackMyFees — Fee Tracker

**Developed by:** Akshat R. Chowdhury, Trishaan Saha, Sashmit Guin (XII-A)  
**Language:** Python 3.x | **Database:** MySQL 8.0  

---

## Setup Instructions

### 1. Install dependencies
```
pip install mysql-connector-python
```

### 2. Set your MySQL password
Open `trackmyfees.py` and edit line 17:
```python
DB_PASS = "root"   # <-- change to your actual password
```

### 3. Run the program
```
python trackmyfees.py
```
The program will automatically create the `trackmyfees` database and all tables on first run.

---

## Database Schema

| Table      | Key Columns                                               |
|------------|-----------------------------------------------------------|
| `courses`  | course_id, course_name, subject, tutor_name, monthly_fee  |
| `students` | student_id, name, class, contact, course_id, join_date    |
| `payments` | payment_id, student_id, amount_paid, payment_date, fee_month, remarks |

---

## Menu Structure

```
TRACKMYFEES
├── 1. Course / Fee Structure
│   ├── 1. Add new course
│   ├── 2. View all courses
│   └── 3. Delete a course
├── 2. Student Management
│   ├── 1. Register new student
│   ├── 2. View all students
│   ├── 3. Search student
│   ├── 4. Update student record
│   └── 5. Delete student
├── 3. Payments
│   ├── 1. Record a payment  (prints receipt)
│   ├── 2. View payment history
│   ├── 3. Delete a payment record
│   └── 4. Reprint a receipt
└── 4. Reports & Dues
    ├── 1. Pending dues -- all students
    ├── 2. Defaulter list
    └── 3. Fee collection summary
```

---

## Typical Workflow

1. **Add a course** (e.g., "Maths Batch A", monthly fee Rs. 1500, tutor "Mr. Sharma")
2. **Register students** and assign them to a course
3. **Record payments** each month — a receipt is printed automatically
4. **Check pending dues** to see who owes what and how much
5. **Generate defaulter list** for students beyond a due threshold
