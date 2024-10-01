import pygame as pg
import random
import sys
import os
import re
import glob
from pathlib import Path
import math
import pygame.gfxdraw as pggfx
from pygame.locals import *

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from perlin_numpy import generate_fractal_noise_3d

class Grass:
    def __init__(self, app, surface, window):
        self.app = app
        self.surface = surface.convert_alpha(surface)
        self.lightMask = None
        self.cloudMask = None
        self.surface.fill((5, 40, 25, 0))
        # self.surface.fill((255, 255, 255, 0))
        self.image = None
        self.cmidx = 0
        self.cloudRate = 30
        self.path = 'assets/img/'

        self.window = window
        self.position = (0, 0)
        self.elements = ("arc","line", "arc", "line", "arc", "dot", "arc", "line", "arc", "line", "arc",)
        self.render()

    def refresh(self):
        self.app._display_surf.fill((5, 40, 25, 0))
        self.app._display_surf.blit(self.image, (0, 0))


    def render(self, force = True):
        if force == True or not self.loadBackground():
            self.background()
            self.image = self.surface.copy()
            self.mask()
            self.app._display_surf.blit(self.lightMask, (0, 0))
            self.image.blit(self.lightMask, (0, 0))
        if not self.loadClouds():
            self.cloud()
        
    def loadBackground(self):
        p = Path(self.path)
        f = p / 'background.png'

        if f.exists():
            self.image = pg.Surface.convert_alpha(pg.image.load(f))
            return True

        return False
    
    def loadClouds(self):
        p = Path(self.path)
        f = p / 'cloudMask_*.png'

        clouds = glob.glob(self.path + 'cloudMask_*.png')

        if len(clouds):
            self.cloudMask = []
            for cloud in clouds:
                cloudImg = pg.Surface.convert_alpha(pg.image.load(cloud))
                cloudImg.set_alpha(64)
                self.cloudMask.append(cloudImg)

            return True
        return False

        
    def animate(self):
        if not self.app.tick % int(self.cloudRate / 2):
            for mask in self.cloudMask:
                # maskRect = mask.get_rect()
                # rightEdge = maskRect.clip(maskRect.width - 2, 0, 2, maskRect.height)
                # bottomEdge = maskRect.clip(0, maskRect.height - 3, maskRect.width - 2, 3)
                # main = maskRect.clip(0, 0, maskRect.width - 2, maskRect.height - 3)
                # mask.fill((255, 255, 255, int(255 * 0)))
                # mask.blit(mask, main)
                mask.scroll(2, 3)
        
        if not self.app.tick % self.cloudRate:
            self.cmidx += 1
            self.cmidx = self.cmidx % len(self.cloudMask)
            
        self.app._display_surf.blit(self.cloudMask[self.cmidx], (0 - ((self.cloudMask[self.cmidx].get_width() - self.app._display_surf.get_width()) / 2), 0 - ((self.cloudMask[self.cmidx].get_height() - self.app._display_surf.get_height()) / 2)))

    def cloud(self):
        np.random.seed(0)
        noise = generate_fractal_noise_3d(
            (8, int(self.window.width / 2), int(self.window.width / 2)), (1, 4, 4), 4, tileable=(True, True, True)
        )

        noise = noise+1
        noise = noise/2

        cloudMask = pg.Surface((int(self.window.width / 2), int(self.window.width / 2)), self.app.surfaceOptions, 32)
        cloudMask = cloudMask.convert_alpha()
        cloudMask.fill((255, 255, 255, int(255 * 0)))

        self.cloudMask = []
        for layer in noise:
            buffer = pg.PixelArray(cloudMask)
            x = 0
            for row in layer:
                y = 0
                for point in row:
                    colorBase = int(255 * point)
                    color = (max(0, colorBase ), max(0, colorBase + random.randint(-2,2)), max(0, colorBase + random.randint(-2,2)), int(251 * point) + random.randint(-2,2))
                    buffer[x, y] = color
                    y += 1
                x += 1
            buffer.close()
            largeMask = pg.Surface((int(self.window.width), int(self.window.width)), self.app.surfaceOptions, 32)
            largeMask.blit(cloudMask, (0,0))
            pg.transform.flip(cloudMask, True, False)
            largeMask.blit(cloudMask, (int(self.window.width / 2),0))
            buffer = largeMask.copy()
            pg.transform.flip(cloudMask, False, True)
            largeMask.blit(buffer, (0,int(self.window.width / 2)))
            largeMask.set_alpha(92)
            self.cloudMask.append(largeMask.copy())

    def mask(self):
        self.lightMask = pg.Surface((int(self.window.width), int(self.window.height)), self.app.surfaceOptions, 32)
        self.lightMask = self.lightMask.convert_alpha(self.lightMask)
        left = random.randint(int(self.window.width * 0.2), int(self.window.width * 0.3))
        width = random.randint(int(self.window.width * 0.4), int(self.window.width * 0.7))

        for i in range(self.window.height + 500, -500, -1):
            height = ((self.window.height + 1000) - (i + 500)) + 2
            colorBase = int((245 * ((i) / (self.window.height+500))))
            color = (max(0, colorBase + random.randint(-2,2)), max(0, colorBase + random.randint(-2,2)), max(0, colorBase + random.randint(-2,2)), int(255 * 0.13))
            pg.draw.ellipse(self.lightMask, color, (left, i, width, height), width=2)
            left -= 1
            width += 2

        

    def background(self, force = True):
        for x in range(0, self.window.height-1, 5):
            y = 0
            while y < self.window.width:
                render = self.elements[random.randint(0,len(self.elements)-1)]
                element = getattr(self, render)
                y += element(x, y) + 3

    def randomShade(self):
        return (random.randint(0, 90), random.randint(20, 170), random.randint(0, 40), random.randint(200, 255))
    
    def randomColor(self):
        return (random.randint(200, 240), random.randint(200, 240), random.randint(200, 240), random.randint(200, 255))
    
    def arc(self, x, y):
        top = x + random.randint(-2,0)
        left = y + random.randint(-2,0)
        width = random.randint(max(3, int(10 * (x / self.window.height))) , max(9, int(30 * (x / self.window.height))))
        height = random.randint(max(18, int(10 * (x / self.window.height))) , max(54, int(90 * (x / self.window.height))))
        rect = (left, top, width, height)

        if random.randint(0, 1):
            start = (90 + random.randint(-15,15)) * (math.pi /180)
            stop = (180 + random.randint(-15,15)) * (math.pi /180)
        else:
            start = ((0 + random.randint(-15,15)) ) * (math.pi /180)
            stop = (90 + random.randint(-15,15)) * (math.pi /180)

        pg.draw.arc(self.surface, self.randomShade(), rect, start, stop, width=1)
        return random.randint(1,4)
    
    def line(self, x, y):
        start = (y + random.randint(-2,2), x + random.randint(-2,0))
        end = (y + random.randint(-3,3), x + random.randint(2,4))
        pg.draw.line(self.surface, self.randomShade(), start, end, 1)
        return random.randint(1,4)

    def dot(self, x, y):
        pggfx.pixel(self.surface, x + random.randint(-2,2), y + random.randint(-2,2), self.randomColor())
        return random.randint(1,2)
    
    def save(self):
        p = Path(self.path)
        p.mkdir(parents=True, exist_ok=True)
        fn = "background.png"
        pg.image.save(self.image, p / fn)

        for i, layer in enumerate(self.cloudMask):
            fn = f'cloudMask_{i}.png'
            pg.image.save(layer, p / fn)


