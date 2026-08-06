import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# 1. Add fee_collection_day column if missing
try:
    cursor.execute("ALTER TABLE student ADD COLUMN fee_collection_day INTEGER DEFAULT 2;")
    print("Added fee_collection_day to student table.")
except Exception as e:
    print("fee_collection_day notice:", e)

# 2. Extract day from existing join_date if join_date column exists
try:
    cursor.execute("SELECT id, join_date FROM student WHERE join_date IS NOT NULL;")
    rows = cursor.fetchall()
    for sid, jdate in rows:
        if jdate and '-' in jdate:
            try:
                day_val = int(jdate.split('-')[-1])
                cursor.execute("UPDATE student SET fee_collection_day = ? WHERE id = ?;", (day_val, sid))
            except ValueError:
                pass
    print("Migrated existing join_date to fee_collection_day.")
except Exception as e:
    print("join_date migration notice:", e)

# 3. Ensure join_month defaults to 2026-07 for existing records
try:
    cursor.execute("UPDATE student SET join_month = '2026-07' WHERE join_month IS NULL OR join_month = '' OR join_month > '2026-07';")
    print("Updated base join_month to 2026-07 for existing students.")
except Exception as e:
    print("join_month update notice:", e)

# 4. Auto-mark July 2026 as PAID for all existing students
try:
    cursor.execute("SELECT id, monthly_fee FROM student;")
    students = cursor.fetchall()
    for sid, fee in students:
        fee_amt = fee if fee else 0.0
        # Check if July 2026 payment exists
        cursor.execute("SELECT id FROM payment WHERE student_id = ? AND month = 'Jul' AND year = 2026;", (sid,))
        p_row = cursor.fetchone()
        if not p_row:
            cursor.execute(
                "INSERT INTO payment (student_id, month, year, amount, payment_method, status, updated_at) VALUES (?, 'Jul', 2026, ?, 'Cash', 'Paid', datetime('now'));",
                (sid, fee_amt)
            )
        else:
            cursor.execute(
                "UPDATE payment SET status = 'Paid', amount = ?, payment_method = COALESCE(payment_method, 'Cash') WHERE id = ?;",
                (fee_amt, p_row[0])
            )
    print("Marked July 2026 as Paid for all existing students.")
except Exception as e:
    print("July payment update notice:", e)

conn.commit()
conn.close()
print("Migration completed successfully.")
