from functools import partial
from matplotlib import rcParams
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import random
import re
import streamlit as st

add_footer="""
<style>

footer{
    visibility:visible;
}
footer:after{
    content: 'Efrat Herbst, Prof. Zohar Yakhini and Dr. Ofer Mokady';
    display:block;
    position:relative;
    color:grey;
    # padding:5px;
    top:3px;
}

</style>
"""

def generate_offspring(seed: str, mutation_rate_offspring: float, 
                       mutation_rate_digit: float, mutation_rate_digit_up: float, 
                       mutation_rate_digit_up_plus: float, 
                       mutation_rate_digit_down_minus: float, number_of_offspring: int) -> list:
    """Generates offspring per parent with random mutations.

    Args:
        seed: parent character combination.
        mutation_rate_offspring: the probability for an offspring to go through mutation.
        mutation_rate_digit: for an offspring which is going under mutation, 
            this is the probability for every digit to go under mutation.
        mutation_rate_digit_up: for a digit which is going under mutation,
            this is the probability for it to go up over down.
        mutation_rate_digit_up_plus: for a digit which is going under a mutation upward,
            this is the probability to go up in +1 over +2 digits.
        mutation_rate_digit_down_minus: for a digit which is going under a mutation downward,
            this is the probability to go down in -1 over -2 digits. 
        number_of_offspring: number of offspring to generate for this parent.

    Returns:
        List of offspring codes.
    """
    offspring = []
    for _ in range(number_of_offspring):
        rand_offspring = random.random()
        if rand_offspring < mutation_rate_offspring:
            mutated = []
            for digit in seed:
                rand_digit = random.random()
                if rand_digit < mutation_rate_digit:
                    if digit == '9':
                        new_digit = '8'
                    elif digit == '0':
                        new_digit = '1'
                    else:
                        rand_direction = random.random()
                        new_digit = int(digit)
                        if rand_direction < mutation_rate_digit_up:  
                            if digit == '8':
                              new_digit += 1
                            else:
                              rand_jump = random.random()
                              if rand_jump < mutation_rate_digit_up_plus: 
                                new_digit += 1
                              else:
                                new_digit += 2
                        else:
                          if digit == '1':
                            new_digit -= 1
                          else:
                            rand_jump = random.random()
                            if rand_jump < mutation_rate_digit_down_minus: 
                              new_digit -= 1
                            else:
                              new_digit -= 2
                    mutated.append(str(new_digit))
                else:
                    mutated.append(digit)
            offspring.append(''.join(mutated))
        else:
           offspring.append(seed)
    return offspring

def calculate_score(offspring: list, target: str) -> list:
    """Computes the distance from each of the offspring to the target seed.

    Args:
        offspring: list of offspring.
        target: target sequence.

    Returns:
        List of distances.
    """
    scores = []
    for number in offspring:
        score = sum(
           abs(int(digit1) - int(digit2)) for digit1, digit2 in zip(str(number), target))
        scores.append(score)
    return scores

