
CREATE TABLE departments (
    dept_id SERIAL PRIMARY KEY,
    dept_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    age INT CHECK (age >= 18),
    dept_id INT,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

INSERT INTO departments (dept_name)
VALUES
('Computer Science'),
('Geoinformatics'),
('Mathematics'),
('Physics'),
('Electronics');

INSERT INTO students (name, age, dept_id)
VALUES
('Tanuja', 23, 1),
('Pooja', 22, 2),
('Teju', 24, 3),
('Le', 21, 4),
('Sneha', 23, 5);

INSERT INTO students (name, age, dept_id)
VALUES
('Deepika', 23, 1),
('Grace', 22, 2),
('Nita', 24, 2),
('Lekha', 21, 4),
('Jahan', 23, 4);

SELECT name, age
FROM students
ORDER BY age DESC;

SELECT name
FROM students
WHERE age > 21 AND dept_id = 2;

SELECT students.name, departments.dept_name
FROM students
INNER JOIN departments
ON students.dept_id = departments.dept_id;

SELECT AVG(age) AS average_age
FROM students;

SELECT dept_id, COUNT(*) AS student_count
FROM students
GROUP BY dept_id;

SELECT dept_id, COUNT(*) AS student_count
FROM students
GROUP BY department_id
HAVING COUNT(*) > 2;

SELECT departments.dept_name, COUNT(students.student_id) AS total_students
FROM departments
LEFT JOIN students
ON departments.dept_id = students.dept_id
GROUP BY departments.dept_name;

UPDATE students
SET age = 25
WHERE name = 'Teju';

DELETE FROM students
WHERE student_id = 5;

CREATE VIEW student_view AS
SELECT 
    students.student_id,
    students.name,
    departments.dept_name,
    students.age
FROM students
INNER JOIN departments
ON students.dept_id = departments.dept_id;

SELECT * FROM student_view;

SELECT *
FROM student_view
WHERE age > 22;