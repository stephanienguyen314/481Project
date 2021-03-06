import sqlite3
import random
from flask import Flask, render_template, request, url_for, flash, redirect, session

# initialize the Flask app
app = Flask(__name__)
app.secret_key = 'Stablecoffee123'

# initialize empty, holds all desired courses; ignore the 'classes' table in schema.sql for now
desired_courses = ['No courses have been selected yet.']
# initialize earliest default start time as 8am - user will have chance to change this
earliest_start = int(800)
# initialize default dismissal time to be 5pm - user will have chance to change this
latest_end = int(1700)

# all times
times = []
for total_time in range(700, 2200, 100):
    for time in range(total_time, total_time + 46, 15):
        times.append(int(time))

# BEGIN HELPER FUNCTIONS
# BEGIN FUNCTIONS WITH DATABASE ACCESSES
# open connection to database
def get_database_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# get all the course titles for display in the dropdown menu in index.html
def getCourseTitles():
    conn = get_database_connection()
    courses = conn.execute('SELECT DISTINCT courseTitle, courseID FROM display').fetchall()
    conn.close()
    return courses

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

# get the user-selected breaks from the breaks database
def getBreaks():
    conn = get_database_connection()
    getData = conn.execute('SELECT * FROM breaks').fetchall()
    conn.close()
    breaks = []
    for i in range(0, len(getData)):
        temp_breaks = range(getData[i]['desiredStartBreak'], getData[i]['desiredEndBreak'])
        breaks.append(temp_breaks)
    return breaks

# get desired breaks for display
def getDisplayBreaks():
    conn = get_database_connection()
    getData = conn.execute('SELECT * FROM breaks').fetchall()
    conn.close()
    return getData

# using a selected courseTitle and sectionID, get the class's lecture times
def getLectureTime(courseTitle, sectionID):

    conn = get_database_connection()

    getData = conn.execute('SELECT lectureStartTime, lectureEndTime FROM courses WHERE courseTitle = ? and sectionID = ?', [courseTitle, sectionID]).fetchall()
    conn.close()
    startTime = getData[0]['lectureStartTime']
    endTime = getData[0]['lectureEndTime']
    return [startTime, endTime]

# determine if a given course and section has a lab component with it
def courseHasLab(courseTitle, sectionID):
    
    conn = get_database_connection()

    getData = conn.execute('SELECT * from courses WHERE courseTitle = ? and sectionID = ?', [courseTitle, sectionID]).fetchall()
    conn.close()
    value = getData[0]['labStartTime']
    if value == 'N':
        return False
    return True

# using a selected courseTitle and sectionID, get the class's lab times
def getLabTime(courseTitle, sectionID):

    conn = get_database_connection()

    getData = conn.execute('SELECT * FROM courses WHERE courseTitle = ? and sectionID = ?', [courseTitle, sectionID]).fetchall()
    conn.close()
    startTime = getData[0]['labStartTime']
    endTime = getData[0]['labEndTime']
    return [startTime, endTime]

# using a selected courseTitle and sectionID, get the class's lecture days
def getLectureDays(courseTitle, sectionID):

    conn = get_database_connection()

    getData = conn.execute('SELECT * FROM courses WHERE courseTitle = ? and sectionID = ?', [courseTitle, sectionID]).fetchall()
    conn.close()
    lectureDays = getData[0]['lectureDays']
    return lectureDays

# using a selected courseTitle and sectionID, get the class's lab days
def getLabDays(courseTitle, sectionID):

    conn = get_database_connection()

    getData = conn.execute('SELECT * FROM courses WHERE courseTitle = ? and sectionID = ?', [courseTitle, sectionID]).fetchall()
    conn.close()
    labDays = getData[0]['labDays']
    return labDays

