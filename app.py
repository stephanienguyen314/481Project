import sqlite3
import random
from flask import Flask, render_template, request, url_for, flash, redirect, session
from werkzeug.exceptions import abort

# initialize the Flask app
app = Flask(__name__)
app.secret_key = 'Stablecoffee123'

# initialize empty, holds all desired courses; ignore the 'classes' table in schema.sql for now
desired_courses = ['no courses selected yet']
# initialize earliest default start time as 8am - user will have chance to change this
earliest_start = int(800)
# initialize default dismissal time to be 5pm - user will have chance to change this
latest_end = int(1700)

# all times
times = []
for total_time in range(700, 2200, 100):
    for time in range(total_time, total_time + 46, 15):
        times.append(int(time))

# open connection to database
def get_database_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# remove this; no longer needed
def get_display_connection():
    conn = sqlite3.connect('display.db')
    conn.row_factory = sqlite3.Row
    return conn

# get all the course titles for display in the dropdown menu in index.html
def getCourseTitles():
    conn = get_database_connection()
    courses = conn.execute('SELECT DISTINCT courseTitle, courseID FROM display').fetchall()
    conn.close()
    return courses

# get the course title from the ID of the course
def getCourseFromID(id):
    print(str(id))
    conn = get_display_connection()
    desiredcourse = conn.execute('SELECT courseTitle from display WHERE courseID = ?', [id]).fetchone()
    conn.close()
    return desiredcourse['courseTitle']

# set the earliest arrival time
def setEarly(time):
    conn = get_database_connection()
    conn.execute('UPDATE desired SET desiredStart = ? where NAME = ?', (time, 'user'))
    conn.commit()
    conn.close()

# get the earliest arrival time
def getEarly():
    conn = get_database_connection()
    earliestTime = conn.execute('SELECT desiredStart from desired').fetchone()
    conn.close()
    return earliestTime['desiredStart']

# set the dismissal time
def setDismissal(time):
    conn = get_database_connection()
    conn.execute('UPDATE desired SET desiredEnd = ? where NAME = ?', (time, 'user'))
    conn.commit()
    conn.close()

# get the dismissal time
def getEnd():
    conn = get_database_connection()
    earliestTime = conn.execute('SELECT desiredEnd from desired').fetchone()
    conn.close()
    return earliestTime['desiredEnd']

# input breaks into breaks database
def setInputBreaks(desiredStart, desiredEnd):
    conn = get_database_connection()
    conn.execute('INSERT INTO breaks (desiredStartBreak, desiredEndBreak) VALUES (?,?)', (desiredStart, desiredEnd))
    conn.commit()
    conn.close()

# NOT IN USE
def setClasses(desiredCourseTitle):
    conn = get_database_connection()
    conn.execute('INSERT INTO classes (className) VALUES (?)', (desiredCourseTitle,))
    conn.commit()
    conn.close()

# NOT IN USE
def getClasses():
    conn = get_database_connection()
    allClasses = conn.execute('SELECT * from classes').fetchall()
    conn.close()
    print('WHY WONT U WORK')
    print(str(allClasses['className']))
    return allClasses['className']

def randomSectionSelection(desiredCourseTitle):
    conn = get_database_connection()
    section = conn.execute('SELECT sectionID from courses WHERE courseTitle = ?', [desiredCourseTitle]).fetchall()
    conn.close()

    # randomly select an element from section
    random_section = random.choice(section)

    return random_section['sectionID']

def fitness(candidates):
    conn = get_database_connection()
    number_desired_courses = len(desired_courses)
    for j in range(0, len)
    # get the lectureStart and lectureEnd times
    #for j in range(0, len(candidates)):
    #    for i in candidates[j]:
    #        print(i, candidates[j][i]) 
        
        #lectureStart = conn.execute('SELECT lectureStartTime from courses WHERE courseTitle, courseID = (?,?)', 
        #[ candidates_list.get(candidates_list[i]), candidates_list.get])
    # get the labStart and labEnd times if applicable
    # get the desired arrival and dismissal times
    # get the desired break times
    # look for collisions, and then return the number of collisions
    pass

@app.route('/')
@app.route('/index', methods=["GET"])
def index():
    courses = getCourseTitles()

    return render_template('index.html', courses=courses, desiredcourses=desired_courses, desiredlength = len(desired_courses), 
    times=times, earliest_start=getEarly(), latest_end=getEnd())

@app.route('/generate')
def generate():
    # this is where we execute the local search algorithm
    # genetic algorithm likely to work best
    # generate all possible candidates, and then perform evolution on them and evaluate them against a fitness function to make sure that all constraints are met

    # generate all possible candidates
    # get list of all desired courses and for each element in this list, randomly select a section and push it to the candidates dictionary
    # randomly generate 50 candidate solutions; this number can be increased
    candidates = []
    for j in range(0, 50):
        for i in range(0, len(desired_courses)):
            # get random section selection
            # add courseTitle, sectionID as a list to candidates
            section = randomSectionSelection(desired_courses[i])
            candidates.append([desired_courses[i], section])
    print(str(candidates))
    fitness(candidates)

    # fitness function: for this problem, means reducing the number of clashes in the schedule


    return render_template('generated.html')


# display individual course information
# course.html will render course title, and all lecture/lab times and give option for student to select that specific course to enroll in
@app.route('/<int:id>', methods=['GET', 'POST'])
def display_course(id):
    # post = get_post(id)
    # comments = get_comments(id)

    # return render_template('post.html', comments=comments, post=post)
    
    if(desired_courses[0] == 'no courses selected yet'):
        desiredCourseTitle = getCourseFromID(id)
        desired_courses[0] = desiredCourseTitle
    else:
        desiredCourseTitle = getCourseFromID(id)
        desired_courses.append(desiredCourseTitle)
    
    return redirect(url_for('index'))

# endpoint for setting arrival time
@app.route('/set_early', methods=['GET', 'POST'])
def set_early():

    if request.method == 'POST':
        desiredArrival = request.form.get('desiredArrival')
        setEarly(desiredArrival)
        return redirect(url_for('index'))

    return render_template('set_early.html', times=times)

# endpoint for setting dismissal time
@app.route('/set_dismissal', methods=['GET', 'POST'])
def set_dismissal():

    if request.method == 'POST':
        desiredDismissal = request.form.get('desiredDismissal')
        setDismissal(desiredDismissal)
        return redirect(url_for('index'))

    return render_template('set_dismissal.html', times=times)

# endpoint to set breaks
@app.route('/set_breaks', methods=['GET', 'POST'])
def set_breaks():

    if request.method == 'POST':
        # read from user submission
        desiredStart = request.form.get('desiredStartBreak')
        desiredEnd = request.form.get('desiredEndBreak')


        setInputBreaks(desiredStart, desiredEnd)

        return redirect(url_for('index'))

    return render_template('set_breaks.html', times=times)

# functions to show html; will be combined with ^ endpoints
@app.route('/course')
def render_course():
    courses = getCourseTitles()
    return render_template('course.html', courses=courses)


if __name__ == "__main__":
 app.run(debug = True)
