#!/usr/bin/python

import sys
import re
import os
import os.path
import xml.etree.cElementTree as ET

# from http://infix.se/2007/02/06/gentlemen-indent-your-xml
def ETindent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for e in elem:
            ETindent(e, level+1)
            if not e.tail or not e.tail.strip():
                e.tail = i + "  "
        if not e.tail or not e.tail.strip():
            e.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


ClassSize = 30

class FetGen():
    def __init__(self):
        self.hours     = [ "09:00", "10:00", "11:00", "13:00", "14:00" ]
        self.days      = [ "Mon", "Tues", "Wed", "Thu", "Fri" ]
#        self.years     = [ str(y) for y in range(7, 13+1) ]
# only doing jnr school for now
# and only doing core subjects
#        self.years     = [ "7", "8" ]
        self.years     = [ "9" ]
        self.houses    = [ "Rata", "Tawa", "Miro" ]
        self.studentIds= [ str(y) for y in range(7, 13+1) ]

        # houses is an example of a category
        # Rata House is an example of a division of a category
        self.core      = [ "PE", "Eng", "Soc", "Math", "Sci" ]
        # each option line is another category?
        # Japanese is an example of the division of a category
        #self.optChoices  = [ [ "Ital", "Art1", "Tech", "Jap" ],
        #                     [ "Lat",  "Art2", "Acc",  "Comp" ] ]
        #self.options   = sum(self.optChoices, [])
        #print self.options
        self.coreGrps  = [ y+h for y in self.years for h in self.houses ]
        #self.optGrps   = [ y+o for y in self.years for o in self.options ]
        self.subjects  = [ g+t for g in self.coreGrps for t in self.core ] 
        #                  self.optGrps)
        self.teachers  = { "Art1"    : [ "Apple" ],
                           "Art2"    : [ "Long" ],
                           "Comp"    : [ "Edison" ],
                           "Eng"     : [ "Green", "Quayle", "Jingle" ],
                           "Ita"     : [ "Knight" ],
                           "Jap"     : [ "Plum" ],
                           "Lat"     : [ "Jingle" ],
                           "Math"    : [ "Falkirk", "Hill" ],
                           "PE"      : [ "White",   "Nielsen" ],
                           "Sci"     : [ "Orange",  "Edison" ],
                           "Soc"     : [ "Brown",   "Indigo"  ],
                           "Tech"    : [ "Coral",   "Mustard" ] }
        self.rooms = [ r+str(n) for r in "ABC" for n in range(1, 3) ]
