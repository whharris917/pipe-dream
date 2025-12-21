import webview
import time
import math
import threading

# This is "The Folly" - your Python application logic
class FollyBackend:
    def __init__(self):
        self.window = None
        self.running = False

    def start_logic_loop(self, window):
        self.window = window
        self.running = True
        
        # Start the physics/logic thread
        # We do this so the GUI doesn't freeze
        t = threading.Thread(target=self._loop)
        t.daemon = True
        t.start()

    def _loop(self):
        print("Folly Physics Engine Started...")
        start_time = time.time()
        
        while self.running:
            elapsed = time.time() - start_time
            
            # --- YOUR PYTHON LOGIC HERE ---
            # Simulate a fan spinning up and down or reacting to data
            # e.g., speed oscillates between 0.5 and 8.0
            target_speed = 4.25 + math.sin(elapsed * 0.5) * 3.75
            
            # Simulate light flickering based on speed/stress
            light_intensity = 100 + (math.sin(elapsed * 20) * 20)
            
            # ------------------------------

            # Send data to the frontend (Three.js)
            # We call the JavaScript function 'updateFollyState'
            if self.window:
                try:
                    self.window.evaluate_js(
                        f'updateFollyState({target_speed}, {light_intensity})'
                    )
                except Exception as e:
                    print(f"Error communicating with UI: {e}")

            # Run logic at 60Hz
            time.sleep(1/60)

    def on_closed(self):
        self.running = False
        print("Folly shutting down.")

# Initialize the App
if __name__ == '__main__':
    folly = FollyBackend()
    
    # Create the window
    # Note: pointing to the local html file
    window = webview.create_window(
        'The Folly', 
        'folly_ui.html',
        width=1200,
        height=800,
        background_color='#000000'
    )
    
    # Start the app
    # webview.start blocks the main thread, so we pass our logic function
    # to run once the window is ready.
    webview.start(folly.start_logic_loop, window)