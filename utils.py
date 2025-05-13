# utils.py
import cv2
import numpy as np

def combine_frames(frame_dict, grid_size):
    """Combine multiple frames into a grid layout"""
    rows, cols = grid_size
    frame_height, frame_width = next(iter(frame_dict.values())).shape[:2]
    
    # Create a blank canvas
    combined_height = frame_height * rows
    combined_width = frame_width * cols
    combined_frame = np.zeros((combined_height, combined_width, 3), dtype=np.uint8)
    
    # Place each frame in the grid
    for lane_idx, frame in frame_dict.items():
        row = lane_idx // cols
        col = lane_idx % cols
        
        y_start = row * frame_height
        y_end = y_start + frame_height
        x_start = col * frame_width
        x_end = x_start + frame_width
        
        # Make sure sizes match
        if frame.shape[:2] != (frame_height, frame_width):
            frame = cv2.resize(frame, (frame_width, frame_height))
            
        combined_frame[y_start:y_end, x_start:x_end] = frame
        
    return combined_frame

def add_header(combined_frame, traffic_light, lane_counts):
    """Add a header showing traffic status to the combined frame"""
    combined_width = combined_frame.shape[1]
    header_height = 60
    
    # Create dark header
    header = np.ones((header_height, combined_width, 3), dtype=np.uint8) * 50  # Dark gray
    
    # Add text showing green lane
    green_lane_text = f"Current Green: Lane {traffic_light.current_green + 1}"
    cv2.putText(
        header, 
        green_lane_text,
        (20, 40), 
        cv2.FONT_HERSHEY_SIMPLEX, 
        1, 
        (0, 255, 0), 
        2
    )
    
    # Add lane counts
    counts_text = "Counts: " + ", ".join([f"Lane {i+1}: {count}" for i, count in enumerate(lane_counts)])
    
    cv2.putText(
        header,
        counts_text,
        (combined_width // 2, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )
    
    # Combine header and frame grid
    return np.vstack([header, combined_frame])

def resize_frame(frame, target_width=None, target_height=None):
    """Resize a frame while maintaining aspect ratio"""
    height, width = frame.shape[:2]
    
    if target_width is None and target_height is None:
        return frame
    
    if target_width is None:
        # Calculate width to maintain aspect ratio
        aspect_ratio = width / height
        target_width = int(target_height * aspect_ratio)
    elif target_height is None:
        # Calculate height to maintain aspect ratio
        aspect_ratio = height / width
        target_height = int(target_width * aspect_ratio)
        
    return cv2.resize(frame, (target_width, target_height))