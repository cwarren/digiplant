from PIL import Image, ImageDraw
import random
import math
import time

##################################
# CONFIGS / CONSTANTS

USING_DEBUG_LEVEL = 1
DEBUG_BASE = 1
DEBUG_EXTREME = 5
def debug(msg, level=DEBUG_BASE):
    if level <= USING_DEBUG_LEVEL:
        print(msg)

DO_PARTICLE_TRACING = True
DO_PROGRESS_LOGGING = True
PROGRESS_LOGGING_DEFAULT_INTERVAL = 100
DO_INCREMENTAL_OUTPUT = True
INCREMENTAL_OUTPUT_DEFAULT_INTERVAL = 1000

COLOR_BG = (0,0,0)
COLOR_PARTICLE_TRACE = (128,0,0)
COLOR_PARTICLE_CUR = (0,0,128)
COLOR_PLANT = (0,128,0)
DEAD_COLORS = [COLOR_BG, COLOR_PARTICLE_TRACE, COLOR_PARTICLE_CUR]

##################################
# COMMAND LINE CONFIGS

# GROW_AMOUNT - number of times to grow the plant by 1 step
# PARTICLE_COUNT - how many particles to keep active at once (more means faster run and denser growth)
# PARTICLE_INJECTION_MAX_RADIUS_FACTOR - as a multiplier of the maximum radius of the plant (i.e the growth point furthest from the center of the seed); the larger, the more spreading the plant and the longer the run time
# PARTICLE_INJECTION_MIN_RADIUS_FACTOR - as a multiplier of the maximum radius of the plant (i.e the growth point furthest from the center of the seed); the larger, the more spreading the plant and the longer the run time
# particles are injected in a ring formed by the difference between the max radius and min radius
# PARTICLE_MOVEMENT_MAX_RADIUS_EXTENSION - as an addition to the PARTICLE_INJECTION_RADIUS; the larger, the more spreading the plant and the longer the run time
# PROGRESS_LOGGING_INTERVAL - print progress report to screen after this many growth actions
# INCREMENTAL_OUTPUT_INTERVAL - output image to file after this many growth actions

GROW_AMOUNT = 300 # number of times to grow the plant by 1 step
PARTICLE_COUNT = 5 # how many particles to keep active at once (more means faster run and denser growth) (20 is a decent base)
PARTICLE_INJECTION_MAX_RADIUS_FACTOR = 2 # as a multiplier of the maximum radius of the plant (i.e the growth point furthest from the center of the seed); the larger, the more spreading the plant and the longer the run time
PARTICLE_INJECTION_MIN_RADIUS_FACTOR = 1 # as a multiplier of the maximum radius of the plant (i.e the growth point furthest from the center of the seed); the larger, the more spreading the plant and the longer the run time
# particles are injected in a ring formed by the difference between the max radius and min radius
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

##################################
# PLANT DATA

SEED_RADIUS = 4 



##################################
# FUNCTIONS - general planar stuff

def distance_between(p1,p2):
    """
    Calculate the Euclidean distance between two points (x1, y1) and (x2, y2).

    Parameters:
    - p1: (x,y) tuple; coordinates of the first point
    - p2: (x,y) tuple; coordinates of the first point

    Returns:
    - The Euclidean distance between the two points.
    """
    x1, y1 = p1
    x2, y2 = p2
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def angle_between(p1,p2):
    """
    Calculate the angle between two points (x1, y1) and (x2, y2).

    Parameters:
    - p1: (x,y) tuple; coordinates of the first point
    - p2: (x,y) tuple; coordinates of the second point

    Returns:
    - The angle between the two points in radians.
    """
    x1, y1 = p1
    x2, y2 = p2
    delta_x = x2 - x1
    delta_y = y2 - y1
    angle = math.atan2(delta_y, delta_x)
    return angle

