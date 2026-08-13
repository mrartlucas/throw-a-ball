"""RGB888 renderers for the 128x128 Roller Ball board and 64x32 secondary display."""
from __future__ import annotations

from throw_a_ball.roller_ball import AimPosition, POCKETS, PowerZone, ShotResult

WIDTH=128; HEIGHT=128; RGB888_BYTE_LENGTH=WIDTH*HEIGHT*3
LOWER_WIDTH=64; LOWER_HEIGHT=32; LOWER_RGB888_BYTE_LENGTH=LOWER_WIDTH*LOWER_HEIGHT*3
Color=tuple[int,int,int]
BLACK=(3,5,12); NAVY=(5,13,35); BLUE=(32,128,255); CYAN=(66,232,255); WHITE=(235,244,255)
YELLOW=(255,202,46); RED=(245,52,40); GREEN=(70,218,106); PURPLE=(178,78,255); GRAY=(98,112,140)
DARK_GRAY=(32,38,52); WOOD=(91,51,29); ORANGE=(255,128,32)

_DIGITS={"0":("111","101","101","101","111"),"1":("010","110","010","010","111"),"2":("111","001","111","100","111"),"3":("111","001","111","001","111"),"4":("101","101","111","001","001"),"5":("111","100","111","001","111"),"6":("111","100","111","101","111"),"7":("111","001","010","010","010"),"8":("111","101","111","101","111"),"9":("111","101","111","001","111")}
_FONT={
"A":("010","101","111","101","101"),"B":("110","101","110","101","110"),"C":("011","100","100","100","011"),"D":("110","101","101","101","110"),"E":("111","100","110","100","111"),"F":("111","100","110","100","100"),"G":("011","100","101","101","011"),"H":("101","101","111","101","101"),"I":("111","010","010","010","111"),"K":("101","101","110","101","101"),"L":("100","100","100","100","111"),"M":("101","111","111","101","101"),"N":("101","111","111","111","101"),"O":("010","101","101","101","010"),"P":("110","101","110","100","100"),"R":("110","101","110","101","101"),"S":("011","100","010","001","110"),"T":("111","010","010","010","010"),"U":("101","101","101","101","111"),"V":("101","101","101","101","010"),"W":("101","101","111","111","101"),"Y":("101","101","010","010","010")," ":("000",)*5}

def _frame(fill:Color=BLACK): return bytearray(fill*(WIDTH*HEIGHT))
def _px(f,x,y,c):
    if 0<=x<WIDTH and 0<=y<HEIGHT:
        i=(y*WIDTH+x)*3; f[i:i+3]=bytes(c)
def _rect(f,x,y,w,h,c):
    for yy in range(max(0,y),min(HEIGHT,y+h)):
        for xx in range(max(0,x),min(WIDTH,x+w)): _px(f,xx,yy,c)
def _circle(f,cx,cy,r,c,*,hollow=False,thickness=2):
    r2=r*r; inner=max(0,r-thickness); i2=inner*inner
    for y in range(cy-r,cy+r+1):
        for x in range(cx-r,cx+r+1):
            d=(x-cx)**2+(y-cy)**2
            if d<=r2 and (not hollow or d>=i2): _px(f,x,y,c)
def _digit(f,ch,x,y,c,s=1):
    p=_DIGITS.get(ch)
    if p:
        for row,bits in enumerate(p):
            for col,bit in enumerate(bits):
                if bit=="1": _rect(f,x+col*s,y+row*s,s,s,c)
def _number(f,v,x,y,c,s=1):
    for i,ch in enumerate(str(v)): _digit(f,ch,x+i*4*s,y,c,s)
def _pocket_color(score): return WHITE if score in (100,20) else YELLOW if score==50 else BLUE if score==40 else CYAN if score==30 else GRAY

def _draw_board(f):
    _rect(f,4,2,120,124,NAVY); _rect(f,7,5,114,118,BLACK); _rect(f,11,13,106,100,NAVY)
    _rect(f,19,105,90,17,WOOD); _rect(f,25,111,78,11,(120,72,38))
    _circle(f,64,78,43,CYAN,hollow=True,thickness=3); _circle(f,64,78,39,(10,24,54)); _number(f,10,58,102,WHITE,2)
    for p in POCKETS:
        c=_pocket_color(p.score); _circle(f,p.x,p.y,p.radius+2,DARK_GRAY); _circle(f,p.x,p.y,p.radius,c,hollow=True,thickness=3); _circle(f,p.x,p.y,max(2,p.radius-4),BLACK); _number(f,p.score,p.x-len(str(p.score))*2,p.y-2,c,1)

