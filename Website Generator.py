from tkinter import *
from tkinter import filedialog
from tkinter.tix import *
from PIL import Image, ImageTk
import os
import atexit
import cv2
import numpy as np
import glob
import webbrowser
import enchant
from yawrap import Yawrap, ExternalJs, EmbedCss, EmbedJs, BODY_END
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
# ------------------------------------------------Functions-------------------------------------------------------------------------

#UI Functions
def show_frame(frame):
    frame.tkraise()

# Manual Window by toplevel
def OpenMaual():
    global userPic
    top = Toplevel()
    top.title("User Manual")
    userPic = ImageTk.PhotoImage(Image.open("Pics/Manual.jpg"))
    userLbl = Label(top, image=userPic, bg="#263A43").pack()
    x = root.winfo_x()
    y = root.winfo_y()
    top.geometry("+%d+%d" % (x + 500, y + 200))
    
# Read and display image
def UploadShowImage():
    global final_pic
    global pic_path
    global imgLbl
    global pic_width
    global pic_height
    fln = filedialog.askopenfilename(initialdir=os.getcwd(), title="Select Image file", filetypes=(("JPG file", ".jpg"), ("PNG file", ".png"), ("All files", ".")))
    img = Image.open(fln)
    img.thumbnail((700, 600))
    img = ImageTk.PhotoImage(img)
    
    if img is not NONE :
        imgg = cv2.imread(fln)
        pic_width = imgg.shape[1]
        pic_height = imgg.shape[0]
        imgLbl.configure(image=img)
        imgLbl.image = img
        final_pic = cv2.imread(fln, cv2.IMREAD_UNCHANGED)
        pic_path = fln

def returnToMain():
    imgLbl.config(image='')
    if os.path.exists("Design.html"):
        os.remove("Design.html")
    show_frame(mainPage)

def exit_handler():
    if os.path.exists("Design.html"):
        os.remove("Design.html")

#Elements Detection Functions
class component:

    # init method or constructor
    def __init__(self,id, name,x,y,w,h,lable):
        self.id = id
        self.name = name
        self.x = x
        self.y = y
        self.w = w
        self.h=h
        self.lable=lable

def detect_btn_comb(obj):
    Button_list = []
    DropDown_list = []
    for f in glob.iglob("images\Button\*"):
        image = cv2.imread(f)
        Button_list.append(image)
    for f in glob.iglob("images\DropDown\*"):
        image = cv2.imread(f)
        DropDown_list.append(image)
    Button_dataset = Button_list[::-1]
    DropDown_dataset = DropDown_list[::-1]

    max = 0
    title = ""
    obj = cv2.resize(obj, (300, 220), interpolation=cv2.INTER_CUBIC)
    for button in Button_dataset:
        button = cv2.resize(button, (300, 220), interpolation=cv2.INTER_CUBIC)

        surf = cv2.xfeatures2d.SURF_create()

        _, descriptors_1 = surf.detectAndCompute(obj, None)
        _, descriptors_2 = surf.detectAndCompute(button, None)

        # feature matching
        bf = cv2.BFMatcher(cv2.NORM_L1, crossCheck=True)
        matches = bf.match(descriptors_1, descriptors_2)
        matches = sorted(matches, key=lambda x: x.distance)
        good_points = []
        for m in matches:
            if m.distance < 0.7:
                good_points.append(m)
        if len(good_points) > max:
            max = len(good_points)
            title = "Button"

    for dropdown in DropDown_dataset:
        dropdown = cv2.resize(dropdown, (300, 220), interpolation=cv2.INTER_CUBIC)

        surf = cv2.xfeatures2d.SURF_create()

        _, descriptors_1 = surf.detectAndCompute(obj, None)
        _, descriptors_2 = surf.detectAndCompute(dropdown, None)

        # feature matching
        bf = cv2.BFMatcher(cv2.NORM_L1, crossCheck=True)
        matches = bf.match(descriptors_1, descriptors_2)
        matches = sorted(matches, key=lambda x: x.distance)
        good_points = []
        for m in matches:
            if m.distance < 0.7:
                good_points.append(m)
        if len(good_points) > max:
            max = len(good_points)
            title = "Dropdown"

    return title

