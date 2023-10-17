import flet
from flet import *
import requests
from bs4 import BeautifulSoup
import math
import webbrowser
import re
import unicodedata
import threading
import time
import ctypes
import os

load_url = "https://www.imocwx.com/i/metar.php"
metars = {}
specialKey = ["VERSION","VATSIM","VATJPN","SANSUKE","TEMP","SQUAWKID","SOURCE"]
version = "beta 1.0"
filepath = os.path.dirname(os.path.abspath(__file__))
textFiles = ["RWYData.txt","AIRCRAFT.txt","AIRLINES.txt"]

RWYData = {}
aircrafts = {}
airlines = {}

def load_text_file():
    for s in textFiles:
        if not os.path.isfile(os.path.join(filepath, s)):
            return s

    with open(os.path.join(filepath, textFiles[0])) as f:
        flines = f.readlines()
        del flines[0]
        for data in flines:
            dataList = data.split(",")
            RWYData[dataList[0]]=[dataList[1],dataList[2],dataList[3],dataList[4],dataList[5],dataList[6].strip()]
    with open(os.path.join(filepath, textFiles[1])) as f:
        flines = f.readlines()
        del flines[0]
        for data in flines:
            dataList = data.split(",")
            if not dataList[0] in aircrafts.keys():
                aircrafts[dataList[0]]=[dataList[1],dataList[2],dataList[3].strip()]
    with open(os.path.join(filepath, textFiles[2])) as f:
        flines = f.readlines()
        del flines[0]
        for data in flines:
            dataList = data.split(",")
            if not dataList[0] in airlines.keys():
                airlines[dataList[0]]=[dataList[1],dataList[2],dataList[3],dataList[4].strip()]
    return ""


def getMetar(port):
    if not port in RWYData.keys():
        return "Error"
    params = {'Area': '0', 'Port': port}
    html = requests.get(load_url, params=params)
    soup = BeautifulSoup(html.content, "html.parser")
    body = soup.find("body")
    lines = body.text
    line = lines.split("\n")
    line_len = len(line)
    metar_temp = []
    if line_len >= 8:
        for i in range(line_len-7):
            metar_temp.append(line[i+3].strip()) 
        return " ".join(metar_temp)
    return "Error"

def codeConvert(port):
    if len(port)==1:
        return "RJ" + port + port
    elif len(port)==2:
        return "RJ" + port
    return port

def metar_summary(s):
    if s == "Error":
        return "Error"
    metar_split = s.split(" ")
    if metar_split[3] == "AUTO":
        del metar_split[3]
    QNH = "ERROR"
    for i in range(len(metar_split)):
        QNH_temp = metar_split[len(metar_split)-i-1]
        if QNH_temp[0] == "A":
            if len(QNH_temp) == 5 or len(QNH_temp) == 6:
                if QNH_temp[1:5].isdecimal():
                        QNH = QNH_temp[:5]
                        break
    metar_short = [metar_split[1],metar_split[2][2:],metar_split[3][:3]+"@"+metar_split[3][3:5],QNH]
    return " ".join(metar_short)

def getAiportName(port):
    airportName = RWYData[port][4]
    return airportName

def getRecommendRWY(port, metar_short):
    priy_rwy = RWYData[port][0]
    oppo_rwy = RWYData[port][1]
    wind = metar_short[2]
    if wind[:3] == "VRB":
        return "RWY" + priy_rwy.zfill(2)
    wind_d = int(wind[:3])
    wind_v = int(wind[4:])
    wind_limit = int(RWYData[port][2])
    wind_diff = int(priy_rwy)*10 - wind_d
    wind_t = -math.cos(math.radians(wind_diff))*wind_v
    recommendRWY = ""
    if wind_t < wind_limit:
        return "RWY" + priy_rwy.zfill(2)
    return "RWY" + oppo_rwy.zfill(2)

