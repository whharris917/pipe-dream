import config

class Camera:
    def __init__(self):
        self.offset_x = 0
        self.offset_y = 0
        self.zoom = 1.0
        self.drag_start = None

    # Removed 'center_on_grid' as the finite grid concept is deprecated in this version

    def world_to_screen(self, wx, wy):
        """Converts World Coordinates (pixels) to Screen Pixels (int)."""
        # World is now 1:1 with pixels, just scaled by zoom
        sx = (wx * self.zoom) + self.offset_x
        sy = (wy * self.zoom) + self.offset_y
        return sx, sy

    def screen_to_world(self, sx, sy):
        """Converts Screen Pixels to World Coordinates (pixels)."""
        wx = (sx - self.offset_x) / self.zoom
        wy = (sy - self.offset_y) / self.zoom
        return wx, wy

    def zoom_towards(self, new_zoom, screen_x, screen_y):
        """Zooms the camera while keeping a specific screen point fixed in the world."""
        # 1. Get world coordinates of the target screen point (before zoom change)
        wx, wy = self.screen_to_world(screen_x, screen_y)
        
        # 2. Apply new zoom
        self.zoom = new_zoom
        
        # 3. Adjust offset to put that world point back under the screen point
        # Derived from: sx = (wx * zoom) + offset  =>  offset = sx - (wx * zoom)
        self.offset_x = screen_x - (wx * self.zoom)
        self.offset_y = screen_y - (wy * self.zoom)