from PIL import Image, ImageDraw
import random
import time
import planar_utils as pu
import plant_growth as pg

##################################
# TODO NOTES AND IDEAS

# ** split this file up into a few files / modules; most of the function defs can be pulled apart
# add unit tests
# do a code cleaning pass
# support command line options for the various configs - turn the numbers in here into defaults
# put separated incrementals into a subfolder in the greenhouse
# write usage documentation in the README
# fancier movement strategies
# other fanciness: nodes, needles/sticks, flowers, fruit, leaves, buds, color shifting, etc.

##################################
# CONFIGS / CONSTANTS

USING_DEBUG_LEVEL = 1
DEBUG_BASE = 1
DEBUG_EXTREME = 5
def debug(msg, level=DEBUG_BASE):
    if level <= USING_DEBUG_LEVEL:
        print(msg)

DO_PARTICLE_TRACING = False
DO_PROGRESS_LOGGING = True
PROGRESS_LOGGING_DEFAULT_INTERVAL = 100
DO_INCREMENTAL_OUTPUT = True
DO_INCREMENTAL_OUTPUT_SEPARATED = False
INCREMENTAL_OUTPUT_DEFAULT_INTERVAL = 200

COLOR_BG = (0,0,0)
COLOR_PARTICLE_TRACE = (128,0,0)
COLOR_PARTICLE_CUR = (0,0,128)
COLOR_PLANT = (0,128,0)
DEAD_COLORS = [COLOR_BG, COLOR_PARTICLE_TRACE, COLOR_PARTICLE_CUR]

##################################
# COMMAND LINE CONFIGS

# GROW_AMOUNT - number of times to grow the plant by 1 step
# PARTICLE_COUNT - how many particles to keep active at once (more means denser growth; also impacts run speed though how is less clear) (20 is a decent base)
# PARTICLE_INJECTION_MAX_RADIUS_FACTOR - as a multiplier of the maximum radius of the plant (i.e the growth point furthest from the center of the seed); the larger, the more spreading the plant and the longer the run time
# PARTICLE_INJECTION_MIN_RADIUS_FACTOR - as a multiplier of the maximum radius of the plant (i.e the growth point furthest from the center of the seed); the larger, the more spreading the plant and the longer the run time
# particles are injected in a ring formed by the difference between the max radius and min radius
# PARTICLE_MOVEMENT_MAX_RADIUS_EXTENSION - as an addition to the PARTICLE_INJECTION_RADIUS; the larger, the more spreading the plant and the longer the run time
# PROGRESS_LOGGING_INTERVAL - print progress report to screen after this many growth actions
# INCREMENTAL_OUTPUT_INTERVAL - output image to file after this many growth actions

GROW_AMOUNT = 1000 # number of times to grow the plant by 1 step
PARTICLE_COUNT = 25 # how many particles to keep active at once (more means denser growth; also impacts run speed though how is less clear) (20 is a decent base)

# particles are injected in a ring formed by the difference between the max radius and min radius
PARTICLE_INJECTION_MAX_RADIUS_FACTOR = 1.6 # as a multiplier of the maximum radius of the plant (i.e the growth point furthest from the center of the seed); the larger, the more spreading the plant and the longer the run time
# NOTE: generally, you want the max to be > 1 and < 3, but you can go higher if you want; higher means sparser, lower means denser
PARTICLE_INJECTION_MIN_RADIUS_FACTOR = .8 # as a multiplier of the maximum radius of the plant (i.e the growth point furthest from the center of the seed); the larger, the more spreading the plant and the longer the run time
# NOTE: min radius factor of < 1 will increase density, and also make things run faster
# NOTE: the higher the proportion of the injection ring that overlaps the plant radius, the denser the structure
PARTICLE_MOVEMENT_MAX_RADIUS_EXTENSION = 20 # as an addition to the PARTICLE_INJECTION_RADIUS; the larger, the more spreading the plant and the longer the run time
PROGRESS_LOGGING_INTERVAL = PROGRESS_LOGGING_DEFAULT_INTERVAL
INCREMENTAL_OUTPUT_INTERVAL = INCREMENTAL_OUTPUT_DEFAULT_INTERVAL


##################################
# IMAGE DATA

IMAGE_PATH = 'black512.png'
IMAGE = Image.open(IMAGE_PATH)
IMAGE_WIDTH, IMAGE_HEIGHT = IMAGE.size
IMAGE_BOUNDING_BOX = ((0, 0), (IMAGE_WIDTH-1, IMAGE_HEIGHT-1))
PIXELS = IMAGE.load()
DRAW = ImageDraw.Draw(IMAGE)

MAX_PARTICLE_INJECT_INNER_RADIUS = max(IMAGE_WIDTH, IMAGE_HEIGHT) // 4 # inner radius for injection can be no more than 1/2 way from the center to the farthest edge
# NOTE: the above assumes the seed is centered in either X or Y

