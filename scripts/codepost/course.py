"""
A class and module to support an entire course.  A
course is connected to both a Canvas course as well
as a CSE course account.

This module loads data from the Canvas course using 
its API (see canvas.py) and then interfaces with the
CSE User Database (see udb.py) to connect users with
their CSE logins.

Using the configuration module (see config.py), users
are separated according to instructors (non-graders),
graders, and students.  If a user cannot be connected
to a CSE login, they are separated into an "orphan"
group.

The Course class itself maintains these groups both
as lists of NUIDs (strings) and maps of NUID => Person (object).

When used as an executable file, all course data is 
loaded and printed to the standard output.  Otherwise, 
a global object (course) is made available.  

In addition to the course data, two functions provide
functionality to randomly create a grading assignment 
(see getAssignment() and assignmentToString()).
"""

from config import config
from canvas import roster
from canvas import groups
import udb
import copy
import math
import random

class Course:
    #all persons will be by NUID
    instructorNuids = []
    instructors = {}

    graderNuids = []
    graders = {}
    
    students = {}
    groups = []
    
    #students with no cse login for some reason
    orphans = {}
    
    def __init__(self, instructorNuids = [], graderNuids = []):
        self.instructorNuids = instructorNuids
        self.graderNuids = graderNuids
        # 1. load full roster and groups from canvas
        # {NUID => Person}
        self.roster = roster
        # [Group]
        self.groups = groups
        # 2. get as many cse logins as possible
        # 2a. dump NUIDs to map
        nuids = self.roster.keys()
        nuidsToCseLogins = dict(zip(nuids, [None for x in nuids]))
        # 2b. update from UDB
        nuidsToCseLogins = udb.mapNuidsToCseLogins(nuidsToCseLogins,config.nuidToCseLoginPickle)
        # 2c. update cse logins for all roster instances
        for nuid,p in self.roster.items():
          if nuid in nuidsToCseLogins and nuidsToCseLogins[nuid] is not None:
            p.cseLogin = nuidsToCseLogins[nuid]
                
        #3. filter into the appropriate group
        #   This is done manually as the "role" is not available from canvas 
        #   using the canvas API and we want more fine-grained control anyway
        #   - If there is no cse login, they are "orphaned"
        #   - Otherwise, they are either a student XOR instructor/grader
        #     - instructors can be graders
        for nuid,p in self.roster.items():
            if p.cseLogin is None:
                self.orphans[nuid] = p
            else:
                if nuid in instructorNuids or nuid in graderNuids:
                    if nuid in instructorNuids: 
                        self.instructors[nuid] = p
                    if nuid in graderNuids: 
                        self.graders[nuid] = p
                else:
                    self.students[nuid] = p

    def __str__(self):
        r = "Instructors (%d): \n"%(len(self.instructors))
        for nuid,p in self.instructors.items():
            r += str(p) + "\n"
        r += "Graders (%d): \n"%(len(self.graders))
        for nuid,p in self.graders.items():
            r += str(p) + "\n"
        r += "Students (%d): \n"%(len(self.students))
        for nuid,p in self.students.items():
            r += str(p) + "\n"
        r += "Orphans (%d): \n"%(len(self.orphans))
        for nuid,p in self.orphans.items():
            r += str(p) + "\n"
        return r

    def getGradingAssignment(self):
        """
        Returns a randomized mapping of graders (Person objects) 
        to a list of students (Group objects) they are assigned 
        to grade.
        
        Assignments are made in a round-robin manner so that the 
        same grader(s) are not always assigned more (or fewer) to
        grade.
        """
        graderNuids = list(self.graders.keys())
        groups = copy.deepcopy(self.groups)
        random.shuffle(graderNuids)
        random.shuffle(groups)
        assignment = {}
        #initialize lists 
        for gNuid in graderNuids:
            assignment[self.graders[gNuid]] = []
        i = 0        
        n = len(graderNuids)
        for group in groups:
            g = self.graders[graderNuids[i]]
            assignment[g].append(group)
            i = (i+1)%n
        return assignment

    def assignmentToString(self,assignment):
        """
        Given an assignment (a mapping of Person objects to a
        list of Person objects) as generated by getAssignment(), 
        this function will create a human-readable string of the
        grading assignments.  For convenience, the printed string
        is in order of name for both graders and students
        """
        r  = "Assigned Grading\n"
        r += "================\n"
        min = math.floor(len(self.students) / len(self.graders))
        max = math.ceil(len(self.students) / len(self.graders))
        r += "Each grader will grade %d - %d students\n"%(min,max)
        #dump graders to list of Person objects
        graders = list(assignment.keys())
        graders.sort(key=lambda x: x.name)
        for grader in graders:
          groups = assignment[grader];
          groups.sort(key=lambda x: x.members[0].name)
          n = len(groups)
          r += "%s (%d assigned)\n"%(grader.name,n)
          for g in groups:
            r += str(g)
        return r

course = Course(instructorNuids=config.instructorNuids, 
                graderNuids=config.graderNuids)
"""
The course object for this module initialized with with
the course data defined in config.py
"""

def printCourse():
    print(course)
    print("\n\n===== Student Emails (for Piazza) =====\n");
    for nuid,p in course.students.items():
        print(p.canvasEmail);

if __name__ == "__main__":
    printCourse()
