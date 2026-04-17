import os, cv2

class BaseVideoWriter:
    def __init__(self):
        self._writer = None
        self._fps = 30

    @property
    def fps(self):
        return self._fps
    
    @fps.setter
    def fps(self, value):
        self._fps = value
    
    def init_writer(self, width, height, filename):        
        if self._writer is None:
            self._writer = cv2.VideoWriter(
                filename, 
                cv2.VideoWriter_fourcc(*'mp4v'), 
                self._fps, (width, height)
                )
            
        return self._writer
    
    def write(self, frame):
        return self._writer.write(frame)
    
    def close_writer(self):
        if self._writer:
            self._writer.release()
        cv2.destroyAllWindows() 


class BaseVideoCap:
    def __init__(self):
        self._capture = None

    def init_cap(self, video_path):
        if self._capture is None:
            self._capture = cv2.VideoCapture(video_path)
            if not self._capture.isOpened():
                raise IOError(f"Cannot open video: {video_path}")
            fps = int(self._capture.get(cv2.CAP_PROP_FPS))
            frame_width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH)) 
            frame_height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        return self._capture, fps, frame_width, frame_height
    
    def close_cap(self):
        self._capture.release()
        cv2.destroyAllWindows()


class BaseVideoStreamer:
    
    output_dir = "./results/"
    os.makedirs(output_dir, exist_ok=True)

    def __init__(self, video_path, save_enabled=False, output_name=None):
        self.frame_id = 0
        self.track_hist = []
        self._save_enabled = save_enabled

        self.video_cap = BaseVideoCap()
        self.cap, video_fps, frame_width, frame_height = self.video_cap.init_cap(video_path)

        if save_enabled:
            self.video_writer = BaseVideoWriter()
            self.video_writer.fps = video_fps
            self.video_writer.init_writer(frame_width, frame_height, self.output_dir + output_name)

    @property
    def save_enabled(self):
        return self._save_enabled
    
    @save_enabled.setter
    def save_enabled(self, value):
        self._save_enabled = value