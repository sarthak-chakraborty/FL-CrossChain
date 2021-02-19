from tensorflow.keras.layers import Conv2D, MaxPool2D, Dropout, Flatten, Dense
from tensorflow.keras import Sequential


def SimpleCNN(input_shape, num_classes):
    model = Sequential([
                Conv2D(32, (3, 3), padding='same', input_shape=input_shape, activation='relu'), 
                Conv2D(32, (3, 3), padding='same', activation='relu'),
                MaxPool2D(),
                Dropout(0.1),
                Conv2D(64, (3, 3), padding='same', activation='relu'), 
                Conv2D(64, (3, 3), padding='same', activation='relu'),
                MaxPool2D(),
                Dropout(0.25),
                Conv2D(128, (3, 3), padding='same', activation='relu'), 
                Conv2D(128, (3, 3), padding='same', activation='relu'),
                MaxPool2D(),
                Dropout(0.25),
                Flatten(),
                Dense(256, activation='relu'),
                Dropout(0.25),
                Dense(num_classes)
            ])

    return model