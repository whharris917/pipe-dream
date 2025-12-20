import sys
import config
from flow_state_app import FlowStateApp

if __name__ == "__main__":
    mode = config.MODE_SIM
    if len(sys.argv) > 1:
        if sys.argv[1] == "editor":
            mode = config.MODE_EDITOR
        elif sys.argv[1] == "sim":
            mode = config.MODE_SIM
            
    app = FlowStateApp(start_mode=mode)
    app.run()