def _meter(f,taps,zone):
    lit=min(12,int(max(0,float(taps))//2)); x0=20; y=115
    for i in range(12):
        c=YELLOW if i<4 else GREEN if i<8 else RED
        _rect(f,x0+i*7,y,5,6,c if i<lit else DARK_GRAY)
    if zone is not None:
        c=YELLOW if zone is PowerZone.YELLOW else GREEN if zone is PowerZone.GREEN else RED
        _rect(f,14,113,3,10,c)

def _aim_arrow(f,x,y,direction,color):
    if direction=="left": points=((x-4,y),(x+4,y),(x-4,y),(x-1,y-3),(x-4,y),(x-1,y+3))
    elif direction=="right": points=((x-4,y),(x+4,y),(x+4,y),(x+1,y-3),(x+4,y),(x+1,y+3))
    else: points=((x,y+4),(x,y-4),(x,y-4),(x-3,y-1),(x,y-4),(x+3,y-1))
    for start in range(0,len(points),2):
        x0,y0=points[start]; x1,y1=points[start+1]; steps=max(abs(x1-x0),abs(y1-y0),1)
        for step in range(steps+1): _px(f,round(x0+(x1-x0)*step/steps),round(y0+(y1-y0)*step/steps),color)
def _aim_slots(f,selected):
    selected_x=selected[0] if selected else None
    for x,direction in ((50,"left"),(64,"up"),(78,"right")): _aim_arrow(f,x,96,direction,ORANGE if x==selected_x else GRAY)

def render_frame(*,score:int,balls_used:int,ball_position=None,last_shot:ShotResult|None=None,message_code:int=0,ui_mode:str="play",style_index:int=0,aim_position:tuple[int,int]|None=None,aim_slots:bool=False,power_taps:float=0,power_zone:PowerZone|None=None)->bytes:
    f=_frame(); _draw_board(f); _rect(f,8,6,112,6,DARK_GRAY); _number(f,score,11,7,YELLOW,1); _number(f,max(0,9-balls_used),105,7,WHITE,1)
    if ui_mode=="aim":
        if aim_slots: _aim_slots(f,aim_position)
        elif aim_position: _circle(f,aim_position[0],aim_position[1],6,ORANGE,hollow=True,thickness=2); _circle(f,aim_position[0],aim_position[1],1,WHITE)
        _rect(f,35,115,58,7,ORANGE)
    elif ui_mode=="power": _meter(f,power_taps,power_zone)
    elif ui_mode=="ready":
        if aim_slots: _aim_slots(f,aim_position)
        c=YELLOW if power_zone is PowerZone.YELLOW else GREEN if power_zone is PowerZone.GREEN else RED
        _rect(f,38,114,52,8,c)
    if last_shot is not None and message_code in (1,2): _rect(f,48,114,32,9,DARK_GRAY); _number(f,last_shot.score,55,116,GREEN if last_shot.score else RED,1)
    if message_code==2: _rect(f,10,115,32,5,RED)
    elif message_code==3: _rect(f,10,114,108,8,PURPLE); _number(f,score,52,116,WHITE,1)
    if ball_position is not None:
        bx,by=ball_position; _circle(f,bx,by,4,BLUE); _circle(f,bx-1,by-1,1,WHITE)
    if len(f)!=RGB888_BYTE_LENGTH: raise RuntimeError("renderer produced wrong framebuffer size")
    return bytes(f)

def _lower_text(frame,text,x,y,color,scale=1):
    for index,char in enumerate(text):
        pattern=_FONT.get(char,_DIGITS.get(char,_FONT[" "]))
        for row,bits in enumerate(pattern):
            for col,bit in enumerate(bits):
                if bit=="1":
                    for yy in range(scale):
                        for xx in range(scale):
                            px=x+index*4*scale+col*scale+xx; py=y+row*scale+yy
                            if 0<=px<LOWER_WIDTH and 0<=py<LOWER_HEIGHT:
                                offset=(py*LOWER_WIDTH+px)*3; frame[offset:offset+3]=bytes(color)
def lower_text_width(text:str,scale:int=1)->int: return max(0,len(text)*4*scale-scale)
def _centered_lower_text(frame,text,y,color,scale=1): _lower_text(frame,text,max(0,(LOWER_WIDTH-lower_text_width(text,scale))//2),y,color,scale)
def _lower_rect(frame,x,y,w,h,color):
    for yy in range(max(0,y),min(LOWER_HEIGHT,y+h)):
        for xx in range(max(0,x),min(LOWER_WIDTH,x+w)):
            off=(yy*LOWER_WIDTH+xx)*3; frame[off:off+3]=bytes(color)
def _power_color(zone):
    if zone is PowerZone.YELLOW: return YELLOW
    if zone is PowerZone.GREEN: return GREEN
    if zone is PowerZone.RED: return RED
    return GRAY

def _draw_lower_aim(frame,aim):
    positions=(14,30,46); selected=(AimPosition.LEFT,AimPosition.CENTER,AimPosition.RIGHT).index(aim)
    for index,x in enumerate(positions):
        color=ORANGE if index==selected else GRAY
        if index==0: pts=((x,15),(x+1,14),(x+1,16),(x+2,13),(x+2,17),(x+2,15),(x+6,15))
        elif index==1: pts=((x+3,12),(x+2,13),(x+4,13),(x+1,14),(x+5,14),(x+3,13),(x+3,18))
        else: pts=((x+6,15),(x+5,14),(x+5,16),(x+4,13),(x+4,17),(x,15))
        for px,py in pts:
            off=(py*LOWER_WIDTH+px)*3; frame[off:off+3]=bytes(color)
def _draw_lower_meter(frame,taps):
    lit=min(12,int(max(0,float(taps))//2))
    for index in range(12):
        color=YELLOW if index<4 else GREEN if index<8 else RED
        if index>=lit: color=DARK_GRAY
        _lower_rect(frame,4+index*5,13,3,6,color)
def _draw_mini_roller(frame,progress):
    _lower_rect(frame,5,11,54,11,DARK_GRAY)
    _lower_rect(frame,8,19,48,2,PURPLE)
    for x in (16,28,40,52): _lower_rect(frame,x,12,4,4,CYAN)
    bx=8+round(max(0.0,min(1.0,float(progress)))*45)
    _lower_rect(frame,bx,17,3,3,BLUE)

def render_lower_frame(label:str,center:str,helper:str,*,aim:AimPosition|None=None,power_taps:float=0,power_zone:PowerZone|None=None,player:int=1,rolling_progress:float|None=None,result_score:int|None=None)->bytes:
    frame=bytearray(BLACK*(LOWER_WIDTH*LOWER_HEIGHT))
    _lower_rect(frame,0,0,64,2,PURPLE)
    _lower_text(frame,f"P{player}",1,3,BLUE,1)
    _centered_lower_text(frame,label.upper(),3,PURPLE)

    if rolling_progress is not None:
        _draw_mini_roller(frame,rolling_progress)
    elif result_score is not None:
        _centered_lower_text(frame,"SCORE",9,GRAY)
        text=str(result_score); scale=2 if len(text)<=3 else 1
        _centered_lower_text(frame,text,15,GREEN if result_score else RED,scale)
    elif aim is not None and label.upper()=="AIM":
        _draw_lower_aim(frame,aim)
    elif label.upper()=="POWER":
        _draw_lower_meter(frame,power_taps)
        if aim is not None:
            _lower_text(frame,aim.value[0].upper(),1,14,ORANGE)
    elif label.upper()=="THROW" and center.upper()=="READY":
        _centered_lower_text(frame,"THROW",9,WHITE,2)
        _centered_lower_text(frame,"READY",20,_power_color(power_zone),1)
        if aim is not None:
            _lower_text(frame,aim.value[0].upper(),1,22,ORANGE)
        if power_zone is not None:
            _lower_rect(frame,58,20,4,6,_power_color(power_zone))
    else:
        center=center.upper(); scale=2 if len(center)<=8 else 1
        _centered_lower_text(frame,center,11 if scale==2 else 14,WHITE,scale)

    if helper:
        _centered_lower_text(frame,helper.upper(),26,CYAN)
    if len(frame)!=LOWER_RGB888_BYTE_LENGTH: raise RuntimeError("lower renderer produced wrong framebuffer size")
    return bytes(frame)
