# traffic_monitor.py
import cv2
import time
import threading
import queue
from vehicle_detector import VehicleDetector
from traffic_light import TrafficLight
from utils import combine_frames, add_header

class TrafficMonitor:
    def __init__(self, video_paths):
        """Initialize the traffic monitoring system"""
        self.video_paths = video_paths
        self.detector = VehicleDetector()
        self.traffic_light = TrafficLight(lanes=len(video_paths))
        
        # For inter-thread communication
        self.lane_counts = [0] * len(video_paths)
        self.lane_counts_lock = threading.Lock()
        self.processing_done = threading.Event()
        self.frames_queue = queue.Queue(maxsize=100)
    
    def process_lane(self, lane_idx, video_path):
        """Process a single lane video"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path}")
            return
        
        frame_count = 0
        skip_frames = 3  # Process every nth frame to improve performance
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                frame_count += 1
                
                if not ret:
                    # If video ends, loop back to beginning
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                    
                # Skip frames for performance
                if frame_count % skip_frames != 0:
                    continue

                # Detect vehicles
                annotated_frame, detections, vehicle_count = self.detector.detect_vehicles(frame)
                
                # Update lane count (with thread safety)
                with self.lane_counts_lock:
                    self.lane_counts[lane_idx] = vehicle_count
                
                # Add traffic light visualization
                traffic_light_img = self.traffic_light.get_traffic_light_image(lane_idx)
                
                # Resize traffic light to fit on the video frame
                traffic_light_img = cv2.resize(traffic_light_img, (80, 240))
                
                # Create a region in the top-right corner for the traffic light
                roi_y = 10
                roi_x = annotated_frame.shape[1] - traffic_light_img.shape[1] - 10
                
                # Get ROI from the frame
                roi = annotated_frame[roi_y:roi_y+traffic_light_img.shape[0], 
                                     roi_x:roi_x+traffic_light_img.shape[1]]
                
                # Save original ROI shape for later
                roi_shape = roi.shape
                
                # Resize traffic light if ROI and traffic light shapes don't match
                if roi_shape[0:2] != traffic_light_img.shape[0:2]:
                    traffic_light_img = cv2.resize(traffic_light_img, (roi_shape[1], roi_shape[0]))
                
                # Blend traffic light into the frame
                try:
                    annotated_frame[roi_y:roi_y+traffic_light_img.shape[0], 
                                   roi_x:roi_x+traffic_light_img.shape[1]] = traffic_light_img
                except ValueError:
                    pass  # Skip blending if sizes don't match
                
                # Add text with vehicle count and lane number
                cv2.putText(
                    annotated_frame,
                    f"Lane {lane_idx+1} Count: {vehicle_count}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )
                
                # Send frame to the queue for combined visualization
                self.frames_queue.put((lane_idx, annotated_frame.copy()))
                
        finally:
            cap.release()
            
    def visualize_combined(self):
        """Create a combined visualization of all lanes"""
        # Determine grid size based on number of lanes
        lanes = len(self.video_paths)
        if lanes <= 2:
            grid_size = (1, lanes)
        else:
            grid_size = (2, 2)  # 2x2 grid for 3-4 lanes
            
        # Get sample frame to determine dimensions
        sample_frames = {}
        timeout_seconds = 10
        start_time = time.time()
        
        # Wait for at least one frame from each lane
        while len(sample_frames) < lanes:
            if time.time() - start_time > timeout_seconds:
                print("Timeout waiting for frames from all lanes")
                return
                
            try:
                lane_idx, frame = self.frames_queue.get(timeout=1)
                if lane_idx not in sample_frames:
                    sample_frames[lane_idx] = frame
                self.frames_queue.task_done()
            except queue.Empty:
                continue
        
        cv2.namedWindow("Traffic Monitoring System", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Traffic Monitoring System", 1280, 720)
        
        last_frames = {}
        try:
            while not self.processing_done.is_set() or not self.frames_queue.empty():
                try:
                    lane_idx, frame = self.frames_queue.get(timeout=0.1)
                    last_frames[lane_idx] = frame
                    self.frames_queue.task_done()
                except queue.Empty:
                    continue
                
                # Only create combined frame when we have at least one frame per lane
                if len(last_frames) == lanes:
                    # Update traffic light based on current lane counts
                    with self.lane_counts_lock:
                        self.traffic_light.update(self.lane_counts)
                    
                    combined_frame = combine_frames(last_frames, grid_size)
                    
                    # Add header with overall status
                    with self.lane_counts_lock:
                        frame_with_header = add_header(combined_frame, self.traffic_light, self.lane_counts)
                    
                    # Display frame
                    cv2.imshow("Traffic Monitoring System", frame_with_header)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
        finally:
            cv2.destroyAllWindows()
            
    def run(self):
        """Run the traffic monitoring system"""
        # Start processing threads for each lane
        lane_threads = []
        for lane_idx, video_path in enumerate(self.video_paths):
            thread = threading.Thread(
                target=self.process_lane,
                args=(lane_idx, video_path),
                daemon=True
            )
            lane_threads.append(thread)
            thread.start()
            
        # Start visualization thread
        viz_thread = threading.Thread(
            target=self.visualize_combined,
            daemon=True
        )
        viz_thread.start()
        
        try:
            # Wait for user to exit with Ctrl+C
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Stopping traffic monitoring...")
        finally:
            # Signal all threads to stop
            self.processing_done.set()
            
            # Give threads time to clean up
            time.sleep(1)
            
            print("Traffic monitoring stopped")