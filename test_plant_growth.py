import pytest
import math
from PIL import Image
import planar_utils as pu
from plant_growth import *

############################
# TEST SUPPORT

def get_test_image(x=4,y=4,bg_rgb = (0,0,0)):
    image = Image.new('RGB', (x, y), bg_rgb)
    return image
    # pixels =  image.load()
    # bounding_box = ((0,0),image.size)
    # return pixels, bounding_box

############################
# TESTS

def test_injected_particle_ring():
    inject_center = (50, 50)
    inner_radius = 10
    outer_radius = 20
    image_bounds = ((0, 0), (100, 100))

    # Call the function with actual dependencies
    particle = injected_particle_ring(inject_center, inner_radius, outer_radius, image_bounds)
    
    # Ensure the returned particle is within the image bounds
    assert pu.is_point_in_rect(particle, image_bounds), "The particle is not within the image bounds"
    
    # Calculate the distance from the particle to the injection center to ensure it's within the specified ring
    distance_from_center = pu.distance_between(inject_center, particle)
    
    print(f"inject_center: {inject_center}")
    print(f"inner_radius: {inner_radius}")
    print(f"outer_radius: {outer_radius}")
    print(f"particle: {particle}")
    print(f"distance_from_center: {distance_from_center}")
    
    # NOTE: the -1 and +1 are there to handle edge cases caused by integer casting of points
    assert inner_radius-1 <= distance_from_center <= outer_radius+1, "The particle is not within the specified ring radius"
    
    # Check if particle coordinates are integers
    assert isinstance(particle[0], int) and isinstance(particle[1], int), "Particle coordinates are not integers"


def test_setup_particle_list():
    num_particles = 5
    inject_center = (50, 50)
    inject_inner_radius = 10
    inject_outer_radius = 20
    bounding_box = ((0, 0), (100, 100))
    
    particles = setup_particle_list(num_particles, inject_center, inject_inner_radius, inject_outer_radius, bounding_box)
    
    # Check if the correct number of particles are created
    assert len(particles) == num_particles, f"Expected {num_particles} particles, got {len(particles)}"


@pytest.mark.parametrize("point_to_test, live_point, gridx, gridy, expected_check", [
    ((1,1),(0, 1),4,4,True), # a live pixel adjacent to (1, 1)
    ((2,2),(0, 1),4,4,False), # no adjacent live pixels
    ((0,0),(0, 1),4,4,True), # live pixel adjacent, some adjacencies out of bounds
])
def test_is_adjacent_to_live_pixel(point_to_test, live_point, gridx, gridy, expected_check):
    dead_colors = [(0, 0, 0), (255, 255, 255)]  # Assuming black and white are "dead" colors
    live_color = (128, 128, 128)  # Example of a "live" color

    # Setup a pixels grid with a live pixel adjacent to the point being checked
    image = get_test_image(gridx, gridy)
    pixels = image.load()
    bounds =  ((0,0),image.size)
    pixels[live_point] = live_color
    
    assert is_adjacent_to_live_pixel(point_to_test, pixels, dead_colors, bounds) == expected_check


@pytest.mark.parametrize("point,bounding_box,expected_bounds", [
    ((5, 5), ((0, 0), (10, 10)), ((0, 0), (10, 10))),
    ((0, 0), ((0, 0), (10, 10)), ((0, 0), (10, 10))),
    ((10, 10), ((0, 0), (10, 10)), ((0, 0), (10, 10))),
])
def test_move_particle_full_random_drift(point, bounding_box, expected_bounds):
    moved_point = move_particle(point, bounding_box, strategy='FULL_RANDOM_DRIFT')
    # Ensure the moved point is still within the bounding box
    assert expected_bounds[0][0] <= moved_point[0] <= expected_bounds[1][0]
    assert expected_bounds[0][1] <= moved_point[1] <= expected_bounds[1][1]
    # Ensure the point has moved to an adjacent location (or potentially stayed the same if it moved to its original position)
    assert pu.distance_between(point, moved_point) <= math.sqrt(2) + .001, "The point did not move to an adjacent position"


def test_grow_at_deposit():
    point = (4, 4)
    plant_color = (0, 128, 0)  # Example plant color
    image =  get_test_image(7,7,(0,0,0))
    pixels = image.load()

    assert pixels[point] == (0,0,0), "Pixel at point not initially black"
    grow_at(point, pixels, plant_color, strategy='DEPOSIT')
    assert pixels[point] == plant_color, "Pixel at point did not change to plant color"


def test_setup_plant_seed_bottom_center():
    im_w, im_h = 100, 100  # Example image size
    image = get_test_image(im_w, im_h,(255,255,255))
    seed_radius = 10
    fill_color = (0, 128, 0)  # Example fill color (green)

    seed_center = setup_plant_seed_bottom_center(image, seed_radius, fill_color)
    expected_seed_center = (im_w // 2, im_h - 1)

    assert seed_center == expected_seed_center, "Seed center is not at the expected position"

    # To further validate, check if the pixel at the seed center is the fill color
    pixels = image.load()
    assert pixels[seed_center] == fill_color, "Seed center pixel color does not match the fill color"


@pytest.mark.parametrize("base_radius,inner_radius_factor,outer_radius_factor,movement_radius_extension,max_inner_radius,expected", [
    (10, 0.5, 1.5, 5, 20, (5, 15, 20)),  # Case where max_inner_radius is not limiting
    (10, 0.8, 2.0, 10, 5, (5, 20, 30)),  # Case where max_inner_radius is limiting
    (10, 1.0, 2.0, 0, 15, (10, 20, 20)),  # Case with no movement extension
])
def test_get_particle_action_radii_from_base_radius(base_radius, inner_radius_factor, outer_radius_factor, movement_radius_extension, max_inner_radius, expected):
    assert get_particle_action_radii_from_base_radius(base_radius, inner_radius_factor, outer_radius_factor, movement_radius_extension, max_inner_radius) == expected


def test_get_particle_within_movement_bounds_ring():
    
    inject_center = (50, 50)
    inject_inner_radius = 5
    inject_outer_radius = 10
    max_movement_radius = 20
    bounding_box = ((0, 0), (200, 200))

    particle_within_bounds = (51, 68)
    
    # Case 1: Particle is within movement bounds
    gotten_particle = get_particle_within_movement_bounds_ring(particle_within_bounds, inject_center, inject_inner_radius, inject_outer_radius, max_movement_radius, bounding_box)
    print(f"particle_within_bounds: {particle_within_bounds}")
    print(f"gotten_particle: {gotten_particle}")
    assert particle_within_bounds == gotten_particle, "The original particle should be returned if within movement bounds"

    # Case 2: Particle is outside movement bounds, expect a new particle
    far_particle = (150, 150)
    new_particle = get_particle_within_movement_bounds_ring(far_particle, inject_center, inject_inner_radius, inject_outer_radius, max_movement_radius, bounding_box)
    assert new_particle != far_particle, "A new particle should be injected if the original is outside movement bounds"
    assert pu.is_point_in_rect(new_particle, bounding_box), "The new particle should be within the bounding box"