def getAircraft(s):
    if s not in aircrafts.keys():
        return None
    aircarft = aircrafts[s]
    out = [s]
    menus = ["Company","Type","WT Cat"]
    for i in range(3):
        out.append(menus[i]+": "+aircarft[i])
    return "\n".join(out)

def getAirline(s):
    if s not in airlines.keys():
        return None
    airline = airlines[s]
    out = [s]
    menus = ["Company","Call Sign","Country","Area"]
    for i in range(4):
        out.append(menus[i]+": "+airline[i])
    return "\n".join(out)

def special(s):
    if s == specialKey[0]:
        return "Version = "+version
    if s == specialKey[1]:
        webbrowser.open("https://vatsim.net/", new=0, autoraise=True)
    if s == specialKey[2]:
        webbrowser.open("https://vatjpn.org/", new=0, autoraise=True)
    if s == specialKey[3]:
        webbrowser.open("https://x.com/sansuke1005", new=0, autoraise=True)
    if s == specialKey[4]:
        webbrowser.open("https://vatjpn.org/document/public/crc/78/171", new=0, autoraise=True)
    if s == specialKey[5]:
        webbrowser.open("https://squawk.id/", new=0, autoraise=True)
    if s == specialKey[6]:
        webbrowser.open(load_url, new=0, autoraise=True)
    return ""    

def autoSelector(s):
    if s in specialKey:
        return special(s)
    if s.isdecimal() and (len(s)==6 or len(s)==7):
        webbrowser.open("https://stats.vatsim.net/stats/"+s, new=0, autoraise=True)
        return ""
    if len(s)==1:
        return getMetar("RJ"+s+s)
    if len(s)==2:
        return getMetar("RJ"+s)
    if s[:2] == "RJ" or s[:2] == "RO":
        return getMetar(s)
    if getAircraft(s) != None:
        return getAircraft(s)
    if getAirline(s) != None:
        return getAirline(s)
    return "Error"


class Task(UserControl):
    def __init__(self, task_name, task_delete, task_clicked):
        super().__init__()
        self.task_name = codeConvert(task_name)
        self.task_delete = task_delete
        self.task_clicked = task_clicked

    def build(self):
        self.metar = getMetar(self.task_name)
        self.metar_short = metar_summary(self.metar).split(" ")

        if self.metar_short[0] == "Error":
            return Column()
        if self.metar_short[0] in metars.keys():
            return Column()
        
        metars[self.task_name]=self.metar

        self.display_view = Container(
            Row(
                alignment="spaceBetween",
                vertical_alignment="center",
                height=17,
                controls=[
                    Text(self.metar_short[0], size=13),
                    Text(self.metar_short[1], size=13),
                    Text(self.metar_short[2], size=13),
                    Text(self.metar_short[3], size=13),
                    Text(getRecommendRWY(self.metar_short[0],self.metar_short), size=13),
                    Row(
                        spacing=0,
                        controls=[
                            IconButton(
                                icons.DELETE_OUTLINE,
                                on_click=self.delete_clicked,
                                icon_size=20,
                                width=20,
                                
                                style=ButtonStyle(
                                    color={
                                        MaterialState.HOVERED: colors.RED,
                                        MaterialState.DEFAULT: colors.ON_BACKGROUND,
                                    },
                                    overlay_color=colors.with_opacity(0, colors.PRIMARY),
                                    padding=0,
                                ),
                            ),
                        ],
                    ),
                ],
            ),
            padding=5,
            ink=True,
            on_click=self.container_clicked,
        )
        return Column(controls=[self.display_view],spacing=0,)
    
    def container_clicked(self, e):
        self.task_clicked(self,getAiportName(self.task_name)+"\n"+metars[self.task_name])

    def delete_clicked(self, e):
        metars.pop(self.metar_short[0])
        self.task_delete(self)


