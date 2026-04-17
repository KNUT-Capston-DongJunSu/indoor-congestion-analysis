import torch, os, cv2
from ultralytics import YOLO
from .preprocessor import PreProcessor
from .postprocessing import process_predicted_results
from backend.config.settings import MODEL_DIR, YOLO_MODEL_NAME

class YoloManager:
    def __init__(self, model_name=YOLO_MODEL_NAME):    
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model_path = os.path.join(MODEL_DIR, model_name)
        self.model = YOLO(model_path).to(self.device)

    def train_yolo(self, config_path, epochs=100, imgsz=640, batch=16, project='results', name=None, lr0=0.01, optimizer='SGD', **kwargs):
        return self.model.train(
            data=config_path,
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            project=project,
            name=name,
            lr0=lr0,
            optimizer=optimizer,
            device=self.device,
            **kwargs
        )

    def smart_predict_yolo(self, frame, stream=False, imgsz=640, conf=0.5, iou=0.7, max_det=300, **kwargs):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        result = self.model.predict(
            source=frame,
            stream=stream,
            imgsz=imgsz,
            conf=conf,
            iou=iou,
            device=self.device,
            max_det=max_det,
            **kwargs
            )[0]
        return process_predicted_results(result)

    def predict_yolo(self, frame, stream=False, imgsz=640, conf=0.5, iou=0.7, max_det=300, **kwargs):
        self.preprocess = PreProcessor(self.model, imgsz)
        frame = self.preprocess.preprocess(frame)

        result = self.model(
            source=frame,
            stream=stream,
            imgsz=imgsz,
            conf=conf,
            iou=iou,
            device=self.device,
            max_det=max_det,
            **kwargs
            )[0]
        return process_predicted_results(result)
    
YOLO_MODEL = YoloManager(YOLO_MODEL_NAME)
    
        