def identifyElement(objects, contour,detected):
    for i in range(len(objects)):
        if contour[i] >= 10:
            detected.append("Imageicon")
        elif (objects[i].size / (objects[i].shape[1] - objects[i].shape[0])) >= 100:
            _,contours, _ = cv2.findContours(objects[i], cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
            if len(contours) <= 40:
                detected.append("Textarea")
            else:
                detected.append("Paragraph")
        else:
            _,contours, _ = cv2.findContours(objects[i], cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
            rect = 0
            combo = 0
            for cnt in contours:
                epsilon = 0.01 * cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, epsilon, True)
                x, y, w, h = cv2.boundingRect(cnt)
                if w > 20 and h > 20:
                    if len(approx) != 4:
                        combo += 1
                        rect = 0
                        break
                    else:
                        rect += 1
            if (rect == 1 or rect == 2) and not (combo > 0):
                detected.append("Textinput")
            else:
                res=detect_btn_comb(objects[i])
                detected.append(res)

def getcontours(img, imgContour, objects, cnt, x_com, y_com, w_com, h_com):
    _,contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    for i in range(len(contours)):
        x, y, w, h = cv2.boundingRect(contours[i])
        if w > 10 and h > 10 and hierarchy[0][i][3] == -1:
            approx = cv2.rectangle(imgContour, (x, y), (x + w, y + h), (0, 0, 255), 0)
            imgCropped = img[y - 5:y + h + 5, x - 5:x + w + 5]
            epsilon = 0.01 * cv2.arcLength(contours[i], True)
            approx = cv2.approxPolyDP(contours[i], epsilon, True)
            cnt.append(len(approx))
            objects.append(imgCropped)
            x_com.append(x*1537/640)
            y_com.append(y*792/480)
            w_com.append(w)
            h_com.append(h)

def textDetection(imgPath, detected, x_com, y_com, w_com, h_com):
    endpoint = "https://graduationp.cognitiveservices.azure.com/"
    key = "74fd15f5dea44f229bf1e7fa99b665ea"
    
    client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(key))

    path = open(imgPath, "rb")

    # Call API with image and raw response (allows you to get the operation location)
    read_response = client.read_in_stream(path, raw=True)
    # Get the operation location (URL with ID as last appendage)
    read_operation_location = read_response.headers["Operation-Location"]
    # Take the ID off and use to get results
    operation_id = read_operation_location.split("/")[-1]

    # Call the "GET" API and wait for the retrieval of the results
    while True:
        read_result = client.get_read_result(operation_id)
        if read_result.status.lower () not in ['notstarted', 'running']:
            break

    text = []
    x1 = []
    x2 = []
    y1 = []
    y2 = []
    label = []

    if read_result.status == OperationStatusCodes.succeeded:
        for text_result in read_result.analyze_result.read_results:
            for line in text_result.lines:
                word = line.text
                if word[0] == "o" or word[0] == "O" or word[0] == ".":
                    d = enchant.Dict("en_US")
                    if d.check(word) == FALSE:
                        detected.append("Radiobutton")
                        x_com.append(int(line.bounding_box[0]*1537/pic_width) - 15)
                        y_com.append(int(line.bounding_box[1]*792/pic_height) + 5)
                        w_com.append(15)
                        h_com.append(15)
                        label.append("")
                        text.append(word[1:])
                        x1.append(int(line.bounding_box[0]))
                        y1.append(int(line.bounding_box[1]))
                        x2.append(int(line.bounding_box[4]))
                        y2.append(int(line.bounding_box[5]))
                        continue

                text.append(line.text)
                x1.append(int(line.bounding_box[0]))
                y1.append(int(line.bounding_box[1]))
                x2.append(int(line.bounding_box[4]))
                y2.append(int(line.bounding_box[5]))               

    return text, x1, y1, x2, y2, label

