import os
import time
import random

from federated.models.models import KerasModel
from federated.dataset.loader import Loader

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


class SGD:

    @staticmethod
    def update(model, loader, num_epochs):
        """
        This is what the interface of SGD should look like
        Any specific requirements for dataset should be taken
        in loader.py

        We can add a validation loader as well
        """
        assert isinstance(loader, Loader)

        history_obj = model.fit(loader.train_dataset,
                                epochs=num_epochs,
                                verbose=1,
                                validation_data=loader.val_dataset,
                                steps_per_epoch=loader.train_steps,
                                validation_steps=loader.val_steps)

        return model, history_obj.history
