from tensorflow.keras.models import Model
import tensorflow as tf
from tensorflow.keras import Input
from tensorflow.keras.layers import Conv2D, BatchNormalization, MaxPool2D, ZeroPadding2D, Activation, Flatten, Dense


def Firei, (x, squeeze_planes, expand1x1_planes, expand3x3_planes):
	# Squeeze
	x = Conv2D(squeeze_planes, kernel_size=(1,1), name="conv-squeeze-{}".format(i))(x)
	x = Activation('relu', "activation-squeeze-{}".format(i))(x)

	# Expand
	expand1x1 = Conv2D(expand1x1_planes, kernel_size=(1,1), name="conv-expand1-{}".format(i))(x)
	expand1x1_act = Activation('relu', name="activation-expand1-{}".format(i))(expand1x1)

	pad = ZeroPadding2D(padding=(1,1), name="zeropad-{}".format(i))(x)
	expand3x3 = Conv2D(expand3x3_planes, kernel_size=(3,3), name="conv-expand2-{}".format(i))(pad)
	expand3x3_act = Activation('relu', name="activation-expand2-{}".format(i))(expand3x3)

	x = tf.keras.layers.add([expand1x1_act, expand3x3_act])

	return x


def VGG(shape, num_classes, size=512):
	tensor = Input(shape=shape)

	x = Conv2D(8, kernel_size=(3, 3), name="conv-initial")(tensor)
	x = BatchNormalization(momentum=0.1, epsilon=1e-5, name="BN")(x)
	x = Activation('relu', name="activation-initial")(x)

	# Channels
	layers = [32, 'M', 64, 'M', 128, 128, 'M', 128, 128, 'M', 128, 128, 'M']

	for i, channels in enumerate(layers):
		if channels == 'M':
			x = MaxPool2D(pool_size=(2,2), strides=2, name="pooling-{}".format(i))(x)
		else:
			x = Fire(i, x, int(channels/4), int(channels/2), int(channels/2))
			x = BatchNormalization(momentum=0.1, epsilon=1e-5, name="BN-{}".format(i))(x)
			x = Activation('relu', name="activation-{}".format(i))(x)

	# Final Layers
	x = Flatten()(x)
	x = Dense(size)(x)
	x = Activation('relu')(x)
	x = Dense(size)(x)
	x = Activation('relu')(x)
	out = Dense(num_classes)(x)

	model = Model(inputs=tensor, outputs=out)

	return model

