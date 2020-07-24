import sys, os, re, json
from bs4 import BeautifulSoup

# ex. tdFavE81131 or tdFavE81131R
departmentInfo = re.compile("([\sA-Z]+)+\s[(]([A-Z]+[0-9]*){1}[)]{1}")
class_td = re.compile("\\b(tdFav){1}([A-Z]){1}([0-9]{2}){1}([0-9]{3,4}){1}([ATSNMR])?\\b")
tr_class_info = re.compile("\\b(tr){1}[A-Z]{1}([0-9]{2}){1}([0-9]{3,4}){1}([A-Z])?([0-9]{1,3})?[A-Z]{1}\\b")
finalExamStartDayAndtime = re.compile('\\b(([A-Z]{1}[a-z]{2}){1}([\s]{1}){1}([\w]{1,2}){1}([\s]{1}){1}([\w]{4})){1}([\s]{1}){1}(([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])\s*([AaPp][Mm]))\\b')

dayOfWeek = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
# Example dev result dvResultTableFL2020E817001

class finalExam:
    def __init__(self):
        self.type = ""
        self.finalExamDay = ""
        self.finalExamStartTime = ""
        self.finalExamEndTime = ""

    def setType(self , str):
        self.type = str

    def setFinalExam(self, str):
        if (str != 'See instructor'):
            str = cleanString(str)
            txt = str.split('-')

            self.finalExamEndTime = txt[1].replace(" ", "")
            self.finalExamEndTime = self.finalExamEndTime.replace(self.finalExamEndTime[-2:], " " + self.finalExamEndTime[-2:])
            time = finalExamStartDayAndtime.findall(str)
            self.finalExamDay = time[0][0]
            self.finalExamStartTime = time[0][7]
            self.finalExamStartTime = self.finalExamStartTime.replace(self.finalExamStartTime[-2:], " " + self.finalExamStartTime[-2:])



class Class:
    def __init__(self):
        self.sec = ""
        self.days = []
        self.startTime = ""
        self.endTime = ""
        self.startDate = ""
        self.endDate = ""
        self.location = ""
        self.locationRef = ""
        self.instructor = ""
        self.instructorLink = ""
        self.finalExam = finalExam()

    def setDays(self, days):
        for char_index in range(len(days)):
            if days[char_index] != "-":
                self.days.append(dayOfWeek[char_index])

    def setSec(self, sec):
        self.sec = sec

    def setTime(self, time):
        time = cleanString(time)
        txt = time.split('-')
        self.startTime = txt[0]
        self.endTime = txt[1]
        self.startTime += "M"
        self.endTime += "M"
        self.startTime = self.startTime.replace(self.startTime[-2:], " " + self.startTime[-2:])
        self.endTime = self.endTime.replace(self.startTime[-2:], " " + self.startTime[-2:])

    def setFinalExam(self, str):
        str = cleanString(str)
        if any(str.isdigit() for c in str):
            self.finalExam.setType("In Class")
            self.finalExam.setFinalExam(str)
        else:
            self.finalExam.setType(str)



    def setLocation(self, str):
        if str == "TBA" or '(None) /' in str:
            str = cleanString(str)
            self.location = str
        else:
            self.location = cleanString(str.contents[0])
            self.locationRef = cleanString(str.attrs['href'])
    def setProfessor(self, str):
        if str == "[TBA]":
            self.instructor = cleanString(str)
        else:
            self.instructorLink = cleanString(str.attrs['href'])
            self.instructor = cleanString(str.contents[0])

    def setStartDate(self, str):
        if str is not None:
            self.startDate = cleanString(str)

    def setEndDate(self, str):
        if str is not None:
            self.endDate = cleanString(str)



class Course:
    def __init__(self):
        self.courseName = ""
        self.courseTag = ""
        self.units = int(0)
        self.description = ""
        self.classes = []

    def setCourseName(self, courseName):
        self.courseName = cleanString(courseName)

    def setCourseTag(self, tag):
        self.courseTag = tag.replace(u'\xa0', u' ')

    def setUnits(self, units):
        self.units = re.findall("\d+\.\d+", units)[0]

    def setDescription(self, des):
        self.description = cleanString(des)

    def addClass(self, c):
        self.classes.append(c)