def textMask(imgMask, x1, y1, x2, y2):
    for i in range(len(x1)):
        cv2.rectangle(imgMask, (int(x1[i]*640/pic_width), int(y1[i]*480/pic_height)), (int(x2[i]*640/pic_width), int(y2[i]*480/pic_height)), (0, 0, 0), -1)
    return imgMask

def component_label(y_components, y_texts, texts, components, label, x_components, x_texts):
    for i in range(len(y_components)):
        if(components[i] == "Radiobutton"):
            continue
        label.append("")
        for j in range(len(y_texts)):
            if abs(y_components[i] - (y_texts[j]*792/pic_height)) <= 25 and abs(x_components[i] - (x_texts[j]*1537/pic_width)) <= 200:
                label[i] = texts[j]
                del texts[j]
                del y_texts[j]
                del x_texts[j]
                break

def image_com():
    global text, x1, y1, x2, y2
    x_com = []
    y_com = []
    w_com = []
    h_com = []
    detected = []

    components = []

    img = final_pic
    img = cv2.resize(img, (640, 480), interpolation=cv2.INTER_AREA)
    text, x1, y1, x2, y2, comp_label = textDetection(pic_path, detected, x_com,y_com,w_com,h_com)
    imgContour = img.copy()
    imgBlur = cv2.GaussianBlur(img, (7, 7), 1) #Gaussian reduces noise in picture./the smallest the kernel, the less visible is the blur.
    imgGray = cv2.cvtColor(imgBlur, cv2.COLOR_BGR2GRAY) #Convert image to gray scale.
    imgCanny = cv2.Canny(imgGray, 40, 100) #apply canny edge detection
    kernel = np.ones((2, 2))
    imgDil = cv2.dilate(imgCanny, kernel, iterations=1) #dilate increases the white region in the image.
    finalImg = textMask(imgDil, x1, y1, x2, y2)

    objects = []
    cnt = []
    getcontours(finalImg, imgContour, objects, cnt, x_com, y_com, w_com, h_com)
    identifyElement(objects, cnt, detected)
    component_label(y_com, y1, text, detected, comp_label, x_com, x1)
    print(detected)
    print(text)
    #detected[6] = "Textinput"
    #text.remove('D')

    for i in range(len(detected)):
        c = component(detected[i] + str(i), detected[i], x_com[i], y_com[i], w_com[i], h_com[i], comp_label[i])
        components.append(c)
    return  components

