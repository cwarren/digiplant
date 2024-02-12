import random
import math

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
    if min_radius > max_radius:
        raise ValueError("The minimum radius must be less than the maximum radius")
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