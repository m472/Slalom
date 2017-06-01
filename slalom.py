#!/usr/bin/python3

import pygame, sys, time
import numpy as np
from pygame.locals import *
from math import sin, cos

pygame.init()

WIDTH, HEIGHT = 900, 400

DISPLAYSURF = pygame.display.set_mode((WIDTH, HEIGHT), 0, 32)
pygame.display.set_caption('Slalom')

BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)

KAYAK_SIZE = (50, 12)
FPS = 60

MAX_FORWARD_SPEED = 25
MAX_BACKWARD_SPEED = 15
MAX_ROTATION_SPEED = 55 * np.pi / 180
KAYAK_DRAG_TENSOR = np.array([[0.2,   0],
                              [  0, 0.4]], float)

class Gate:
    def __init__(self, position, width, isDownstream):
        self.position = np.array(position, float)
        self.width = width
        self.leftPostPos = self.position - np.array([0, width/2])
        self.rightPostPos = self.position + np.array([0, width/2])
        self.isDownstream = isDownstream

    def checkPassed(self, prevPose, currPose):
        pos_downstream = min(prevPose[0], currPose[1])
        pos_upstream = max(prevPose[0], currPose[1])
        if prevPose[0] <= self.position[0] < currPose[0]:
            vertical_pos = (prevPose + currPose)[1] / 2
            return self.leftPostPos[1] < vertical_pos < self.rightPostPos[1]
        else:
            return False

    def draw(self, surf):
        color = GREEN if self.isDownstream else RED
        pygame.draw.circle(surf, color,
                          np.array(self.leftPostPos, int), 5, 0)
        pygame.draw.circle(surf, color,
                          np.array(self.rightPostPos, int), 5, 0)

GATE_WIDTH = 35
COURSE = [Gate([150, 150], GATE_WIDTH, True),
          Gate([300, 200], GATE_WIDTH, True),
          Gate([450, 150], GATE_WIDTH, True),
          Gate([650, 250], GATE_WIDTH, True),
          Gate([750, 170], GATE_WIDTH, True)]

current_pose = np.array([0, 200, 0], float)
current_flow = np.array([70, 0], float)
current_speed = np.array([0, 0], float)

kayak_surface = pygame.Surface(KAYAK_SIZE)
kayak_surface.fill(BLUE)
pygame.draw.ellipse(kayak_surface, YELLOW, (0, 0) + KAYAK_SIZE, 0)
pygame.draw.circle(kayak_surface, WHITE,
                   np.array(KAYAK_SIZE) // 2 + np.array([2, 0]), 5, 0)


fpsClock = pygame.time.Clock()
start_time = time.time()
penalty_time = 0

def setVelocity(vel):
    current_speed[0] = vel

def setRotationSpeed(rot_vel):
    current_speed[1] = rot_vel

def terminate():
    pygame.quit()
    sys.exit()

keymappings = {
    K_UP : [(setVelocity, MAX_FORWARD_SPEED), (setVelocity, 0)],
    K_DOWN : [(setVelocity, MAX_BACKWARD_SPEED), (setVelocity, 0)],
    K_LEFT : [(setRotationSpeed, MAX_ROTATION_SPEED), (setRotationSpeed, 0)],
    K_RIGHT : [(setRotationSpeed, -MAX_ROTATION_SPEED), (setRotationSpeed, 0)],
    K_ESCAPE : [(terminate,), (None,)],
}

current_gate = 0
isFinished = False

pygame.font.init()
myfont = pygame.font.SysFont('Ubuntu', 18)

while not isFinished:
    for event in pygame.event.get():
        if event.type == QUIT:
            terminate()
        if event.type == KEYDOWN:
            try:
                func, *args = keymappings[event.key][0]
                func(*args)
            except:
                pass
        if event.type == KEYUP:
            try:
                func, *args = keymappings[event.key][1]
                func(*args)
            except:
                pass

    # Update game data
    last_pose = current_pose.copy()
    rot_matrix = np.array([[cos(current_pose[2]), -sin(current_pose[2])],
                           [sin(current_pose[2]), cos(current_pose[2])]], float)
    rotated_flow_tensor = rot_matrix.T.dot(KAYAK_DRAG_TENSOR.dot(rot_matrix))
    current_pose[0] += (current_flow[0] * rotated_flow_tensor[0, 0] \
                     + current_speed[0] * np.cos(current_pose[2])) * 1.0/FPS
    current_pose[1] += (current_flow[1] * rotated_flow_tensor[1, 1] \
                     - current_speed[0] * np.sin(current_pose[2])) * 1.0/FPS
    current_pose[2] += current_speed[1] * 1.0/FPS

    # check if finished
    if current_pose[0] > WIDTH:
        isFinished = True

    # collision detection
    for gate in COURSE:
        pass

    for ind, gate in enumerate(COURSE):
        # check if a gate was passed in flow direction
        if gate.checkPassed(last_pose, current_pose):
            if ind != current_gate:
                penalty_time += 10
            current_gate = ind + 1

    # Draw
    surface2 = pygame.transform.rotate(kayak_surface,
                                       current_pose[2] * 180 / np.pi)
    surfsize = np.array(surface2.get_size(), int)

    DISPLAYSURF.fill(BLUE)
    DISPLAYSURF.blit(surface2, tuple(current_pose[:2] - surfsize / 2))

    half_gate_width = np.array([0, GATE_WIDTH//2])
    for gate in COURSE:
        gate.draw(DISPLAYSURF)

    textsurface = myfont.render('{0:.2f}'.format(time.time() - start_time + penalty_time),
                                False, WHITE)
    DISPLAYSURF.blit(textsurface, ((WIDTH - textsurface.get_size()[0])/2, 50))

    pygame.display.update()

    fpsClock.tick(FPS)

while True:
    DISPLAYSURF.fill(BLACK)
    pygame.draw.rect(DISPLAYSURF, BLUE, (100, 0, WIDTH - 200, HEIGHT))
    pygame.display.update()
    fpsClock.tick(FPS)


