import csv
import sqlite3

connection = sqlite3.connect('database.db')

with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

with open('ALL_COURSES.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        cur.execute('INSERT INTO courses (courseTitle, courseID, sectionID, lectureStartTime, lectureEndTime, lectureDays, labStartTime, labEndTime, labDays) VALUES (?,?,?,?,?,?,?,?,?)', 
        (row['courseTitle'], row['courseID'], row['sectionID'], row['lectureStartTime'],
        row['lectureEndTime'], row['lectureDays'], row['labStartTime'], row['labEndTime'], row['labDays']))

        cur.execute('INSERT INTO display (courseTitle, courseID) VALUES (?,?)', 
        (row['courseTitle'], row['courseID']))

cur.execute('INSERT INTO desired (name, desiredStart, desiredEnd) VALUES (?,?,?)', ('user', 800, 1700))
cur.execute('INSERT INTO classes (className) VALUES (?)', ('No classes have been selected.',))

connection.commit()
connection.close()

