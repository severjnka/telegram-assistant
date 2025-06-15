import sqlite3
import csv

# Можно указать тип для фильтрации (например, 'idea', 'complaint', 'question', 'feedback', 'other')
FILTER_TYPE = None  # Например, 'idea' или None для всех

conn = sqlite3.connect("assistant_data.db")
cur = conn.cursor()

rows = []
if FILTER_TYPE:
    query = "SELECT id, type, user_id, username, text, date FROM messages WHERE type=? ORDER BY date DESC"
    for row in cur.execute(query, (FILTER_TYPE,)):
        rows.append(row)
else:
    query = "SELECT id, type, user_id, username, text, date FROM messages ORDER BY date DESC"
    for row in cur.execute(query):
        rows.append(row)

# Вывод в консоль
print("id | type | user_id | username | text | date")
print("-" * 100)
for row in rows:
    print(row)

# Экспорт в CSV
with open("collected_data.csv", "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "type", "user_id", "username", "text", "date"])
    writer.writerows(rows)

print("Данные экспортированы в collected_data.csv")

conn.close()