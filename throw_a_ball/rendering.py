"""Dependency-free RGB888 renderer for the 128x128 Roller Ball prototype."""
from __future__ import annotations

from throw_a_ball.roller_ball import POCKETS, PowerZone, ShotResult

WIDTH = 128
HEIGHT = 128
RGB888_BYTE_LENGTH = WIDTH * HEIGHT * 3
Color = tuple[int, int, int]
BLACK=(3,5,12); NAVY=(5,13,35); BLUE=(32,128,255); CYAN=(66,232,255); WHITE=(235,244,255)
YELLOW=(255,202,46); RED=(245,52,40); GREEN=(70,218,106); PURPLE=(178,78,255); GRAY=(98,112,140)
DARK_GRAY=(32,38,52); WOOD=(91,51,29); ORANGE=(255,128,32)

_DIGITS={
"0":("111","101","101","101","111"),"1":("010","110","010","010","111"),
"2":("111","001","111","100","111"),"3":("111","001","111","001","111"),
"4":("101","101","111","001","001"),"5":("111","100","111","001","111"),
"6":("111","100","111","101","111"),"7":("111","001","010","010","010"),
"8":("111","101","111","101","111"),"9":("111","101","111","001","111")}


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

def _pocket_color(score):
    return WHITE if score in (100,20) else YELLOW if score==50 else BLUE if score==40 else CYAN if score==30 else GRAY

def _draw_board(f):
    _rect(f,4,2,120,124,NAVY); _rect(f,7,5,114,118,BLACK); _rect(f,11,13,106,100,NAVY)
    _rect(f,19,105,90,17,WOOD); _rect(f,25,111,78,11,(120,72,38))
    _circle(f,64,78,43,CYAN,hollow=True,thickness=3); _circle(f,64,78,39,(10,24,54)); _number(f,10,58,102,WHITE,2)
    for p in POCKETS:
        c=_pocket_color(p.score); _circle(f,p.x,p.y,p.radius+2,DARK_GRAY); _circle(f,p.x,p.y,p.radius,c,hollow=True,thickness=3)
        _circle(f,p.x,p.y,max(2,p.radius-4),BLACK); _number(f,p.score,p.x-len(str(p.score))*2,p.y-2,c,1)

def _meter(f,taps,zone):
    x0=20; y=115
    for i in range(12):
        c=YELLOW if i<4 else GREEN if i<8 else RED
        _rect(f,x0+i*7,y,5,6,c if i<taps else DARK_GRAY)
    if zone is not None:
        c=YELLOW if zone is PowerZone.YELLOW else GREEN if zone is PowerZone.GREEN else RED
        _rect(f,14,113,3,10,c)

def render_frame(*,score:int,balls_used:int,ball_position=None,last_shot:ShotResult|None=None,message_code:int=0,
                 ui_mode:str="play",style_index:int=0,aim_position:tuple[int,int]|None=None,power_taps:int=0,power_zone:PowerZone|None=None)->bytes:
    f=_frame(); _draw_board(f)
    _rect(f,8,6,112,6,DARK_GRAY); _number(f,score,11,7,YELLOW,1); _number(f,max(0,9-balls_used),105,7,WHITE,1)

    if ui_mode=="style":
        _rect(f,18,44,92,42,DARK_GRAY); _rect(f,24,51,36,28,BLUE if style_index==0 else GRAY); _rect(f,68,51,36,28,PURPLE if style_index==1 else GRAY)
        _number(f,1,38,61,WHITE,2); _number(f,2,82,61,WHITE,2); _rect(f,28 if style_index==0 else 72,82,28,3,YELLOW)
    elif ui_mode=="aim":
        if aim_position:
            _circle(f,aim_position[0],aim_position[1],6,ORANGE,hollow=True,thickness=2); _circle(f,aim_position[0],aim_position[1],1,WHITE)
        _rect(f,35,115,58,7,ORANGE)
    elif ui_mode=="power":
        _meter(f,min(power_taps,12),power_zone)
    elif ui_mode=="ready":
        _rect(f,38,114,52,8,GREEN)

    if last_shot is not None and message_code in (1,2):
        _rect(f,48,114,32,9,DARK_GRAY); _number(f,last_shot.score,55,116,GREEN if last_shot.score else RED,1)
    if message_code==2: _rect(f,10,115,32,5,RED)
    elif message_code==3: _rect(f,10,114,108,8,PURPLE); _number(f,score,52,116,WHITE,1)
    if ball_position is not None:
        bx,by=ball_position; _circle(f,bx,by,4,BLUE); _circle(f,bx-1,by-1,1,WHITE)
    if len(f)!=RGB888_BYTE_LENGTH: raise RuntimeError("renderer produced wrong framebuffer size")
    return bytes(f)
