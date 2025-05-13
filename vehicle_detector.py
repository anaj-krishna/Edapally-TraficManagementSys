# vehicle_detector.py
import cv2
import numpy as np
from ultralytics import YOLO
import supervision as sv

class VehicleDetector:
    def __init__(self, model_path="yolov8n.pt"):
        """Initialize the vehicle detector with YOLO model"""
        self.model = YOLO(model_path)
        
        # Define vehicle classes from COCO dataset
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
        
        # Create annotator for drawing bounding boxes
        self.box_annotator = sv.BoxAnnotator(
            thickness=2,
            text_thickness=2,
            text_scale=1
        )
    
    def detect_vehicles(self, frame):
        """Detect vehicles in a frame and return results"""
        results = self.model(frame, classes=self.vehicle_classes)[0]
        detections = sv.Detections.from_ultralytics(results)
        
        # Extract class names for annotations
        class_ids = detections.class_id
        # Get confidence scores
        confidence = detections.confidence if detections.confidence is not None else [1.0] * len(class_ids)
        
        # Convert class IDs to COCO class names
        class_names = {
            2: "car",
            3: "motorcycle", 
            5: "bus",
            7: "truck"
        }
        
        labels = [
            f"{class_names.get(class_id, 'unknown')} {conf:.2f}"
            for class_id, conf in zip(class_ids, confidence)
        ]
        
        # Draw bounding boxes on frame
        annotated_frame = self.box_annotator.annotate(
            scene=frame.copy(),
            detections=detections,
            labels=labels
        )
        
        return annotated_frame, detections, len(detections)