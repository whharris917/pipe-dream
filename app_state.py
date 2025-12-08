import time
from enum import Enum, auto
import config

class InteractionState(Enum):
    IDLE = auto()
    PANNING = auto()
    PAINTING = auto()
    DRAGGING_GEOMETRY = auto()
    EDITING_CONSTRAINT = auto()

class AppState:
    def __init__(self):
        # Core State
        self.mode = config.MODE_SIM
        self.state = InteractionState.IDLE
        
        # Camera
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.last_mouse_pos = (0, 0)
        
        # Selection
        self.selected_walls = set()
        self.selected_points = set()
        
        # Constraint Construction State
        self.pending_constraint = None
        self.pending_targets_walls = []
        self.pending_targets_points = []
        
        # Tool System
        self.tools = {} # Map tool_id -> Tool Instance
        self.current_tool = None # Active Tool Instance
        
        # Snapping Helpers
        self.current_snap_target = None
        self.new_wall_start_snap = None
        
        # IO / Clipboard
        self.placing_geo_data = None
        self.sim_backup_state = None
        self.current_filepath = None
        
        # Status Bar
        self.status_msg = ""
        self.status_time = 0
        
        # UI References
        self.input_world = None
        self.temp_constraint_active = False

    def set_status(self, msg):
        self.status_msg = msg
        self.status_time = time.time()

    def change_tool(self, tool_id):
        if self.current_tool:
            self.current_tool.deactivate()
        
        if tool_id in self.tools:
            self.current_tool = self.tools[tool_id]
            self.current_tool.activate()
            self.set_status(f"Tool: {self.current_tool.name}")