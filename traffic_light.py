# traffic_light.py
import cv2
import numpy as np
import time
import threading

class TrafficLight:
    def __init__(self, lanes=4):
        self.lanes = lanes
        self.current_green = 0  # Start with lane 0 having green
        self.min_green_time = 15  # Minimum green light duration in seconds
        self.max_green_time = 60  # Maximum green light duration in seconds
        self.yellow_time = 3  # Yellow light duration in seconds
        
        # Traffic light states
        self.states = np.zeros((lanes, 3), dtype=np.uint8)  # [R, Y, G] for each lane
        for i in range(lanes):
            if i == self.current_green:
                self.states[i] = [0, 0, 1]  # Green for current lane
            else:
                self.states[i] = [1, 0, 0]  # Red for other lanes
                
        self.last_change_time = time.time()
        self.is_changing = False
    
    def update(self, lane_counts):
        """Update traffic light based on lane counts"""
        current_time = time.time()
        time_elapsed = current_time - self.last_change_time
        
        # Don't change if minimum time hasn't passed or currently in transition
        if time_elapsed < self.min_green_time or self.is_changing:
            return
            
        # Force change if max time elapsed
        if time_elapsed >= self.max_green_time:
            self._initiate_light_change(lane_counts)
            return
            
        # Check if another lane has significantly more traffic
        current_count = lane_counts[self.current_green]
        max_count = max(lane_counts)
        max_lane = lane_counts.index(max_count)
        
        # Change light if another lane has 50% more vehicles than current lane
        if max_lane != self.current_green and max_count > current_count * 1.5:
            self._initiate_light_change(lane_counts)
    
    def _initiate_light_change(self, lane_counts):
        """Start the process of changing lights"""
        self.is_changing = True
        
        # Set current green lane to yellow
        self.states[self.current_green] = [0, 1, 0]
        
        # Schedule next state change after yellow_time
        threading.Timer(self.yellow_time, self._complete_light_change, args=[lane_counts]).start()
    
    def _complete_light_change(self, lane_counts):
        """Complete the light change after yellow light duration"""
        # Set current lane to red
        self.states[self.current_green] = [1, 0, 0]
        
        # Determine next green lane (highest count excluding current)
        lane_counts_copy = lane_counts.copy()
        lane_counts_copy[self.current_green] = -1  # Exclude current lane
        next_green = lane_counts_copy.index(max(lane_counts_copy))
        
        # Set new green lane
        self.current_green = next_green
        self.states[self.current_green] = [0, 0, 1]
        
        # Reset timer and flag
        self.last_change_time = time.time()
       # self.is_changing = False
    
    def get_traffic_light_image(self, lane_number):
        """Generate a traffic light image for visualization"""
        height, width = 150, 50
        image = np.ones((height, width, 3), dtype=np.uint8) * 128  # Gray background
        
        # Draw traffic light housing
        cv2.rectangle(image, (5, 5), (width-5, height-5), (100, 100, 100), -1)
        
        # Draw the three lights
        colors = [(0, 0, 255), (0, 255, 255), (0, 255, 0)]  # Red, Yellow, Green
        positions = [(25, 25), (25, 75), (25, 125)]
        radius = 15
        
        for i, (color, position) in enumerate(zip(colors, positions)):
            # Determine if this light is active for this lane
            is_active = self.states[lane_number][i] == 1
            
            # Draw circle with either bright (active) or dim (inactive) color
            actual_color = color if is_active else tuple(int(c * 0.3) for c in color)
            cv2.circle(image, position, radius, actual_color, -1)
        
        return image