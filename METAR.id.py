import flet
from flet import *
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import math
import webbrowser
import re
import unicodedata
import threading
import time
import ctypes
import os
import sys

load_url = "https://www.imocwx.com/i/metar.php"
metars = {}
specialKey = ["VERSION","VATSIM","VATJPN","SANSUKE","TEMP","SQUAWKID","SOURCE","METAR.ID"]
version = "beta 1.0"
filepath = os.path.dirname(os.path.abspath(sys.argv[0]))
textFiles = ["RWYData.txt","AIRCRAFT.txt","AIRLINES.txt"]

RWYData = {}
aircrafts = {}
airlines = {}
fixnames = {}

def check_version():
    try:
        corrent_version = requests.get("https://raw.githubusercontent.com/sansuke1005/METAR.id/main/corrent_version.txt",timeout=3.5).text
    except RequestException:
        return 3
    if corrent_version == "404: Not Found":
        return 2
    if version == corrent_version:
        return 0
    return 1
    
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
    if os.path.isfile(os.path.join(filepath, "FIXNAMES.txt")):
        with open(os.path.join(filepath, "FIXNAMES.txt")) as f:
            flines = f.readlines()
            del flines[0]
            for data in flines:
                dataList = data.split(",")
                if not dataList[0] in fixnames.keys():
                    fixnames[dataList[0]]=dataList[2]
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
    if metar_split[3] == "AUTO" or metar_split[3] == "COR":
        del metar_split[3]
    if "NIL" in metar_split[3]:
        metar_short = [metar_split[1],metar_split[2][2:],"N/A","N/A"]
        return " ".join(metar_short)
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
    if wind == "N/A":
        return ["RWY" + priy_rwy.zfill(2),False]
    if wind[:3] == "VRB":
        return ["RWY" + priy_rwy.zfill(2),False]
    wind_d = int(wind[:3])
    wind_v = int(wind[4:])
    wind_limit = int(RWYData[port][2])
    wind_diff = int(priy_rwy)*10 - wind_d
    wind_t = -math.cos(math.radians(wind_diff))*wind_v
    recommendRWY = ""
    if wind_t < wind_limit:
        if wind_t > 0:
            return ["RWY" + priy_rwy.zfill(2),True]
        else:
            return ["RWY" + priy_rwy.zfill(2),False]
    return ["RWY" + oppo_rwy.zfill(2),False]

def chekIMC(metar):
    if metar == "Error":
        return False
    metar_split = metar.split(" ")
    if metar_split[3] == "AUTO" or metar_split[3] == "COR":
        del metar_split[3]

    if "NIL" in metar_split[3]:
        return False

    for s in metar_split:
        if s.isdecimal():
            if int(s) < 5000:
                return True

    for s in metar_split:
        if "BKN" in s or "OVC" in s :
            if s[3:].isdecimal():
                if int(s[3:]) < 10:
                    return True
    return False

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
    menus = ["Company","Callsign","Country"]
    for i in range(3):
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
    if s == specialKey[7]:
        webbrowser.open("https://github.com/sansuke1005/METAR.id", new=0, autoraise=True)
    return ""    

def get_fix_name(s):
    if s not in fixnames.keys():
        return None
    fixname = "Name: " + fixnames[s]
    return s + "\n" + fixname

