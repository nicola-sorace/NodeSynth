import numpy as np
import pygame

PR = 8 #Port radius
HH = 25 #Header height
TBW = 60 #Text-box width
NCR = 3 #Connected node circle radius

CRHEADER = 20 #Header for node creation menu
CRH = 20 #Height of each item in node creation menu

#Constants referring each type of menu:
M_NEWNODE = 0
M_NODE = 1

BGCOLOR = (26,26,26)
NODECOLOR = (200,200,200)
INCOLOR = (0,0,150)
OUTCOLOR = (0,0,150)
WIRECOLOR = (200,200,200)
SPOOLCOLOR = (255,0,255)
CURSCOLOR = (255,0,255)

pygame.init()
FONT = pygame.font.SysFont("monospace", 14)

class Input:
    def __init__(self, name, default):
        self.name = name
        self.default = default

        self.connected = False
        self.source = None
        self.n = 0 #Indicates which of source's outputs we are connected to

    def getValue(self, t):
        if not self.connected: return self.default
        else: return self.source.getValue(self.n, t)

    def connect(self, source, n):
        self.connected = True
        self.source = source
        self.n = n
    def disconnect(self):
        self.connected = False

class Node:
    def __init__(self, x, y, name, ins, outs, width):
        self.name = name
        self.ins = ins
        self.outs = outs

        self.b = (x, y, width, 0) #Node's bounding box
        self.bIn = (0, 0, 0, 0) #Input ports' bounding box
        self.bOut = (0, 0, 0, 0) #Output ports' bounding box
        self.bTxt = (0, 0, 0, 0) #Input value's text boxes' (when nothing is connected) bounding box
        self.updateBounds() #TODO Remove once default Node is no longer being used (update is redundant)

    def getValue(self, n, t):   #Nodes must extend this method
        return self.ins[0].getValue(t)

    def draw(self, screen):
        pygame.draw.rect(screen, NODECOLOR, self.b)
        pygame.draw.rect(screen, BGCOLOR, self.b, 1)

        w = FONT.size(self.name)[0]
        name = FONT.render(self.name, 1, (0, 0, 0))
        screen.blit(name, (self.b[0]+(self.b[2]-w)/2, self.b[1]))

        for port in enumerate(self.ins):
            pygame.draw.ellipse(screen, INCOLOR, [self.b[0]-PR, self.b[1]+port[0]*PR*3+HH, PR*2, PR*2])
            pygame.draw.ellipse(screen, BGCOLOR, [self.b[0]-PR, self.b[1]+port[0]*PR*3+HH, PR*2, PR*2],1)
            w = self.bIn[2]-PR*2 #FONT.size(port[1].name)[0]
            pygame.draw.rect(screen, INCOLOR, [self.b[0], self.b[1]+port[0]*PR*3+HH, w+PR, PR*2])
            name = FONT.render(port[1].name, 1, (255, 255, 255))
            screen.blit(name, (self.b[0], self.b[1]+port[0]*PR*3+HH))

            if port[1].connected:
                p1 = (self.b[0]-PR, self.b[1]+port[0]*PR*3+PR+HH)
                p2 = (port[1].source.b[0]+port[1].source.b[2]+PR, port[1].source.b[1]+port[1].n*PR*3+PR+HH)
                pygame.draw.line(screen, WIRECOLOR, p1, p2,2)
                pygame.draw.ellipse(screen, WIRECOLOR, [p1[0]-NCR, p1[1]-NCR, NCR*2, NCR*2])
                pygame.draw.ellipse(screen, WIRECOLOR, [p2[0]-NCR, p2[1]-NCR, NCR*2, NCR*2])
            else:
                if port[1].default > 9999999: txt = str("%.1e" % port[1].default)
                else: txt = str(port[1].default)
                pygame.draw.rect(screen, (255,255,255), [self.bIn[0]+self.bIn[2], self.bIn[1]+port[0]*PR*3, TBW, PR*2])
                name = FONT.render(txt, 1, (0, 0, 0))
                screen.blit(name, (self.bIn[0]+self.bIn[2]+(TBW-FONT.size(txt)[0])/2, self.bIn[1]+port[0]*PR*3))

        for port in enumerate(self.outs):
            pygame.draw.ellipse(screen, OUTCOLOR, [self.b[0]+self.b[2]-PR, self.b[1]+port[0]*PR*3+HH, PR*2, PR*2])
            pygame.draw.ellipse(screen, BGCOLOR, [self.b[0]+self.b[2]-PR, self.b[1]+port[0]*PR*3+HH, PR*2, PR*2],1)
            w = self.bOut[2]-PR*2 #FONT.size(port[1])[0]
            pygame.draw.rect(screen, OUTCOLOR, [self.b[0]+self.b[2]-PR-w, self.b[1]+port[0]*PR*3+HH, w+PR, PR*2])
            name = FONT.render(port[1], 1, (255, 255, 255))
            screen.blit(name, (self.b[0]+self.b[2]-w, self.b[1]+port[0]*PR*3+HH))

    def drag(self, drag):
        self.b = (self.b[0]+drag[0], self.b[1]+drag[1], self.b[2], self.b[3])
        self.bIn = (self.bIn[0]+drag[0], self.bIn[1]+drag[1], self.bIn[2], self.bIn[3])
        self.bOut = (self.bOut[0]+drag[0], self.bOut[1]+drag[1], self.bOut[2], self.bOut[3])
        self.bTxt = (self.bTxt[0]+drag[0], self.bTxt[1]+drag[1], self.bTxt[2], self.bTxt[3])

    def destroy(self, nodes):
        self.disconnectAll(nodes)
        nodes.remove(self)

    def disconnectAll(self, nodes):
        for node in nodes:
            for port in node.ins:
                if port.source == self or node == self: port.disconnect()

    def getIndex(self, y): #Returns index of port being hovered on. (0/1->input/ouput port, mouse's y-position (x is irrelevant))
        y = y-self.b[1]-HH #Transform y into relative position
        return int(y/(PR*3))

    def updateBounds(self):

        self.b = (self.b[0], self.b[1], self.b[2], max(len(self.ins)*PR*3+HH,len(self.outs)*PR*3+HH))

        h = len(self.ins)*PR*3
        self.bIn = (self.b[0]-PR, self.b[1]+HH, 0, h)
        for port in self.ins:
            w = FONT.size(port.name)[0]+PR*2
            if w > self.bIn[2]:
                self.bIn = (self.bIn[0], self.bIn[1], w, self.bIn[3])
        self.bTxt = (self.bIn[0]+self.bIn[2], self.bIn[1], TBW, self.bIn[3])

        h = len(self.outs)*PR*3
        self.bOut = (self.b[0]+self.b[2], self.b[1]+HH, 0, h)
        for port in self.outs:
            w = FONT.size(port)[0]+PR*2
            if w > self.bOut[2]: self.bOut = (self.b[0]+self.b[2]-w+PR, self.bOut[1], w, self.bOut[3])


