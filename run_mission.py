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
import json

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately
actions = ['movenorth 1', 'movesouth 1', 'moveeast 1', 'movewest 1']
agent = tabularQlearner(actions=actions)
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
# mission_file = './tree_finder_world1.xml'
mission_file = './tree_finder_world1.xml'
with open(mission_file, 'r') as f:
    print "Loading mission from %s" % mission_file
    mission_xml = f.read()
    my_mission = MalmoPython.MissionSpec(mission_xml, True)

agent_host.setObservationsPolicy(MalmoPython.ObservationsPolicy.LATEST_OBSERVATION_ONLY)
agent_host.setVideoPolicy(MalmoPython.VideoPolicy.LATEST_FRAME_ONLY)

global lavaCoords
lavaCoords = []
lapis_x = int(round(1999 + 21 * (random.random())))
lapis_z = int(round(-9 + 28 * (random.random())))


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


lapis_x, lapis_z = checkLapis(lapis_x, lapis_z)

for x in range(1999, 2020):
    for z in range(-9, 19):
        if random.random() < 0.5:
            x1, x2, z1, z2 = lavaSize(x, z)
            pathcheck(x1, x2, z1, z2, lapis_x, lapis_z, lavaCoords)

def testTree():
    obs_text = world_state.observations[-1].text
    obs = json.loads(obs_text)  # most recent observation
    # self.logger.debug(obs)

    if u'floor3x3' not in obs or u'Yaw' not in obs:
        print("Incomplete observation received %s" % obs_text)
        # self.logger.error("Incomplete observation received %s" % obs_text)

    yaw = int(obs[u'Yaw'])
    treePos = str(agent.findTreePos(agent_host, world_state, yaw)[0])

    print("Tree Pos: %s; " % treePos)

max_retries = 3

# if agent_host.receivedArgument("test"):
#     num_repeats = 1
#
# else:
num_repeats = 10

cumulative_rewards = []
for i in range(num_repeats):

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

    # Testing Tree Finder
    # counter = 0
    # while world_state.is_mission_running and counter < 10:
    #     if len(world_state.observations) > 0 and not \
    #             world_state.observations[-1].text == "{}":
    #         counter += 1
    #         print(counter)
    #         time.sleep(0.1)
    #         testTree()
    #     break


    # print("OUTPUT GRAPH")
    # agent.drawGraph(cumulative_rewards)

    # -- clean up -- #
    time.sleep(0.5)  # (let the Mod reset)

agent.saveModel()

print "Done."

print
print "Cumulative rewards for all %d runs:" % num_repeats
print cumulative_rewards


