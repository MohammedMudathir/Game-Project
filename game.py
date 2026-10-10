#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Snowman Dodge - branches fall down the tree, move the snowman
left/right to dodge them.

Controls:
    LEFT / A    move to the left side of the tree
    RIGHT / D   move to the right side of the tree
    SPACE       start / restart
    ESC         quit
"""
import os
import random
import pygame

# window
width = 1400
height = 700
FPS = 60

# tree
TreeWidth = 60
TreeStartWidth = (width - TreeWidth) // 2
branchWidth = TreeWidth * 3
branchHeight = height // 40
branchGap = 220            # vertical distance between falling branches

# snowman
snowmanDist = 40           # distance from tree
snowmanY = 7 * height // 8 # y of the snowman's middle ball
rad = 18                   # radius of the middle ball

# speed (pixels per frame)
startSpeed = 4.0
speedStep = 0.25           # added every time a branch is dodged
maxSpeed = 16.0

# colours
bgColor = pygame.Color(200, 230, 255)
groundColor = pygame.Color("white")
trunkColor = pygame.Color(110, 70, 40)
fgColor = pygame.Color(30, 130, 60)
snowColor = pygame.Color("white")
outlineColor = pygame.Color(60, 60, 80)
noseColor = pygame.Color("orange")
textColor = pygame.Color(30, 30, 50)

highScoreFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscore.txt")


def loadHighScore():
    try:
        with open(highScoreFile) as f:
            return int(f.read().strip() or 0)
    except (OSError, ValueError):
        return 0


def saveHighScore(score):
    try:
        with open(highScoreFile, "w") as f:
            f.write(str(score))
    except OSError:
        pass


class Branch:

    def __init__(self, y, pos):
        self.y = y      # height from top
        self.pos = pos  # "left" or "right"
        self.passed = False

    def rect(self):
        if self.pos == "left":
            x = TreeStartWidth - branchWidth
        else:
            x = TreeStartWidth + TreeWidth
        return pygame.Rect(x, int(self.y), branchWidth, branchHeight)

    def show(self, screen):
        pygame.draw.rect(screen, fgColor, self.rect(), border_radius=4)

    def update(self, speed):
        self.y += speed


class Snowman:

    # snowman is either left or right - always has same y coordinate
    def __init__(self, pos):
        self.pos = pos

    def centreX(self):
        if self.pos == "left":
            return TreeStartWidth - snowmanDist - rad
        return TreeStartWidth + TreeWidth + snowmanDist + rad

    def rect(self):
        # hit box covering the head and middle ball
        x = self.centreX()
        top = snowmanY - rad - int(rad * 1.4)
        return pygame.Rect(x - rad, top, rad * 2, snowmanY + rad - top)

    def show(self, screen):
        x = self.centreX()
        balls = [
            (snowmanY + int(rad * 1.6), int(rad * 1.3)),  # bottom
            (snowmanY, rad),                               # middle
            (snowmanY - int(rad * 1.6), int(rad * 0.75)),  # head
        ]
        for y, r in balls:
            pygame.draw.circle(screen, snowColor, (x, y), r)
            pygame.draw.circle(screen, outlineColor, (x, y), r, 2)

        headY = balls[2][0]
        eyeOff = rad // 4
        pygame.draw.circle(screen, outlineColor, (x - eyeOff, headY - 3), 2)
        pygame.draw.circle(screen, outlineColor, (x + eyeOff, headY - 3), 2)
        # carrot nose points away from the tree
        nose = 10 if self.pos == "right" else -10
        pygame.draw.polygon(screen, noseColor,
                            [(x, headY), (x, headY + 4), (x + nose, headY + 2)])


class Game:

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Snowman Dodge")
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.bigFont = pygame.font.SysFont(None, 72)
        self.font = pygame.font.SysFont(None, 36)
        self.highScore = loadHighScore()
        self.state = "start"  # "start", "playing" or "over"
        self.reset()

    def reset(self):
        self.snowman = Snowman("right")
        self.speed = startSpeed
        self.score = 0
        # stack branches above the screen so they fall in one after another
        self.branches = [Branch(-i * branchGap, random.choice(["left", "right"]))
                         for i in range(height // branchGap + 2)]

    def handleKey(self, key):
        if key == pygame.K_ESCAPE:
            return False
        if self.state == "playing":
            if key in (pygame.K_LEFT, pygame.K_a):
                self.snowman.pos = "left"
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.snowman.pos = "right"
        elif key == pygame.K_SPACE:
            self.reset()
            self.state = "playing"
        return True

    def update(self):
        if self.state != "playing":
            return

        hitBox = self.snowman.rect()
        topY = min(b.y for b in self.branches)
        for branch in self.branches:
            branch.update(self.speed)

            if branch.pos == self.snowman.pos and branch.rect().colliderect(hitBox):
                self.gameOver()
                return

            if not branch.passed and branch.y > hitBox.bottom:
                branch.passed = True
                self.score += 1
                self.speed = min(maxSpeed, self.speed + speedStep)

            # recycle branches that left the screen back to the top
            if branch.y > height:
                branch.y = topY - branchGap
                branch.pos = random.choice(["left", "right"])
                branch.passed = False
                topY = branch.y

    def gameOver(self):
        self.state = "over"
        if self.score > self.highScore:
            self.highScore = self.score
            saveHighScore(self.highScore)

    def drawText(self, text, font, y):
        surface = font.render(text, True, textColor)
        self.screen.blit(surface, surface.get_rect(center=(width // 2, y)))

    def draw(self):
        self.screen.fill(bgColor)
        groundY = snowmanY + int(rad * 2.9)
        pygame.draw.rect(self.screen, trunkColor, pygame.Rect(TreeStartWidth, 0, TreeWidth, groundY))
        for branch in self.branches:
            branch.show(self.screen)
        # ground drawn after branches so they disappear into the snow
        pygame.draw.rect(self.screen, groundColor, pygame.Rect(0, groundY, width, height - groundY))
        self.snowman.show(self.screen)

        hud = self.font.render(f"Score: {self.score}   Best: {self.highScore}", True, textColor)
        self.screen.blit(hud, (20, 20))

        if self.state != "playing":
            panel = pygame.Surface((560, 200), pygame.SRCALPHA)
            panel.fill((255, 255, 255, 220))
            self.screen.blit(panel, panel.get_rect(center=(width // 2, height // 3 + 45)))

        if self.state == "start":
            self.drawText("Snowman Dodge", self.bigFont, height // 3)
            self.drawText("LEFT / RIGHT to dodge the branches", self.font, height // 3 + 60)
            self.drawText("Press SPACE to start", self.font, height // 3 + 100)
        elif self.state == "over":
            self.drawText("Game Over!", self.bigFont, height // 3)
            self.drawText(f"You dodged {self.score} branches", self.font, height // 3 + 60)
            self.drawText("Press SPACE to play again", self.font, height // 3 + 100)

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN:
                    running = self.handleKey(e.key) and running

            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    Game().run()