#                      [ "Lab"+str(n) for n in range(1, 6) ] +
#                      [ "Tech"+str(n) for n in range(1, 4) ] +
#                      [ "CompLab" ] )
                         
        self.fet = ET.Element("FET")

    def getTeacher(self, subject):
        teachers = self.teachers[subject]
        teacher = teachers.pop(0)
        teachers.append(teacher)
        return teacher

    def getTeachers(self):
        names = []
        for nameList in self.teachers.itervalues():
            for name in nameList:
                if name not in names:
                    names.append(name)
        names.sort()
        return names

    def getRoom(self):
        # TODO research generators again!!!
        rooms = self.rooms
        room = rooms.pop(0)
        rooms.append(room)
        return room

    def write(self):
        root = self.genXml()
        ETindent(root) 
        doc = ET.ElementTree(root)
        #print tostring(root)
        #doc.write(sys.stdout, method="xml", encoding="utf-8")
        print '<?xml version="1.0" encoding="utf-8"?>'
        print '<!DOCTYPE FET>\n'
        doc.write(sys.stdout)
        print '\n\n'

    def genXml(self):
        fet = ET.Element("FET")
        fet.attrib["version"] = "5.9.0"
        ET.SubElement(fet, "Institution_Name").text = "Imaginary High School";
        fet.append(self.genHours())
        fet.append(self.genDays())
        fet.append(self.genStudents())
        fet.append(self.genTeachers())
        fet.append(self.genSubjects())
        fet.append(self.genActivityTags())
        fet.append(self.genActivities())
        fet.append(self.genBuildings())
        fet.append(self.genRooms())
        fet.append(self.genTimeConstraints())
        fet.append(self.genSpaceConstraints())
        return fet

    def genHours(self):
        hours = ET.Element("Hours_List")
        ET.SubElement(hours, "Number").text = str(len(self.hours))
        for h in self.hours:
            ET.SubElement(hours, "Name").text = h
        return hours

    def genDays(self):
        days = ET.Element("Days_List")
        ET.SubElement(days, "Number").text = str(len(self.days))
        for d in self.days:
            ET.SubElement(days, "Name").text = d
        return days

    def genStudents(self):
        students = ET.Element("Students_List")
        for y in self.years:
            students.append(self.genYear(y))
        return students

    def genYear(self, y):
        year = ET.Element("Year")
        ET.SubElement(year, "Name").text = y
        ET.SubElement(year, "Number_of_Students").text = str(len(self.houses) * 
                                                             ClassSize)
        for h in self.houses:
            year.append(self.genHouseGroup(y+h))
        return year

    def genHouseGroup(self, g):
        group = ET.Element("Group")
        ET.SubElement(group, "Name").text = g
        ET.SubElement(group, "Number_of_Students").text = str(ClassSize)
        return group

    def genStudentsAsSubgroups(self, g):
        return subgroup

    def genTeachers(self):
        names = self.getTeachers()
        teachers = ET.Element("Teachers_List")
        for n in names:
            teacher = ET.SubElement(teachers, "Teacher")
            ET.SubElement(teacher, "Name").text = n
        return teachers

    def genSubjects(self):
        subjects = ET.Element("Subjects_List")
        # TODO non core subjects
        for n in self.core:
            subject = ET.SubElement(subjects, "Subject")
            ET.SubElement(subject, "Name").text = n
        return subjects

    def genActivityTags(self):
        tags = ET.Element("Activity_Tags_List")
        tags.text = "\n"
        return tags

    def genActivities(self):
        acts = ET.Element("Activities_List")
        id = 2
        for g in self.coreGrps:
            for s in self.core:
                actGrpId = id
                for split in range(3):
                    act = ET.SubElement(acts, "Activity")
                    ET.SubElement(act, "Teacher").text  = self.getTeacher(s)
                    ET.SubElement(act, "Subject").text  = s
                    ET.SubElement(act, "Duration").text = "1"
                    ET.SubElement(act, "Total_Duration").text = "3"
                    ET.SubElement(act, "Id").text       = str(id)
                    ET.SubElement(act, "Activity_Group_Id").text = str(actGrpId)
                    ET.SubElement(act, "Active").text   = "true"
                    ET.SubElement(act, "Students").text = g
                    id += 1
        return acts

    def genBuildings(self):
        buildings = ET.Element("Buildings_List")
        buildings.text = "\n"
        return buildings

    def genRooms(self):
        rooms = ET.Element("Rooms_List")
        for r in self.rooms:
            room = ET.SubElement(rooms, "Room")
            ET.SubElement(room, "Name").text     = r
            ET.SubElement(room, "Building").text = "\n      "
            ET.SubElement(room, "Capacity").text = str(ClassSize+2)
        return rooms

    def genTimeConstraints(self):
        constraints = ET.Element("Time_Constraints_List")
        basic = ET.SubElement(constraints, "ConstraintBasicCompulsoryTime")
        ET.SubElement(basic, "Weight_Percentage").text = "100"
        id = 2
        for g in self.coreGrps:
            for s in self.core:
                actGrpId = id
                minndays = ET.SubElement(constraints, 
                                         "ConstraintMinNDaysBetweenActivities")
                ET.SubElement(minndays, "Weight_Percentage").text       = "95"
                ET.SubElement(minndays, "Consecutive_If_Same_Day").text = "true"
                ET.SubElement(minndays, "Number_of_Activities").text    = "3"
                for split in range(3):
                    ET.SubElement(minndays, "Activity_Id").text = str(id)
                    id += 1
                ET.SubElement(minndays, "MinDays").text = "1"

        return constraints

    def genSpaceConstraints(self):
        constraints = ET.Element("Space_Constraints_List")
        basic = ET.SubElement(constraints, "ConstraintBasicCompulsorySpace")
        ET.SubElement(basic, "Weight_Percentage").text = "100"
        for s in self.core:
            pref = ET.SubElement(constraints, "ConstraintSubjectPreferredRooms")
            ET.SubElement(pref, "Weight_Percentage").text = "90"
            ET.SubElement(pref, "Subject").text           = s
            ET.SubElement(pref, "Number_of_Preferred_Rooms").text = "3"
            for r in range(3):
                ET.SubElement(pref, "Preferred_Room").text = self.getRoom()
        for name in self.getTeachers():
            home = ET.SubElement(constraints, "ConstraintTeacherHomeRoom")
            ET.SubElement(home, "Weight_Percentage").text = "90"
            ET.SubElement(home, "Teacher").text           = name
            ET.SubElement(home, "Room").text              = self.getRoom()
        return constraints

if __name__ == "__main__":
    fg = FetGen()
    fg.write()
#    fg.write()


