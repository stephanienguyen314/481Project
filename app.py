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
    cursor = conn.cursor()
    cursor.execute('INSERT INTO breaks (desiredStartBreak, desiredEndBreak) VALUES (?,?)', (desiredStart, desiredEnd))
    conn.commit()
    cursor.close()
    conn.close()

def getBreaks():
    conn = get_database_connection()
    getData = conn.execute('SELECT * FROM breaks').fetchall()
    conn.close()
    breaks = []
    for i in range(0, len(getData)):
        temp_breaks = range(getData[i]['desiredStartBreak'], getData[i]['desiredEndBreak'])
        breaks.append(temp_breaks)
    
    return breaks

def getLectureTime(courseTitle, sectionID):

    conn = get_database_connection()

    getData = conn.execute('SELECT lectureStartTime, lectureEndTime FROM courses WHERE courseTitle = ? and sectionID = ?', [courseTitle, sectionID]).fetchall()
    conn.close()
    startTime = getData[0]['lectureStartTime']
    endTime = getData[0]['lectureEndTime']
    return [startTime, endTime]

def courseHasLab(courseTitle, sectionID):
    
    conn = get_database_connection()

    getData = conn.execute('SELECT * from courses WHERE courseTitle = ? and sectionID = ?', [courseTitle, sectionID]).fetchall()
    conn.close()
    value = getData[0]['labStartTime']
    if value == 'N':
        return False
    return True

def getLabTime(courseTitle, sectionID):

    conn = get_database_connection()

    getData = conn.execute('SELECT * FROM courses WHERE courseTitle = ? and sectionID = ?', [courseTitle, sectionID]).fetchall()
    conn.close()
    startTime = getData[0]['labStartTime']
    endTime = getData[0]['labEndTime']
    return [startTime, endTime]

def getLectureDays(courseTitle, sectionID):

    conn = get_database_connection()

    getData = conn.execute('SELECT * FROM courses WHERE courseTitle = ? and sectionID = ?', [courseTitle, sectionID]).fetchall()
    conn.close()
    lectureDays = getData[0]['lectureDays']
    return lectureDays

def getLabDays(courseTitle, sectionID):

    conn = get_database_connection()

    getData = conn.execute('SELECT * FROM courses WHERE courseTitle = ? and sectionID = ?', [courseTitle, sectionID]).fetchall()
    conn.close()
    labDays = getData[0]['labDays']
    return labDays

def getClassTimes(times):

    examine_for_collisions = []
    for j in range(0, len(times)):

        # for classes that have labs
        if len(times[j])> 2:
            lectureDays = str(times[j][0])
            lectureTime = times[j][1]

            if(len(lectureDays) > 2):
                splitLectureDays = lectureDays.split()

                for p in range(0, len(splitLectureDays)):
                    examine_for_collisions.append([splitLectureDays[p], lectureTime])

            else:
                examine_for_collisions.append([lectureDays, lectureTime])

            labDays = str(times[j][2]) 
            labTime = times[j][3]

            if(len(labDays) > 2):
                splitLabDays = labDays.split()
                print('splitLabDays is ' + str(splitLabDays))
                for o in range(0, len(splitLabDays)):
                    examine_for_collisions.append([splitLabDays[o], labTime])

            else:
                examine_for_collisions.append([labDays, labTime])

        # for classes with just lecture
        else:
            lectureDays = str(times[j][0])
            lectureTime = times[j][1]

            if(len(lectureDays) > 2):
                splitLectureDays = lectureDays.split()
                for q in range(0, len(splitLectureDays)):
                    examine_for_collisions.append([splitLectureDays[q], lectureTime])

    return examine_for_collisions

def findInternalCollisions(candidates, times):

    temp_collisions = int(0)

    examine_for_collisions = getClassTimes(times)
    print('examine_for_collisions is ' + str(examine_for_collisions))

    for a in range(0, len(examine_for_collisions)):
        for b in range(a + 1, len(examine_for_collisions)):
            if examine_for_collisions[a][0] == examine_for_collisions[b][0]:
                x = examine_for_collisions[a][1]
                y = examine_for_collisions[b][1]
                overlap = max(0, min(x[1], y[1]) - max(x[0], y[0]))

                if(overlap > 0):
                    temp_collisions = temp_collisions + 1

    return temp_collisions
        
def findArrivalDismissalCollisions(candidates, times, desiredArrival, desiredDismissal):
    temp_collisions = int(0)
    examine_for_collisions = getClassTimes(times)

    for a in range(0, len(examine_for_collisions)):
        
        if(min(examine_for_collisions[a][1]) < desiredArrival):
            temp_collisions = temp_collisions + 1
        if(max(examine_for_collisions[a][1]) + 1 > desiredDismissal):
            temp_collisions = temp_collisions + 1

    return temp_collisions