class OutputNode(Node):
    def __init__(self, x, y):
        Node.__init__(self, x, y,
            "Output",
            [Input("In", 0)],
            [""],
            100)

    def removeFrom(self, nodes):
        pass

class ValueNode(Node):
    def __init__(self, x, y):
        Node.__init__(self, x, y,
            "Value",
            [Input("Value", 0)],
            [""],
            116)

class GeneratorNode(Node):
    def __init__(self, x, y):
        Node.__init__(self, x, y,
            "Wave Generator",
            [Input("Amplitude", 1), Input("Frequency", 1), Input("X-Offset", 0), Input("Y-Offset", 0)],
            ["Sine","Square","Triangle","Sawtooth","Heaviside", "y = x"],
            230)

    def getValue(self, n, t):
        a = self.ins[0].getValue(t)
        f = self.ins[1].getValue(t)
        x = self.ins[2].getValue(t)
        y = self.ins[3].getValue(t)

        t = t*f-x

        out = 0

        if   n==0: out = np.sin(2*np.pi*t)     #Sine
        elif n==1: out = 2*(np.round(t%1)-0.5) #out = (-1 if t%1<0.5 else 1)       #Square
        elif n==2: out = np.abs(((t-0.25)%1-0.5)*2)*2-1                             #Triangle
        elif n==3: out = (t%1-0.5)*2                  #Sawtooth
        elif n==4: out = heaviside(t)                  #Heaviside
        elif n==5: out = t                             #y=x

        return a*out+y

class MathNode(Node):
    def __init__(self, x, y):
        Node.__init__(self, x, y,
            "Math",
            [Input("a", 0), Input("b", 0)],
            ["a+b","a*b","max","min"],
            130)

    def getValue(self, n, t):
        a = self.ins[0].getValue(t)
        b = self.ins[1].getValue(t)
        if   n==0: return a+b
        elif n==1: return a*b
        elif n==2: return np.maximum(a,b)
        elif n==3: return np.minimum(a,b)
        else: return 0