def natural_selection() -> None:
    """Main function for Natural Selection page.
    """
    global generation, best_offspring, carry_on
    generation = 0
    best_offspring = []
    carry_on = True

    #Page setup
    help_number_of_digits = 'Representing the length of the character combination'
    number_of_digits = st.sidebar.slider(
       'Number of digits', 1, 20, 6, 1, help=help_number_of_digits)
    
    placeholder_seed = '5' * number_of_digits
    label_seed = 'Enter the seed (%s-digit number): ' %number_of_digits
    help_seed = 'Representing the character combination of the original parent'
    seed = st.text_input(
       label=label_seed, value=placeholder_seed, max_chars=number_of_digits, help=help_seed)
    
    placeholder_target = '9' * number_of_digits
    label_target = 'Enter the target (%s-digit number): ' %number_of_digits
    help_target = 'Representing the character combination which best fits the current environment'
    target = st.text_input(
       label=label_target, value=placeholder_target, max_chars=number_of_digits, help=help_target)
    
    st.button('Re-run')

    label_average_number_of_offspring = 'Number of offspring on average'
    help_average_number_of_offspring = ('Offspring rate per parent is randomly drawn from a '
        'poisson distribution with the selected rate')
    average_number_of_offspring = st.sidebar.slider(
       label_average_number_of_offspring, 1.0, 2.0, 1.2, 0.1, help=help_average_number_of_offspring)
    
    label_number_of_parents = 'Number of parents'
    help_number_of_parents = 'Number of parents selected in each generation'
    number_of_parents = st.sidebar.slider(
       label_number_of_parents, 0, 1000, 200, 10, help=help_number_of_parents)
    
    label_mutation_rate_offspring = 'Probability for mutation in an offspring'
    help_mutation_rate_offspring = 'Offspring probability to mutate'
    mutation_rate_offspring = st.sidebar.slider(
       label_mutation_rate_offspring, 0.0, 1.0, 0.05, 0.01, help=help_mutation_rate_offspring) 
    
    label_mutation_rate_digit = 'Probability for mutation in a digit'
    help_mutation_rate_digit = ('For an offspring which got selected to mutate, this is the '
            'probability for each of the digits to mutate. This mutation represents a slight '
            'change in a character state')
    mutation_rate_digit = st.sidebar.slider(
       label_mutation_rate_digit, 0.0, 1.0, 0.1, 0.05, help=help_mutation_rate_digit)

    label_mutation_rate_digit_up = 'Probability for mutated digit to go up (versus down)'
    help_mutation_rate_digit_up = ('For a digit which got selected to mutate, this is the '
            'probability for it to move up or down. For example, this is the probability for a '
            'bird\'s wing to get slightly longer or slightly shorter')
    mutation_rate_digit_up = st.sidebar.slider(
       label_mutation_rate_digit_up, 0.0, 1.0, 0.5, 0.05, help=help_mutation_rate_digit_up)
    
    label_mutation_rate_digit_up_plus = ('Probability for mutated digit to jump 1 step up '
        '(versus 2 steps up)')
    help_mutation_rate_digit_up_plus = ('For a digit which got selected to mutate up, '
        'this is the probability for it to move one digit up over two digits up')
    mutation_rate_digit_up_plus = st.sidebar.slider(
       label_mutation_rate_digit_up_plus, 0.0, 1.0, 1.0, 0.05, 
       help=help_mutation_rate_digit_up_plus)

    label_mutation_rate_digit_down_minus = ('Probability for mutated digit to jump 1 step down '
        '(versus 2 steps down)')
    help_mutation_rate_digit_down_minus = ('For a digit which got selected to mutate down, '
        'this is the probability for it to move one digit down over two digits down')
    mutation_rate_digit_down_minus = st.sidebar.slider(
       label_mutation_rate_digit_down_minus, 0.0, 1.0, 1.0, 0.05, 
       help=help_mutation_rate_digit_down_minus)

    if len(seed) != number_of_digits or not seed.isdigit():
        st.error('Invalid seed number. Please enter a %s-digit number.' %number_of_digits)

    if len(target) != number_of_digits or not target.isdigit():
        st.error('Invalid target number. Please enter a %s-digit number.' %number_of_digits)

    #First generation.
    all_offspring = []
    initial_seed = seed
    initial_score = sum(abs(int(digit1) - int(digit2)) for digit1, digit2 in zip(seed, target))
    offspring = []
    for i in range(number_of_parents):
        number_of_offspring = np.random.poisson(average_number_of_offspring)
        offspring.extend(
           generate_offspring(
              seed, 
              mutation_rate_offspring, 
              mutation_rate_digit, 
              mutation_rate_digit_up, 
              mutation_rate_digit_up_plus, 
              mutation_rate_digit_down_minus, 
              number_of_offspring))
    scores = calculate_score(offspring, target)
    scores_sorted = scores.copy()
    scores_sorted.sort(reverse=False)
    min_scores = scores_sorted[:number_of_parents]
    best_offspring = []
    for score in min_scores:
        best_offspring.append(offspring[scores.index(score)])
    
    #Visualization           
    fig = plt.figure()
    X = np.random.uniform(0, 1, (len(offspring)))
    Y = np.random.uniform(0, 1, (len(offspring)))
    scat = plt.scatter(X, Y, c=scores, vmax=initial_score, vmin=0)
    cbar = plt.colorbar()
    cbar.set_label('Distance from %s' %target)
    text_1 = 'Generation: %s, Best offspring: %s, Distance: %s \n' %(
       generation, best_offspring[0], min_scores[0])
    plt.title(text_1, fontsize = 11)
    generation += 1
    all_offspring.append(offspring)

    def gen():
        """Generates frames as long as simulation has not ended.
        """
        global carry_on
        i = 0
        while carry_on:
            i += 1
            yield i
        
    def update(frame_number):
        """Updates computations and plots for every generation.

        Args:
            frame_number: frame number.

        Returns:
            Updated frame.
        """
        global generation, best_offspring, carry_on

        offspring = []
        for parent in best_offspring:
            number_of_offspring = np.random.poisson(average_number_of_offspring)
            offspring.extend(
               generate_offspring(
                  parent, 
                  mutation_rate_offspring, 
                  mutation_rate_digit, 
                  mutation_rate_digit_up, 
                  mutation_rate_digit_up_plus, 
                  mutation_rate_digit_down_minus, 
                  number_of_offspring))
        scores = calculate_score(offspring, target)
        scores_sorted = scores.copy()
        scores_sorted.sort(reverse=False)
        min_scores = scores_sorted[:number_of_parents]
        best_offspring = []
        for score in min_scores:
            best_offspring.append(offspring[scores.index(score)])

        # Visualization.          
        X = np.random.uniform(0, 1, (len(offspring)))
        Y = np.random.uniform(0, 1, (len(offspring)))
        scat.set_offsets(np.c_[X, Y])
        scat.set_array(scores)
        text_1 = 'Generation: %s, Best offspring: %s, Distance: %s \n' %(
           generation, best_offspring[0], min_scores[0])
        plt.title(text_1, fontsize=11)
        plt.axis('off')
        generation += 1
        all_offspring.append(offspring)

        if min_scores[0] == 0:
            carry_on = False
            print('\nTarget reached!')
            
        return scat,

    rcParams['animation.embed_limit'] = 2**128
    with st.spinner(text='Running simulation...  \rAnimation coming momentarily'):
        ani = FuncAnimation(fig, update, 
                    frames=gen, save_count=None, interval=100, repeat=False) 
        animjs = ani.to_jshtml()
        click_on_play = """document.querySelector('.anim-buttons button[title="Play"]').click();"""
        pattern = re.compile(r"(setTimeout.*?;)(.*?})", re.MULTILINE | re.DOTALL)
        new_animjs = pattern.sub(rf"\1 \n {click_on_play} \2", animjs)

    st.components.v1.html(new_animjs, height=600, scrolling=True)

