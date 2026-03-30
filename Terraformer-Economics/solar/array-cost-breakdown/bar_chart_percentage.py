
import sys
import math
import re
import pygame
import os

"""
Y axis max value:

ebos:       $236
module:     $247
officework: $66
other:      $372
sbos:       $30

Well, just set it as 1 to get percent.
"""

# --- User-configurable variables ---


# Path to the image file to select points from (relative to this script's directory)
image_file = os.path.join(os.path.dirname(__file__), 'opex.jpg')  # Change as needed

# Maximum pixel dimensions for normalization (will be set from image)
max_x = None  # Will be set after loading image
max_y = None  # Will be set after loading image

# Real-world bounds for scaling
x_min = 0   # e.g., corresponds to pixel x = 0
x_max = 1  # e.g., corresponds to pixel x = max_x
y_min = 0     # e.g., corresponds to pixel y = 0
y_max = 1    # e.g., corresponds to pixel y = max_y

# Options
apply_log_scale = False          # True to transform outputs with natural log
sort_method = 'x'                # 'x' or 'distance'
ref_point = (0, 0)               # Reference for distance sorting

# --- Core functions ---
def normalize_points(points, max_x, max_y):
    """
    Normalize raw pixel points to [0, 1] based on max_x and max_y.
    """
    return [(x / max_x, y / max_y) for x, y in points]

def scale_points(norm_points, x_min, x_max, y_min, y_max):
    """
    Scale normalized points into real-world units defined by bounds.
    """
    return [(
        x_min + x_n * (x_max - x_min),
        y_min + y_n * (y_max - y_min)
    ) for x_n, y_n in norm_points]

def sort_points(points, method, reference=(0, 0)):
    """
    Sort points by 'x' or by Euclidean distance from reference.
    """
    if method == 'x':
        return sorted(points, key=lambda p: p[0])
    elif method == 'distance':
        rx, ry = reference
        return sorted(points, key=lambda p: math.hypot(p[0] - rx, p[1] - ry))
    else:
        raise ValueError("sort_method must be 'x' or 'distance'.")

def apply_log(points):
    """
    Apply natural log to each coordinate; all values must be positive.
    """
    logged = []
    for x, y in points:
        if x <= 0 or y <= 0:
            raise ValueError(f"Cannot log non-positive value: ({x}, {y})")
        logged.append((math.log(x), math.log(y)))
    return logged

# --- Main interactive point selection and processing ---
def main():
    global max_x, max_y
    pygame.init()
    pygame.display.set_mode((1, 1))

    try:
        image = pygame.image.load(image_file).convert_alpha()
    except pygame.error as e:
        print(f"Failed to load image '{image_file}': {e}")
        return

    orig_width, orig_height = image.get_size()
    max_x, max_y = orig_width, orig_height
    screen = pygame.display.set_mode((orig_width, orig_height), pygame.RESIZABLE)
    pygame.display.set_caption("Left-click to add points, right-click to remove. Mouse wheel to zoom. ESC/Q to quit.")

    zoom = 1.0
    offset_x, offset_y = 0, 0
    points = []
    clock = pygame.time.Clock()
    running = True

    last_zoom = zoom
    scaled_img = image

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                sx, sy = event.pos
                ix = (sx - offset_x) / zoom
                iy = (sy - offset_y) / zoom
                px, py = int(ix), int(iy)
                if 0 <= px < orig_width and 0 <= py < orig_height:
                    pt = (px, py)
                    if event.button == 1:
                        points.append(pt)
                    else:
                        if points:
                            nearest = min(points, key=lambda p: (p[0]-px)**2 + (p[1]-py)**2)
                            points.remove(nearest)
            elif event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                img_x = (mx - offset_x) / zoom
                img_y = (my - offset_y) / zoom
                factor = 1.2 if event.y > 0 else 1 / 1.2
                zoom = max(0.1, min(zoom * factor, 18))
                offset_x = mx - img_x * zoom
                offset_y = my - img_y * zoom

        if zoom != last_zoom:
            sw = max(1, int(orig_width * zoom))
            sh = max(1, int(orig_height * zoom))
            scaled_img = pygame.transform.scale(image, (sw, sh))
            last_zoom = zoom

        screen.fill((30, 30, 30))
        screen.blit(scaled_img, (offset_x, offset_y))

        # Draw X markers
        for p in points:
            cx = (p[0] + 0.5) * zoom + offset_x
            cy = (p[1] + 0.5) * zoom + offset_y
            sx = int(cx)
            sy = int(cy)
            s = 5
            pygame.draw.line(screen, (255,0,0), (sx-s, sy-s), (sx+s, sy+s), 2)
            pygame.draw.line(screen, (255,0,0), (sx-s, sy+s), (sx+s, sy-s), 2)

        pygame.display.flip()
        clock.tick(60)


    pygame.quit()
    print(f"Image dimensions: {orig_width} x {orig_height}")
    print("Final points (pixels):")
    flipped_points = [(p[0], orig_height - 1 - p[1]) for p in points]
    print(flipped_points)
    print("Final real values:")
    norm = normalize_points(flipped_points, max_x, max_y)
    real = scale_points(norm, x_min, x_max, y_min, y_max)
    if apply_log_scale:
        try:
            real = apply_log(real)
        except Exception as e:
            print(f"Log error: {e}")
    sorted_real = sort_points(real, sort_method, reference=ref_point)
    for x, y in sorted_real:
        print(f"  {x:.6f}, {y:.6f}")

    # Compute bar segment percentages from y-values
    y_vals = sorted(y for _, y in sorted_real)
    boundaries = [0.0] + y_vals + [1.0]
    segments = [boundaries[i+1] - boundaries[i] for i in range(len(boundaries) - 1)]
    print("\nBar segment percentages (bottom to top):")
    for s in segments:
        print(f"  {s:.6f}")

if __name__ == '__main__':
    main()