def polar_to_cartesian(center, r, theta):
    """
    Convert polar coordinates to cartesian coordinates, given a center point.

    Parameters:
    - center: (x,y) tuple; coordinates of the center point
    - r: float; radial distance from the center point
    - theta: float; angle from the center point in radians

    Returns:
    - A (x,y) tuple representing the cartesian coordinates, where x and y are integers
    """
    centerX, centerY = center
    x = r * math.cos(theta)
    y = r * math.sin(theta)
    cartesianX = centerX + x
    cartesianY = centerY + y
    return (int(cartesianX), int(cartesianY))

def constrain_point_to_bounding_box(point, bounding_box):
    """
    Constrain the point coordinates to be within the given bounding box; a dimension that is out of bounds is set to the closest edge of the bounding box.

    Parameters:
    - point: an (x,y) tuple, using an image orientation of the plane (i.e. upper left is 0,0)
    - bounding_box: Tuple of (upper left point, lower right point) representing the bounding box.

    Returns:
    - a point with the x and y values within the bounding box
    """
    x, y = point
    (min_x, min_y), (max_x, max_y) = bounding_box
    constrained_x = max(min_x, min(x, max_x))
    constrained_y = max(min_y, min(y, max_y))
    return (constrained_x, constrained_y)

def constrain_point_to_circle(point, center, radius):
    """
    Constrain the point coordinates to be within the given circle; a dimension that is out of bounds is set to the closest point on the edge of the circle.
    
    Parameters:
    - point: an (x,y) tuple, using an image orientation of the plane (i.e. upper left is 0,0)
    - center: an (x,y) tuple, using an image orientation of the plane (i.e. upper left is 0,0)
    - radius: the radius of the circle

        Returns:
    - a point with the x and y values within the circle
    """
    distance = distance_between(point, center)
    if distance <= radius: # The point is already within the circle
        return point
    else:
        angle = angle_between(center, point)
        return polar_to_cartesian(center, radius, angle)

def get_adjacent_points(point):
    """
    Get the 8 adjacent coordinates surrounding the given x, y coordinate.

    Parameters:
    - point: an (x,y) tuple, using an image orientation of the plane (i.e. upper left is 0,0

    Returns:
    - A tuple of tuples, each representing an (x, y) coordinate of an adjacent point.
    """
    x, y = point
    return (
        (x - 1, y - 1),  # Top-left
        (x, y - 1),      # Top-center
        (x + 1, y - 1),  # Top-right
        (x - 1, y),      # Left
        (x + 1, y),      # Right
        (x - 1, y + 1),  # Bottom-left
        (x, y + 1),      # Bottom-center
        (x + 1, y + 1)   # Bottom-right
    )

def get_random_point_in_circle(center, radius):
    """
    Get a random point within the given circle. 

    Parameters:
    - center: an (x,y) tuple, using an image orientation of the plane (i.e. upper left is 0,0
    - radius: the radius of the circle

    Returns:
    - a random point within the circle as an (x,y) tuple, where the x and y values are integers
    """
    angle = random.uniform(0, 2 * math.pi)  # Random angle
    r = radius * math.sqrt(random.uniform(0, 1))  # Random radius, sqrt for uniform distribution
    x,y = polar_to_cartesian(center, r, angle)
    return (int(x), int(y))

def get_random_point_in_ring(center, min_radius, max_radius):
    """
    Get a random point within the given circle. 

    Parameters:
    - center: an (x,y) tuple, using an image orientation of the plane (i.e. upper left is 0,0
    - min_radius: the minimum, inner radius of the ring
    - max_radius: the maximum, outer radius of the ring

    Returns:
    - a point within the ring as an (x,y) tuple, where the x and y values are integers
    """
    angle = random.uniform(0, 2 * math.pi)
    r = random.uniform(min_radius, max_radius)
    return polar_to_cartesian(center, r, angle)

def is_point_in_rect(point, box):
    """
    Check if the given point is within the given rectangle.

    Parameters:
    - point: an (x,y) tuple, using an image orientation of the plane (i.e. upper left is 0,0
    - box: a tuple of (upper left point, lower right point) representing the bounding box.

    Returns:
    - True if the point is within the rectangle, False otherwise
    """
    (x, y) = point
    (upper_left, lower_right) = box    
    (x_min, y_min) = upper_left
    (x_max, y_max) = lower_right    
    if x_min <= x <= x_max and y_min <= y <= y_max:
        return True
    else:
        return False

