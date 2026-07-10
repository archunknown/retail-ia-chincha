import cv2
import numpy as np
import base64
import random

class VisionSystem:
    def __init__(self):
        # We can attempt to load yolov8n, but use a fallback simulator to guarantee stability
        self.yolo_model = None
        try:
            from ultralytics import YOLO
            # Load model in a non-blocking/fail-safe way
            self.yolo_model = YOLO('yolov8n.pt')
        except Exception:
            pass

    def get_cell_image_and_process(self, grid_state, camera_id):
        """
        Generates a synthetic camera view for a given camera, processes it through the OpenCV pipeline,
        and runs a simulated YOLOv8-nano detection with trust thresholds.
        
        A camera centered at (Cx, Cy) sees a 3x3 window of cells.
        """
        # Find camera position
        cam = None
        for c in grid_state.get('camaras', []):
            if c['id'] == camera_id:
                cam = c
                break
        
        if not cam:
            # Fallback to center
            cx, cy = 3, 3
        else:
            cx, cy = cam['x'], cam['y']

        # Dimensions of synthetic image (450x450, i.e., 3x3 cells of 150x150 pixels)
        cell_size = 150
        img_size = cell_size * 3
        frame = np.zeros((img_size, img_size, 3), dtype=np.uint8)

        # Draw grid cells in the camera's field of view (X from cx-1 to cx+1, Y from cy-1 to cy+1)
        # Note: Grid coordinates are 1-indexed (1 to 5)
        # Let's map cells in grid_state
        cells_dict = {}
        for cell in grid_state.get('celdas', []):
            cells_dict[(cell['x'], cell['y'])] = cell['val']

        detections = []
        
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                gx = cx + dx
                gy = cy + dy
                
                # Screen rect for this cell
                px_start_x = (dx + 1) * cell_size
                px_start_y = (dy + 1) * cell_size
                px_end_x = px_start_x + cell_size
                px_end_y = px_start_y + cell_size

                # If outside grid boundary, draw walls (dark gray)
                if not (1 <= gx <= 5 and 1 <= gy <= 5):
                    cv2.rectangle(frame, (px_start_x, px_start_y), (px_end_x, px_end_y), (30, 30, 30), -1)
                    cv2.line(frame, (px_start_x, px_start_y), (px_end_x, px_end_y), (50, 50, 50), 1)
                    continue

                val = cells_dict.get((gx, gy), 0)
                
                # Draw base path or shelf
                if val in (1, 10):
                    # Shelf area background (textured brown/blue)
                    cv2.rectangle(frame, (px_start_x + 5, px_start_y + 5), (px_end_x - 5, px_end_y - 5), (40, 50, 60), -1)
                    # Border
                    color = (0, 200, 0) if val == 1 else (0, 0, 255)
                    cv2.rectangle(frame, (px_start_x + 5, px_start_y + 5), (px_end_x - 5, px_end_y - 5), color, 3)
                    
                    label = "Estante Lleno" if val == 1 else "Estante Vacio"
                    cv2.putText(frame, label, (px_start_x + 10, px_start_y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
                    # Store bounding box for YOLO simulation
                    detections.append({
                        'bbox': (px_start_x + 5, px_start_y + 5, px_end_x - 5, px_end_y - 5),
                        'class': 'Estante Lleno' if val == 1 else 'Estante Vacio',
                        'conf': random.uniform(0.92, 0.98) if val == 1 else random.uniform(0.94, 0.99)
                    })
                else:
                    # Path cell (light gray pattern)
                    cv2.rectangle(frame, (px_start_x, px_start_y), (px_end_x, px_end_y), (80, 80, 80), -1)
                    # Grid line
                    cv2.rectangle(frame, (px_start_x, px_start_y), (px_end_x, px_end_y), (100, 100, 100), 1)

                # Check if Guardian is in this cell
                g_pos = grid_state.get('guardian_pos')
                if g_pos and g_pos[0] == gx and g_pos[1] == gy:
                    # Draw Guardian (blue shield/circle)
                    cx_p = px_start_x + cell_size // 2
                    cy_p = px_start_y + cell_size // 2
                    cv2.circle(frame, (cx_p, cy_p), 35, (255, 120, 0), -1) # Blue in BGR
                    cv2.circle(frame, (cx_p, cy_p), 35, (255, 255, 255), 2)
                    cv2.putText(frame, "G", (cx_p - 10, cy_p + 10), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)
                    
                    detections.append({
                        'bbox': (px_start_x + 15, px_start_y + 15, px_end_x - 15, px_end_y - 15),
                        'class': 'Guardian',
                        'conf': random.uniform(0.95, 0.99)
                    })

                # Check if Intruder is in this cell
                i_pos = grid_state.get('intruder_pos')
                if i_pos and i_pos[0] == gx and i_pos[1] == gy:
                    # Draw Intruder (red circle)
                    cx_p = px_start_x + cell_size // 2
                    cy_p = px_start_y + cell_size // 2
                    cv2.circle(frame, (cx_p, cy_p), 35, (0, 0, 255), -1) # Red in BGR
                    cv2.circle(frame, (cx_p, cy_p), 35, (255, 255, 255), 2)
                    cv2.putText(frame, "I", (cx_p - 8, cy_p + 10), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)
                    
                    # Ethics threshold simulation: let's assign a confidence level
                    # Sometimes it's highly clear (e.g. 94%), sometimes blurry (e.g. 82% - triggers manual validation!)
                    conf = grid_state.get('intruder_conf', 0.85) # default 85% to trigger alert
                    detections.append({
                        'bbox': (px_start_x + 15, px_start_y + 15, px_end_x - 15, px_end_y - 15),
                        'class': 'Intruso',
                        'conf': conf
                    })

        # Process through the OpenCV pipeline
        # 1. Grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 2. Gaussian Blur
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 3. Canny Edge Detection
        canny = cv2.Canny(blur, 50, 150)

        # 4. YOLO Object Detection Frame (Original + Bounding Boxes)
        yolo_frame = frame.copy()
        
        manual_confirmation_required = False
        unconfirmed_detection = None
        
        for det in detections:
            bbox = det['bbox']
            cls = det['class']
            conf = det['conf']
            
            # Determine color based on class
            if cls == 'Guardian':
                color = (255, 120, 0)
            elif cls == 'Intruso':
                # Check confidence threshold (90% auto, 70-89% manual)
                if conf >= 0.90:
                    color = (0, 0, 255) # Clear Red
                elif 0.70 <= conf < 0.90:
                    color = (0, 165, 255) # Orange (Warning)
                    manual_confirmation_required = True
                    unconfirmed_detection = {
                        'class': cls,
                        'conf': conf,
                        'bbox': bbox
                    }
                else:
                    color = (128, 128, 128) # Gray (Ignore)
            elif cls == 'Estante Lleno':
                color = (0, 255, 0)
            else:
                color = (0, 0, 255)

            # Draw bounding box
            cv2.rectangle(yolo_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            
            # Draw label
            label_text = f"{cls} {conf*100:.1f}%"
            cv2.putText(yolo_frame, label_text, (bbox[0], bbox[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Encode all frames to base64 from memory buffers
        original_b64 = self._to_base64(frame)
        gray_b64 = self._to_base64(gray)
        blur_b64 = self._to_base64(blur)
        canny_b64 = self._to_base64(canny)
        yolo_b64 = self._to_base64(yolo_frame)

        return {
            'original': original_b64,
            'grayscale': gray_b64,
            'blur': blur_b64,
            'canny': canny_b64,
            'yolo_detect': yolo_b64,
            'manual_confirmation_required': manual_confirmation_required,
            'unconfirmed_detection': unconfirmed_detection
        }

    def _to_base64(self, img):
        # Encode image to jpg in memory buffer
        success, encoded_img = cv2.imencode('.jpg', img)
        if not success:
            return ""
        # Convert buffer to base64 string
        return base64.b64encode(encoded_img).decode('utf-8')
