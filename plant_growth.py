import planar_utils as pu

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