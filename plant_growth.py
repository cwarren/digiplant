from PIL import ImageDraw
import planar_utils as pu
import random

def injected_particle_ring(inject_center, inner_radius, outer_radius, image_bounds):
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


def setup_particle_list(num_particles, inject_center, inject_inner_radius, inject_outer_radius, bounding_box):
    """
    Create a list of particles, with each particle having a random position and radius.
    The particles are placed in a ring around the center of the plant, with the ring radius

    Parameters:
    - num_particles: The number of particles to create.
    - inject_params: A tuple of (inject_center (x,y), inject_inner_radius, inject_outer_radius)
    - bounding_box: Tuple of ((min_x, min_y), (max_x, max_y)) representing the bounding box of the injection area (usually the image bounds)

    Returns:
    - A list of particles, each with a random position and radius.
    """
    particles = []
    for _ in range(num_particles):
        particles.append(injected_particle_ring(inject_center, inject_inner_radius, inject_outer_radius, bounding_box))
    return particles

def is_adjacent_to_live_pixel(point, pixels, dead_colors, bounding_box):
    """
    Determine if the given point is adjacent to a live pixel, where 'live' is defined as a pixel that has a color value that's not in the DEAD_COLORS list

    Parameters:
    - point: an (x,y) tuple, using an image orientation of the plane (i.e. upper left is 0,0); NOTE: negative values will wrap!
    - pxs: a grid of pixels as loaded from an image, using an image orientation of the plane (i.e. upper left is 0,0)

    Returns:
    - True if the point is adjacent to a live pixel, False otherwise
    """
    adjacent_points = pu.get_adjacent_points(point)
    adjacent_points = pu.filter_points_within_bounding_box(adjacent_points, bounding_box)
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

def move_particle(point, bounding_box, strategy = 'FULL_RANDOM_DRIFT'):
    """
    get a moved version of the given point according to the given strategy.

    Parameters:
    - point: an (x,y) tuple, using an image orientation of the plane (i.e. upper left is 0,0)
    - bounding_box: Tuple of ((min_x, min_y), (max_x, max_y)) reprenting the limits of movement
    - strategy: the drift strategy to use. Options are:
    - 'FULL_RANDOM_DRIFT': drift the point to a randomly chosen adjacent (8-box) one

    Returns:
    - a point that has been moved according to the given strategy
    """
    if strategy == 'FULL_RANDOM_DRIFT':
        adjacent_points = pu.get_adjacent_points(point)
        # Choose one of the adjacent points at random
        point = random.choice(adjacent_points)
        
    return pu.constrain_point_to_bounding_box(point,bounding_box)

def grow_at(point, pixels, plant_color, strategy = 'DEPOSIT'):
    """
    grow a plant at the given point according to the given strategy.

    Parameters:
    - point: an (x,y) tuple, using an image orientation of the plane (i.e. upper left is 0,0
    - pixels: a grid of pixel values, using an image orientation of the plane (i.e. upper left is 0,0)
    - strategy: the growth strategy to use. Options are:
    - 'DEPOSIT': convert a single pixel at the given point into part of the plant

    Returns:
    - None
    """
    if strategy == 'DEPOSIT':
        pixels[point[0],point[1]] = plant_color

def setup_plant_seed_bottom_center(image, seed_radius, fill_color):
    """
    Set up the plant seed.

    Parameters:
    - image: the image to draw on
    - seed_radius: the radius of the plant seed
    - fill_color: the color to fill the plant seed with

    Returns:
    - an (x,y) tuple representing the center of the plant seed
    """
    im_w, im_h = image.size
    draw = ImageDraw.Draw(image)
    seedx, seedy = im_w // 2, im_h - 1
    seed_left_up_point = (seedx - seed_radius, seedy - seed_radius)
    seed_right_down_point = (seedx + seed_radius, seedy + seed_radius)
    draw.ellipse([seed_left_up_point, seed_right_down_point], outline=fill_color, fill=fill_color)
    seed_center = (seedx, seedy)
    return seed_center


def get_particle_action_radii_from_base_radius(base_radius, plant_genetics):
    """
    Get a list of particle radii, given the base radius.

    Parameters:
    - base_radius: the base radius to use
    - inner_radius_factor: the factor to use for the inner radius; a multiplier of the base radius
    - outer_radius_factor: the factor to use for the outer radius; a multiplier of the base radius
    - movement_radius_extension: the amount beyond the outer radius that a particle may be moved
    - max_inner_radius: the maximum inner radius to use

    Returns:
    - a list of particle radii: inject_inner_radius, inject_outer_radius, and max_movement_radius
    """
    particle_inject_inner_radius = min(plant_genetics['max_particle_inject_inner_radius'], base_radius * plant_genetics['particle_injection_min_radius_factor'])
    particle_inject_outer_radius = base_radius * plant_genetics['particle_injection_max_radius_factor']
    particle_max_movement_radius = particle_inject_outer_radius + plant_genetics['particle_movement_max_radius_extension']
    return particle_inject_inner_radius, particle_inject_outer_radius, particle_max_movement_radius


def get_particle_within_movement_bounds_ring(orig_particle, inject_center, inject_inner_radius, inject_outer_radius, max_movement_radius, bounding_box):
    """
    Determine if the given particle is within the movement bounds of the given particle based on the inject center and max movement radius. If so, return it, and if not return a newly injected particle.

    Parameters:
    - particle: a particle object, an (x,y) tuple where x and y are integer cooridinates on a grid with 0,0 in the upper left
    - particle_inject_center: the center of the particle injection ring, an (x,y) tuple where x and y are integer cooridinates on a grid with 0,0 in the upper left
    - particle_inject_inner_radius: the inner radius of the particle injection ring
    - particle_inject_outer_radius: the outer radius of the particle injection ring
    - particle_max_movement_radius: the maximum movement radius of the particle from the inject center
    - bounding_box: the bounding box of the grid that contains the particle, a tuple of ((min_x, min_y), (max_x, max_y))

    Returns:
    - a particle object that is within the movement bounds; either the original particle, or a new or a newly injected particle
    """
    particle_distance = pu.distance_between(inject_center,orig_particle)
    if particle_distance > max_movement_radius:
        return injected_particle_ring(inject_center, inject_inner_radius, inject_outer_radius, bounding_box)
    return orig_particle