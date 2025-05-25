import cv2
import numpy as np
import onnxruntime

session = onnxruntime.InferenceSession("path to your trained YOLO") # Note I am taking onnx model here
input_name = session.get_inputs()[0].name
input_shape = session.get_inputs()[0].shape

# I only made very basic preprocessing, modify/add more operations as you need
def preprocess(image, size=640):
    img = cv2.resize(image, (size, size))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    img = np.expand_dims(img, axis=0)
    return img

def postprocess(outputs, conf_thresh=0.5):
    preds = outputs[0]
    boxes = []
    for pred in preds[0]:
        x1, y1, x2, y2, conf, cls = pred
        if conf > conf_thresh:
            boxes.append((int(x1), int(y1), int(x2), int(y2), float(conf), int(cls)))
    return boxes


cap = cv2.VideoCapture(0) # your webcam


while True:

    ret, frame = cap.read()
    if not ret:
        break

    h0, w0 = frame.shape[:2]
    input_tensor = preprocess(frame, size=640)
    outputs = session.run(None, {input_name: input_tensor})
    boxes = postprocess(outputs, conf_thresh=0.5)

    for (x1, y1, x2, y2, conf, cls_id) in boxes:
        scale_x = w0 / 640
        scale_y = h0 / 640
        x1, x2 = int(x1 * scale_x), int(x2 * scale_x)
        y1, y2 = int(y1 * scale_y), int(y2 * scale_y)
        label = f"{cls_id} ({conf:.2f})"
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 255, 0), 2)

    cv2.imshow("Digit Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

