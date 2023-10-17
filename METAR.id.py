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
specialKey = ["VERSION","VATSIM","VATJPN","SANSUKE","TEMP","SQUAWKID"]
version = "beta 1.0"
filepath = os.path.dirname(os.path.abspath(__file__))

RWYData = {}
with open(os.path.join(filepath, "RWYData.txt")) as f:
    flines = f.readlines()
    del flines[0]
    for data in flines:
        dataList = data.split(",")
        RWYData[dataList[0]]=[dataList[1],dataList[2],dataList[3],dataList[4],dataList[5],dataList[6].strip()]
aircrafts = {}
with open(os.path.join(filepath, "AIRCRAFT.txt")) as f:
    flines = f.readlines()
    del flines[0]
    for data in flines:
        dataList = data.split(",")
        if not dataList[0] in aircrafts.keys():
            aircrafts[dataList[0]]=[dataList[1],dataList[2],dataList[3].strip()]
airlines = {}
with open(os.path.join(filepath, "AIRLINES.txt")) as f:
    flines = f.readlines()
    del flines[0]
    for data in flines:
        dataList = data.split(",")
        if not dataList[0] in airlines.keys():
            airlines[dataList[0]]=[dataList[1],dataList[2],dataList[3],dataList[4].strip()]

def getMetar(port):
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
    else:
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
    metar_short = [metar_split[1],metar_split[2][2:],metar_split[3][:3]+"@"+metar_split[3][3:5],metar_split[-1][:5]]
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
    return ""

def autoSelector(s):
    if s in specialKey:
        return special(s)
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
            print("Error")
            return Column()
        if self.metar_short[0] in metars.keys():
            print("Same")
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
        self.dd = Dropdown(
                            width=65,
                            content_padding= 5,
                            text_size=13,
                            value="5min",
                            on_change=self.dd_change,
                            options=[
                                dropdown.Option("None"),
                                dropdown.Option("5min"),
                                dropdown.Option("10min"),
                                dropdown.Option("15min"),
                                dropdown.Option("30min"),
                                dropdown.Option("45min"),
                                dropdown.Option("60min"),
                            ],
                        )
        self.tasks = Column(spacing=0)
        self.info = TextField(
            text_size=13,
            multiline=True,
            disabled=True,
            value="",
            min_lines=4,
            content_padding= padding.only(left=5),
            color = colors.ON_BACKGROUND,
            #filled=True,
            #border_radius=0,
        )
        self.pb = ProgressBar(width=300, color=colors.PRIMARY, bgcolor=colors.BACKGROUND, value=0)

        self.t = CustomThread1(self.reload_clicked,self.dd)
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
                        self.dd,
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
                    height=230,
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

    def dd_change(self, e):
        self.t.kill()
        self.t = CustomThread1(self.reload_clicked,self.dd)
        self.t.start()

    


def main(page: Page):
    page.title = "METAR.id"
    #page.theme_mode = "LIGHT"
    page.window_width = 300
    page.window_height = 400
    page.window_maximizable = False
    page.window_resizable = False
    page.window_always_on_top = True
    page.theme = theme.Theme(color_scheme_seed='blue')
    #page.on_window_event = window_event
    page.update()

    # create application instance
    app = TodoApp()

    

    # add application's root control to the page
    page.add(app)


class CustomThread1(threading.Thread):
  def __init__(self, reload_clicked, dd):
    super().__init__()
    self.reload_clicked = reload_clicked
    self.dd = dd

  def kill(self):
    ret = ctypes.pythonapi.PyThreadState_SetAsyncExc(self.native_id, ctypes.py_object(SystemExit))
    if ret > 1:  # 状態が変更されたスレッドの数を返す。通常は、1。見つからなかった場合は、0。
      ctypes.pythonapi.PyThreadState_SetAsyncExc(self.native_id, None)  # たぶん必要ないが念のため。まだ送られていない例外を消去
  
  def run(self):
    while True:
        if self.dd.value == "None":
            while True:
                time.sleep(1)
                print("waiting")
        interval = int(re.findall(r"\d+", self.dd.value)[0])
        time.sleep(interval*60)
        self.reload_clicked(None)




flet.app(target=main)
