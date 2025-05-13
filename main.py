# main.py
import os
import sys
from traffic_monitor import TrafficMonitor

def main():
    # Define video paths - edit these to match your actual paths
    video_paths = [
        os.path.join('videos', 'traffic1.mp4'),
        os.path.join('videos', 'traffic2.mp4'),
        os.path.join('videos', 'traffic3.mp4'),
        os.path.join('videos', 'traffic4.mp4')
    ]
    
    # Check if videos exist
    for path in video_paths:
        if not os.path.exists(path):
            print(f"Error: Video file '{path}' not found.")
            print("Please make sure your video files are in the 'videos' directory.")
            return
    
    print("Starting Traffic Monitoring System...")
    print("Processing videos:")
    for i, path in enumerate(video_paths):
        print(f"Lane {i+1}: {path}")
    
    print("\nControls:")
    print("- Press 'q' to quit the application")
    print("- Press 'Ctrl+C' in the terminal to stop the system")
    
    # Create and run the traffic monitor
    monitor = TrafficMonitor(video_paths)
    
    try:
        monitor.run()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()