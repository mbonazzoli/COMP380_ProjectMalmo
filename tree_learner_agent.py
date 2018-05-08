"""Code written by Matt Bonazzoli, Ben Lewis, Brett Graham for COMP380 final project 2018.
    Tabular Q learning agent that supplies the Q table and reinforcement structure for finding a tree.
    Structure and Reference aided by the Project Malmo tutorial_6.py file"""
import MalmoPython
import json
import logging
import Tkinter as tk
import random
import sys
import time
import matplotlib.pyplot as plt
import numpy as np

class tabularQlearner:
    def __init__(self, training=True, actions=[], epsilon=0.1, alpha=0.1, gamma=1.0, model=None):
        self.epsilon = epsilon  # chance of taking a random action instead of the best

        self.logger = logging.getLogger(__name__)
        if False:  # True if you want to see more information
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        self.logger.handlers = []
        self.logger.addHandler(logging.StreamHandler(sys.stdout))

        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma

        self.canvas = None
        self.root = None

        self.x = None
        self.y = None
        self.z = None

        self.numActions = 0
        self.newPos = 180

        self.forward_reward = False
        self.f_reward_val = 2

        # self.training

        if training:
            if(model == None):
                self.q_table = {}
            else:
                self.q_table = self.loadModel(model)
            self.training = training
        else:
            self.training = training
            self.q_table = self.loadModel(model)

        # if(model == None):
        #     self.q_table = {}
        # else:
        #     self.training = training
        #     self.q_table = self.loadModel(model)

    def updateQTable(self, reward, current_state):
        """Change q_table to reflect what we have learnt."""

        # retrieve the old action value from the Q-table (indexed by the previous state and the previous action)
        old_q = self.q_table[self.prev_s][self.prev_a]

        new_q = old_q + self.alpha * (reward + self.gamma * max(self.q_table[current_state]) - old_q)

        # assign the new action value to the Q-table
        self.q_table[self.prev_s][self.prev_a] = new_q

    def updateQTableFromTerminatingState(self, reward):
        """Change q_table to reflect what we have learnt, after reaching a terminal state."""

        # retrieve the old action value from the Q-table (indexed by the previous state and the previous action)
        old_q = self.q_table[self.prev_s][self.prev_a]

        new_q = old_q + self.alpha * (reward - old_q)

        # assign the new action value to the Q-table
        self.q_table[self.prev_s][self.prev_a] = new_q

    def act(self, world_state, agent_host, current_r):
        """take 1 action in response to the current world state"""

        if self.forward_reward:
            current_r += self.f_reward_val
        obs_text = world_state.observations[-1].text
        obs = json.loads(obs_text)  # most recent observation
        self.logger.debug(obs)

        if self.numActions % 10 == 0:
            # Locate the position of the tree
            treePos = self.findTreePos(agent_host, world_state)[0]
            print("Tree Position: %d" % treePos)

            self.newPos = self.discreteTreePos(treePos)
            print("New Position: %d" % self.newPos)

            agent_host.sendCommand("setYaw %d" % self.newPos)

        current_s_list = self.createGridObs(obs['floor3x3'])
        current_s_list = current_s_list[:9]
        self.rotateStateSpace(current_s_list, self.newPos)
        # current_s_list.append(treePos)

        current_s = ": ".join(current_s_list)
        print("Current State %s" % current_s)

        if current_s not in self.q_table:
            self.q_table[current_s] = ([0] * len(self.actions))

        # update Q values
        if self.training and self.prev_s is not None and self.prev_a is not None:
            self.updateQTable(current_r, current_s)

        # select the next action
        rnd = random.random()
        if rnd < self.epsilon and self.training:
            a = random.randint(0, len(self.actions) - 1)
            self.logger.info("Random action: %s" % self.actions[a])
        else:
            m = max(self.q_table[current_s])
            self.logger.debug("Current values: %s" % ",".join(str(x) for x in self.q_table[current_s]))
            l = list()
            for x in range(0, len(self.actions)):
                if self.q_table[current_s][x] == m:
                    l.append(x)
            y = random.randint(0, len(l) - 1)
            a = l[y]
            self.logger.info("Taking q action: %s" % self.actions[a])
            if self.actions[a] == "move 1":
                self.forward_reward = True
            else:
                self.forward_reward = False

        # try to send the selected action, only update prev_s if this succeeds
        try:
            agent_host.sendCommand(self.actions[a])
            self.prev_s = current_s
            self.prev_a = a

        except RuntimeError as e:
            self.logger.error("Failed to send command: %s" % e)

        # Adding 360 to offset number off commands sent to turn
        self.numActions += 1
        return current_r

    def run(self, agent_host):
        """run the agent on the world"""

        total_reward = 0

        self.prev_s = None
        self.prev_a = None

        is_first_action = True

        # main loop:
        world_state = agent_host.getWorldState()
        while world_state.is_mission_running:

            current_r = 0

            if is_first_action:
                self.numActions = 0
                # wait until have received a valid observation
                while True:
                    time.sleep(0.1)
                    world_state = agent_host.getWorldState()
                    for error in world_state.errors:
                        self.logger.error("Error: %s" % error.text)
                    for reward in world_state.rewards:
                        current_r += reward.getValue()
                    if world_state.is_mission_running and len(world_state.observations) > 0 and not \
                    world_state.observations[-1].text == "{}":
                        self.x, self.y, self.z = self.getXYZ(world_state)
                        total_reward += self.act(world_state, agent_host, current_r)
                        break
                    if not world_state.is_mission_running:
                        break
                is_first_action = False
            else:
                # wait for non-zero reward
                while world_state.is_mission_running and current_r == 0:

                    time.sleep(0.1)
                    world_state = agent_host.getWorldState()
                    for error in world_state.errors:
                        self.logger.error("Error: %s" % error.text)
                    for reward in world_state.rewards:
                        current_r += reward.getValue()
                # allow time to stabilise after action
                while True:
                    time.sleep(0.01)
                    world_state = agent_host.getWorldState()
                    for error in world_state.errors:
                        self.logger.error("Error: %s" % error.text)
                    for reward in world_state.rewards:
                        current_r += reward.getValue()
                    if world_state.is_mission_running and len(world_state.observations) > 0 and not \
                    world_state.observations[-1].text == "{}":
                        self.x, self.y, self.z = self.getXYZ(world_state)
                        total_reward += self.act(world_state, agent_host, current_r)
                        break
                    if not world_state.is_mission_running:
                        break

        # process final reward
        self.logger.debug("Final reward: %d" % current_r)
        total_reward += current_r

        # update Q values
        if self.training and self.prev_s is not None and self.prev_a is not None:
            self.updateQTableFromTerminatingState(current_r)

        return total_reward, self.q_table

    # def findTreePos(self, agent_host, world_state):
    #     """Turns the agent in a circle to identify the nearest object sticking up in the world (hopefully a tree)"""
    #     video_height = 480
    #     video_width = 640
    #
    #     middle_pixel = (video_width*4*(video_height/2)) + ((video_width/2)*4) + 3
    #     diff_max = 0
    #     diff_max_yaw = 0
    #     obj_dist = 0
    #     prev_depth = 0
    #
    #     print("Locating Tree...")
    #     print
    #
    #     for i in range(-180, 180, 5):
    #         if world_state.is_mission_running:
    #             world_state = agent_host.getWorldState()
    #             # Make sure we get new frame
    #             while world_state.number_of_video_frames_since_last_state == 0 and world_state.is_mission_running:
    #                 time.sleep(0.05)
    #                 world_state = agent_host.getWorldState()
    #                 # print(world_state.number_of_video_frames_since_last_state)
    #
    #             if world_state.is_mission_running:
    #                 # print(world_state)
    #                 # print(len(world_state.video_frames))
    #                 frame = world_state.video_frames[0].pixels
    #                 curr_depth = frame[middle_pixel]
    #                 # print("Current Depth %d" % curr_depth)
    #
    #                 if i == 0:
    #                     prev_depth = curr_depth
    #                 else:
    #                     # if diff negative looking at left side of object
    #                     diff = abs(curr_depth-prev_depth)
    #                     # time.sleep(0.01)
    #                     # print("Current Difference %d" % diff)
    #
    #                     if diff > diff_max:
    #                         diff_max = diff
    #                         obj_dist = curr_depth
    #                         diff_max_yaw = i
    #                 new_yaw = diff_max_yaw
    #                 turnCommand = "setYaw %s" % new_yaw
    #                 agent_host.sendCommand(turnCommand)
    #                 agent_host.sendCommand("tp "+str(self.x)+" "+str(self.y)+" "+str(self.z))
    #                 # time.sleep(0.05)
    #
    #     print("Found Tree!")
    #     return diff_max_yaw, obj_dist

    def findTreePos(self, agent_host, world_state):
        """Turns the agent in a circle to identify the nearest object sticking up in the world (hopefully a tree)"""
        video_height = 240*4
        video_width = 320*4

        middle_pixel = (video_width*4*(video_height/2)) + ((video_width/2)*4) + 3
        minDepth = 255
        treeYaw = 180

        print("Locating Tree...")
        print

        for i in range(-180, 185, 5):
            if world_state.is_mission_running:
                world_state = agent_host.getWorldState()
                # Make sure we get new frame
                while world_state.number_of_video_frames_since_last_state == 0 and world_state.is_mission_running:
                    time.sleep(0.05)
                    world_state = agent_host.getWorldState()
                    # print(world_state.number_of_video_frames_since_last_state)

                if world_state.is_mission_running:
                    # print(world_state)
                    # print(len(world_state.video_frames))
                    frame = world_state.video_frames[0].pixels
                    curr_depth = frame[middle_pixel]
                    # print("Current Depth %d" % curr_depth)

                    if curr_depth < minDepth:
                        treeYaw = i
                        minDepth = curr_depth

                    new_yaw = i
                    turnCommand = "setYaw %s" % new_yaw
                    agent_host.sendCommand(turnCommand)
                    agent_host.sendCommand("tp "+str(self.x)+" "+str(self.y)+" "+str(self.z))
                    # time.sleep(0.05)

        print("Found Tree!")
        return treeYaw, minDepth

    def getXYZ(self, world_state):

        obs_text = world_state.observations[-1].text
        obs = json.loads(obs_text)  # most recent observation

        if u'XPos' not in obs or u'YPos' not in obs or u'ZPos' not in obs:
            print("Incomplete observation received %s" % obs_text)
            self.logger.error("Incomplete observation received %s" % obs_text)
            return None

        x = obs[u'XPos']
        y = obs[u'YPos']
        z = obs[u'ZPos']

        return x, y, z

    def discreteTreePos(self, pos):
        """Takes in a continuous yaw position and returns discrete north, south, west, east
        (180, 0, 90, -90) position to turn to """
        print pos
        if 135 <= pos <= 180 or -135 >= pos >= -180:
            return 180
        elif 0 <= pos <= 45 or 0 >= pos >= -45:
            return 0
        elif 45 < pos < 135:
            return 90
        elif -45 > pos > -135:
            return -90
        else:
            print("POSITION OUT OF ACCEPTABLE RANGE")

    def rotateStateSpace(self, stateSpace, direction):
        """Takes in a state space and a direction (-90,0,90,180) and orients the blocks to match roby's world"""
        newStateSpace = []
        if direction == 90:
            for i in range(6, 9):
                for j in range(0, 3):
                    newStateSpace.append(stateSpace[i - 3*j])
            return newStateSpace
        elif direction == 0:
            for i in range(0, 9):
                newStateSpace.append(stateSpace[8-i])
            return newStateSpace
        elif direction == -90:
            for i in range(0, 3):
                for j in range(0, 3):
                    newStateSpace.append(stateSpace[(2-i)+3*j])
            return newStateSpace
        elif direction == 180:
            return stateSpace
        else:
            print("INVALID DIRECTION")
            return None

    def drawGraph(self, rewards):

        if self.training:
            title = "Training"
        else:
            title = "Testing"

        plt.plot(np.arange(0, len(rewards)), rewards)

        plt.ylabel("Reward Value")
        plt.xlabel("Epoch")
        plt.title(title)

        plt.show()

    def createGridObs(self, grid):
        stringObs = ": ".join(grid[:9])
        listObs = grid[:9]
        return listObs

    def saveModel(self):
        """Writes trained model to a file for evaluation"""
        model = json.dumps(self.q_table)
        f = open("tree_model.json", "w")
        f.write(model)
        f.close()
        print("Wrote model <tree_model.json> to file.")

    def loadModel(self, model_file):
        """Loads previously tested model file for evaluation"""
        with open(model_file) as f:
            return json.load(f)

    def setTraining(self, bool):
        self.training = bool

if __name__ == '__main__':

    # agent_host = MalmoPython.AgentHost()
    # world_state = agent_host.getWorldState()
    #
    # print(world_state.video_frames[0].pixels)
    # print
    # print(world_state.observations)

    agent = tabularQlearner()

    # State Space test for rotating state space to agent view
    stateSpace = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    print(agent.rotateStateSpace(stateSpace, -90))
    print(agent.rotateStateSpace(stateSpace, 90))
    print(agent.rotateStateSpace(stateSpace, 180))
    print(agent.rotateStateSpace(stateSpace, 0))
