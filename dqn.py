#!/usr/bin/env python
import random
from random import randrange
from random import uniform
from cnn import CNN
import os
import tensorflow as tf
import numpy as np

class DQN:
	def __init__(self, ale, session, capacity, epsilon, learning_rate, momentum, sq_momentum, hist_len, num_legal_actions, 
		tgt_update_freq, discount):
		self.ale = ale
		self.session = session
		self.capacity = capacity
		self.legal_actions = ale.getLegalActionSet()
		self.epsilon = epsilon
		self.num_updates = 0
		self.discount = discount
		self.tgt_update_freq = tgt_update_freq
		self.chkpt_freq = 10000
		self.prediction_net = CNN(learning_rate, momentum, sq_momentum, hist_len, num_legal_actions)
		self.target_net = CNN(learning_rate, momentum, sq_momentum, hist_len, num_legal_actions)
		self.checkpoint_directory = "checkpoints"

		self.session.run(tf.global_variables_initializer())

		self.saver = tf.train.Saver(
			[
			#weights prediction
			self.prediction_net.weights_conv1,
			self.prediction_net.weights_conv2,
			self.prediction_net.weights_conv3,
			self.prediction_net.weights_fc1,
			self.prediction_net.weights_output,
			#bias prediction
			self.prediction_net.bias_conv1,
			self.prediction_net.bias_conv2,
			self.prediction_net.bias_conv3,
			self.prediction_net.bias_fc1,
			self.prediction_net.bias_output,
			#weights target
			self.target_net.weights_conv1,
			self.target_net.weights_conv2,
			self.target_net.weights_conv3,
			self.target_net.weights_fc1,
			self.target_net.weights_output,
			#bias target
			self.target_net.bias_conv1,
			self.target_net.bias_conv2,
			self.target_net.bias_conv3,
			self.target_net.bias_fc1,
			self.target_net.bias_output
			],
			max_to_keep=3
		)
		checkpoint = tf.train.get_checkpoint_state(self.checkpoint_directory)
		if checkpoint and checkpoint.model_checkpoint_path:
			print "Loading the saved weights..."
			self.saver.restore(self.session, checkpoint.model_checkpoint_path)
			self.counter = int(checkpoint.model_checkpoint_path.split('-')[-1])
			print "Load complete."
		else:
			print "No saved weights. Beginning with random weights."


	def get_action(self, state):
		rand = uniform(0,1)
		if (rand < self.epsilon):
			return self.legal_actions[randrange(len(self.legal_actions))]
		else:
			#Choose greedy action
			mod_state = np.array([state], dtype=np.float32)
			if not (np.shape(mod_state) == (1, 84, 84, 4)):
				print "Invalid shape"
				print "Orig Shape " + str(np.shape(state))
				print "Mod shape " + str(np.shape(mod_state))
			q_vals = self.prediction_net.q.eval(
	        		feed_dict = {self.prediction_net.state: mod_state})[0]
			return np.argmax(q_vals)

	def set_epsilon(self, epsilon):
		self.epsilon = epsilon

	def compute_labels(self, sample, minibatch_size):
	    label = np.zeros(minibatch_size)
	    for i in range(minibatch_size):
	        if (sample[i].game_over):
	            label[i] = sample[i].reward
	        else:
	        	q_vals = self.target_net.q.eval(
	        		feed_dict = {self.target_net.state:[sample[i].new_state]})
	    		label[i] = sample[i].reward + self.discount * q_vals.max()
	    return label

	def reset_target_network(self):
		#Copy Weights
		self.session.run(self.target_net.weights_conv1.assign(self.prediction_net.weights_conv1))
		self.session.run(self.target_net.weights_conv2.assign(self.prediction_net.weights_conv2))
		self.session.run(self.target_net.weights_conv3.assign(self.prediction_net.weights_conv3))
		self.session.run(self.target_net.weights_fc1.assign(self.prediction_net.weights_fc1))
		self.session.run(self.target_net.weights_output.assign(self.prediction_net.weights_output))
		#Copy Bias
		self.session.run(self.target_net.bias_conv1.assign(self.prediction_net.bias_conv1))
		self.session.run(self.target_net.bias_conv2.assign(self.prediction_net.bias_conv2))
		self.session.run(self.target_net.bias_conv3.assign(self.prediction_net.bias_conv3))
		self.session.run(self.target_net.bias_fc1.assign(self.prediction_net.bias_fc1))
		self.session.run(self.target_net.bias_output.assign(self.prediction_net.bias_output))
	
	def sample_minibatch(self, replay_memory, minibatch_size):
		return random.sample(replay_memory, minibatch_size)

	def train(self, replay_memory, minibatch_size):
	    #sample a minibatch of transitions
	    sample = self.sample_minibatch(replay_memory, minibatch_size)
	    #set label
	    labels = self.compute_labels(sample, minibatch_size)
	    
	    state = [x.state for x in sample]
	    actions = [x.action for x in sample]

	    feed_dict={
		    self.prediction_net.state : state,
		    self.prediction_net.actions : actions,
		    self.prediction_net.target : labels.tolist()
	    }

	    #Perform the gradient descent step
	    self.prediction_net.train_agent.run(feed_dict=feed_dict)

	    #increment update counter
	    self.num_updates = self.num_updates + 1
	    if self.num_updates % self.tgt_update_freq:
	    	self.reset_target_network()

	    if self.num_updates % self.chkpt_freq == 0:
	    	print "Saving Weights"
	    	self.saver.save(self.session, os.path.join(self.checkpoint_directory, "model"), global_step = self.num_updates)
	    	print "Saved."