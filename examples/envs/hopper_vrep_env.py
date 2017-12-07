
import vrep_env
import vrep # vrep.sim_handle_parent

import os
vrep_scenes_path = os.environ['VREP_SCENES_PATH']

import gym
from gym import spaces
import numpy as np

class HopperVrepEnv(vrep_env.VrepEnv):
	metadata = {
		'render.modes': [],
	}
	def __init__(
		self,
		server_addr='127.0.0.1',
		server_port=19997,
		scene_path=vrep_scenes_path+'/hopper.ttt',
	):
		vrep_env.VrepEnv.__init__(
			self,
			server_addr,
			server_port,
			scene_path,
		)
		
		# All joints
		joint_names = ['thigh_joint','leg_joint','foot_joint']
		# All shapes
		shape_names = ['torso','thigh','leg','foot']
		
		# Getting object handles
		
		# Meta
		self.camera = self.get_object_handle('camera')
		
		# Actuators
		self.oh_joint = list(map(self.get_object_handle, joint_names))
		# Shapes
		self.oh_shape = list(map(self.get_object_handle, shape_names))
		
		# One action per joint
		num_act = len(self.oh_joint)
		# Multiple dimensions per shape
		num_obs = (len(self.oh_shape)*3*2)+1
		
		self.joints_max_velocity = 8.0
		act = np.array( [self.joints_max_velocity] * num_act )
		obs = np.array(          [np.inf]          * num_obs )
		
		self.action_space      = spaces.Box(-act,act)
		self.observation_space = spaces.Box(-obs,obs)
		
		print('HopperVrepEnv: initialized')
	
	def _make_observation(self):
		lst_o = []
		
		# Include z position in observation
		torso_pos = self.obj_get_position(self.oh_shape[0])
		lst_o += [torso_pos[2]]
		
		# Include shapes relative velocities in observation
		for i_oh in self.oh_shape:
			lin_vel , ang_vel = self.obj_get_velocity(i_oh)
			lst_o += ang_vel
			lst_o += lin_vel
		
		self.observation = np.array(lst_o).astype('float32')
	
	def _make_action(self, a):
		for i_oh, i_a in zip(self.oh_joint, a):
			self.obj_set_velocity(i_oh, i_a)
	
	def _step(self, action):
		# actions = np.clip(actions,-self.joints_max_velocity, self.joints_max_velocity)
		assert self.action_space.contains(action), "%r (%s) invalid"%(action, type(action))
		
		# Actuate
		self._make_action(action)
		# Step
		self.step_simulation()
		# Observe
		self._make_observation()
		
		# Reward
		torso_pos_z  = self.observation[0] # up/down
		torso_lvel_x = self.observation[4]
		r_alive = 1.0
		
		reward = (16.0)*(r_alive) +(8.0)*(torso_lvel_x)
		
		# Early stop
		stand_threshold = 0.10
		done = (torso_pos_z < stand_threshold)
		
		return self.observation, reward, done, {}
	
	def _reset(self):
		if self.sim_running:
			self.stop_simulation()
		self.start_simulation()
		self._make_observation()
		return self.observation
	
	def _render(self, mode='human', close=False):
		pass
	
	def _seed(self, seed=None):
		return []
	
def main(args):
	env = HopperVrepEnv()
	for i_episode in range(16):
		observation = env.reset()
		total_reward = 0
		for t in range(256):
			action = env.action_space.sample()
			observation, reward, done, _ = env.step(action)
			total_reward += reward
			if done:
				break
		print("Episode finished after {} timesteps.\tTotal reward: {}".format(t+1,total_reward))
	env.close()
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))