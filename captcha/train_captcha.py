#############訓練模型###################
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# 訓練集路徑
dataset_dir = r"C:\Users\user\source\repos\AutoClock\captcha_dataset"

# 圖片大小 (依照切割出來的字形狀)
img_w, img_h = 19, 22

# 讀取資料並做資料增強
datagen = ImageDataGenerator(
    rescale=1./255,
    validation_split=0.2
)

train_gen = datagen.flow_from_directory(
    dataset_dir,
    target_size=(img_h, img_w),
    color_mode='grayscale',
    batch_size=32,
    class_mode='categorical',
    subset='training'
)

val_gen = datagen.flow_from_directory(
    dataset_dir,
    target_size=(img_h, img_w),
    color_mode='grayscale',
    batch_size=32,
    class_mode='categorical',
    subset='validation'
)

# 建立 CNN 模型
model = models.Sequential([
    layers.Conv2D(32, (3,3), activation='relu', input_shape=(img_h, img_w, 1)),
    layers.MaxPooling2D((2,2)),
    layers.Conv2D(64, (3,3), activation='relu'),
    layers.MaxPooling2D((2,2)),
    layers.Flatten(),
    layers.Dense(128, activation='relu'),
    layers.Dense(train_gen.num_classes, activation='softmax')
])

model.compile(optimizer='adam',
              loss='categorical_crossentropy',
              metrics=['accuracy'])

# 訓練
model.fit(train_gen, epochs=20, validation_data=val_gen)

# 儲存模型
model.save(r"C:\Users\user\source\repos\AutoClock\captcha\captcha_model.h5")
print("✅ 模型已存檔")