def autoSelector(s):
    if s in specialKey:
        return [special(s),None]
    if s.isdecimal() and (len(s)==6 or len(s)==7):
        webbrowser.open("https://stats.vatsim.net/stats/"+s, new=0, autoraise=True)
        return ["",None]
    if len(s)==1:
        return [getMetar("RJ"+s+s),"METAR"]
    if len(s)==2:
        return [getMetar("RJ"+s),"METAR"]
    if s[:2] == "RJ" or s[:2] == "RO":
        return [getMetar(s),"METAR"]
    if get_fix_name(s) != None:
        return [get_fix_name(s),"Fix"]
    if getAircraft(s) != None:
        return [getAircraft(s),"Aircraft"]
    if getAirline(s) != None:
        return [getAirline(s),"Airline"]
    return ["Error",None]


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

        self.recommendRWY = getRecommendRWY(self.metar_short[0],self.metar_short)
        self.textRWY = Text(self.recommendRWY[0], size=13, text_align = TextAlign.CENTER)
        if self.recommendRWY[1]:
            self.textRWY.color = colors.RED

        self.display_view = Container(
            Row(
                alignment="spaceBetween",
                vertical_alignment="center",
                height=17,
                controls=[
                    Container(
                        Text(self.metar_short[0], size=13, text_align = TextAlign.CENTER),
                        width=40,
                    ),
                    Container(
                        Text(self.metar_short[1], size=13, text_align = TextAlign.CENTER),
                        width=40,
                    ),
                    Container(
                        Text(self.metar_short[2], size=13, text_align = TextAlign.CENTER),
                        width=53,
                    ),
                    Container(
                        Text(self.metar_short[3], size=13, text_align = TextAlign.CENTER),
                        width=40,
                    ),
                    Container(
                        self.textRWY,
                        width=45,
                    ),

                    IconButton(
                        icons.DELETE_OUTLINE,
                        on_click=self.delete_clicked,
                        icon_size=18,
                        width=20,
                        
                        style=ButtonStyle(
                            color={
                                MaterialState.HOVERED: colors.RED,
                                MaterialState.DEFAULT: colors.ON_BACKGROUND,
                            },
                            overlay_color=colors.with_opacity(0, colors.PRIMARY),
                            padding=1,
                        ),
                    ),
                ],
            ),
            padding=5,
            ink=True,
            on_click=self.container_clicked,
        )
        if chekIMC(self.metar):
            self.display_view.bgcolor = colors.with_opacity(0.1, colors.RED)
        return Column(controls=[self.display_view],spacing=0,)
    
    def container_clicked(self, e):
        self.task_clicked(self,getAiportName(self.task_name)+"\n"+metars[self.task_name],"METAR")

    def delete_clicked(self, e):
        metars.pop(self.metar_short[0])
        self.task_delete(self)


class TodoApp(UserControl):
    def build(self):
        self.new_task = TextField(
            text_size=13,
            expand=True, 
            on_submit=self.add_clicked, 
            on_change=self.check_alnum,
            content_padding= padding.only(left=5),
            border_color = colors.OUTLINE,
        )
        self.tasks = Column(spacing=0, scroll=ScrollMode.AUTO,)
        self.info = TextField(
            text_size=13,
            multiline=True,
            read_only=True,
            value="",
            min_lines=4,
            max_lines=4,
            content_padding= 5,
            border_color = colors.OUTLINE_VARIANT,
            focused_border_color = colors.OUTLINE_VARIANT,
            focused_border_width = 1,
            label=None,
            label_style = TextStyle(
                size = 13,
                color = colors.OUTLINE_VARIANT,
            )
            
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
                    height=215,
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
        if info[0][:5] == "METAR":
            task = Task(self.new_task.value, self.task_delete, self.task_clicked)
            self.tasks.controls.append(task)
        else:
            self.task_clicked(None, info[0], info[1])
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

    def task_clicked(self, task, new_info, info_label):
        self.info.value = new_info
        self.info.label = info_label
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
    page.window_height = 396
    page.window_maximizable = False
    page.window_resizable = False
    page.window_always_on_top = True
    page.theme = theme.Theme(color_scheme_seed='blue')
    page.update()

    app = TodoApp()
    page.add(app)


    version_status = check_version()
    def dlf_update(e):
        if version_status == 1:
            webbrowser.open("https://github.com/sansuke1005/METAR.id/releases", new=0, autoraise=True)
        page.window_destroy()

    dlg_update = AlertDialog(
        modal=True,

        actions_alignment=MainAxisAlignment.END,
    )
    status_title = ["","アップデートがあります","アプリは現在使用できません","ネットワークエラー"]
    if version_status != 0:
        time.sleep(0.1)
        page.dialog = dlg_update
        dlg_update.title = Text(status_title[version_status])
        if version_status == 1:
            dlg_update.actions = [TextButton("Go to Github", on_click=dlf_update)]
        else:
            dlg_update.actions = [TextButton("OK", on_click=dlf_update)]
        dlg_update.open = True
        page.update()

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
