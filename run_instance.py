import sys
import config
from flow_state_app import FlowStateApp

def main():
    mode_arg = "sim"
    if len(sys.argv) > 1:
        mode_arg = sys.argv[1]
    
    # Map arg to Config Constant
    start_mode = config.MODE_SIM
    if mode_arg == "editor":
        start_mode = config.MODE_EDITOR
        
    # We need to update FlowStateApp to accept a start_mode
    app = FlowStateApp(start_mode)
    app.run()

if __name__ == "__main__":
    main()