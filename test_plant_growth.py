import pytest
import math
from PIL import Image
import planar_utils as pu
from plant_growth import *

############################
# TEST SUPPORT

def get_test_pixel_grid_and_bounds(x=4,y=4,bg_rgb = (0,0,0)):
    image = Image.new('RGB', (x, y), bg_rgb)
    pixels =  image.load()
    bounding_box = ((0,0),image.size)
    return pixels, bounding_box

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
    pixels, bounds =  get_test_pixel_grid_and_bounds(gridx, gridy)
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






