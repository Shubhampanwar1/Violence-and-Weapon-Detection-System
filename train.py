from ultralytics import YOLO

# 1. Load the foundational Deep Learning brain
model = YOLO('yolov8n.pt') 

# 2. Define the training loop
if __name__ == '__main__':
    print("Initiating Sentinel AI Training Sequence...")
    
    # 3. Start the mathematical training process
    results = model.train(
        data='C:/Users/HP/OneDrive/Documents/Minor project/Detection System/weapon-detection-v1.v12i.yolov8/data.yaml', # UPDATE THIS PATH
        epochs=50, 
        imgsz=640, 
        batch=16, 
        device=0, 
        plots=True 
    )
    
    print("Training Complete. Model saved successfully.")