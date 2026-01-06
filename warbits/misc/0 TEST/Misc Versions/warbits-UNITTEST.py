# concurrency_tests.py
import unittest
import threading
import multiprocessing
import time
import queue
import math
import random

# Import concurrency logic from warbits_main
from warbits_main import (
    attempt_full_cpu_usage,
    attempt_full_gpu_usage,
    simulate_bullet_trajectory,
    simulate_rocket_trajectory,
    simulate_bomb_trajectory,
    spawn_explosion,
    spawn_parachute,
    # etc.
)

def bullet_worker(params):
    pos, vel = params
    traj = simulate_bullet_trajectory(pos, vel)
    return len(traj)

def rocket_worker(params):
    pos, vel = params
    return len(simulate_rocket_trajectory(pos, vel))

def bomb_worker(params):
    x_init, y_init, z_init, vx_init, vy_init, vz_init = params
    path = simulate_bomb_trajectory(x_init, y_init, z_init, vx_init, vy_init, vz_init)
    return len(path)

# Now define tests:

class TestMultiThreadedScenarios(unittest.TestCase):
    def setUp(self):
        self.stop_flag = False
        self.log_queue = queue.Queue()

    def tearDown(self):
        self.stop_flag = True
        while not self.log_queue.empty():
            self.log_queue.get()

    def bomb_thread(self):
        for i in range(5):
            if self.stop_flag:
                break
            x_init = random.uniform(800,1200)
            y_init = random.uniform(2000,3000)
            z_init = random.uniform(800,1500)
            vx_init= random.uniform(10,30)
            vy_init= random.uniform(-5,5)
            vz_init= random.uniform(-2,0)
            path = simulate_bomb_trajectory(x_init,y_init,z_init,vx_init,vy_init,vz_init)
            if path:
                final_z = path[-1][2]
                self.log_queue.put(("BombFinalZ", final_z))
            time.sleep(0.1)

    def bogie_thread(self):
        frame = 0
        hit=False
        while not self.stop_flag and frame<30:
            # let the 'bogie' descend
            z_ = 500 - 15*frame
            if z_<=0 and not hit:
                spawn_explosion((1000, 2000, 0))
                self.log_queue.put("BogieHit")
                hit=True
            frame+=1
            time.sleep(0.05)

    def test_bomb_and_bogie(self):
        t1 = threading.Thread(target=self.bomb_thread)
        t2 = threading.Thread(target=self.bogie_thread)
        t1.start()
        t2.start()

        # Wait longer to ensure bogie definitely hits
        time.sleep(3.0)
        self.stop_flag=True
        t1.join()
        t2.join()

        results=[]
        while not self.log_queue.empty():
            results.append(self.log_queue.get())

        bombs = [r for r in results if isinstance(r, tuple) and r[0]=="BombFinalZ"]
        bogies= [r for r in results if r=="BogieHit"]
        self.assertTrue(len(bombs)>0, "No bombs found!")
        self.assertTrue(len(bogies)>0, "No bogie hit found!")


class TestParallelPhases(unittest.TestCase):
    def setUp(self):
        self.tasks=[]
        for i in range(5):
            px,py,pz = (0+ i*10, 6000+i, 3000)
            vx,vy,vz = (5+i, 1.0, -0.5)
            self.tasks.append(('bullet',(px,py,pz),(vx,vy,vz)))

    def dispatch_task(self,task):
        kind=task[0]
        if kind=="bullet":
            _, pos, vel=task
            return bullet_worker((pos, vel))
        elif kind=="bomb":
            # etc
            pass
        return 0

    def test_run_phases(self):
        with multiprocessing.Pool(2) as pool:
            results= pool.map(self.dispatch_task, self.tasks)
        for r in results:
            self.assertTrue(r>0)

class TestHighLoadIntegration(unittest.TestCase):
    def setUp(self):
        self.stop_flag=False
        self.log_queue=queue.Queue()

    def tearDown(self):
        self.stop_flag=True
        while not self.log_queue.empty():
            self.log_queue.get()

    def bullet_rocket_thread(self):
        for i in range(20):
            if self.stop_flag:
                break
            if random.random()<0.5:
                length=len(simulate_bullet_trajectory((100,200,300),(5,5,-1)))
                self.log_queue.put(f"BULLET={length}")
            else:
                length=len(simulate_rocket_trajectory((200,300,50),(8,3,-2)))
                self.log_queue.put(f"ROCKET={length}")
            time.sleep(0.02)

    def process_bomb_spam(self,count):
        valid=0
        for i in range(count):
            path= simulate_bomb_trajectory(1200,2000,800, 10,0,-1)
            if len(path)>0:
                valid+=1
        return valid

    def test_high_load(self):
        t= threading.Thread(target=self.bullet_rocket_thread)
        t.start()

        with multiprocessing.Pool(2) as p:
            results= [p.apply_async(self.process_bomb_spam,(10,)) for _ in range(2)]
            bomb_counts=[r.get() for r in results]
        total_bombs= sum(bomb_counts)

        time.sleep(0.5)
        self.stop_flag=True
        t.join()

        logs=[]
        while not self.log_queue.empty():
            logs.append(self.log_queue.get())

        self.assertTrue(total_bombs>0)
        self.assertTrue(any("BULLET" in x for x in logs or []) or any("ROCKET" in x for x in logs or []))

if __name__=="__main__":
    multiprocessing.freeze_support()
    unittest.main(verbosity=2)