# using a selected courseTitle, get a random section for that course
def randomSectionSelection(desiredCourseTitle):
    conn = get_database_connection()
    section = conn.execute('SELECT sectionID from courses WHERE courseTitle = ?', [desiredCourseTitle]).fetchall()
    conn.close()

    # randomly select an element from section
    random_section = random.choice(section)

    return random_section['sectionID']

# END FUNCTIONS WITH DATABASE ACCESSES

# using the times list, which contains meeting-day information for the classes in a candidate schedule
# separate it all into a list to start comparing for collisions
def getClassTimes(times):

    examine_for_collisions = []
    for j in range(0, len(times)):
        
        # for classes that have labs
        if (len(times[j]) > 2):
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

            else:
                examine_for_collisions.append([lectureDays, lectureTime])


    return examine_for_collisions

# BEGIN FUNCTIONS USED IN GENETIC ALGORITHM
# BEGIN FUNCTIONS USED IN THE FITNESS FUNCTION
# find if classes within a given candidate solution will collide with each other
def findInternalCollisions(examine_for_collisions):

    temp_collisions = int(0)

    # nested for loop, because we are examining all dates/times with each other
    for a in range(0, len(examine_for_collisions)):
        for b in range(a + 1, len(examine_for_collisions)):
            # only need to compare dates/times for which the days are the same
            if examine_for_collisions[a][0] == examine_for_collisions[b][0]:
                x = examine_for_collisions[a][1]
                y = examine_for_collisions[b][1]
                overlap = max(0, min(x[len(x)-1], y[len(y)-1]) - max(x[0], y[0]))
                #print('x[0] is ' + str(x[0]) + ' and y[0] is ' + str(y[0]))
                #print('x[1] is ' + str(x[1]) + ' and y[1] is ' + str(y[1]))
                #print('overlap is ' + str(overlap))

                if(overlap > 0):
                    temp_collisions = temp_collisions + 1

    return temp_collisions

# find if classes within a given candidate solution collide with the desiredArrival and desiredDismissal times
def findArrivalDismissalCollisions(examine_for_collisions, desiredArrival, desiredDismissal):
    temp_collisions = int(0)

    for a in range(0, len(examine_for_collisions)):
        x = examine_for_collisions[a][1]
        if(x[0] < desiredArrival):
            temp_collisions = temp_collisions + 1
        if(x[len(x)-1] > desiredDismissal):
            temp_collisions = temp_collisions + 1

    return temp_collisions

# find if classes within a given candidate solution collide with the desired break times
def findBreaksCollisions(breaks, examine_for_collisions):
    temp_collisions = int(0)

    for a in range(0, len(examine_for_collisions)):
        for b in range(0, len(breaks)):
            x = examine_for_collisions[a][1]
            y = breaks[b]

            overlap = max(0, min(x[len(x)-1], y[len(y)-1]) - max(x[0], y[0]))

            if(overlap > 0):
                temp_collisions = temp_collisions + 1

    return temp_collisions

# END FUNCTIONS USED IN THE FITNESS FUNCTION