def findBreaksCollisions(breaks, candidates, times):
    temp_collisions = int(0)
    examine_for_collisions = getClassTimes(times)

    for a in range(0, len(examine_for_collisions)):
        for b in range(0, len(breaks)):
            x = examine_for_collisions[a][1]
            y = breaks[b]
            overlap = max(0, min(x[1], y[1]) - max(x[0], y[0]))

            if(overlap > 0):
                temp_collisions = temp_collisions + 1

    return temp_collisions

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

    fitnessEachCandidate = []
    # collision evaluations:
    # 1. do classes collide with each other?
    # 2. do classes collide with desiredArrival and desiredDismissal
    # 3. do classes collide with breaks?

    # 1. evaluate collisions with each other
    for j in range(0, len(candidates)):
        # each time we encounter a collision, this number will go up
        collisions = int(0)
        times = []
        for i in range(0, len(desired_courses)):
            meetingInfo = []
            courseTitle = candidates[j][i][0]
            sectionID = candidates[j][i][1]

            lectureDays = getLectureDays(courseTitle, sectionID)
            meetingInfo.append(lectureDays)

            # returns an array with lectureStartTime and lectureEndTime
            lectureTimes = getLectureTime(courseTitle, sectionID)
            meetingInfo.append(range(lectureTimes[0], lectureTimes[1]))
            
            hasLab = courseHasLab(courseTitle, sectionID)

            if (hasLab):
                labDays = getLabDays(courseTitle, sectionID)
                meetingInfo.append(labDays)

                labTimes = getLabTime(courseTitle, sectionID)
                meetingInfo.append(range(labTimes[0], labTimes[1]))

            times.append(meetingInfo)

        internalCollisions = findInternalCollisions(candidates, times)

        collisions = collisions + int(internalCollisions)

        # 2. evaluate collisions with desiredArrival and desiredDismissal
        desiredArrival = getEarly()
        desiredDismissal = getEnd()

        arrivalDismissalCollisions = findArrivalDismissalCollisions(candidates, times, desiredArrival, desiredDismissal)

        collisions = collisions + int(arrivalDismissalCollisions)

        # 3. evaluate collisions with breaks
        breaks = getBreaks()
        breaksCollisions = findBreaksCollisions(breaks, candidates, times)
        collisions = collisions + int(breaksCollisions)

        print('total number of collisions is ' + str(collisions))

        fitnessEachCandidate.append(collisions)

    return fitnessEachCandidate

def crossover():
    pass

def mutation():
    pass

@app.route('/')
@app.route('/index', methods=["GET"])
def index():
    courses = getCourseTitles()

    return render_template('index.html', courses=courses, desiredcourses=desired_courses, desiredlength = len(desired_courses), 
    times=times, earliest_start=getEarly(), latest_end=getEnd())

@app.route('/generate')
def generate():
    # this is where we execute the local search algorithm; this uses a genetic algorithm
    # genetic algorithm likely to work best
    # generate a limited list of possible candidates,
    # and then perform evolution on them, thus getting other candidates,
    # and then evaluate them against a fitness function to make sure that all constraints are met
    # the candidates where there are no collisions will be returned to the user


    # generate possible candidates
    # get list of all desired courses and for each element in this list, randomly select a section and push it to the candidates dictionary
    # randomly generate 15 candidate solutions; this number can be increased
    candidates = []
    for j in range(0, 20):
        temp = []
        for i in range(0, len(desired_courses)):
            # get random section selection
            # add courseTitle, sectionID as a list to candidates
            section = randomSectionSelection(desired_courses[i])
            temp.append([desired_courses[i], section])
        candidates.append(temp)
    print(str(candidates))

    # take current candidates and perform crossover on them twice
    # then append these new crossed-over candidates to the candidates list

    # take current candidates and perform mutation on them
    # then append these new mutated candidates to the candidates list
    
    fitnessCandidates = fitness(candidates)

    viableSolutions = []

    for k in range(0, len(fitnessCandidates)):
        if(fitnessCandidates[k] == 0):
            viableSolutions.append(k)

    finalAnswer = []
    for a in range(0, len(viableSolutions)):
        finalAnswer.append(candidates[viableSolutions[a]])

    print('the final answer is ' + str(finalAnswer))
    return render_template('generated.html')

# display individual course information
# course.html will render course title, and all lecture/lab times and give option for student to select that specific course to enroll in
@app.route('/display_course', methods=['GET', 'POST'])
def display_course():
    # post = get_post(id)
    # comments = get_comments(id)

    # return render_template('post.html', comments=comments, post=post)
    courses = getCourseTitles()
    if request.method == 'POST':
        course = request.form.get('courses')
    
        if(desired_courses[0] == 'no courses selected yet'):
            desired_courses[0] = course
        else:
            desired_courses.append(course)
    
        return redirect(url_for('index'))

    return render_template('course.html', courses=courses)

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

        print('desiredStart is ' + str(desiredStart))
        print('desiredEnd is ' + str(desiredEnd))

        setInputBreaks(desiredStart, desiredEnd)

        return redirect(url_for('index'))

    return render_template('set_breaks.html', times=times)


if __name__ == "__main__":
 app.run(debug = True)