class TransformNode(Node):
    def __init__(self, x, y):
        Node.__init__(self, x, y,
            "Transform",
            [Input("In", 0), Input("Amplitude", 1), Input("Frequency", 1), Input("X-Offset", 0), Input("Y-Offset", 0)],
            ["Out"],
            190)

    def getValue(self, n, t):
        a = self.ins[1].getValue(t)
        f = self.ins[2].getValue(t)
        x = self.ins[3].getValue(t)
        y = self.ins[4].getValue(t)
        return a*self.ins[0].getValue(t*f-x)+y

class SectionNode(Node):
    def __init__(self, x, y):
        Node.__init__(self, x, y,
            "Section",
            [Input("In", 0), Input("Min", 0), Input("Max", 1)],
            ["Min", "Max", "Both"],
            150)

    def getValue(self, n, t):
        v = self.ins[0].getValue(t)
        mi = self.ins[1].getValue(t)
        ma = self.ins[2].getValue(t)

        if n==0 or n==2:
            v = v*heaviside(t-mi)
        if n==1 or n==2:
            v = v*heaviside(ma-t)

        return v

''' Failed node tests:
class SmoothNode(Node):
    def __init__(self, x, y):
        Node.__init__(self, x, y,
            "Smoothing",
            [Input("In", 0), Input("Factor", 1), Input("Steps", 1)],
            ["Out"],
            160)

    def getValue(self, n, t):
        i = self.ins[0]
        f = self.ins[1].getValue(t)
        s = self.ins[2].getValue(t)

        return np.sum([i.getValue(t+(f/s)*x) for x in range(int(-s),int(s))]) / (s*2)

        #return np.sum([i.getValue(t+x/100) for x in range(int(-f),int(+f))]) / (f*2+1)

class EchoNode(Node):
    def __init__(self, x, y):
        Node.__init__(self, x, y,
            "Echo",
            [Input("In", 0), Input("Number", 1), Input("Delay", 100), Input("Falloff", 0.5)],
            ["Out", "Echo Only"],
            220)

    def getValue(self, n, t):
        if n==0: v = self.ins[0].getValue(t)
        else: v = 0
        r = int(self.ins[1].getValue(t))
        d = self.ins[2].getValue(t)
        f = self.ins[3].getValue(t)

        for i in range(1,r+1):
            v += f**i * self.ins[0].getValue(t - d*i)

        return v
'''

class OscilloscopeNode(Node):
    def __init__(self, x, y):

        self.cBG = (0,0,0)
        self.cFG = (0,255,0)
        self.cFG2 = (50,50,50)
        self.cER = (255,0,0) #Clipping color (a.k.a. 'error' color)

        self.HEADER = 80
        self.W = 200
        self.H = 100

        Node.__init__(self, x, y,
            "Oscilloscope",
            [Input("In", 0), Input("Scale", 2)],
            [""],
            250)

    def draw(self, screen):
        Node.draw(self, screen)

        self.bGraph = [self.b[0]+(self.b[2]-self.W)/2, self.b[1]+self.HEADER, self.W, self.H]
        pygame.draw.rect(screen, self.cBG, [self.bGraph[0],self.bGraph[1]-1,self.bGraph[2],self.bGraph[3]+3])

        for i in range(1,4):
            y = self.bGraph[1]+(self.bGraph[3]/4)*i
            pygame.draw.line(screen, self.cFG2, (self.bGraph[0], y), (self.bGraph[0]+self.bGraph[2]-1, y))

        oldY = self.getY(0)

        for x in range(1,self.W+1):
            y = self.getY(x)
            pygame.draw.aaline(screen, self.cFG, (self.b[0]+(self.b[2]-self.W)/2 + x-1, oldY[1]), (self.b[0]+(self.b[2]-self.W)/2 + x, y[1]))
            if oldY[0]: pygame.draw.rect(screen, self.cER, [self.b[0]+(self.b[2]-self.W)/2 + x-1, oldY[1], 1, 1])
            oldY = y

    def getY(self, x):
        v = self.ins[0].getValue((x/self.W)*self.ins[1].getValue(0))
        return (v>1 or v<-1, self.b[1]+self.HEADER+self.H/2- min(max(v,-1),1) *self.H/2)

    def updateBounds(self):
        Node.updateBounds(self)
        self.b = [self.b[0],self.b[1],self.b[2],self.b[3]+self.H+30]

def heaviside(t):
    t = np.maximum(0,np.minimum(0.9,t+0.5))
    return np.round(t%1)

NEWNODESLIST = [ValueNode(0,0), GeneratorNode(0,0), TransformNode(0,0), SectionNode(0,0), MathNode(0,0), OscilloscopeNode(0,0)]
NODEMENU = ["Duplicate", "Disconnect all", "", "Delete node"]