#HTML Functions
def htmlGeneration():
    components=image_com()

    shapes_id = []
    shapes = []
    shapes_pos = []
    shapes_size = []
    shapes_text = []

    for i in range(len(components)):
        shapes_id.append(components[i].id)
        shapes.append(components[i].name)
        pos = []
        pos.append(str(components[i].x))
        pos.append(str(components[i].y))
        shapes_pos.append(pos)
        size = []
        size.append(str(components[i].h))
        size.append(str(components[i].w))
        shapes_size.append(size)
        shapes_text.append(components[i].lable)

    labels_id = []
    labels_text = []
    labels_pos = []
    for i in range(len(text)):
        labels_id.append("text" + str(i))
        labels_text.append(text[i])
        pos = []
        pos.append(str(x1[i]* (1537/pic_width) ))
        pos.append(str(y1[i]* (792/pic_height) ))
        labels_pos.append(pos)

    out_file = '/tmp/css_1.html'
    doc = Yawrap(out_file, 'HTML Design')

    EmbedJsStr = """\
    function dragElement(element) {
    var pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
    document.getElementById(element.id).onmousedown = dragMouseDown;

    function dragMouseDown(e) {
        e = e || window.event;
        e.preventDefault();
        // get the mouse cursor position at startup:
        pos3 = e.clientX;
        pos4 = e.clientY;
        document.onmouseup = closeDragElement;
        // call a function whenever the cursor moves:
        document.onmousemove = elementDrag;
    }

    function elementDrag(e) {
        e = e || window.event;
        e.preventDefault();
        // calculate the new cursor position:
        pos1 = pos3 - e.clientX;
        pos2 = pos4 - e.clientY;
        pos3 = e.clientX;
        pos4 = e.clientY;
        // set the element's new position:
        element.style.top = (element.offsetTop - pos2) + "px";
        element.style.left = (element.offsetLeft - pos1) + "px";
    }

    function closeDragElement() {
        /* stop moving when mouse button is released:*/
        document.onmouseup = null;
        document.onmousemove = null;
    }
    };
    
    $(document).ready(function() {
        $(function dragLabels(val) { $(val).draggable();}); 
    });

    """

    for i, val in enumerate(shapes):
        if val == "Button":
            if shapes_text[i] != "":
                with doc.tag('button', id = shapes_id[i]):
                    doc.text(shapes_text[i])
            else:
                with doc.tag('button', id = shapes_id[i]):
                    doc.text("Button")
        if val == "Imageicon":
            doc.stag('img', src = "C:/Users/farah/Desktop/College/4th year/ALL IN 1/Pics/icon.JPG", id = shapes_id[i], alt = "image")
        if val == "Textinput":
            if shapes_text[i] != "":
                doc.stag('input', type = 'text', placeholder = shapes_text[i], id = shapes_id[i])
            else:
                doc.stag('input', type = 'text', id = shapes_id[i])
        if val == "Textarea":
            if shapes_text[i] != "":
                with doc.tag('textarea', id = shapes_id[i]):
                    doc.text(shapes_text[i])
            else:
                with doc.tag('textarea', id = shapes_id[i]):
                    pass
        if val == "Dropdown":
            with doc.tag('select', name = 'Dropdown', id = shapes_id[i]):
                if shapes_text[i] == "":
                    for value, description in (
                        ("Option 1", "Option 1"),
                        ("Option 2", "Option 2"),
                        ("Option 3", "Option 3")
                    ):
                        with doc.tag('option', value = value):
                            doc.text(description)
                else:
                    for value, description in (
                        (shapes_text[i] + " 1", shapes_text[i] + " 1"),
                        (shapes_text[i] + " 2", shapes_text[i] + " 2"),
                        (shapes_text[i] + " 3", shapes_text[i] + " 3")
                    ):
                        with doc.tag('option', value = value):
                            doc.text(description)

        if val == "Radiobutton":
                doc.stag('input', type = 'radio', name = "group", id = shapes_id[i], value = shapes_text[i])
        if val == "Paragraph":
            with doc.tag('div', id = shapes_id[i]):
                with doc.tag('p'):
                    doc.text('Paragraph is here')
                    doc.stag('br')
                    doc.text('---------------------')
                    doc.stag('br')
                    doc.text('---------------------')

    #labels loop
    for i, val in enumerate(labels_text):
        with doc.tag('label', id = labels_id[i]):
            doc.text(val)

    qoute_str="'"
    with doc.tag("script"):
        for val in shapes_id:
            doc.text("dragElement(document.getElementById("+qoute_str+val+qoute_str+"))")

        for val in labels_id:
            doc.text("dragElement(document.getElementById("+qoute_str+val+qoute_str+"))")
            

    #css for shapes loop
    cssStr = ""
    for index, (j, k) in enumerate(zip(shapes_pos, shapes_size)):
        cssStr += "\t#"+ shapes_id[index] +"{cursor: move; left: " + j[0] + "px; top: " + j[1]+ "px; position: absolute; height: " + k[0]+ "px; width: " + k[1] + "px}\n".expandtabs(2)

    #css for labels loop
    for index, j in enumerate(labels_pos):
        cssStr += "\t#"+ labels_id[index] +"{cursor: move; left: " + j[0] + "px; top: " + j[1]+ "px; position: absolute; font-size:18px}\n".expandtabs(2)                 
        #label{display: inline-block; width: 150px; text-align: right;}\n".expandtabs(2)

    doc.add(EmbedCss(cssStr))
    doc.add(EmbedJs(EmbedJsStr))
    doc.render()       
    return doc.getvalue()

def continueBtn():
    global res
    res = htmlGeneration()
    show_frame(displayPage)

def OpenWebsite():
    file = open("Design.html", "w")
    file.write(res)
    webbrowser.open_new('Design.html')
    file.close()

def downloadCode():
    file = open("Design_as_HTML.html", "w")
    file.write(res)
    file = open("Design_as_text.txt", "w")
    file.write(res)
    file.close()