def get_random_point_in_rect(box):
    """
    Get a random point within the given rectangle.

    Parameters:
    - box: a tuple of (upper left point, lower right point) representing the bounding box.

    Returns:
    - a point within the rectangle as an (x,y) tuple, where the x and y values are integers
    """
    upper_left, lower_right = box
    x_min, y_min = upper_left
    x_max, y_max = lower_right    
    x = random.uniform(x_min, x_max)
    y = random.uniform(y_min, y_max)
    return (int(x), int(y))

def filter_coordinates_within_bounding_box(coordinates, box):
    """
    Filters a list of (x, y) coordinates to return only those within a given bounding box.

    Parameters:
    - coordinates: List of (x, y) tuples representing the coordinates.
    - bounding_box: a tuple of (upper left point, lower right point) representing the bounding box.

    Returns:
    - List of (x, y) tuples from the provided coordinates list that are within the bounding box. NOTE: this does not constrain the coordinates to be within the bounding box, but filters the provided list to only include coordinates that are within the bounding box.
    """
    min_x, min_y = box[0]
    max_x, max_y = box[1]
    filtered_coordinates = [
        (x, y) for x, y in coordinates
        if min_x <= x <= max_x and min_y <= y <= max_y
    ]
    return filtered_coordinates

##################################
# FUNCTIONS - plant growth stuff

def is_adjacent_to_live_pixel(point):
    """
    Determine if the given point is adjacent to a live pixel, where 'live' is defined as a pixel that has a color value that's not in the DEAD_COLORS list

    Parameters:
    - point: an (x,y) tuple, using an image orientation of the plane (i.e. upper left is 0,0

    Returns:
    - True if the point is adjacent to a live pixel, False otherwise
    """
    adjacent_points = get_adjacent_points(point)
    for adj_point in adjacent_points:
        try:
            # Check if the adjacent point is within the image bounds
            # NOTE: color check uses [:3] since the source has an alpha channel that we don't care about
            if PIXELS[adj_point][:3] not in DEAD_COLORS:
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
        adjacent_points = get_adjacent_points(point)
        # Choose one of the adjacent points at random
        point = random.choice(adjacent_points)
        
    return constrain_point_to_bounding_box(point,IMAGE_BOUNDING_BOX)

def grow_at(point, strategy = 'DEPOSIT'):
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
        PIXELS[point[0],point[1]] = COLOR_PLANT

def set_up_plant_seed():
    """
    Set up the plant seed.

    Returns:
    - an (x,y) tuple representing the center of the plant seed
    """
    seedx, seedy = IMAGE_WIDTH // 2, IMAGE_HEIGHT - 1
    seed_left_up_point = (seedx - SEED_RADIUS, seedy - SEED_RADIUS)
    seed_right_down_point = (seedx + SEED_RADIUS, seedy + SEED_RADIUS)
    DRAW.ellipse([seed_left_up_point, seed_right_down_point], outline=COLOR_PLANT, fill=COLOR_PLANT)
    seed_center = (seedx, seedy)
    return seed_center

def get_particle_action_radii_from_base_radius(base_radius):
    """
    Get a list of particle radii, given the base radius.

    Parameters:
    - base_radius: the base radius to use

    Returns:
    - a list of particle radii: inject_inner_radius, inject_outer_radius, and max_movement_radius
    """
    particle_inject_inner_radius = base_radius * PARTICLE_INJECTION_MIN_RADIUS_FACTOR
    particle_inject_outer_radius = base_radius * PARTICLE_INJECTION_MAX_RADIUS_FACTOR
    particle_max_movement_radius = particle_inject_outer_radius + PARTICLE_MOVEMENT_MAX_RADIUS_EXTENSION
    return particle_inject_inner_radius, particle_inject_outer_radius, particle_max_movement_radius

