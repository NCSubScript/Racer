debug = 0
if debug > 1:
    import time
    start_time = time.time()
    from inspect import currentframe, getframeinfo
    
import sys
import math
import json
import copy
import inspect
from inspect import currentframe, getframeinfo


def point(x, y):
    return {'x': x, 'y': y}

def vector(d, m):
    return {'d': d, 'm': m}

def deriv(a, b):
    return {'dx': a['x'] - b['x'], 'dy': a['y'] - b['y']}

def angleDelta(a, b, c = 0, l = 8):
    delta = 0
    targetA = a + 180
    targetB = b + 180
    delta = abs(targetA - targetB) % 360
    deltaB = abs(targetA - delta) % 360
    deltaC = abs(targetB - delta) % 360


    if delta > 180:
        delta = 360 - delta

    if deltaB < deltaC or c < 0:
        delta = delta * -1

    delta /= l

    return delta

def targetAngleOffset(target, center, offset):
    return (abs(target - center) % 360) - offset

class Root():
    data = {}
    def __init__(self):
        self.data['previous'] = {}

    def toJSON(self):
        return json.dumps(
        self,
        default=lambda o: {o.data}, 
        sort_keys=True,
        indent=4)

    def add(self, k, v):
        try:
            self.data[k].append(v)
        except:
            self.data[k] = [v]

    def update(self, arg, t = None):
        if isinstance(arg, dict) and t == None:
            for k, v in arg.items():
                if k in self.data:
                    self.data['previous'][k] = self.data[k]
                self.data[k] = v
        else:
            if t in self.data:
                self.data['previous'][t] = self.data[t]
            self.data[t] = arg

    def __str__(self):
        return str(self.toJSON())

class Entity(Root):
    parent = None
    def __init__(self, parent, data = {}):
        super(Entity, self).__init__()
        self.parent = parent
        self.data = data
        self.data['previous'] = {}

    

    def updateVector(self):
        dert = deriv(self.data['location'], self.data['target']['location'])
        dertd = deriv(self.data['target']['location'], self.data['location'])

        if 'location' in self.data['previous']:
            der = deriv(self.data['previous']['location'], self.data['location'])
        else: 
            der = deriv(self.data['location'], self.data['location'])

        speed =  math.sqrt(abs(der['dx'] ** 2) + abs(der['dy'] ** 2))

        self.data['target']['angle'] = math.atan2(dert['dy'], dert['dx']) * (180 / math.pi)
        self.data['target']['dist'] = math.sqrt((dertd['dx'] ** 2) + abs(dertd['dy'] ** 2))

        if (der['dy'] != 0):
            angle = (math.atan2(der['dy'],  der['dx']) * (180 / math.pi)) 
        else:
            if 'vector' in self.data['previous']:
                angle = self.data['previous']['vector']['d']
            else:
                angle = self.data['angle']

        self.update(vector(angle, speed), 'vector')
        
        

    def setSpeed(self):
        thrust = 100
        angleOffset = self.data['angle'] - self.data['angleOffset'] % 360
        if abs(self.data['angleOffset']) > 45:
            thrust = thrust * (1 - (abs(self.data['angleOffset']) / 180))
            thrust = thrust * 1.25
            if thrust > 100:
                thrust = 100
        else:
            thrust =  100
        
        # print(str(int(thrust)), file=sys.stderr, flush=True)

        # distance = self.data['target']['dist'] * 0.2

        if self.data['target']['type'] == 'checkpoint':
            if not ((self.data['ncid'] == 0) and (self.data['lap'] == 3)):
                if self.data['target']['dist'] < 2500:
                    # thrust = thrust * ((1 - abs(self.data['angleOffset'])) / 180)
                    thrust = thrust * (1 - (self.data['target']['dist'] / 2500)) * 2
                    if thrust < 10:
                        thrust = 10
                    if thrust > 100:
                        thrust = 100
                    if self.data['abortEarlyTurn'] == False:
                        self.data['earlyTurn'] = True
                        

        
        self.update("BOOST" if self.boost() else int(thrust), 'thrust')

    def boost(self):
        if self.parent.data['boost']:
            if self.data['target']['type'] == 'checkpoint':
                if self.parent.data['tick'] >= 25:
                    if self.data['target']['dist'] > 4500:
                        if ((self.data['target']['angle'] <= 1 and self.data['target']['angle'] >=0) or (self.data['target']['angle'] >= -1 and self.data['target']['angle'] <=0)):
                            self.parent.data['boost'] = False
                            return True

        return False

    def setMove(self):
        delta = angleDelta(self.data['target']['angle'], self.data['vector']['d'], targetAngleOffset(self.data['angle'], self.data['target']['angle'], self.data['angleOffset']))
        # print("delta: " + str(delta), file=sys.stderr, flush=True)
        delta *= math.pi / 180

        x = math.cos(delta) *  (self.data['target']['location']['x'] - self.data['location']['x']) - math.sin(delta) * (self.data['target']['location']['y'] - self.data['location']['y']) + self.data['location']['x']
        y = math.sin(delta) *  (self.data['target']['location']['x'] - self.data['location']['x']) + math.cos(delta) * (self.data['target']['location']['y'] - self.data['location']['y']) + self.data['location']['y']

        if x < 0:
            x = 0
        if x > 15999:
            x = 15999
        if y < 0:
            y = 0
        if y > 8999:
            y = 8999
        
        self.update(point(x, y), 'move')

    def setTarget(self, t, i):
        if t == 'checkpoint':
            if self.data['earlyTurn'] == True:
                i += 1
            if i >= len(self.parent.data[t]):
                i = 0
            target = {'location': self.parent.data[t][i]}
        else:
            target = self.parent.data[t][i]

        target['type'] = t
        self.data['target'] = target
        

        self.updateVector()

        if t == 'checkpoint':
            if (self.data['earlyTurn'] == True and self.data['target']['dist'] > 3500):
                self.data['earlyTurn'] = False
                self.data['abortEarlyTurn'] = True
                # print("turnEarly > 2500: " + str(self.data['earlyTurn']))

        if self.parent.data['tick'] > 1:
            if 'angleOffset' not in self.data:
                self.data['angleOffset'] = self.data['angle'] + self.data['target']['angle']
            self.setSpeed()
            self.setMove()
        else :
            self.data['move'] = point(self.parent.data['checkpoint'][1]['x'], self.parent.data['checkpoint'][1]['y'])
            self.data['thrust'] = 100      



class Game(Root):
    def __init__(self):
        super(Game, self).__init__()
        self.data['previous'] = {}

    def createEntity(self, title, data):
        self.add(title, Entity(self, data))
    
    def createItem(self, title, data):
        self.add(title, data)