def browse_download():
    if os.path.exists("Design.html"):
        os.remove("Design.html")
    tempdir = filedialog.askdirectory(parent=root, initialdir=os.getcwd(), title='Please select a folder')
    if len(tempdir) > 0:
        os.chdir(tempdir)
        downloadCode()

# ------------------------------------------------UI-------------------------------------------------------------------------
root = Tk()
# root.state('zoomed') lw fullscreen with titlebar
root.geometry("{}x{}+{}+{}".format(1237, 692, -10, 0))  # format(wight, height, start of wight, start of height)
root.resizable(0, 0)
root.title("Website Generator")

root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

displayPage = Frame(root, bg="#263A43")
mainPage = Frame(root, bg="#263A43")

for frame in (displayPage, mainPage):
    frame.grid(row=0, column=0, sticky='nsew')

# ---------mainPage code---------
# display image
imgLbl = Label(mainPage, background="#263A43", text=" ")
imgLbl.place(x=mainPage.winfo_screenwidth() / 2, y=475, anchor=CENTER)

global isUploaded
isUploaded = 0

# create Tooltip (hint bta3 usermanual icon)
tip = Balloon(mainPage)
tip.message.config(fg="#263A43")

# user manual button
icon = Image.open("Pics/instructions.png")
icon_resized = icon.resize((40, 40), Image.ANTIALIAS)
manualicon = ImageTk.PhotoImage(icon_resized)
manuallbl = Label(mainPage, image=manualicon)
manualBtn = Button(mainPage, image=manualicon, relief=FLAT, command=OpenMaual, borderwidth=0, background="#263A43",
                   activebackground="#1e2e35", activeforeground="#F6EEC9")
manualBtn.place(x=1180, y=10)
tip.bind_widget(manualBtn, balloonmsg="User Manual")

# upload button
uploadBtn = Button(mainPage, text="Upload picture", command=UploadShowImage, bg="#C93F2B", font="Calibri", fg="#F6EEC9",
                   relief=FLAT, activebackground="#A03222", activeforeground="#F6EEC9", borderwidth=0)
uploadBtn.place(x=mainPage.winfo_screenwidth() / 2, y=140, anchor=CENTER)

# continue button
contBtn = Button(mainPage, text="Continue", command=lambda: continueBtn(), font="Calibri", bg="#799AA3",
                 fg="#F6EEC9", activebackground="#607b82", activeforeground="#F6EEC9", relief=FLAT, borderwidth=0)
contBtn.place(x=900, y=540)

# ---------displayPage code---------
# done label
DoneLbl = Label(displayPage, text="Done", bg="#263A43", fg="#F6EEC9")
DoneLbl.config(font=("Calibri", 46))
DoneLbl.place(x=displayPage.winfo_screenwidth() / 2, y=150, anchor=CENTER)

# download button
downloadBtn = Button(displayPage, command=browse_download, text="Download html/css code", font="Calibri", bg="#799AA3",
                     fg="#F6EEC9", activebackground="#607b82", activeforeground="#F6EEC9", relief=FLAT, borderwidth=0)
downloadBtn.place(x=displayPage.winfo_screenwidth() / 2, y=300, anchor=CENTER)

# webpage download
webPageBtn = Button(displayPage, command=OpenWebsite, text="Open web page", font="Calibri", bg="#799AA3", fg="#F6EEC9",
                    activebackground="#607b82", activeforeground="#F6EEC9", relief=FLAT, borderwidth=0)
webPageBtn.place(x=displayPage.winfo_screenwidth() / 2, y=450, anchor=CENTER)

# upload again button
againLbl = Button(displayPage, text="Upload again", command=lambda: returnToMain(), font=("Calibri", 16), borderwidth=0,
                  bg="#263A43", fg="#C93F2B", activebackground="#263A43", activeforeground="#C93F2B")
againLbl.place(x=displayPage.winfo_screenwidth() / 2, y=600, anchor=CENTER)

# ---------Close Application---------
atexit.register(exit_handler)

root.mainloop()