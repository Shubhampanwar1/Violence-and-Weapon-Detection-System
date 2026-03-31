from ultralytics import YOLO

# Load model
model = YOLO('yolov8n.pt') 

# defining trainig loop
if __name__ == '__main__':
    print("Initiating Sentinel AI Training Sequence...")

    results = model.train(
        data='C:/Users/HP/OneDrive/Documents/Minor project/Detection System/weapon-detection-v1.v12i.yolov8/data.yaml', # UPDATE THIS PATH
        epochs=50, 
        imgsz=640, 
        batch=16, 
        device=0, 
        plots=True 
    )
    
    print("Training Complete. Model saved successfully.")
