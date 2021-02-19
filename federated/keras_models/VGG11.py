from tensorflow.keras.models import Model
import tensorflow as tf
from tensorflow.keras import Input
from tensorflow.keras.layers import Conv2D, BatchNormalization, MaxPool2D, ZeroPadding2D, Activation, Flatten, Dense


def Fire(x, squeeze_planes, expand1x1_planes, expand3x3_planes):
	# Squeeze
	x = Conv2D(squeeze_planes, kernel_size=(1,1))(x)
	x = Activation('relu')(x)

	# Expand
	expand1x1 = Conv2D(expand1x1_planes, kernel_size=(1,1))(x)
	expand1x1_act = Activation('relu')(expand1x1)

	pad = ZeroPadding2D(padding=(1,1))(x)
	expand3x3 = Conv2D(expand3x3_planes, kernel_size=(3,3))(pad)
	expand3x3_act = Activation('relu')(expand3x3)

	x = tf.keras.layers.add([expand1x1_act, expand3x3_act])

	return x


def VGG(shape, num_classes, size=512):
	tensor = Input(shape=shape)

	x = Conv2D(8, kernel_size=(3, 3))(tensor)
	x = BatchNormalization(momentum=0.1, epsilon=1e-5)(x)
	x = Activation('relu')(x)

	# Channels
	layers = [32, 'M', 64, 'M', 128, 128, 'M', 128, 128, 'M', 128, 128, 'M']

	for channels in layers:
		if channels == 'M':
			x = MaxPool2D(pool_size=(2,2), strides=2)(x)
		else:
			x = Fire(x, int(channels/4), int(channels/2), int(channels/2))
			x = BatchNormalization(momentum=0.1, epsilon=1e-5)(x)
			x = Activation('relu')(x)

	# Final Layers
	x = Flatten()(x)
	x = Dense(size)(x)
	x = Activation('relu')(x)
	x = Dense(size)(x)
	x = Activation('relu')(x)
	out = Dense(num_classes)(x)

	model = Model(inputs=tensor, outputs=out)

	return model

