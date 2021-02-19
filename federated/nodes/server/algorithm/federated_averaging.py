import numpy as np
import tensorflow as tf


class FederatedAveraging:

    @staticmethod
    def fit(global_kmodel, new_kmodel_list, data_count_list):
        print("[Federated Averaging]")

        # updated_weights = [None for i in range(len(global_model.weights))]

        total_data_count = np.sum(data_count_list)

        new_weights_weighted_list = []
        for model_no in range(len(new_kmodel_list)):
            new_kmodel_weights = new_kmodel_list[model_no].weights
            data_count = data_count_list[model_no]

            for i in range(len(new_kmodel_weights)):
                new_kmodel_weights[i] = data_count * new_kmodel_weights[i] / total_data_count

            new_weights_weighted_list.append(new_kmodel_weights)

        summed_weights = np.sum(np.array(new_weights_weighted_list), axis=0)

        # assert(len(summed_weights) == len(updated_weights))

        # print("Updating Weights...")
        # for i in range(len(updated_weights)):
        #     updated_weights[i] = summed_weights[i]

        print("Weights Updated...")
        global_kmodel.set_weights(summed_weights)

        return global_kmodel

