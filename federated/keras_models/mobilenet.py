from tensorflow.keras.models import Model
from tensorflow.keras import Input
from tensorflow.keras.layers import Conv2D, BatchNormalization, DepthwiseConv2D, Dense, GlobalAvgPool2D, Activation


def block(tensor, channels, strides):
    """Depthwise separable conv: A Depthwise conv followed by a Pointwise conv."""

    # Depthwise
    x = DepthwiseConv2D(kernel_size=(3, 3), strides=strides, use_bias=False, padding='same')(tensor)
    x = BatchNormalization(momentum=0.1, epsilon=1e-5)(x)
    x = Activation('relu')(x)

    # Pointwise
    x = Conv2D(channels, kernel_size=(1, 1), strides=(1, 1), use_bias=False, padding='valid')(x)
    x = BatchNormalization(momentum=0.1, epsilon=1e-5)(x)
    x = Activation('relu')(x)
    return x


def MobileNet(shape, num_classes):
    tensor = Input(shape=shape)

    # Initial Conv Layer
    x = Conv2D(32, kernel_size=(3, 3), strides=(1,1), use_bias=False, padding='same')(tensor)
    x = BatchNormalization(momentum=0.1, epsilon=1e-5)(x)
    x = Activation('relu')(x)


    # (Channels, Strides)
    layers = [
        (64, (1, 1)),
        (128, (2, 2)),
        (128, (1, 1)),
        (256, (2, 2)),
        (256, (1, 1)),
        (512, (2, 2)),
        *[(512, (1, 1)) for _ in range(5)],
        (1024, (2, 2)),
        (1024, (1, 1))
    ]

    # Depthwise and Pointwise layers
    for channels, strides in layers:
        x = block(x, channels, strides)


    # Final Layers
    x = GlobalAvgPool2D()(x)
    x = Dense(num_classes)(x)

    model = Model(inputs=tensor, outputs=x)

    return model