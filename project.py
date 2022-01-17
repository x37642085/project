import requests
import json

from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify

from bs4 import BeautifulSoup

courseList = []

course_url = "https://querycourse.ntust.edu.tw/querycourse/api"
GPA_url = "https://gpa.ntustexam.com/query?keywords="
payload = {
    "CourseName" : "",
    "CourseNo" : "CS",
    "CourseNotes" : "",
    "CourseTeacher" : "",
    "Dimension" : "",
    "ForeignLanguage" : 0,
    "Language" : "zh",
    "OnlyNTUST" : 0,
    "OnlyGeneral" : 0,
    "OnlyMaster" : 0,
    "OnlyUnderGraduate" : 0,
    "Semester" : "1091"
}


#課程查詢爬蟲
def courseCrawler(courseNo, OnlyNTUST, OnlyGeneral, semester):
    payload["CourseNo"] = courseNo
    payload["OnlyNTUST"] = OnlyNTUST
    payload["OnlyGeneral"] = OnlyGeneral
    payload["Semester"] = semester
    data = requests.post(url = course_url + "/courses",data=payload).content.decode("utf-8")
    data = json.loads(data)
    return data

#課程GPA爬蟲
def GPAcrawler(courseNo):
    data = requests.get(url = GPA_url + courseNo)
    soup = BeautifulSoup(data.text, "html.parser")
    GPAdata = soup.find_all("tr", class_="data-row")
    GPAinfoList = []
    for temp in GPAdata:
        GPAinfo = {}
        GPAinfo["Semester"] = temp.select("td")[4].text
        GPAinfo["Teacher"] = temp.select("td")[3].text
        GPAinfo["GPA"] = temp.select("td")[6].text
        GPAinfoList.append(GPAinfo)
    return GPAinfoList

def filter(data, requireOption, filterTimeSet):
    for course in data:
        #課程是否包含時間  ex. course["Node"] = "M1,M2,M3"
        if( course["Node"] != None ):
            #course["RequireOption"] = R or E
            if(course["RequireOption"] in requireOption ):
                #"M1,M2,M3" -> "M1","M2","M3"
                courseTime = course["Node"].split(',')
                for filterTime in filterTimeSet:
                    if(filterTime in courseTime):
                        courseInfo = {}
                        courseInfo["CourseNo"] = course["CourseNo"]
                        courseInfo["CourseName"] = course["CourseName"]
                        if course["RequireOption"] == "R":
                            courseInfo["RequireOption"] = "必"
                        else:
                            courseInfo["RequireOption"] = "選"
                        courseInfo["Node"] = course["Node"]
                        courseInfo["Tag"] = filterTime
                        courseList.append(courseInfo)


titleText = ""

app = Flask(__name__)

@app.route("/", methods = ['GET','POST'])
def index():
    if request.method == 'POST':

        filterTimeSet = []

        semester = request.values["semesterSelect"]
        if request.values["searchStyle"] == "byTime":
            filterTimeSet = request.values["searchCondition1"].split(',')
            titleText = request.values["searchCondition1"]
        else:
            courseNo = request.values["searchCondition2"]
            data = courseCrawler(courseNo, 0, 0, semester)
            for course in data:
                if( course["Node"] != None ):
                    filterTimeSet += course["Node"].split(',')
            titleText = request.values["searchCondition2"]

        comparativeCourse = request.form.getlist("comparativeCourse")
        requireOption = ""
        courseList.clear()
        if "CSR" in comparativeCourse or "CSO" in comparativeCourse:
            #CS
            requireOption = ""
            if "CSR" in comparativeCourse:
                requireOption = "R"
            if "CSO" in comparativeCourse:
                requireOption = requireOption +  "E"
            data = courseCrawler("CS", 0, 0, semester)
            filter(data, requireOption, filterTimeSet)
            
        if "EECSR" in comparativeCourse or "EECSO" in comparativeCourse:
            #EC, ET, EE
            requireOption = ""
            if "EECSR" in comparativeCourse:
                requireOption = "R"
            if "EECSO" in comparativeCourse:
                requireOption = requireOption +  "E"
            data = courseCrawler("EC", 0, 0, semester)
            filter(data, requireOption, filterTimeSet)
            data = courseCrawler("ET", 0, 0, semester)
            filter(data, requireOption, filterTimeSet)
            data = courseCrawler("EE", 0, 0, semester)
            filter(data, requireOption, filterTimeSet)
        if "GE" in comparativeCourse:
            requireOption = "R"
            data = courseCrawler("", 0, 1, semester)
            filter(data, requireOption, filterTimeSet)
        if "EP" in comparativeCourse:
            requireOption = "RE"
            data = courseCrawler("EP", 0, 0, semester)
            filter(data, requireOption, filterTimeSet)

        return render_template("home.html", titleText = titleText, filterTimeSet = filterTimeSet, courseList = courseList)
    else:
        return render_template("home.html", titleText = "", filterTimeSet = [], courseList = courseList)

@app.route("/GPA", methods = ['GET','POST'])
def GPA():
    courseNo = request.args.get('courseNo')
    GPAinfoList = GPAcrawler(courseNo)
    return jsonify(GPAinfoList)


app.run()


