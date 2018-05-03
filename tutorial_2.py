from __future__ import print_function
# ------------------------------------------------------------------------------------------------
# Copyright (c) 2016 Microsoft Corporation
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
# NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ------------------------------------------------------------------------------------------------

# Tutorial sample #2: Run simple mission using raw XML

from builtins import range
import MalmoPython
import os
import sys
import time
import random

if sys.version_info[0] == 2:
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately
else:
    import functools
    print = functools.partial(print, flush=True)

# More interesting generator string: "3;7,44*49,73,35:1,159:4,95:13,35:13,159:11,95:10,159:14,159:6,35:6,95:6;12;"

missionXML='''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

  <About>
    <Summary>Tree Finder</Summary>
  </About>

  <ServerSection>
    <ServerInitialConditions>
        <Time><StartTime>1</StartTime></Time>
    </ServerInitialConditions>
    <ServerHandlers>
      <FlatWorldGenerator generatorString="3;7,220*1,5*3,2;3;,biome_1"/>
      <DrawingDecorator>
        <!-- coordinates for cuboid are inclusive -->
        <DrawCuboid x1 = "1998" y1 = "226" z1 = "-10" x2 = "2020" y2 = "300" z2 = "20" type = "air"/>

        <DrawCuboid x1="-2" y1="3045" z1="-2" x2="20" y2="300" z2="20" type="stone" />
        <DrawCuboid x1 = "1998" y1 = "226" z1 = "-10" x2 = "2020" y2 = "226" z2 = "20" type = "dirt"/>
        <DrawCuboid x1 = "1997" y1 = "226" z1 = "-11" x2 = "1998" y2 = "226" z2 = "21" type = "lava"/>
        <DrawCuboid x1 = "2021" y1 = "226" z1 = "-11" x2 = "2022" y2 = "226" z2 = "21" type = "lava"/>
        <DrawCuboid x1 = "2021" y1 = "226" z1 = "20" x2 = "2022" y2 = "226" z2 = "21" type = "lava"/>
        <DrawCuboid x1 = "1997" y1 = "226" z1 = "-10" x2 = "2020" y2 = "226" z2 = "-11" type = "lava"/>
        <DrawCuboid x1 = "1998" y1 = "226" z1 = "21" x2 = "2020" y2 = "226" z2 = "20" type = "lava"/>

      </DrawingDecorator>
      <ServerQuitFromTimeUp timeLimitMs="20000"/>
      <ServerQuitWhenAnyAgentFinishes/>
    </ServerHandlers>
  </ServerSection>

  <AgentSection mode="Survival">
    <Name>Roby</Name>
    <AgentStart>
      <Placement x="2003" y="227.0" z="4" pitch="60" yaw="0"/>
    </AgentStart>
    <AgentHandlers>
      <DiscreteMovementCommands/>
      <ObservationFromFullStats/>
      <ObservationFromGrid>
        <Grid name="floor3x3">
            <min x="-1" y="-1" z="-1"/>
            <max x="1" y="1" z="1"/>
        </Grid>
      </ObservationFromGrid>
      <RewardForTouchingBlockType>
        <Block reward="-100.0" type="lava" behaviour="onceOnly"/>
        <Block reward="100.0" type="log" behaviour="onceOnly"/>
      </RewardForTouchingBlockType>
      <RewardForSendingCommand reward="-1" />
        <RewardForCollectingItem>
            <Item reward="200" type="log"/>
            <Item reward="-200" type="stone"/>
            <Item reward="-200" type="sandstone"/>
        </RewardForCollectingItem>
      <AgentQuitFromTouchingBlockType>
          <Block type="lava" />
      </AgentQuitFromTouchingBlockType>
    </AgentHandlers>
  </AgentSection>
</Mission>

'''

# Create default Malmo objects:

agent_host = MalmoPython.AgentHost()
try:
    agent_host.parse( sys.argv )
except RuntimeError as e:
    print('ERROR:',e)
    print(agent_host.getUsage())
    exit(1)
if agent_host.receivedArgument("help"):
    print(agent_host.getUsage())
    exit(0)

my_mission = MalmoPython.MissionSpec(missionXML, True)
my_mission_record = MalmoPython.MissionRecordSpec()