# fitness for this problem is defined as minimizing the number of collisions between the candidate solution
# and the parameters of the problem: classes colliding with each other, classes colliding with 
# desired arrival time and desired dismissal time, and classes colliding with desired break times
def fitness(candidates):

    fitnessEachCandidate = []
    # collision evaluations:
    # 1. do classes collide with each other?
    # 2. do classes collide with desiredArrival and desiredDismissal
    # 3. do classes collide with breaks?

    # first, begin by obtaining all the meeting days/times for each class in each candidate schedule
    
    for j in range(0, len(candidates)):
        # each time we encounter a collision, this number will go up
        collisions = int(0)
        times = []
        # examine 1 candidate solution at a time
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

        # times list contains all the meeting date/time information for the classes within a candidate schedule
        # for example, for CPSC 120, Section 1 and CPSC 121, Section 1,
        # the meeting date is MO 1000-1115 and WE 1000-1245, and
        # TU TH 1430-1530 and TU 1530-1730, respectively
        # times now stores this as [['MO', range(1000, 1115), 'FR', range(1300, 1545)]], ['MO WE', range(1200, 1250), 'MO', range(1300, 1500)]]
        # then, this information is separated so that each meeting day/time is separated into its own list entry
        # for example, ['MO WE', range(1200, 1250)] will become ['MO', range(1200, 1250)], ['WE', range(1200, 1250)]
        examine_for_collisions = getClassTimes(times)

        # 1. evaluate collisions with each other, meaning for example if the candidate solution is:
        # [[CPSC 120, Section 1], [CPSC 121, Section 1], and [CPSC 131, Section 1]], do these 3 collide with each other?
        internalCollisions = findInternalCollisions(examine_for_collisions)

        # add the number of internal collisions to the total collisions count for this candidate solution
        collisions = collisions + int(internalCollisions)

        # 2. evaluate collisions with desiredArrival and desiredDismissal, meaning
        # no class can start earlier than the user inputted desired arrival time and no later than 
        # the user inputted desired dismissal time
        desiredArrival = getEarly()
        desiredDismissal = getEnd()

        arrivalDismissalCollisions = findArrivalDismissalCollisions(examine_for_collisions, desiredArrival, desiredDismissal)
        # add the number of collisions to the total collisions count for this candidate solution
        collisions = collisions + int(arrivalDismissalCollisions)

        # 3. evaluate collisions with breaks, meaning
        # no class should be happening during any of the user selected break periods
        breaks = getBreaks()
        breaksCollisions = findBreaksCollisions(breaks, examine_for_collisions)
        # add the number of collisions to the total collisions count for this candidate solution
        collisions = collisions + int(breaksCollisions)

        # finally, append the number of collisions to the fitnessEachCandidate list;
        # the indices of fitnessEachCandidate correspond to the indices of candidates list
        # so that they match up with each other
        fitnessEachCandidate.append(collisions)

    # return the fitnessEachCandidate list, which will be used to determined viable solutions in generated() method
    # viable solutions are solutions where the number of collisions is 0.
    return fitnessEachCandidate

# takes 2 candidate solutions and crosses them over with each other
# to produce 2 new child candidate solutions
def crossover(candidate1, candidate2, candidates):

    # used for "cutting" the 2 candidate solutions
    slice1candidate1 = []
    slice1candidate2 = []
    slice2candidate1 = []
    slice2candidate2 = []

    # because we need an integer; result rounds down
    # so for example, 5 // 2 = int(2.5) = 2
    half = len(candidate1) // 2

    # cut the first half of candidate1 and first half of candidate2
    for a in range(0, half):
        slice1candidate1.append(candidate1[a])
        slice1candidate2.append(candidate2[a])

    # cut the second half of candidate1 and second half of candidate 2
    for b in range(half, len(candidate1)):
        slice2candidate1.append(candidate1[b])
        slice2candidate2.append(candidate2[b])

    # cross them over with each other
    child1 = (slice1candidate1 + slice2candidate2)
    child2 = (slice1candidate2 + slice2candidate1)
    # in nature, chance of mutation is about 1/2
    chance1 = random.choice([1, 2])
    chance2 = random.choice([1, 2])
    # if chance is true, perform mutation on child1
    if(chance1 == 1):
        child1 = mutation(child1)
    if(chance2 == 1):
        child2 = mutation(child2)

    # and append them to candidates list, which contains
    # all possible candidate solutions

    candidates.append(child1)
    candidates.append(child2)

    # return candidates list
    return candidates

def mutation(candidate):

    # pick a random course in the candidate schedule
    randomSelection = random.choice(candidate)
    # get that random course's courseTitle
    courseTitle = randomSelection[0]
    # get a random section from that course to replace the current section with
    sectionID = randomSectionSelection(courseTitle)

    # replace the old value in candidate with the new value
    candidate = [[courseTitle, sectionID] if x==[courseTitle, randomSelection[1]] else x for x in candidate]
    
    return candidate