##################################
# PLANT DATA

SEED_RADIUS = 4 

##################################
# TEXT FORMATTING

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

##################################
##################################
##################################
# MAIN

def main():
    particle_inject_center = pg.set_up_plant_seed(IMAGE, SEED_RADIUS, COLOR_PLANT)

    particle_inject_inner_radius, particle_inject_outer_radius, particle_max_movement_radius = pg.get_particle_action_radii_from_base_radius(
        SEED_RADIUS,
        PARTICLE_INJECTION_MIN_RADIUS_FACTOR,
        PARTICLE_INJECTION_MAX_RADIUS_FACTOR,
        PARTICLE_MOVEMENT_MAX_RADIUS_EXTENSION,
        MAX_PARTICLE_INJECT_INNER_RADIUS
        )

    tmark_first, tmark_last, tmark_cur = time.time(), time.time(), time.time()

    particles = pg.setup_particle_list(PARTICLE_COUNT, particle_inject_center, particle_inject_inner_radius, particle_inject_outer_radius, IMAGE_BOUNDING_BOX)
    debug(f"{len(particles)} particles injected")
    debug(f"particles: {particles}")

    # create incremental output file base name, based on growth size and timestamp
    incremental_output_file_base = f"plant_{GROW_AMOUNT}_{tmark_first}_incr"

    # MAIN LOOP
    ## initialize counters for moves and growth, and initialize plant radius
    growth_counter = 0
    loop_counter = 0
    incremental_output_counter = 0
    plant_radius = SEED_RADIUS
    ## while the plant is growing, get a particle, move it, and append it back on the list; handle growth and out-of-bounds replacement as needed
    while growth_counter < GROW_AMOUNT:
        loop_counter += 1
        particle = particles.pop(0)
        debug(f"acting on particle {particle}", DEBUG_EXTREME)

        if DO_PARTICLE_TRACING:
            PIXELS[particle[0],particle[1]] = COLOR_PARTICLE_TRACE

        particle = pg.move_particle(particle)

        if pg.is_adjacent_to_live_pixel(particle, PIXELS, DEAD_COLORS):
            pg.grow_at(particle, PIXELS)
            growth_counter += 1
            growth_radius = pu.distance_between(particle_inject_center,particle)
            if growth_radius > plant_radius:
                plant_radius = growth_radius
                particle_inject_inner_radius, particle_inject_outer_radius, particle_max_movement_radius = pg.get_particle_action_radii_from_base_radius(
                    plant_radius,
                    PARTICLE_INJECTION_MIN_RADIUS_FACTOR,
                    PARTICLE_INJECTION_MAX_RADIUS_FACTOR,
                    PARTICLE_MOVEMENT_MAX_RADIUS_EXTENSION,
                    MAX_PARTICLE_INJECT_INNER_RADIUS
                    )

            new_particle = pg.injected_particle(particle_inject_center, particle_inject_inner_radius, particle_inject_outer_radius, IMAGE_BOUNDING_BOX)
            particles.append(new_particle)
            if DO_PROGRESS_LOGGING and growth_counter % PROGRESS_LOGGING_INTERVAL == 0:
                tmark_cur = time.time()
                print(f"growth_counter: {growth_counter}/{GROW_AMOUNT}, {int((tmark_cur - tmark_last) * 1000)} ms elapsed for that increment")
                tmark_last = tmark_cur
            if DO_INCREMENTAL_OUTPUT and growth_counter % INCREMENTAL_OUTPUT_INTERVAL == 0:
                incremental_output_counter += 1
                incremental_output_path = f"greenhouse/{incremental_output_file_base}.png"
                if DO_INCREMENTAL_OUTPUT_SEPARATED:
                    incremental_output_path = f"greenhouse/{incremental_output_file_base}_{lpad(incremental_output_counter,4)}.png"
                print(f"Saving incremental output to {incremental_output_path}")
                IMAGE.save(incremental_output_path)
        else:
            particle_distance = pu.distance_between(particle_inject_center,particle)
            if particle_distance > particle_max_movement_radius:
                particle = pg.injected_particle(particle_inject_center, particle_inject_inner_radius, particle_inject_outer_radius, IMAGE_BOUNDING_BOX)
            particles.append(particle)
            if DO_PARTICLE_TRACING:
                PIXELS[particle[0],particle[1]] = COLOR_PARTICLE_CUR

    total_elapsed_s = int((time.time() - tmark_first))
    final_output_path = f"greenhouse/plant_{GROW_AMOUNT}_{tmark_first}_{total_elapsed_s}.png"
    IMAGE.save(final_output_path)
    print(f"Done. Total elapsed time for plant generation: {total_elapsed_s} s")
    print(f"Image saved to {final_output_path}")

if __name__ == "__main__":
    main()