import os
import glob
from deepface import DeepFace
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns


# ----Step 1----#
# Get data#
dataset_dir = "/Users/nguyentietkhang/Downloads/Xulyanhso/analysic/test"

# Save data#
y_pred = []
y_true = []

# Check any class#
for emotion_folder in os.listdir(dataset_dir):
    folder_patd = os.path.join(dataset_dir, emotion_folder)
    # condition choose right class#
    if not os.path.isdir(folder_patd):
        continue

    # get 50 images random#
    images_paths = glob.glob(os.path.join(folder_patd, "*.jpg"))[:50]

    for image_path in images_paths:
        try:
            # run deepface#
            result = DeepFace.analyze(image_path,
                                      actions=['emotion'],
                                      detector_backend='retinaface',
                                      enforce_detection=False,
                                      silent=True)
            emotions = result[0]['emotion']
            dominant_emotion = result[0]['dominant_emotion']
            pred = max(emotions, key=emotions.get)

            # save#
            y_true.append(emotion_folder)
            y_pred.append(pred)
        except Exception as e:
            print(f"Lỗi ở ảnh{image_path}: {e}")

# print#
print(classification_report(y_true, y_pred))


# plot#
labels = sorted(list(set(y_true) | set(y_pred)))

cm = confusion_matrix(y_true, y_pred, labels=labels)

# draw plot#
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt=' d', cmap='Blues',
            xticklabels=labels, yticklabels=labels)
plt.title('Confusion Matrix: Thực tế vs Dự đoán')
plt.xlabel('Dự đoán (Predicted)')
plt.ylabel('Thực tế (True)')
plt.show()
