import pytest
import math
from planar_utils import *

def test_distance_between():
    # Test with known distance
    assert distance_between((0, 0), (3, 4)) == 5
    # Test with same point (should be 0)
    assert distance_between((1, 1), (1, 1)) == 0


@pytest.mark.parametrize("p1, p2, expected", [
    ((0, 0), (1, 0),0), # horizontal points
    ((0, 0), (0, 1),math.pi / 2), # vertical points
    ((0, 0), (1, 1),math.pi / 4) # 45 degree points
])
def test_angle_between(p1, p2, expected):
    assert math.isclose(angle_between(p1, p2), expected, rel_tol=1e-9)


@pytest.mark.parametrize("r,theta,expected", [
    (10, math.pi / 2, (0, 10)),  # 90 degrees
    (math.sqrt(2), math.pi / 4, (1, 1))  # 45 degrees, r = sqrt(2) to get (1,1) from (0,0) after converting
])
def test_polar_to_cartesian(r, theta, expected):
    center = (0, 0)
    result = polar_to_cartesian(center, r, theta)
    assert result == expected
    # Additional assertion to check if the result coordinates are integers
    assert isinstance(result[0], int) and isinstance(result[1], int), "The result coordinates are not integers"


def test_constrain_point_to_bounding_box():
    # Test a point outside the bounding box should be constrained to the edge
    bounding_box = ((0, 0), (10, 10))
    point = (-5, 5)
    assert constrain_point_to_bounding_box(point, bounding_box) == (0, 5)


def test_constrain_point_to_circle_inside():
    center = (0, 0)
    radius = 5
    point_inside = (3, 4)  # A point inside the circle, Pythagorean triple ensures it's inside
    # Test that a point inside the circle remains unchanged
    assert constrain_point_to_circle(point_inside, center, radius) == point_inside


def test_constrain_point_to_circle_outside():
    center = (0, 0)
    radius = 5
    point_outside = (10, 10)  # A point clearly outside the circle
    constrained_point = constrain_point_to_circle(point_outside, center, radius)
    # Test that a point outside the circle is brought to the edge
    # This checks that the constrained point is exactly on the circle's radius from the center and is the right angle (45 degrees, pi/4 radians)
    pytest.approx(distance_between(constrained_point, center), 1) == radius # NOTE: the approximation range is so large because the constrained point is integers only
    assert math.isclose(angle_between(center, constrained_point), math.pi / 4)


def test_get_adjacent_points():
    point = (5, 5)
    expected = (
        (4, 4),  # Top-left
        (5, 4),  # Top-center
        (6, 4),  # Top-right
        (4, 5),  # Left
        (6, 5),  # Right
        (4, 6),  # Bottom-left
        (5, 6),  # Bottom-center
        (6, 6)   # Bottom-right
    )
    assert get_adjacent_points(point) == expected


def test_get_random_point_in_circle():
    center = (0, 0)
    radius = 10
    point = get_random_point_in_circle(center, radius)
    
    # Check if the point is within the circle
    dist = distance_between(center, point)
    assert dist <= radius

    # Check if point coordinates are integers
    assert isinstance(point[0], int) and isinstance(point[1], int)


def test_get_random_point_in_ring():
    center = (0, 0)
    min_radius = 5
    max_radius = 10
    point = get_random_point_in_ring(center, min_radius, max_radius)
    
    # Check if the point's coordinates are integers
    assert isinstance(point[0], int) and isinstance(point[1], int), "The coordinates of the point are not integers"
    
    # Check if the point is within the ring
    dist = distance_between(center, point)

    # NOTE: the -1 and +1 are there to handle edge cases caused by integer casting of points
    assert min_radius - 1 <= dist <= max_radius + 1, "The point is not within the specified ring"


def test_get_random_point_in_ring_invalid_radius():
    center = (0, 0)
    min_radius = 10
    max_radius = 5
    with pytest.raises(ValueError):
        get_random_point_in_ring(center, min_radius, max_radius)


@pytest.mark.parametrize("point,box,expected", [
    ((5, 5), ((0, 0), (10, 10)), True),  # Inside
    ((-1, 5), ((0, 0), (10, 10)), False),  # Left outside
    ((5, -1), ((0, 0), (10, 10)), False),  # Top outside
    ((11, 5), ((0, 0), (10, 10)), False),  # Right outside
    ((5, 11), ((0, 0), (10, 10)), False),  # Bottom outside
    ((0, 0), ((0, 0), (10, 10)), True),  # On the upper left edge
    ((10, 10), ((0, 0), (10, 10)), True),  # On the lower right edge
])
def test_is_point_in_rect(point, box, expected):
    assert is_point_in_rect(point, box) == expected


def test_get_random_point_in_rect():
    box = ((0, 0), (10, 10))
    point = get_random_point_in_rect(box)
    
    # Check if the point's coordinates are integers
    assert isinstance(point[0], int) and isinstance(point[1], int), "The coordinates of the point are not integers"
    
    # Extract coordinates for clarity
    x, y = point
    x_min, y_min = box[0]
    x_max, y_max = box[1]
    
    # Check if the point is within the rectangle
    assert x_min <= x <= x_max, "X coordinate is out of the box"
    assert y_min <= y <= y_max, "Y coordinate is out of the box"


def test_filter_points_within_bounding_box():
    coordinates = [(0, 0), (5, 5), (10, 10), (-1, -1), (11, 11)]
    box = ((0, 0), (10, 10))
    expected_filtered_coordinates = [(0, 0), (5, 5), (10, 10)]
    
    filtered_coordinates = filter_points_within_bounding_box(coordinates, box)
    
    assert filtered_coordinates == expected_filtered_coordinates, "Filtered coordinates do not match expected list"



