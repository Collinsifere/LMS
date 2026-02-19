import sqlite3

conn = sqlite3.connect("instance/lms.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM submissions")  # replace 'users' with your table
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()




