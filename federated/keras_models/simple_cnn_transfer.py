from tensorflow.keras.layers import Conv2D, MaxPool2D, Dropout, Flatten, Dense
from tensorflow.keras import Sequential


def SimpleCNN(input_shape, num_classes):
    model = Sequential([
                Conv2D(32, (3, 3), padding='same', input_shape=input_shape, name='conv2D_32_1', activation='relu'), 
                Conv2D(32, (3, 3), padding='same', name='conv2D_32_2', activation='relu'),
                MaxPool2D(),
                Dropout(0.1),
                Conv2D(64, (3, 3), padding='same', name='conv2D_64_1', activation='relu'), 
                Conv2D(64, (3, 3), padding='same', name='conv2D_64_2', activation='relu'),
                MaxPool2D(),
                Dropout(0.25),
                Conv2D(128, (3, 3), padding='same', name='conv2D_128_1', activation='relu'), 
                Conv2D(128, (3, 3), padding='same', name='conv2D_128_2', activation='relu'),
                MaxPool2D(),
                Dropout(0.5),
                Conv2D(256, (3, 3), padding='same', name='conv2D_256_1', activation='relu'), 
                Conv2D(256, (3, 3), padding='same', name='conv2D_256_2', activation='relu'),
                Conv2D(256, (3, 3), padding='same', name='conv2D_256_3', activation='relu'),
                MaxPool2D(),
                Dropout(0.25),
                Flatten(),
                Dense(512, activation='relu'),
                Dense(num_classes)
            ])

    for layer in model.layers:
        if layer.name.startswith("conv"):
            t = layer.name.split('_')
            if t[1] != '256':
                layer.trainable = False

    return model