class TodoApp(UserControl):
    def build(self):
        self.new_task = TextField(
            text_size=13,
            #capitalization="CHARACTERS",
            expand=True, 
            on_submit=self.add_clicked, 
            on_change=self.check_alnum,
            content_padding= padding.only(left=5),
        )
        self.tasks = Column(spacing=0, scroll=ScrollMode.AUTO,)
        self.info = TextField(
            text_size=13,
            multiline=True,
            disabled=True,
            value="",
            min_lines=4,
            max_lines=4,
            content_padding= padding.only(left=5,bottom=5),
            color = colors.ON_BACKGROUND,
            #filled=True,
            #border_radius=0,
        )
        self.pb = ProgressBar(color=colors.PRIMARY, bgcolor=colors.BACKGROUND, value=0)

        self.t = CustomThread1(self.reload_clicked)
        self.t.start()



        # application's root control (i.e. "view") containing all other controls
        return Column(
            spacing=5,
            controls=[
                Row(
                    spacing=5,
                    height=30,
                    controls=[
                        self.new_task,
                        FloatingActionButton(
                            icon=icons.CACHED,
                            on_click=self.reload_clicked,
                            width=30,
                            shape=RoundedRectangleBorder(radius=5),
                            
                        ),
                    ],
                ),
                Container(
                    self.tasks,
                    height=225,
                ),
                Container(
                    self.info,
                ),
                self.pb,
                
            ],
        )
        
    

    def add_clicked(self, e):
        self.pb.value = None
        self.update()
        info = autoSelector(self.new_task.value)
        if info[:5] == "METAR":
            task = Task(self.new_task.value, self.task_delete, self.task_clicked)
            self.tasks.controls.append(task)
        else:
            self.task_clicked(None,info)
        self.new_task.value = ""
        self.pb.value = 0
        self.update()

    def check_alnum(self,e):
        if re.compile("[a-zA-Z0-9]+").match(self.new_task.value):
            hankaku=True
            for c in self.new_task.value:
                if not unicodedata.east_asian_width(c) == "Na":
                    print(unicodedata.east_asian_width(c))
                    hankaku=False
            if hankaku==True:
                self.new_task.value = self.new_task.value.upper()
                self.update()
        #if not re.compile("[a-zA-Z0-9]+").match(self.new_task.value):
            


    def task_delete(self, task):
        self.tasks.controls.remove(task)
        self.update()

    def task_clicked(self, task, new_info):
        self.info.value = new_info
        self.update()

    def reload_clicked(self, e):
        self.pb.value = None
        self.tasks.controls = []
        self.update()
        metars_copy = metars.copy()
        metars.clear()
        for key in metars_copy:
            new_task = Task(key, self.task_delete, self.task_clicked)
            self.tasks.controls.append(new_task)
            self.update()
        self.pb.value = 0
        self.update()

def main(page: Page):
    page.title = "METAR.id"
    #page.theme_mode = "LIGHT"
    page.window_width = 300
    page.window_height = 400
    page.window_maximizable = False
    page.window_resizable = False
    page.window_always_on_top = True
    page.theme = theme.Theme(color_scheme_seed='blue')
    page.update()

    app = TodoApp()
    page.add(app)

    def dlf_clicked(e):
        page.window_destroy()

    dlg_modal = AlertDialog(
        modal=True,
        title=Text("ファイルが見つかりません"),
        actions=[
            TextButton("OK", on_click=dlf_clicked),
        ],
        actions_alignment=MainAxisAlignment.END,
    )
    isTextLoaded = load_text_file()
    if not isTextLoaded == "":
        time.sleep(0.1)
        page.dialog = dlg_modal
        dlg_modal.content = Text(isTextLoaded)
        dlg_modal.open = True
        page.update()

    


    

class CustomThread1(threading.Thread):
  def __init__(self, reload_clicked):
    super().__init__()
    self.reload_clicked = reload_clicked
  
  def run(self):
    while True:
        time.sleep(300)
        self.reload_clicked(None)




flet.app(target=main)
