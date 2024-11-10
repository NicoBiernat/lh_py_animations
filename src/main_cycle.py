import tkinter as tk
import multiprocessing, time, sys, signal
from pyghthouse.ph import Pyghthouse
from mp_firework import Fireworks
from mp_bouncers import BounceAnimation as Bouncers
from mp_lavablob import Lavablobs
from mp_rgbtest import RgbTest
from mp_rain import RainAnimation
from mp_rebound import ReboundAnimation
from mp_diffraction import DiffAnimation
from stopwatch import Stopwatch
from color_functions import interpolate

class AnimationController():   
    def __init__(self, time_per_anim) -> None:
        self.keep_going = True
        signal.signal(signal.SIGINT, self._handle_sigint)
        self.run(time_per_anim)
        
    
    @staticmethod     
    def read_auth(filename="auth.txt"):
        with open(filename) as src:
            username, token = None, None
            lines = src.readlines()
            for line in lines:
                line = line.split(":")
                if len(line) == 2:
                    match line[0].strip().lower():
                        case 'name':
                            username = line[1].strip()
                            print(f"Username read from file: {username}")
                        case 'username':
                            username = line[1].strip()
                            print(f"Username read from file: {username}")
                        case 'token':
                            token = line[1].strip()
                            print(f"Token read from file: {token}")
                        case _:
                            print(f"Unrecognized Key: '{line[0]}'")
            if not username or not token:
                print(f"Error: File {filename} is incomplete!")
            return username, token

    @staticmethod     
    def send_frame(ph: Pyghthouse, image: list): 
        img = ph.empty_image()
        for x in range(min(len(img), len(image[0]))):
            for y in range(min(len(img[0]), len(image))):
                img[x][y] = image[y][x]
        ph.set_image(img)
        
    @staticmethod     
    def send_faded_frame(ph: Pyghthouse, image: list, factor: float):
        img = ph.empty_image()
        for x in range(min(len(img), len(image[0]))):
            for y in range(min(len(img[0]), len(image))):
                img[x][y] = interpolate(image[y][x], img[x][y], factor) 
        ph.set_image(img)
        
    def _handle_sigint(self, signum, frame):
        print("Ctrl+C detected. Stopping animations...")
        self.keep_going = False
        
    ##### RUN METHOD #####
    def run(self, time_per_anim):
        username, token = self.read_auth()
        if not username or not token:
            exit(1)
            
        animations = [Fireworks(), 
                    Lavablobs(),
                    #RgbTest(), 
                    RainAnimation(), 
                    ReboundAnimation(), 
                    DiffAnimation(), 
                    Bouncers()]
        
        fps = 40
        
        ph = Pyghthouse(username, token)
        ph.start()
        
        anim_timer = Stopwatch()
        frametimer = Stopwatch() 
        update_interval = 1/(fps-1)
        n = 0
        while self.keep_going:
            framequeue = multiprocessing.Queue()
            commandqueue = multiprocessing.Queue()
            anim_timer.set(time_per_anim)
            anim = animations[n].get_instance(28, 27, framequeue, commandqueue, fps=fps, animspeed = 1)
            print(f"Starting animation '{anim.name}' for {time_per_anim} seconds.")
            anim.params(28, 27, framequeue, commandqueue, fps=fps, animspeed = 1)
            anim.start()
            
            image = Pyghthouse.empty_image()
            opacity = 0
            while not anim_timer.has_elapsed() and self.keep_going:   
                frametimer.set(update_interval)
                while not framequeue.empty(): 
                    image = framequeue.get_nowait()
                if opacity < 255:
                    self.send_faded_frame(ph, image, opacity/256)
                    opacity += 4
                else:
                    self.send_frame(ph, image)
                commandqueue.put("keep_running")
                time.sleep(frametimer.remaining())
                
            for i in range(256, 0, -4):
                frametimer.set(update_interval)
                while not framequeue.empty(): 
                    image = framequeue.get_nowait()
                self.send_faded_frame(ph, image, i/256)
                commandqueue.put("keep_running")
                time.sleep(frametimer.remaining())
                    
            #Fireworks().terminate()
            print("Attempting to terminate process...")
            anim.stop()
            anim.join(timeout = 2)
            print("Child process terminated.")
            n = (n+1) % len(animations)
    
if __name__ == "__main__":
    time_per_anim=int(sys.argv[1]) if len(sys.argv) > 1 else 30
    AnimationController(time_per_anim)