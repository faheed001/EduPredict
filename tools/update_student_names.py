import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / 'data' / 'student_performance_dataset.csv'
DB_PATH = ROOT / 'data' / 'edupredict.db'

def run():
    df = pd.read_csv(DATA_PATH)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    updated_count = 0

    for _, row in df.iterrows():
        sid = int(row['student_id'])
        code = f"STU{sid:04d}"
        name = str(row['student_name']).strip()
        clean_email = name.lower().replace("'", "").replace(" ", ".") + "@campus.edu"
        cur.execute("UPDATE students SET full_name=?, email=? WHERE student_code=?", (name, clean_email, code))
        updated_count += cur.rowcount

    # Update demo student in users table
    first_student_name = str(df.iloc[0]['student_name']).strip()
    cur.execute("UPDATE users SET full_name=? WHERE username='student'", (first_student_name,))

    con.commit()
    print(f"Successfully updated {updated_count} students in SQLite database.")
    
    sample = cur.execute("SELECT id, student_code, full_name, email FROM students LIMIT 10").fetchall()
    print("Sample updated records:")
    for s in sample:
        print(" ", s)
    con.close()

if __name__ == '__main__':
    run()
