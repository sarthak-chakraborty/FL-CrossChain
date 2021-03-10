import os
import sys
import json

import numpy as np
import tensorflow as tf


class Loader:
	"""
	See fashion-mnist for example
	"""

	@property
	def name(self):
		raise NotImplementedError

	@property
	def train_dataset(self):
		"""
		returns tuple (x_train, y_train)

		NOTE: Should cache first
		"""
		raise NotImplementedError

	@property
	def test_dataset(self):
		"""
		return tuple (x_test, y_test)

		NOTE: Should cache first
		"""
		raise NotImplementedError

	@property
	def val_dataset(self):
		"""
		return tuple (x_val, y_val)
		"""
		raise NotImplementedError


class Cifar10(Loader):
	"""
	Cifar10 dataset loader
	"""

	def __init__(self, target_height, target_width, partition='iid', batch_size=10, validation_split=0.1, client_id=None):

		self.client_id = client_id
		self.batch_size = batch_size
		self.target_height = target_height
		self.target_width = target_width
		self.partition = partition
		self.validation_split = validation_split
		self.num_data = 0
		self._train_ds = None
		self._test_ds = None
		self._val_ds = None
		self._load_data()

	def _load_data(self):
		if self.client_id is None:
			data_dir = "/app/data/cifar-10/testdata/"
			img_gen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1/255.0)
			
			self._test_ds = img_gen.flow_from_directory(data_dir, 
														target_size=(self.target_height, self.target_width), 
														batch_size=self.batch_size,
														class_mode='sparse',
														shuffle=False,
														seed=0)
			self.num_data = len(self._test_ds)

		else:
			data_dir = "/app/data/cifar-10/dataclient/{}/client_{}/".format(self.partition, self.client_id)
			img_gen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1/255.0, validation_split=0.1)
			self._train_ds = img_gen.flow_from_directory(data_dir, 
														target_size=(self.target_height, self.target_width), 
														batch_size=self.batch_size,
														class_mode='sparse',
														subset='training',
														seed=0)
			self._val_ds = img_gen.flow_from_directory(data_dir, 
														target_size=(self.target_height, self.target_width), 
														batch_size=self.batch_size,
														class_mode='sparse',
														subset='validation', 
														seed=0)

			self.num_data = len(self._train_ds) * self.batch_size
			self.train_steps = len(self._train_ds)
			self.val_steps = len(self._val_ds)


	@property
	def name(self):
		return 'Cifar10'

	@property
	def train_dataset(self):
		return self._train_ds

	@property
	def val_dataset(self):
		return self._val_ds

	@property
	def test_dataset(self):
		return self._test_ds
		

class Cifar100(Loader):
	"""
	Cifar100 dataset loader
	"""

	def __init__(self, target_height, target_width, partition='iid', batch_size=10, validation_split=0.1, client_id=None):

		self.client_id = client_id
		self.batch_size = batch_size
		self.target_height = target_height
		self.target_width = target_width
		self.partition = partition
		self.validation_split = validation_split
		self._train_ds = None
		self._test_ds = None
		self._val_ds = None
		self._load_data()

	def _load_data(self):
		if self.client_id is None:
			data_dir = "/app/data/cifar-100/testdata/"
			img_gen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1/255.0)
			
			self._test_ds = img_gen.flow_from_directory(data_dir, 
														target_size=(self.target_height, self.target_width), 
														batch_size=self.batch_size,
														class_mode='sparse',
														shuffle=False,
														seed=0)
			
		else:
			data_dir = "/app/data/cifar-100/dataclient/{}/client_{}/".format(self.partition, self.client_id)
			img_gen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1/255.0, validation_split=0.1)
			self._train_ds = img_gen.flow_from_directory(data_dir, 
														target_size=(self.target_height, self.target_width), 
														batch_size=self.batch_size,
														class_mode='sparse',
														shuffle=False,
														seed=0,
														subset='training')
			self._val_ds = img_gen.flow_from_directory(data_dir, 
														target_size=(self.target_height, self.target_width), 
														batch_size=self.batch_size,
														class_mode='sparse',
														shuffle=False,
														seed=0,
														subset='validation')

			self.num_data = len(self._train_ds) * self.batch_size
			self.train_steps = len(self._train_ds)
			self.val_steps = len(self._val_ds) 

	@property
	def name(self):
		return 'Cifar100'

	@property
	def train_dataset(self):
		return self._train_ds

	@property
	def val_dataset(self):
		return self._val_ds

	@property
	def test_dataset(self):
		return self._test_ds


class MNIST(Loader):
	"""
	MNIST dataset loader
	"""

	def __init__(self, client_id=None, batch_size=10):

		self.client_id = client_id
		self.batch_size = batch_size
		self._train_ds = None
		self._test_ds = None
		self._val_ds = None
		self._load_data()

	def _load_data(self):
		(x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
		x_train = x_train.reshape(-1, 28, 28, 1)
		x_test = x_test.reshape(-1, 28, 28, 1)
		if self.client_id is None:
			img_gen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1/255.0)
			
			self._test_ds = img_gen.flow(x_test,
										y_test,
										batch_size=self.batch_size,
										shuffle=False,
										seed=0)

		else:
			img_gen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1/255.0, validation_split=0.1)
			self._train_ds = img_gen.flow(x_train[1000 * self.client_id : 1000 * (self.client_id + 1)],
											y_train[1000 * self.client_id : 1000 * (self.client_id + 1)],
											batch_size=self.batch_size,
											subset='training',
											seed=0)
			self._val_ds = img_gen.flow(x_train[1000 * self.client_id : 1000 * (self.client_id + 1)],
														y_train[1000 * self.client_id : 1000 * (self.client_id + 1)], 
														batch_size=self.batch_size,
														subset='validation', 
														seed=0)

			self.num_data = len(self._train_ds) * self.batch_size
			self.train_steps = len(self._train_ds)
			self.val_steps = len(self._val_ds)


	@property
	def name(self):
		return 'MNIST'

	@property
	def train_dataset(self):
		return self._train_ds

	@property
	def val_dataset(self):
		return self._val_ds

	@property
	def test_dataset(self):
		return self._test_ds
   

