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


import MalmoPython
import os
import sys
import time
from tree_learner_agent import tabularQlearner
import random

# ------------------------------ Methods for world builder ------------------------------ #

def checkLapis(x, z):
    if x == 2003 and z == 4:
        while x == 2003 and z == 4:
            x = int(round(1999 + 21 * (random.random())))
            z = int(round(-9 + 28 * (random.random())))
        return x, z
    else:
        my_mission.drawCuboid(x, 226, z, x, 230, z, "lapis_block")
        # print(x, z)
        return x, z


def lavaSize(x, z):
    x1 = x
    x2 = int(round(x + 4 * (random.random())))
    z1 = z
    z2 = int(round(z + 4 * (random.random())))
    return x1, x2, z1, z2


def pathcheck(x1, x2, z1, z2, lapisx, lapisz, lavalist):
    checkLava = []
    # print(x1, x2, z1, z2)
    if x1 == x2 and z1 == z2:
        checkLava.append((x1, z1))
    elif x1 == x2:
        for i in range(z1, z2 + 1):
            checkLava.append((x1, i))
    elif z1 == z2:
        for i in range(x1, x2 + 1):
            checkLava.append((i, z1))

    else:
        for i in range(x1, x2 + 1):
            for j in range(z1, z2 + 1):
                checkLava.append((i, j))

    # print(checkLava)
    for i in range(0, len(checkLava)):
        # print(checkLava[i])
        if checkLava[i][0] == 2003 and checkLava[i][1] == 4:
            # print("true")
            return
        elif checkLava[i][0] == lapisx and checkLava[i][1] == lapisz:
            # print("true2")
            return

    for i in range(0, len(checkLava)):
        if (checkLava[i][0], checkLava[i][1]) in lavalist:
            return
        elif ((checkLava[i][0] + 1), checkLava[i][0]) in lavalist:
            return
        elif (checkLava[i][0], (checkLava[i][1] + 1)) in lavalist:
            return
        elif ((checkLava[i][0] - 1), checkLava[i][0]) in lavalist:
            return
        elif (checkLava[i][0], (checkLava[i][1] - 1)) in lavalist:
            return
        elif (checkLava[i][0] + 1, (checkLava[i][1] + 1)) in lavalist:
            return
        elif (checkLava[i][0] + 1, (checkLava[i][1] - 1)) in lavalist:
            return
        elif (checkLava[i][0] - 1, (checkLava[i][1] + 1)) in lavalist:
            return
        elif (checkLava[i][0] - 1, (checkLava[i][1] - 1)) in lavalist:
            return
    for i in range(0, len(checkLava)):
        lavaCoords.append(checkLava[i])
    my_mission.drawCuboid(x1, 226, z1, x2, 226, z2, "lava")


# ------------------------------ Methods for world builder ------------------------------ #


sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately
actions_obj = ['movenorth 1', 'movesouth 1', 'moveeast 1', 'movewest 1']
actions_subj = ['move 1', 'move -1', 'strafe 1', 'strafe -1']

modes = {'Training': True, 'training': True, 'testing': False, 'Testing': False}

valid_answer = False

while not valid_answer:
    answer1 = raw_input("training or testing: ")
    if str(answer1) in modes:
        valid_answer = True
    else:
        print("Incorrect Input")

mode = modes[answer1]

if not mode:
    modelFile = raw_input("Enter model json file as <file>.json")
else:
    answer2 = input("Do you have a model (True or False):")
    if answer2:
        modelFile = raw_input("Enter model json file as <file>.json")
    else:
        modelFile = None

agent = tabularQlearner(actions=actions_subj, model=modelFile)
agent_host = MalmoPython.AgentHost()

try:
    agent_host.parse(sys.argv)
except RuntimeError as e:
    print 'ERROR:', e
    print agent_host.getUsage()
    exit(1)
if agent_host.receivedArgument("help"):
    print agent_host.getUsage()
    exit(0)

# -- set up the mission -- #

mission_file = './tree_finder_world1.xml'

with open(mission_file, 'r') as f:
    print "Loading mission from %s" % mission_file
    mission_xml = f.read()
    my_mission = MalmoPython.MissionSpec(mission_xml, True)

agent_host.setObservationsPolicy(MalmoPython.ObservationsPolicy.LATEST_OBSERVATION_ONLY)
agent_host.setVideoPolicy(MalmoPython.VideoPolicy.LATEST_FRAME_ONLY)

global lavaCoords
lavaCoords = []
# lapis_x = int(round(1999 + 21 * (random.random())))
# lapis_z = int(round(-9 + 28 * (random.random())))
lapis_x = int(round(2005 + 5 * (random.random())))
lapis_z = int(round(-4 + 5 * (random.random())))


lapis_x, lapis_z = checkLapis(lapis_x, lapis_z)

for x in range(1999, 2020):
    for z in range(-9, 19):
        if random.random() < 0.5:
            x1, x2, z1, z2 = lavaSize(x, z)
            pathcheck(x1, x2, z1, z2, lapis_x, lapis_z, lavaCoords)

max_retries = 3

if mode:
    num_repeats = 50
else:
    num_repeats = 10

cumulative_rewards = []
for i in range(num_repeats):
    if not mode and num_repeats == 7:
        agent.setTraining(False)
    if i%25 == 24:
        agent.saveModel()
    print
    print 'Repeat %d of %d' % (i + 1, num_repeats)

    my_mission_record = MalmoPython.MissionRecordSpec()
    for retry in range(max_retries):
        try:
            agent_host.startMission(my_mission, my_mission_record)
            break
        except RuntimeError as e:
            if retry == max_retries - 1:
                print "Error starting mission:", e
                exit(1)
            else:
                time.sleep(2.5)

    print "Waiting for the mission to start",
    world_state = agent_host.getWorldState()
    while not world_state.has_mission_begun:
        sys.stdout.write(".")
        time.sleep(0.1)
        world_state = agent_host.getWorldState()
        for error in world_state.errors:
            print "Error:", error.text
    print

    # -- run the agent in the world -- #
    cumulative_reward, q_table = agent.run(agent_host)
    print 'Cumulative reward: %d' % cumulative_reward
    print 'Q_table %s' % q_table
    cumulative_rewards += [cumulative_reward]

    # -- clean up -- #
    time.sleep(0.5)  # (let the Mod reset)

if agent.training:
    agent.saveModel()

print
print "Cumulative rewards for all %d runs:" % num_repeats
print cumulative_rewards

print("OUTPUT GRAPH")
agent.drawGraph(cumulative_rewards)

print "Done."