class Department:
    def __init__(self):
        self.departmentName = ""
        self.departmentCode = ""
        self.courses = []

    def addDepartmentInfo(self, value):
        value = cleanString(value)
        regex = departmentInfo.findall(value)

        if len(regex) == 0:
            sys.exit("Failed to get department name and code from: " + value)

        if len(regex[0]) == 0:
            sys.exit("Failed to find any string for regex: " + value)

        self.departmentName = regex[0][0]
        self.departmentCode = regex[0][1]


    def addCourse(self, course):
        self.courses.append(course)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=False, indent=4)



def main(argv):
    if (len(argv) < 1):
        sys.exit(f"Usage: {sys.argv[0]} filename or filepath/filename")

    file = sys.argv[1]

    if not os.path.exists(file):
        sys.exit(f"Error: file '{sys.argv[1]}' not found.")

    parseFile(file)

def cleanString(input):
    return re.sub(' +', ' ', re.sub(r'\n', ' ', re.sub(r'\t', '', re.sub(r'\r', '', input))))

def parseFile(file):
    with open(file) as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    #Create the empty object to store all data in
    department = Department()
    allCourses = []

    # Get the div wit hall the courses in it
    coursesDiv = soup.find_all("div", id="Body_divResults")

    if len(coursesDiv) == 0:
        sys.exit("Failed to find Body_divResults in html.")

    departmentInfoTable = coursesDiv[0].find_all("table", id="tabDeptBar0")
    #tabDeptBar0
    departmentInfoLinks = departmentInfoTable[0].find_all("a", class_="RedLink")

    if len(departmentInfoLinks) == 0:
        sys.exit("Failed to department links to obtain department data.")

    department.addDepartmentInfo(departmentInfoLinks[0].contents[0])

    # get the first link
    allTd = coursesDiv[0].find_all("td", class_=class_td)

    for td in allTd:
        course = Course()

        for parent in td.parents:
            allA = parent.find_all('a')
            course.setCourseTag(allA[0].contents[0])
            course.setCourseName(allA[1].contents[0])
            course.setUnits(allA[2].contents[0])
            break

        #Add the course to the department
        department.addCourse(course)

    # Get all the course descriptions
    description = []
    for dev in soup.find_all("div", class_="DivDetail"):
        allA = dev.find_all('a')
        if (len(allA[1].contents) == 1):
            description.append(allA[1].contents[0])
        else:
            description.append("")

    # Get all the Table Row's with course info
    allTr = soup.find_all("tr", id=tr_class_info)

    # Add the courses with detail
    for i, course in enumerate(department.courses):
        course.setDescription(description[i])
        tag_split = course.courseTag.split()
        if len(tag_split) == 0:
            sys.exit("Failed to get class tag.")
        tag = tag_split[0]+tag_split[-1]
        for tr in allTr:
            if tag in tr.attrs.get("id"):
                classDetailTD = tr.find_all("td")
                c = Class()

                c.setSec(classDetailTD[1].contents[0])

                if (classDetailTD[2].contents[0] != "TBA"):
                    c.setDays(classDetailTD[2].contents[0])

                if (len(classDetailTD[3].contents) != 0):
                    c.setTime(classDetailTD[3].contents[0])

                c.setLocation(classDetailTD[4].contents[0])
                c.setProfessor(classDetailTD[5].contents[0])

                c.setFinalExam(classDetailTD[6].contents[0])

                #class start/end day
                if (len(tr.parent.find_all("tr")[1].find_all("a")) > 1 ):
                    if (tr.parent.find_all("tr")[1].find_all("a")[1].next_sibling is not None):
                        c.setStartDate(tr.parent.find_all("tr")[1].find_all("a")[1].next_sibling)
                        c.setEndDate(tr.parent.find_all("tr")[1].find_all("a")[2].next_sibling)
                else:
                    c.setStartDate(tr.parent.find_all("tr")[3].find_all("a")[1].next_sibling)
                    c.setEndDate(tr.parent.find_all("tr")[3].find_all("a")[2].next_sibling)

                course.addClass(c)


    jsonStr = department.toJSON()
    #print(jsonStr)

    fileName = department.departmentName + "-" + department.departmentCode + ".json"
    writeJson = open(fileName, "w")

    writeJson.write(jsonStr)
    writeJson.close()

    #closing html
    f.close()

if __name__ == "__main__":
    main(sys.argv)