class Window:
    width = 1024
    height = 768
    # width = 1920
    # height = 1400
    def __init__(self):
        pass

    def size(self):
        return (self.width, self.height)
    
    def updateSize(self, w, h):
        self.width = w
        self.height = h

class App:

    def __init__(self):
        self.tick = 0
        self.fps = 30
        self._running = True
        self.window = Window()
        self.surfaceOptions = pg.HWSURFACE | pg.DOUBLEBUF | pg.RESIZABLE
        


    def on_init(self):
        pg.init()

        #pygame.FULLSCREEN
        self._display_surf = pg.display.set_mode(self.window.size(), self.surfaceOptions, 32, 0, True)
        self.background = Grass(self, self._display_surf, self.window)



    def on_event(self, event):
        if event.type == pg.QUIT:
            self._running = False
        if event.type == pg.VIDEORESIZE:
            self._display_surf = pg.display.set_mode((event.w, event.h), self.surfaceOptions, 32, 0, True)
            self.window.updateSize(event.w, event.h)
            self.background = Grass(self, self._display_surf, self.window)


        if event.type == pg.KEYUP:
            if event.key == pg.K_s:
                self.background.save()


        if event.type == pg.MOUSEBUTTONDOWN:
            mouse = pg.mouse.get_pos()
            

    def on_input(self):
        key = pg.key.get_pressed()

    def on_loop(self):
        pass

    def on_render(self, tick = 30):
        self.background.refresh()
        # self.background.animate()
        pg.display.flip()
        pg.time.Clock().tick(tick)

    def on_cleanup(self):
        pg.quit()
 
    def on_execute(self):
        if self.on_init() == False:
            self._running = False
 
        while( self._running ):
            for event in pg.event.get():
                self.on_event(event)
            self.on_input()
            self.on_loop()
            self.on_render(self.fps)
            self.tick += 1

        self.on_cleanup()

    

if __name__ == "__main__" :
    # print(sys.argv[1])
    theApp = App()
    theApp.on_execute()