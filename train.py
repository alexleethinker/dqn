import sys
from random import randrange
from dqn import DQN
from ale_python_interface import ALEInterface
from collections import deque
from collections import namedtuple
import preprocess as pp

#SETUP
Experience = namedtuple('Experience', 'state action reward new_state')

def train(minibatch_size=32, replay_capacity=1000, hist_len=4, tgt_update_freq=10000,
    discount=0.99, act_rpt=4, upd_freq=4, learning_rate=0.00025, grad_mom=0.95,
    sgrad_mom=0.95, min_sq_grad=0.01, init_epsilon=1.0, fin_epsilon=0.1, 
    fin_exp=1000000, replay_size=50000, noop_max=30):
    #Create ALE object
    if len(sys.argv) < 2:
      print 'Usage:', sys.argv[0], 'rom_file'
      sys.exit()

    ale = ALEInterface()

    # Get & Set the desired settings
    ale.setInt('random_seed', 123)

    # Set USE_SDL to true to display the screen. ALE must be compilied
    # with SDL enabled for this to work. On OSX, pygame init is used to
    # proxy-call SDL_main.
    USE_SDL = True
    if USE_SDL:
      if sys.platform == 'darwin':
        import pygame
        pygame.init()
        ale.setBool('sound', False) # Sound doesn't work on OSX
      elif sys.platform.startswith('linux'):
        ale.setBool('sound', True)
      ale.setBool('display_screen', True)

    # Load the ROM file
    ale.loadROM(sys.argv[1])

    #initialize epsilon
    epsilon = init_epsilon

    # create DQN agent
    agent = DQN(ale, 1000000, 32, epsilon)

    # Initialize replay memory to capacity replay_capacity
    replay_memory = deque([], replay_capacity)

    # Initialize action-value function Q with random weights h
    #weights = ?????????
    #----Handled with Tensorflow
    # Initialize target action-value function Q^ with weights h2 5 h
    #tgt_weights = weights
    #----Handled with Tensorflow

    num_frames = 0
    #TODO Change the episode ranges to be a function of frames
    for episode in range(2):
        img = ale.getScreenRGB()
        #initialize sequence with initial image
        seq = list()
        seq.append(img)
        proc_seq = list()
        proc_seq.append(pp.preprocess(seq))
        total_reward = 0
        state = img
        while not ale.game_over():
            action = agent.get_action(state)
            reward = 0
            #skip frames by repeating action
            for i in range(act_rpt):
                reward = reward + ale.act(action)
            #cap reward
            reward = cap_reward(reward)
            # game state is just the pixels of the screen
            img = ale.getScreenRGB()
            #set s(t+1) = s_t, a_t, x_t+1
            seq.append(action)
            seq.append(img)
            #preprocess s_t+1
            proc_seq.append(pp.preprocess(seq))
            #store transition (phi(t), a_t, r_t, phi(t+1)) in replay_memory
            exp = get_experience(proc_seq, action, reward, hist_len)
            replay_memory.append(exp)

            num_frames = num_frames + 1
            total_reward += reward
        print('Episode %d ended with score: %d' % (episode, total_reward))
        ale.reset_game()
    print "num frames is " + str(num_frames)

def get_experience(proc_seq, action, reward, hist_len):
    tplus = len(proc_seq) - 1
    exp_state = list()
    exp_new_state = list()
    if len(proc_seq) < hist_len:
        num_copy = hist_len - (len(proc_seq) - 1)
        for i in range(num_copy):
            exp_state.append(proc_seq[0])
        for i in range(len(proc_seq) - 1):
            exp_state.append(proc_seq[i])

        num_copy = hist_len - len(proc_seq)
        for i in range(num_copy):
            exp_new_state.append(proc_seq[0])
        for i in range(len(proc_seq) - 1):
            exp_new_state.append(proc_seq[i])

    else:
        for i in range(len(proc_seq) - 1 - hist_len, len(proc_seq) - 2):
            exp_state.append(proc_seq[i])
        for i in range(len(proc_seq) - hist_len, len(proc_seq) - 1):
            exp_new_state.append(proc_seq[i])
    exp = Experience(state=exp_state, action=action, reward=reward, new_state=exp_new_state)
    return exp
    
def cap_reward(reward):
    if reward > 0:
        return 1
    elif reward < 0:
        return -1
    else:
        return 0

if __name__ == '__main__':
    train()