st.set_page_config(page_title='Natural Selection', page_icon=':earth_americas:')
st.markdown(add_footer, unsafe_allow_html=True)
st.markdown('# Natural Selection')
st.sidebar.header('Parameters')
st.sidebar.write('Change any of the following parameters to generate a new simulation')
st.write(
    '''This simulation demonstrates the process of Natural Selection, 
    starting from a seed number (representing the character combination in the original parent), 
    and ending at a target number (representing the character combination which best fits the 
    environment).'''
)
with st.expander('Learn more'):
    st.write('''
        The character combination is represented by a string of digits, where each digit 
             represents a character (for example, one digit could represent the color of feathers 
             of a bird, while another digit could represent the length of its beak). 
             Each character may have 10 variations (character states) represented 
             by the digits 0-9 (for example, different shades of brown in the feathers of a bird). 
             A random process generates mutations in every 
             generation. Mutation in each character may change it slightly, so 
             that a digit can mutate up to +-2 digits at most in each generation 
             (for example, the color of a bird's feathers could get slightly darker or brighter). 
             The offspring having a character combination number closest to the target combination 
             are selected as parents for the next generation (for example, because the color of 
             their feathers allows them to hide better from predators, 
             and the length of their beak allows them to hunt more food). 
             Distance is measured by the sum of absolute differences between each digit in an 
             offpring combination and its corresponding digit in the target combination.
             
    Note that the target number represents the character combination which best fits 
             specific environment conditions. In real life, environment conditions 
             change all the time (for example, because of global warming). 
             The character combination which gives the most probability to survive changes 
             respectively.
        
    Changing the parameters, seed and target numbers will automatically generate 
             a new simulation. You can also click the Re-run button to generate 
             a new simulation using the same parameters to observe a different 
             random process. Note that some parameter combinations may result in 
             a very long time to convergence.

    ''')


natural_selection()
