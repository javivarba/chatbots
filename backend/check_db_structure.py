import sqlite3

conn = sqlite3.connect('bjj_academy.db')
cursor = conn.cursor()

print("=" * 60)
print("ESTRUCTURA DE LA TABLA CONVERSATION")
print("=" * 60)

cursor.execute("PRAGMA table_info(conversation);")
columns = cursor.fetchall()

for col in columns:
    print(f"{col[1]} ({col[2]})")

print("\n" + "=" * 60)
print("ESTRUCTURA DE LA TABLA LEAD")
print("=" * 60)

cursor.execute("PRAGMA table_info(lead);")
columns = cursor.fetchall()

for col in columns:
    print(f"{col[1]} ({col[2]})")

print("\n" + "=" * 60)
print("ESTRUCTURA DE LA TABLA ACADEMY")
print("=" * 60)

cursor.execute("PRAGMA table_info(academy);")
columns = cursor.fetchall()

for col in columns:
    print(f"{col[1]} ({col[2]})")

conn.close()