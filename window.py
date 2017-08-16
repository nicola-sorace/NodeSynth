import threading
from threading import Thread
import string

import pygame

from nodes import *

def isWithin(point, rect):
    if point[0]>rect[0] and point[0]<rect[0]+rect[2] and point[1]>rect[1] and point[1]<rect[1]+rect[3]: return True
    else: return False

class Instrument:
    def __init__(self):
        self.outNode = OutputNode(700,10)
        self.nodes = [self.outNode, GeneratorNode(20,10), GeneratorNode(20,250), MathNode(400,100), OscilloscopeNode(700, 300)]
        self.nodes[0].ins[0].connect(self.nodes[1], 0)
        self.nodes[4].ins[0].connect(self.nodes[0], 0)

class Window(threading.Thread):

    def __init__(self):
        super(Window, self).__init__()

        self.killSound = False #Make true to force-kill all sounds

        self.screen = pygame.display.set_mode((1000, 600), pygame.RESIZABLE) #TODO Resizable window
        pygame.display.set_caption("NodeSynth2", "NS2")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 15)
        self.done = False

        self.mouseDown = False
        self.mouse = (0,0)
        self.mouseTaken = False #Becomes true to prevent dragging/selecting etc. two things at once

        self.drag = (0,0)
        self.dragging = None #Holds node being dragged

        self.spooling = False #True when dragging to connect a new node
        self.spool = (0, None, 0) #(0/1->input/output port, Node being dragged from, index of port)

        self.writing = False
        self.write = ("", None, 0)

        self.menuing = False
        self.bMenu = (0,0,0,0)
        self.menu = (0,None,-1) #Menu info: (type of menu, node (or None), selected item (-1=none))
        self.menuTitle = ""
        self.menuList = [""]

        self.instrument = Instrument()

    def run(self):
        while not self.done:

            self.drag = (0,0)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
                elif event.type == pygame.VIDEORESIZE: #TODO Make this work
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.menuing:
                            if self.menu[2] != -1:
                                if self.menu[0] == M_NEWNODE: self.instrument.nodes.append(NEWNODESLIST[self.menu[2]].__class__(self.bMenu[0],self.bMenu[1]))
                                elif self.menu[0] == M_NODE:
                                    if self.menu[2] == 0: self.menu[1].disconnectAll(self.instrument.nodes)
                                    elif self.menu[2] == 2: self.menu[1].destroy(self.instrument.nodes)
                            self.menuing = False
                            self.menu = (self.menu[0], self.menu[2], -1)
                        else: self.mouseDown = True
                    elif event.button == 3:

                        nodeHover = False #True if mouse is hovering over a node
                        for node in self.instrument.nodes:
                            if isWithin(self.mouse, node.b):
                                nodeHover = True
                                self.menu = (1,node,-1)
                                break
                        if not nodeHover:
                            self.menu = (0,None,-1)

                        if self.menu[0] == M_NEWNODE:
                            self.menuTitle = "Create Node"
                            self.menuList = [node.name for node in NEWNODESLIST]
                        elif self.menu[0] == M_NODE:
                            self.menuTitle = self.menu[1].name
                            self.menuList = NODEMENU
                        self.bMenu = [self.mouse[0], self.mouse[1], max([FONT.size(x)[0] for x in self.menuList+[self.menuTitle]])+6, CRHEADER+len(self.menuList)*CRH]

                        self.menuing = True
                        self.mouseTaken = True
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.mouseDown = False
                    if not self.menuing: self.mouseTaken = False
                    self.dragging = None
                    if self.spooling:
                        self.spooling = False
                        for node in self.instrument.nodes:
                            #TODO Connecting nodes into a loop should not be allowed.
                            if node != self.spool[1] and isWithin(self.mouse, (node.b[0]-PR, node.b[1], node.b[2]+PR*2, node.b[3])):
                                if (isWithin(self.mouse, node.bIn) or isWithin(self.mouse, node.bTxt)) and self.spool[0]==1:
                                    inPort = node.ins[node.getIndex(self.mouse[1])]
                                    if inPort.connected and inPort.source == self.spool[1] and inPort.n == self.spool[2]: inPort.disconnect()
                                    else: inPort.connect(self.spool[1],self.spool[2])
                                elif isWithin(self.mouse, node.bOut) and self.spool[0]==0:
                                    inPort = self.spool[1].ins[self.spool[2]]
                                    n = node.getIndex(self.mouse[1])
                                    if inPort.connected and inPort.source == node and inPort.n == n: inPort.disconnect()
                                    else: inPort.connect(node,n)
                                break

                elif event.type == pygame.MOUSEMOTION:
                    if self.mouseDown: self.drag = (-self.mouse[0]+event.pos[0], -self.mouse[1]+event.pos[1])
                    self.mouse = event.pos

                    if self.menuing and isWithin(self.mouse, [self.bMenu[0],self.bMenu[1]+CRHEADER,self.bMenu[2],self.bMenu[3]-CRHEADER]): self.menu = (self.menu[0], self.menu[1], int((self.mouse[1]-self.bMenu[1]-CRHEADER)/CRH))
                    else: self.menu = (self.menu[0], self.menu[1], -1)


                elif event.type == pygame.KEYDOWN:
                    #print(event.key)
                    if event.key == 32: self.killSound = True

                    if self.writing:
                        if event.key == 8: self.write = (self.write[0][:-1], self.write[1],self.write[2])
                        elif event.key == 27:
                            self.writing = False
                        elif event.key == 13 or event.key == 271:
                            try:
                                v = eval(self.write[0])
                                self.write[1].ins[self.write[2]].default = v
                            except:
                                pass
                            self.writing = False
                        elif chr(event.key).isprintable(): self.write = (self.write[0]+chr(event.key), self.write[1],self.write[2])

            self.screen.fill(BGCOLOR)

            for node in self.instrument.nodes:
                #TODO Way too much repetition. This section can probably be simplified a lot.
                if self.dragging == node or (not self.mouseTaken and self.mouseDown and isWithin(self.mouse, (node.b[0]-PR, node.b[1], node.b[2]+PR*2, node.b[3]))):
                    self.mouseTaken = True
                    if (not self.dragging) and isWithin(self.mouse, node.bIn):
                        self.writing = False
                        self.spooling = True
                        self.spool = (0, node, node.getIndex(self.mouse[1]))
                    elif (not self.dragging) and isWithin(self.mouse, node.bOut):
                        self.writing = False
                        self.spooling = True
                        self.spool = (1, node, node.getIndex(self.mouse[1]))
                    elif (not self.dragging) and isWithin(self.mouse, node.bTxt):
                        n = node.getIndex(self.mouse[1])
                        if not node.ins[n].connected:
                            self.writing = True
                            self.write = (str(node.ins[n].default), node, n)
                    else:
                        self.writing = False
                        self.instrument.nodes.insert(0, self.instrument.nodes.pop(self.instrument.nodes.index(node)))
                        self.dragging = node
                        node.drag(self.drag)

            for node in reversed(self.instrument.nodes): node.draw(self.screen)

            if self.spooling:
                if self.spool[0] == 0: pygame.draw.aaline(self.screen, SPOOLCOLOR, (self.spool[1].b[0]-PR, self.spool[1].b[1]+self.spool[2]*PR*3+PR+HH), self.mouse)
                else: pygame.draw.aaline(self.screen, SPOOLCOLOR, self.mouse, (self.spool[1].b[0]+self.spool[1].b[2]+PR, self.spool[1].b[1]+self.spool[2]*PR*3+PR+HH))

            if self.writing:

                b = self.write[1].bTxt
                b = (b[0], b[1]+self.write[2]*PR*3, b[2], PR*2)

                w = FONT.size(self.write[0])[0]

                pygame.draw.rect(self.screen, (255,255,200), b)
                name = FONT.render(self.write[0], 1, (0, 0, 0))
                self.screen.blit(name, (b[0]+(TBW-w)/2, b[1]))

                pygame.draw.line(self.screen, CURSCOLOR, (b[0]+(TBW+w)/2,b[1]+2), (b[0]+(TBW+w)/2,b[1]+b[3]-2))

            if self.menuing:
                pygame.draw.rect(self.screen, (255,255,255), self.bMenu)

                if self.menu[2]>-1: pygame.draw.rect(self.screen, (150,150,255), [self.bMenu[0], self.bMenu[1]+CRHEADER+self.menu[2]*CRH, self.bMenu[2], CRH])

                name = FONT.render(self.menuTitle, 1, (0, 0, 0))
                self.screen.blit(name, (self.bMenu[0]+(self.bMenu[2]-FONT.size(self.menuTitle)[0])/2, self.bMenu[1]))

                pygame.draw.line(self.screen, BGCOLOR, (self.bMenu[0],self.bMenu[1]+CRHEADER-1), (self.bMenu[0]+self.bMenu[2],self.bMenu[1]+CRHEADER-1))

                for action in enumerate(self.menuList):
                    name = FONT.render(action[1], 1, (0, 0, 0))
                    self.screen.blit(name, (self.bMenu[0]+2, self.bMenu[1]+CRHEADER+CRH*action[0]))

                pygame.draw.rect(self.screen, BGCOLOR, self.bMenu, 1)

            pygame.display.flip()
            self.clock.tick(60)
