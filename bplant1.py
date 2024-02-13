from PIL import Image, ImageDraw
import time
import planar_utils as pu
import plant_growth as pg
import sys
import yaml

##################################
# TODO NOTES AND IDEAS

# get the plant attribute configs from a "genetics" file instead of having them hard-coded here
# add command-line configs for grow amount, logging flag and increment, and inremental output flags and increment, and debug level
# put separated incrementals into a subfolder in the greenhouse
# write usage documentation in the README
# fancier movement strategies
# other fanciness: nodes, needles/sticks, flowers, fruit, leaves, buds, color shifting, etc.

##################################
# CONFIGS / CONSTANTS

DEBUG_LOW = 1
DEBUG_DEVELOPING = 2
DEBUG_RICH = 3
DEBUG_VERY_RICH = 4
DEBUG_EXTREME = 5

USING_DEBUG_LEVEL = DEBUG_DEVELOPING
def debug(msg, level=DEBUG_LOW):
    if level <= USING_DEBUG_LEVEL:
        print(msg)

DO_PARTICLE_TRACING = False
DO_PROGRESS_LOGGING = True
PROGRESS_LOGGING_DEFAULT_INTERVAL = 100
DO_INCREMENTAL_OUTPUT = True
DO_INCREMENTAL_OUTPUT_SEPARATED = False
INCREMENTAL_OUTPUT_DEFAULT_INTERVAL = 400

COLOR_RGBA_BG = (0,0,0,255) #### TODO: remove this once image is set up from plant genetics!
COLOR_RGB_PARTICLE_TRACE = (128,0,0)
COLOR_RGB_PARTICLE_CUR = (0,0,128)

PROGRESS_LOGGING_INTERVAL = PROGRESS_LOGGING_DEFAULT_INTERVAL
INCREMENTAL_OUTPUT_INTERVAL = INCREMENTAL_OUTPUT_DEFAULT_INTERVAL

##################################
# PLANT IMAGE DATA

IMAGE_WIDTH = 256
IMAGE_HEIGHT = 256
IMAGE = Image.new('RGBA', (IMAGE_WIDTH, IMAGE_HEIGHT), COLOR_RGBA_BG)
IMAGE_BOUNDING_BOX = ((0, 0), (IMAGE_WIDTH-1, IMAGE_HEIGHT-1))
PIXELS = IMAGE.load()
DRAW = ImageDraw.Draw(IMAGE)

##################################

