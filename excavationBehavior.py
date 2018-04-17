""" Roby Behavior File for COMP 380 Project using Malmo """
import MalmoPython


class excavationBehavior(object):
    def __init__(self, agent_host = None):
        if agent_host is None:
            print("No agent_host argument sent to excavationBehvaior Class!")
        # Initialize states for behavior
        self.FSM = {'excavating': self.updateExcavate,
                    'returning': self.updateReturn,
                    }
        self.agent_host = agent_host
        self.worldState = agent_host.world
        self.startPos = self.worldState.observations['cell']
        self.excavateDim = (5, 5, 5)
        self.safePos
   

    def updateExcavate(self):

        pass

    def updateReturn(self):
        pass
        
    def updateHeading(self):
        x = self.r.readHeading()

    def updateScanning(self):
        """Robot is in scanning state where the max light is going to be read"""
        print("Update Scanning")
        print("x = ", self.x)
        print("heading =", self.r.readHeading())
        if self.r.readAmbient() > self.maxLight:
            ev3.Sound.beep()
            self.maxLight = self.r.readAmbient()
            self.lightAngle = self.r.readHeading()

        if self.r.readAmbient() >=19:
            return 'triumph'
        print(self.r.readHeading())
        print(self.lightAngle)
        print(self.x)
        if self.r.readHeading() < (self.x -1) and self.r.readHeading() > (self.x-11):
            # ev3.sound.beep()
            self.r.curve(-.1, .1)
            self.oldState = 'scanning'
            return 'turnToLight'

    def updateTurnToLight(self):
        """ Robot stops when it has returned to face the brightest light."""
        print("Update Turn to Light")
        print(self.r.readHeading())
        print("x= ", self.x)
        print(self.maxLight)
        if self.r.readAmbient() >=19:
            return 'triumph'
        if(self.r.readHeading() < self.lightAngle+5 and self.r.readHeading() > self.lightAngle-5):
            self.r.forward(.2)
            self.oldState = 'turnToLight'
            return 'travelToLight'

        else: 
            self.r.curve(.1, -.1)

    def updateTravelToLight(self):
        print("Update Travel to Light")
        print(self.r.readDist ())
        print(self.r.readAmbient())
        print(self.r.readTouch())
        if((self.r.readDist() < 10)):
            self.r.backward(.5)
            self.oldState = 'travelToLight'
            return 'stuckOnWall'

        if(self.r.readAmbient() < self.maxLight - 5):
            self.r.curve(.1, -.1)
            self.oldState = 'travelToLight'
            return 'scanning'
        if self.r.readAmbient() >=19:
            return 'triumph'

    def updateStuckOnWall(self):
        print("stuckOnWall")
        if(self.r.readDist() > 20):
            self.r.curve(.1, -.1)
            self.oldState = 'stuckOnWall'
            return 'scanning'
    
    def updateTriumph(self):
        self.r.stop()
        ev3.Sound.speak("I have conquered the dark box")
        self.r.stop()
        self.z = 'end'
            
    def run(self):
        """Runs FSM to update based on sensor readings"""
        updateFunc = self.FSM[self.state]
        newState = updateFunc()
        print("start=", self.state)
        if self.oldState != newState:
            self.updateHeading()
        if newState is not None:
            self.state = newState

def runBehavior(behavObj, runTime = None):
    """Takes in a behavior object and an optional time to run. It runs
    a loop that calls the run method of the behavObj over and over until
    either the time runs out or a button is pressed."""
    buttons = ev3.Button()
    startTime = time.time()
    elapsedTime = time.time() - startTime
    ev3.Sound.speak("Starting")
    while (not buttons.any()) and ((runTime is None) or (elapsedTime < runTime)):
        behavObj.run()
        # Could add time.sleep here if need to slow loop down
        elapsedTime = time.time() - startTime
    # self.r.zeroPointer()
    # self.r.mmot.wait_until_not_moving()
    ev3.Sound.speak("Done")


if __name__ == '__main__':

    agent_host = MalmoPython.AgentHost()
    world_state = agent_host.getWorldState()

    print(world_state.observations)

    # escapeBoxRoby = excavationBehavior(agent_host)
   
    print("Run Behavior")
    runBehavior(escapeBoxRoby)
    print("behavior ran")
