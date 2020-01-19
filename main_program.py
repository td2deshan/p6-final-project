from tkinter import *
from tkinter import scrolledtext
import numpy as np
import cv2
import firebase_admin
from firebase_admin import credentials, firestore
from pyzbar import pyzbar
from tkinter import messagebox
import re

#init
window = Tk()
window.title("Attendence")
window.geometry('700x500')

# get years from db
years = None
# for option menues
default_option_name = 'not selected'
# current working file
file_name = None
#to store courses
courses = []
#store week number
week = 'week'

# ------------------- cloud DB setup ----------------------------------
try:
    cred = credentials.Certificate("AttendanceUSJ-179e8409be0e.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    years = db.collection(u'year')
except Exception as err:
    #print(err)
    print("please check you'r internet connection")

# -------------------year option menu ----------------------------------
def selectYearEvent(event):
    global file_name
    yr = opt_year.get()
    if yr != default_option_name:
        courses = []
        available_courses = years.document(yr).collection(u'course')
        for doc in available_courses.stream():
            courses.append(doc.id)
        course_list(courses)

    if len(courses) > 0:
        try:
            scan_btn.configure(state="active")
            file_name = courses_listBox.get(courses_listBox.curselection())
        except TclError:
            messagebox.showinfo("Error", "please select courses")
        
opt_year = StringVar(window)
opt_year.set(default_option_name)
yrs = []
# get years from db
isCollected = True;
while (isCollected):
    try:
        for doc in years.stream():
            yrs.append(doc.id)
            print(doc.id)
        isCollected=False;
    except:
        messagebox.showinfo("Error", "Connect to wifi")

opt_menu_year = OptionMenu(window, opt_year, *yrs, command=selectYearEvent)
opt_menu_year.grid(column=1, row=0)

selectYear_lbl = Label(window, text="Select Year: ")
selectYear_lbl.grid(column=0, row=0)
# -------------------End year option menu ----------------------------------

#---------------------For cv2-----------------------------------
def nothing(x):
    pass

def scan_from_cam():
    global file_name
    frame = np.zeros((300,512,3), np.uint8)
    
    ref_ids = set()  # for no duplicate ref_ids
    cam = cv2.VideoCapture(0)  # cam port id usaually 1 or 0

    windowName = 'scan id'
    cv2.namedWindow(windowName)
    cv2.createTrackbar('to_close_window_btn', windowName, 0, 1, nothing)
    font = cv2.FONT_HERSHEY_SIMPLEX

    while True:
        _, frame = cam.read(0)
        data = pyzbar.decode(frame)
        refNo = 'no barcode founded'
        x = y = 10
        try:
            refNo = data[0].data.decode('utf8')
            ref_ids.add(str(refNo))
            #print(refNo)
            # add countor box
            for coords in data:
                (x, y, w, h) = coords.rect
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

        except IndexError:
            pass
            #print('no id')
        except Exception as e:
            print(e)
            
        cv2.putText(frame, refNo, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        cv2.imshow(windowName, frame)
        k = cv2.waitKey(100) & 0xFF

        #btn for close cv2 imshow window
        bool_ok = cv2.getTrackbarPos('to_close_window_btn', windowName)
        if bool_ok:
            break
        
    cam.release()
    cv2.destroyAllWindows()
    crs = courses_listBox.get(courses_listBox.curselection())
    file_name = crs

    if len(ref_ids) > 0:
        with open(file_name, 'a+') as f:
            for i in ref_ids:
                f.write(i+"\n")

    

# ---------------- main window ----------------------------------
# dispaly selected course name
year_lbl = Label(window, text="Select year: ")
year_lbl.grid(column=0, row=0)

week_lbl = Label(window, text="Select week: ")
week_lbl.grid(column=2, row=0)

course_lbl = Label(window, text="Course name: ")
course_lbl.grid(column=4, row=0)

#------------------- scan btn------------------------------------
scan_btn = Button(window, text="Scan",
                  command=scan_from_cam, height=10, width=10, state=DISABLED)
scan_btn.grid(column=0, row=1)
# ---------------- end main window ----------------------------------

#--------------------select week-------------------------------------------
weekVal = StringVar(window)
weekVal.set(week)
weeks = [f'week{i}' for i in range(1, 15)]
opt_menu_week = OptionMenu(window, weekVal, *weeks,command=selectYearEvent)
opt_menu_week.grid(column=3, row=0)
#----------------------end select week-----------------------------------------


#------------------- exit btn------------------------------------
exit_btn = Button(window, text="Exit",
                  command=window.destroy, height=10, width=10)
exit_btn.grid(column=2, row=1)
# ---------------- end main window ----------------------------------


def upload_to_cloud():
    global file_name, course_lbl
    
    try:
        yr = opt_year.get()
        crs = courses_listBox.get(courses_listBox.curselection())
        course_lbl.configure(text=crs)
        file_name = crs
        
        location = years.document(yr).collection(u'course').document(crs).collection('attendance')
        week = weekVal.get()
        if file_name != None:
            with open(file_name) as f: 
                d = f.readline()
                while d != '':
                    #to remove '\n' used regex
                    #otherwise give error in firebase
                    fi = re.findall('([A-Z0-9]*)', d)[0]
                    location.document(fi).set({week: 1})
                    d = f.readline()
        
    except Exception as err:
        #print('check you\' internet connection')
        print(err)
    

#------------------- upload btn------------------------------------
upload_btn = Button(window, text="Upload",
                  command=upload_to_cloud, height=10, width=10)
upload_btn.grid(column=1, row=1)
#------------------- end upload btn------------------------------------

# ----------------main window ----------------------------------
courses_listBox = Listbox(window)
courses_listBox.grid(column=5, row=0)

def course_list(courses):
    courses_listBox.delete(0,END)
    for i in courses:
        courses_listBox.insert(END, i)

course_list(courses)
# ---------------- end main window ----------------------------------

window.mainloop()