def injected_particle(inject_center, inner_radius, outer_radius):
    """
    Get an (x,y) tuple representing a particle that has been injected into the growing medium

    Parameters:
    - center: an (x,y) tuple representing the center of the injection area
    - inner_radius: the inner radius of the injection ring
    - outer_radius: the outer radius of the injection ring

    Returns:
    - an (x,y) tuple representing the center of the injected particle, where x and y are integers
    """
    p = get_random_point_in_ring(inject_center, inner_radius, outer_radius)
    while not is_point_in_rect(p, IMAGE_BOUNDING_BOX):
        p = get_random_point_in_ring(inject_center, inner_radius, outer_radius)
    return p



##################################
##################################
##################################
# MAIN

def main():
    particle_inject_center = set_up_plant_seed()
    particle_inject_inner_radius, particle_inject_outer_radius, particle_max_movement_radius = get_particle_action_radii_from_base_radius(SEED_RADIUS)

    tmark_first = time.time()
    tmark_last = time.time()
    tmark_cur = time.time()

    particles = []
    for i in range(PARTICLE_COUNT):
        particles.append(injected_particle(particle_inject_center, particle_inject_inner_radius, particle_inject_outer_radius))
    debug(f"{len(particles)} particles injected")
    debug(f"particles: {particles}")

    # create incremental output file name, based on growth size and timestamp
    incremental_output_path = f"greenhouse/plant_{GROW_AMOUNT}_{tmark_first}_incr.png"

    # main loop
    ## initialize counters for moves and growth
    growth_counter = 0
    loop_counter = 0
    plant_radius = SEED_RADIUS
    ## while the plant is growing, get a particle, move it, and append it back on the list; handle growth and out-of-bounds replacement as needed
    while growth_counter < GROW_AMOUNT:
        loop_counter += 1
        particle = particles.pop(0)
        debug(f"acting on particle {particle}", DEBUG_EXTREME)

        if DO_PARTICLE_TRACING:
            PIXELS[particle[0],particle[1]] = COLOR_PARTICLE_TRACE

        particle = move_particle(particle)

        if is_adjacent_to_live_pixel(particle):
            grow_at(particle)
            growth_counter += 1
            growth_radius = distance_between(particle_inject_center,particle)
            if growth_radius > plant_radius:
                plant_radius = growth_radius
                particle_inject_inner_radius, particle_inject_outer_radius, particle_max_movement_radius = get_particle_action_radii_from_base_radius(plant_radius)
            new_particle = injected_particle(particle_inject_center, particle_inject_inner_radius, particle_inject_outer_radius)
            particles.append(new_particle)
            if DO_PROGRESS_LOGGING and growth_counter % PROGRESS_LOGGING_INTERVAL == 0:
                tmark_cur = time.time()
                print(f"growth_counter: {growth_counter}/{GROW_AMOUNT}, {int((tmark_cur - tmark_last) * 1000)} ms elapsed for that increment")
                tmark_last = tmark_cur
            if DO_INCREMENTAL_OUTPUT and growth_counter % INCREMENTAL_OUTPUT_INTERVAL == 0:
                print(f"TODO: Saving incremental output to {incremental_output_path}")
        else:
            particle_distance = distance_between(particle_inject_center,particle)
            if particle_distance > particle_max_movement_radius:
                particle = injected_particle(particle_inject_center, particle_inject_inner_radius, particle_inject_outer_radius)
            particles.append(particle)
            if DO_PARTICLE_TRACING:
                PIXELS[particle[0],particle[1]] = COLOR_PARTICLE_CUR

    total_elapsed_ms = int((time.time() - tmark_first) * 1000)
    final_output_path = f"greenhouse/plant_{GROW_AMOUNT}_{tmark_first}_{total_elapsed_ms}.png"
    IMAGE.save(final_output_path)
    print(f"Done. Total elapsed time for plant generation: {total_elapsed_ms} ms")

if __name__ == "__main__":
    main()