xcheck = []
zcheck = []
global lavaCoords
lavaCoords = []
lapis_x = int(round(1999 + 21*(random.random())))
lapis_z = int(round(-9 + 28*(random.random())))
def checkLapis(x, z):
  if x == 2003 and z == 4: 
    checkLapis(int(round(1999 + 21*(random.random()))), int(round(-9 + 28*(random.random()))))
  else: 
    my_mission.drawCuboid( x,226,z,x,230,z,"lapis_block")
    return x, z

def lavaSize(x, z):
  x1 = x
  x2 = int(round(x + 4*(random.random())))
  z1 = z
  z2 = int(round(z + 4*(random.random())))
  return x1, x2, z1, z2

def pathcheck(x1, x2, z1, z2, lapisx, lapisz, lavalist):
  checkLava = []
  print(x1, x2, z1, z2)
  if x1 == x2 and z1==z2:
    checkLava.append((x1, z1))
  elif x1 == x2:
    for i in range(z1, z2+1):
      checkLava.append((x1, i))
  elif z1 ==z2: 
    for i in range(x1, x2+1):
      checkLava.append((i, z1))

  else:
    for i in range(x1, x2+1):
      for j in range(z1, z2+1): 
        checkLava.append((i,j))

  print(checkLava)
  for i in range(0, len(checkLava)):
    print(checkLava[i])
    if checkLava[i][0] == 2003 and checkLava[i][1]==4:
      print("true")
      return
    elif checkLava[i][0] == lapisx and checkLava[i][1]==lapisz:
      print("true2")
      return

  for i in range(0, len(checkLava)):
    if (checkLava[i][0], checkLava[i][1]) in lavalist:
      print("hi")
      return 0
    elif ((checkLava[i][0] + 1), checkLava[i][0]) in lavalist:
      print("hi")
      return 0
    elif (checkLava[i][0], (checkLava[i][1]+1)) in lavalist:
      print("hi")
      return 0
    elif ((checkLava[i][0]-1), checkLava[i][0]) in lavalist:
      print("hi")
      return 0
    elif (checkLava[i][0], (checkLava[i][1]-1)) in lavalist:
      print("hi")
      return 0
    elif (checkLava[i][0]+1, (checkLava[i][1]+1)) in lavalist:
      print("hi")
      return 0
    elif (checkLava[i][0]+1, (checkLava[i][1]-1)) in lavalist:
      print("hi")
      return 0
    elif (checkLava[i][0]-1, (checkLava[i][1]+1)) in lavalist:
      print("hi")
      return 0
    elif (checkLava[i][0]-1, (checkLava[i][1]-1)) in lavalist:
      print("hi")
      return 0
  print("still running")
  for i in range(0, len(checkLava)):
    lavaCoords.append(checkLava[i])
  my_mission.drawCuboid(x1, 226, z1, x2, 226, z2, "lava")

lapis_x, lapis_z = checkLapis(lapis_x, lapis_z)

for x in range(1999, 2020):
    for z in range(-9,19):
        if random.random()<0.5:
          x1, x2, z1, z2 = lavaSize(x,z)
          pathcheck(x1, x2, z1, z2, lapis_x, lapis_z, lavaCoords)
          print(lavaCoords)



agent_host.sendCommand("turn -0.5")
agent_host.sendCommand("move 1")
agent_host.sendCommand("jump 1")
# Attempt to start a mission:
max_retries = 3
for retry in range(max_retries):
    try:
        agent_host.startMission( my_mission, my_mission_record )
        break
    except RuntimeError as e:
        if retry == max_retries - 1:
            print("Error starting mission:",e)
            exit(1)
        else:
            time.sleep(2)

# Loop until mission starts:
print("Waiting for the mission to start ", end=' ')
world_state = agent_host.getWorldState()
while not world_state.has_mission_begun:
    print(".", end="")
    time.sleep(0.1)
    world_state = agent_host.getWorldState()
    for error in world_state.errors:
        print("Error:",error.text)

print()
print("Mission running ", end=' ')

# Loop until mission ends:
agent_host.sendCommand("move 1")
while world_state.is_mission_running:
    print(".", end="")
    time.sleep(0.1)
    world_state = agent_host.getWorldState()
    for error in world_state.errors:
        print("Error:",error.text)

print()
print("Mission ended")
# Mission has ended.