def setup_derived_plant_genetics(plant_genetics):
    """
    Add derived plant genetics

    Parameters:
    - plant_genetics: configuration of how the plant grows

    Returns:
    - None
    """
    plant_genetics['color_rgb_bg'] = tuple(plant_genetics['color_rgb_bg'])
    plant_genetics['color_rgba_bg'] = tuple(plant_genetics['color_rgba_bg'])
    plant_genetics['color_rgb_plant'] = tuple(plant_genetics['color_rgb_plant'])

    plant_genetics['dead_colors'] = [plant_genetics['color_rgb_bg'], COLOR_RGB_PARTICLE_TRACE, COLOR_RGB_PARTICLE_CUR]
    plant_genetics['max_particle_inject_inner_radius'] = int(max(plant_genetics['width'], plant_genetics['height']) * .8) # inner radius for injection can go most of the way to the edge
    if plant_genetics['seed_location'] == 'BOTTOM_CENTER':
        plant_genetics['particle_inject_center'] = (plant_genetics['width'] // 2, plant_genetics['height'] - 1)
    else: # default is bottom center
        plant_genetics['particle_inject_center'] = (plant_genetics['width'] // 2, plant_genetics['height'] - 1)

def lpad(tnum, n):
    """
    Left-pad a number with zeros to make it a fixed-width string.

    Parameters:
    - tnum: the number to left-pad
    - n: the number of zeros to add to the left of the number

    Returns:
    - the left-padded string
    """
    padded_string = "{:0>{width}}".format(tnum, width=n)
    return padded_string


def handle_progress_logging(growth_counter, grow_max, tmark_last):
    """
    Handle logging of progress to the screen.

    Parameters:
    - grow_count: the number of growth actions that have been performed
    - tmark_last: the time in seconds when the last progress report was printed

    Returns:
    - tmark_cur: the time in seconds when the current progress report was printed
    """
    
    if DO_PROGRESS_LOGGING and growth_counter % PROGRESS_LOGGING_INTERVAL == 0:        
        tmark_cur = time.time()
        print(f"growth_counter: {growth_counter}/{grow_max}, {int((tmark_cur - tmark_last) * 1000)} ms elapsed for that increment")
        return tmark_cur
    return tmark_last


def handle_incremental_output(incremental_output_counter, growth_counter, incremental_output_file_base):
    """
    Handle output of the image to file at a given interval

    Parameters:
    - incremental_output_counter: the number of growth actions that have been performed
    - growth_counter: the number of growth actions that have been performed
    - incremental_output_file_base: the base name of the file to output to

    Returns:
    - the new incremental output counter value
    """
    if DO_INCREMENTAL_OUTPUT and growth_counter % INCREMENTAL_OUTPUT_INTERVAL == 0:
        incremental_output_counter += 1
        incremental_output_path = f"greenhouse/{incremental_output_file_base}.png"
        if DO_INCREMENTAL_OUTPUT_SEPARATED:
            incremental_output_path = f"greenhouse/{incremental_output_file_base}_{lpad(incremental_output_counter,4)}.png"
        print(f"Saving incremental output to {incremental_output_path}")
        IMAGE.save(incremental_output_path)
    return incremental_output_counter

        
##################################
##################################
##################################
# MAIN

def main(plant_genetics):

    pg.setup_plant_seed_bottom_center(IMAGE,plant_genetics['seed_radius'], plant_genetics['color_rgb_plant'])    

    particle_inject_inner_radius, particle_inject_outer_radius, particle_max_movement_radius = pg.get_particle_action_radii_from_base_radius(
        plant_genetics['seed_radius'],
        plant_genetics
        )

    tmark_first, tmark_last = time.time(), time.time()

    particles = pg.setup_particle_list(plant_genetics['particle_count'], plant_genetics['particle_inject_center'], particle_inject_inner_radius, particle_inject_outer_radius, IMAGE_BOUNDING_BOX)
    debug(f"{len(particles)} particles injected")
    debug(f"particles: {particles}", DEBUG_DEVELOPING)

    # create incremental output file base name, based on growth size and timestamp
    incremental_output_file_base = f"plant_{plant_genetics['grow_amount']}_{tmark_first}_incr"
    debug(f"incremental_output_file_base: {incremental_output_file_base}", DEBUG_DEVELOPING)

    # MAIN LOOP
    ## while the plant is growing, get a particle, move it, and append it back on the list; handle growth and out-of-bounds replacement as needed
    growth_counter = 0
    incremental_output_counter = 0
    plant_radius = plant_genetics['seed_radius']
    while growth_counter < plant_genetics['grow_amount']:
        particle = particles.pop(0)
        debug(f"acting on particle {particle}", DEBUG_EXTREME)

        if DO_PARTICLE_TRACING:
            PIXELS[particle[0],particle[1]] = COLOR_RGB_PARTICLE_TRACE

        particle = pg.move_particle(particle, IMAGE_BOUNDING_BOX)

        if pg.is_adjacent_to_live_pixel(particle, PIXELS, plant_genetics['dead_colors'], IMAGE_BOUNDING_BOX):
            growth_counter += 1
            pg.grow_at(particle, PIXELS, plant_genetics['color_rgb_plant'])
            debug(f"grew at {particle}", DEBUG_VERY_RICH)

            new_radii = pg.grow_radii(particle, plant_radius, plant_genetics)
            if new_radii is not None:
                plant_radius, particle_inject_inner_radius, particle_inject_outer_radius, particle_max_movement_radius = new_radii

            new_particle = pg.injected_particle_ring(plant_genetics['particle_inject_center'], particle_inject_inner_radius, particle_inject_outer_radius, IMAGE_BOUNDING_BOX)
            particles.append(new_particle)
            tmark_last = handle_progress_logging(growth_counter, plant_genetics['grow_amount'], tmark_last)
            incremental_output_counter = handle_incremental_output(incremental_output_counter, growth_counter, incremental_output_file_base)
        else:
            particle = pg.get_particle_within_movement_bounds_ring(particle,
                                                                   plant_genetics['particle_inject_center'], 
                                                                   particle_inject_inner_radius, 
                                                                   particle_inject_outer_radius, 
                                                                   particle_max_movement_radius, 
                                                                   IMAGE_BOUNDING_BOX)
            particles.append(particle)
            if DO_PARTICLE_TRACING:
                PIXELS[particle[0],particle[1]] = COLOR_RGB_PARTICLE_CUR

    total_elapsed_s = int((time.time() - tmark_first))
    final_output_path = f"greenhouse/plant_{plant_genetics['grow_amount']}_{tmark_first}_{total_elapsed_s}.png"
    IMAGE.save(final_output_path)
    print(f"Done. Total elapsed time for plant generation: {total_elapsed_s} s")
    print(f"Image saved to {final_output_path}")


if __name__ == "__main__":
    with open("plant_genetics.yaml", 'r') as stream:
        plant_genetics = yaml.safe_load(stream)
    setup_derived_plant_genetics(plant_genetics)

    debug(f"plant_genetics: {plant_genetics}", DEBUG_DEVELOPING)
    # sys.exit()


    main(plant_genetics)