# END GENETIC ALGORITHM FUNCTIONS

# BEGIN ENDPOINTS
@app.route('/')
@app.route('/index', methods=["GET"])
def index():
    courses = getCourseTitles()

    return render_template('index.html', courses=courses, desiredcourses=desired_courses, desiredlength = len(desired_courses), 
    times=times, earliest_start=getEarly(), latest_end=getEnd(), desiredbreaks = getDisplayBreaks(), desiredbreakslength = len(getDisplayBreaks()))

@app.route('/generate')
def generate():
    # this is where we execute the local search algorithm; this uses a genetic algorithm
    # generate a limited list of possible candidates,
    # and then perform evolution on them, thus getting other candidates,
    # and then evaluate them against a fitness function to make sure that all constraints are met
    # the candidates where there are no collisions will be returned to the user


    # generate possible candidates
    # get list of all desired courses and for each element in this list, randomly select a section and push it to the candidates dictionary
    # randomly generate 20 candidate solutions; this number can be increased, and a more exhaustive set of solutions likely to result
    candidates = []
    for j in range(0, 20):
        temp = []
        for i in range(0, len(desired_courses)):
            # get random section selection
            # add courseTitle, sectionID as a list to candidates
            section = randomSectionSelection(desired_courses[i])
            temp.append([desired_courses[i], section])
        candidates.append(temp)

    # take current candidates and perform crossover on them
    # then append these new crossed-over candidates to the candidates list
    # mutation is done inside crossover() function as well
    for s in range(0, 7):
        for r in range(0, len(candidates), 2):
            candidates = crossover(candidates[r], candidates[r+1], candidates)

        # evaluate fitness
        fitnessCandidates = fitness(candidates)

        viableSolutions = []

        # this is "killing" the unfit candidate solutions in the population
        # allowing only the ones with 2 or fewer collisions to survive, and we will perform 
        # crossover and mutation on them again
        for k in range(0, len(fitnessCandidates)):
            if(fitnessCandidates[k] <= 2):
                viableSolutions.append(k)

        survivors = []
        # store surviving candidate solutions
        for w in range(0, len(viableSolutions)):
            survivors.append(candidates[viableSolutions[w]])

        # if no viable solutions, where the number of collisions is less than or equal to 2 exist
        # that means no one in the population has survived to reproduce other candidate solutions
        # thus, we end the loop and return an empty list
        # if there is only 1 viable solution that has survived, then we also need to end the loop
        # because you need at least 2 candidate solutions to have crossovers and reproduce
        if((len(viableSolutions) == 0) or (len(viableSolutions) == 1)):
            break
        # if we find two or more candidate solutions, then keep going with more generations
        else:
            candidates = survivors

    # now, make sure that viableSolutions only contains candidates whose fitness value is 0
    fitnessCandidates = fitness(candidates)

    viableSolutions = []

    # this is "killing" the unfit candidate solutions in the population
    # allowing only the ones with 2 or fewer collisions to survive, and we will perform 
    # crossover and mutation on them again
    for q in range(0, len(fitnessCandidates)):
        if(fitnessCandidates[q] == 0):
            viableSolutions.append(q)

    if(len(viableSolutions) > 0):
        print('viable solutions have been found')
        print('viableSolutions is ' + str(viableSolutions))
        #print('candidates are ' + str(candidates))
    else:
        print('no viable solutions found')

    finalAnswer = []
    for a in range(0, len(viableSolutions)):
        finalAnswer.append(candidates[viableSolutions[a]])

    # remove duplicates from finalAnswer
    if not finalAnswer:
        collision_number = 'found'
    else:
        collision_number = 'empty'

    res = [] 
    [res.append(x) for x in finalAnswer if x not in res] 

    return render_template('generated.html', finalAnswers=res, collision_number = collision_number)

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
    
        if(desired_courses[0] == 'No courses have been selected yet.'):
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
