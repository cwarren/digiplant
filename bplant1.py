from PIL import Image, ImageDraw
import random
import time
import planar_utils as pu

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
# FUNCTIONS - plant growth stuff

def is_adjacent_to_live_pixel(point, pixels, dead_colors):
    """
    Determine if the given point is adjacent to a live pixel, where 'live' is defined as a pixel that has a color value that's not in the DEAD_COLORS list

    Parameters:
    - point: an (x,y) tuple, using an image orientation of the plane (i.e. upper left is 0,0)
    - pxs: a grid of pixel values, using an image orientation of the plane (i.e. upper left is 0,0)

    Returns:
    - True if the point is adjacent to a live pixel, False otherwise
    """
    adjacent_points = pu.get_adjacent_points(point)
    for adj_point in adjacent_points:
        try:
            # Check if the adjacent point is within the image bounds
            # NOTE: color check uses [:3] since the source has an alpha channel that we don't care about
            if pixels[adj_point][:3] not in dead_colors:
                return True
        except IndexError:
            # If adj_point is out of image bounds, ignore it
            continue
    return False

def move_particle(point, strategy = 'FULL_RANDOM_DRIFT'):
    """
    get a moved version of the given point according to the given strategy.

    Parameters:
    - point: an (x,y) tuple, using an image orientation of the plane (i.e. upper left is 0,0
    - strategy: the drift strategy to use. Options are:
    - 'FULL_RANDOM_DRIFT': drift the point to a randomly chosen adjacent (8-box) one

    Returns:
    - a point that has been moved according to the given strategy
    """
    if strategy == 'FULL_RANDOM_DRIFT':
        adjacent_points = pu.get_adjacent_points(point)
        # Choose one of the adjacent points at random
        point = random.choice(adjacent_points)
        
    return pu.constrain_point_to_bounding_box(point,IMAGE_BOUNDING_BOX)

def grow_at(point, pixels, strategy = 'DEPOSIT'):
    """
    grow a plant at the given point according to the given strategy.

    Parameters:
    - point: an (x,y) tuple, using an image orientation of the plane (i.e. upper left is 0,0
    - strategy: the growth strategy to use. Options are:
    - 'DEPOSIT': convert a single pixel at the given point into part of the plant

    Returns:
    - None
    """
    if strategy == 'DEPOSIT':
        pixels[point[0],point[1]] = COLOR_PLANT

def set_up_plant_seed(image, seed_radius, fill_color):
    """
    Set up the plant seed.

    Returns:
    - an (x,y) tuple representing the center of the plant seed
    """
    # seedx, seedy = IMAGE_WIDTH // 2, IMAGE_HEIGHT - 1
    # seed_left_up_point = (seedx - SEED_RADIUS, seedy - SEED_RADIUS)
    # seed_right_down_point = (seedx + SEED_RADIUS, seedy + SEED_RADIUS)
    # DRAW.ellipse([seed_left_up_point, seed_right_down_point], outline=COLOR_PLANT, fill=COLOR_PLANT)
    # seed_center = (seedx, seedy)
    # return seed_center
    im_w, im_h = image.size
    draw = ImageDraw.Draw(image)
    seedx, seedy = im_w // 2, im_h - 1
    seed_left_up_point = (seedx - seed_radius, seedy - seed_radius)
    seed_right_down_point = (seedx + seed_radius, seedy + seed_radius)
    draw.ellipse([seed_left_up_point, seed_right_down_point], outline=fill_color, fill=fill_color)
    seed_center = (seedx, seedy)
    return seed_center

def get_particle_action_radii_from_base_radius(base_radius, inner_radius_factor, outer_radius_factor, movement_radius_extension, max_inner_radius):
    """
    Get a list of particle radii, given the base radius.

    Parameters:
    - base_radius: the base radius to use

    Returns:
    - a list of particle radii: inject_inner_radius, inject_outer_radius, and max_movement_radius
    """
    # particle_inject_inner_radius = min(MAX_PARTICLE_INJECT_INNER_RADIUS, base_radius * PARTICLE_INJECTION_MIN_RADIUS_FACTOR)
    # particle_inject_outer_radius = base_radius * PARTICLE_INJECTION_MAX_RADIUS_FACTOR
    # particle_max_movement_radius = particle_inject_outer_radius + PARTICLE_MOVEMENT_MAX_RADIUS_EXTENSION
    particle_inject_inner_radius = min(max_inner_radius, base_radius * inner_radius_factor)
    particle_inject_outer_radius = base_radius * outer_radius_factor
    particle_max_movement_radius = particle_inject_outer_radius + movement_radius_extension
    return particle_inject_inner_radius, particle_inject_outer_radius, particle_max_movement_radius

def injected_particle(inject_center, inner_radius, outer_radius, image_bounds):
    """
    Get an (x,y) tuple representing a particle that has been injected into the growing medium

    Parameters:
    - center: an (x,y) tuple representing the center of the injection area
    - inner_radius: the inner radius of the injection ring
    - outer_radius: the outer radius of the injection ring

    Returns:
    - an (x,y) tuple representing the center of the injected particle, where x and y are integers
    """
    p = pu.get_random_point_in_ring(inject_center, inner_radius, outer_radius)
    while not pu.is_point_in_rect(p, image_bounds):
        p = pu.get_random_point_in_ring(inject_center, inner_radius, outer_radius)
    return p

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
    particle_inject_center = set_up_plant_seed(IMAGE, SEED_RADIUS, COLOR_PLANT)

    particle_inject_inner_radius, particle_inject_outer_radius, particle_max_movement_radius = get_particle_action_radii_from_base_radius(
        SEED_RADIUS,
        PARTICLE_INJECTION_MIN_RADIUS_FACTOR,
        PARTICLE_INJECTION_MAX_RADIUS_FACTOR,
        PARTICLE_MOVEMENT_MAX_RADIUS_EXTENSION,
        MAX_PARTICLE_INJECT_INNER_RADIUS
        )

    tmark_first, tmark_last, tmark_cur = time.time(), time.time(), time.time()

    particles = []
    for i in range(PARTICLE_COUNT):
        particles.append(injected_particle(particle_inject_center, particle_inject_inner_radius, particle_inject_outer_radius, IMAGE_BOUNDING_BOX))
    debug(f"{len(particles)} particles injected")
    debug(f"particles: {particles}")

    # create incremental output file base name, based on growth size and timestamp
    incremental_output_file_base = f"plant_{GROW_AMOUNT}_{tmark_first}_incr"

    # main loop
    ## initialize counters for moves and growth
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

        particle = move_particle(particle)

        if is_adjacent_to_live_pixel(particle, PIXELS, DEAD_COLORS):
            grow_at(particle, PIXELS)
            growth_counter += 1
            growth_radius = pu.distance_between(particle_inject_center,particle)
            if growth_radius > plant_radius:
                plant_radius = growth_radius
                particle_inject_inner_radius, particle_inject_outer_radius, particle_max_movement_radius = get_particle_action_radii_from_base_radius(
                    plant_radius,
                    PARTICLE_INJECTION_MIN_RADIUS_FACTOR,
                    PARTICLE_INJECTION_MAX_RADIUS_FACTOR,
                    PARTICLE_MOVEMENT_MAX_RADIUS_EXTENSION,
                    MAX_PARTICLE_INJECT_INNER_RADIUS
                    )

            new_particle = injected_particle(particle_inject_center, particle_inject_inner_radius, particle_inject_outer_radius, IMAGE_BOUNDING_BOX)
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
                particle = injected_particle(particle_inject_center, particle_inject_inner_radius, particle_inject_outer_radius, IMAGE_BOUNDING_BOX)
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