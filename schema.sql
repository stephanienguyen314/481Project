DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS display;
DROP TABLE IF EXISTS desired;
DROP TABLE IF EXISTS classes;
DROP TABLE IF EXISTS breaks;
DROP TABLE IF EXISTS candidates;

CREATE TABLE courses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  courseTitle TEXT NOT NULL,
  courseID INT NOT NULL,
  sectionID INT NOT NULL,
  lectureStartTime INT NOT NULL,
  lectureEndTime INT NOT NULL,
  lectureDays TEXT NOT NULL,
  labStartTime INT NOT NULL,
  labEndTime INT NOT NULL,
  labDays TEXT NOT NULL
);

CREATE TABLE display (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    courseTitle TEXT NOT NULL,
    courseID INT NOT NULL
);

CREATE TABLE desired (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    desiredStart INT NOT NULL,
    desiredEnd INT NOT NULL
);

CREATE TABLE classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    className TEXT NOT NULL
);

CREATE TABLE breaks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    desiredStartBreak INT NOT NULL,
    desiredEndBreak INT NOT NULL
);

CREATE TABLE candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    courseTitle TEXT NOT NULL,
    courseID TEXT NOT NULL
);
