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

FPS = 60
KAYAK_SHAPE = np.array([[  0.        ,   6.        ],
                        [ 19.93968637,  11.62191781],
                        [ 23.37756333,  12.        ],
                        [ 31.45958987,  11.55616438],
                        [ 44.53558504,   8.59726027],
                        [ 50.        ,   6.        ],
                        [ 50.        ,   6.        ],
                        [ 44.53558504,   3.40273973],
                        [ 31.45958987,   0.44383562],
                        [ 23.37756333,   0.        ],
                        [ 19.93968637,   0.37808219],
                        [  0.        ,   6.        ]])

MAX_FORWARD_SPEED = 25
MAX_BACKWARD_SPEED = 15
MAX_ROTATION_SPEED = 55 * np.pi / 180
KAYAK_DRAG_TENSOR = np.array([[0.2,   0],
                              [  0, 0.4]], float)

class Kayak:
    def __init__(self, initial_pose, initial_velocity, color, helmet_color, drag_tensor):
        self.current_pose = np.array(initial_pose, float)
        self.last_pose = self.current_pose
        self.current_velocity = np.array(initial_velocity, float)
        self.drag_tensor = np.array(drag_tensor, float)
        self.current_angular_velocity = 0
        self.current_forward_velocity = 0

        self.surface = pygame.Surface(np.max(KAYAK_SHAPE, axis=0))
        self.surface.fill(BLUE)
        pygame.draw.polygon(self.surface, color, KAYAK_SHAPE, 0)
        pygame.draw.circle(self.surface, helmet_color, np.array(np.max(KAYAK_SHAPE, axis=0), int) // 2 + np.array([2, 0]), 5, 0)

    def setVelocity(self, velocity):
        self.current_forward_velocity = velocity

    def setAngularVelocity(self, velocity):
        self.current_angular_velocity = velocity

    def updateVelocity(self, flow):
        self.current_velocity = np.zeros_like(self.current_velocity)
        rot_matrix = np.array([[cos(self.current_pose[2]), -sin(self.current_pose[2])],
                            [sin(self.current_pose[2]), cos(self.current_pose[2])]], float)
        rotated_drag_tensor = rot_matrix.T.dot(self.drag_tensor.dot(rot_matrix))

        self.current_velocity[:2] += flow * np.diag(rotated_drag_tensor)
        self.current_velocity[:2] += self.current_forward_velocity * np.array([cos(self.current_pose[2]), -sin(self.current_pose[2])])
        self.current_velocity[2] += self.current_angular_velocity

    def updatePose(self, dt):
        self.last_pose = self.current_pose.copy()
        self.current_pose += self.current_velocity * dt

    def draw(self, surf):
        rot_surf = pygame.transform.rotate(self.surface, self.current_pose[2] * 180 / np.pi)
        surfsize = np.array(rot_surf.get_size(), int)
        surf.blit(rot_surf, tuple(self.current_pose[:2] - surfsize / 2))

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
        positions = [pos_upstream, pos_downstream]

        if not self.isDownstream:
            positions = positions[::-1]

        if positions[0] < self.position[0] < self.position[1]:
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
          Gate([650, 250], GATE_WIDTH, False),
          Gate([750, 170], GATE_WIDTH, True)]

current_flow = np.array([70, 0], float)

fpsClock = pygame.time.Clock()
start_time = time.time()
penalty_time = 0

def terminate():
    pygame.quit()
    sys.exit()

kayak = Kayak([0,200,0], [0,0,0], YELLOW, WHITE, KAYAK_DRAG_TENSOR)
current_gate = 0
isFinished = False

keymappings = {
    K_UP : [(kayak.setVelocity, MAX_FORWARD_SPEED), (kayak.setVelocity, 0)],
    K_DOWN : [(kayak.setVelocity, -MAX_BACKWARD_SPEED), (kayak.setVelocity, 0)],
    K_LEFT : [(kayak.setAngularVelocity, MAX_ROTATION_SPEED), (kayak.setAngularVelocity, 0)],
    K_RIGHT : [(kayak.setAngularVelocity, -MAX_ROTATION_SPEED), (kayak.setAngularVelocity, 0)],
    K_ESCAPE : [(terminate,), (None,)],
}

pygame.font.init()
myfont = pygame.font.SysFont('Ubuntu', 24)

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
    kayak.updateVelocity(current_flow)
    kayak.updatePose(1.0/FPS)

    # check if finished
    if kayak.current_pose[0] > WIDTH:
        isFinished = True
        end_time = time.time()
        if current_gate != len(COURSE):
            penalty_time += 10

    # collision detection
    for gate in COURSE:
        pass

    for ind, gate in enumerate(COURSE):
        # check if a gate was passed in flow direction
        if gate.checkPassed(kayak.last_pose, kayak.current_pose):
            if ind != current_gate:
                penalty_time += 50
            current_gate = ind + 1

    # Draw
    DISPLAYSURF.fill(BLUE)
    kayak.draw(DISPLAYSURF)

    half_gate_width = np.array([0, GATE_WIDTH//2])
    for gate in COURSE:
        gate.draw(DISPLAYSURF)

    textsurface = myfont.render('{0:.2f}'.format(time.time() - start_time + penalty_time),
                                False, WHITE)
    DISPLAYSURF.blit(textsurface, ((WIDTH - textsurface.get_size()[0])/2, 50))
    pygame.display.update()
    fpsClock.tick(FPS)

namebuffer = ''
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            terminate()
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                terminate()
            elif event.key == K_RETURN:
                terminate()
            elif event.key == K_BACKSPACE:
                namebuffer = namebuffer[:-1]
            elif ord('a') <= event.key <= ord('z'):
                namebuffer += chr(event.key)

    DISPLAYSURF.fill(BLACK)
    pygame.draw.rect(DISPLAYSURF, BLUE, (100, 0, WIDTH - 200, HEIGHT))

    textsurface = myfont.render('Gesamtzeit: {0:.2f}'.format(end_time - start_time + penalty_time),
                                False, WHITE)
    DISPLAYSURF.blit(textsurface, ((WIDTH - textsurface.get_size()[0])/2, 100))

    textsurface = myfont.render('Bitte Name eingeben:', False, WHITE)
    DISPLAYSURF.blit(textsurface, ((WIDTH - textsurface.get_size()[0])/2, 150))

    textsurface = myfont.render(namebuffer, False, WHITE)
    DISPLAYSURF.blit(textsurface, ((WIDTH - textsurface.get_size()[0])/2, 170))

    pygame.display.update()
    fpsClock.tick(FPS)

