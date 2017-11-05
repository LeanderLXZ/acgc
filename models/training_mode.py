import random
import time
from models import utils
from models.parameters import SingleModel
from models.parameters import ChampionModel
from models.parameters import PrejudgeTraining
from models.parameters import ModelStacking


class TrainingMode:

    def __init__(self):
        pass

    @staticmethod
    def get_train_function(train_mode, model_name, grid_search_n_cv=None, reduced_feature_list=None,
                           load_pickle=False, train_args=None, train_options=None):

        if train_mode == 'train_single_model':
            model_arg = {'reduced_feature_list': reduced_feature_list, 'train_args': train_args,
                         'train_options': train_options, 'mode': train_mode}
        elif train_mode == 'auto_grid_search':
            model_arg = {'reduced_feature_list': reduced_feature_list, 'grid_search_n_cv': grid_search_n_cv,
                         'train_args': train_args, 'train_options': train_options, 'mode': train_mode}
        elif train_mode == 'auto_train_boost_round':
            model_arg = {'reduced_feature_list': reduced_feature_list, 'grid_search_n_cv': grid_search_n_cv,
                         'train_args': train_args, 'train_options': train_options, 'mode': train_mode}
        elif train_mode == 'auto_train':
            model_arg = {'reduced_feature_list': reduced_feature_list, 'train_args': train_args,
                         'train_options': train_options, 'mode': train_mode}
        else:
            raise ValueError('Wrong Training Mode!')

        if model_name in ['lr', 'rf', 'et', 'ab', 'gb', 'xgb', 'xgb_sk',
                          'lgb', 'lgb_sk', 'cb', 'dnn', 'stack_lgb']:

            SM = SingleModel(**model_arg)
            train_functions = {'lr': SM.lr_train,
                               'rf': SM.rf_train,
                               'et': SM.et_train,
                               'ab': SM.ab_train,
                               'gb': SM.gb_train,
                               'xgb': SM.xgb_train,
                               'xgb_sk': SM.xgb_train_sklearn,
                               'lgb': SM.lgb_train,
                               'lgb_sk': SM.lgb_train_sklearn,
                               'cb': SM.cb_train,
                               'dnn': SM.dnn_tf_train,
                               'stack_lgb': SM.stack_lgb_train}

            return train_functions[model_name]

        elif model_name == 'christar':
            CM = ChampionModel(**model_arg)
            return CM.Christar1991

        elif model_name == 'stack_t':
            STK = ModelStacking(**model_arg)
            return STK.stack_tree_train

        elif model_name == 'stack_pt':
            STK = ModelStacking(**model_arg)
            return STK.prejudge_stack_tree_train

        elif model_name == 'prejudge_b':
            PJ = PrejudgeTraining(reduced_feature_list=reduced_feature_list,
                                  load_pickle=load_pickle, train_options=train_options)
            return PJ.binary_train

        elif model_name == 'prejudge_m':
            PJ = PrejudgeTraining(reduced_feature_list=reduced_feature_list,
                                  load_pickle=load_pickle, train_options=train_options)
            return PJ.multiclass_train

        else:
            raise ValueError('Wrong Model Name!')

    def train_single_model(self, model_name, train_seed, cv_seed, num_boost_round=None, epochs=None,
                           auto_idx=None, reduced_feature_list=None, load_pickle=False, base_parameters=None,
                           train_args=None, train_options=None):
        """
            Training Single Model
        """
        # Get Train Function
        train_function = \
            self.get_train_function('train_single_model', model_name, load_pickle=load_pickle,
                                    reduced_feature_list=reduced_feature_list, train_args=train_args,
                                    train_options=train_options)

        # Training Model
        if model_name == 'stack_lgb':
            train_function(train_seed, cv_seed, auto_idx=auto_idx, num_boost_round=num_boost_round)
        else:
            if num_boost_round is not None:
                train_function(train_seed, cv_seed, parameters=base_parameters, num_boost_round=num_boost_round)
            elif epochs is not None:
                train_function(train_seed, cv_seed, parameters=base_parameters, epochs=epochs)
            else:
                train_function(train_seed, cv_seed, parameters=base_parameters)

    def auto_grid_search(self, model_name=None, parameter_grid_list=None, reduced_feature_list=None,
                         save_final_pred=False, n_epoch=1, grid_search_n_cv=5, base_parameters=None,
                         train_args=None, train_options=None, num_boost_round=None):
        """
            Automatically Grid Searching
        """
        # Get Train Function
        train_options['save_final_pred'] = save_final_pred
        train_function = \
            self.get_train_function('auto_grid_search', model_name, grid_search_n_cv=grid_search_n_cv,
                                    reduced_feature_list=reduced_feature_list, train_args=train_args,
                                    train_options=train_options)

        for parameter_grid in parameter_grid_list:

            gs_start_time = time.time()

            print('======================================================')
            print('Auto Grid Searching Parameter...')
            print('======================================================')

            n_param = len(parameter_grid)
            n_value = len(parameter_grid[0][1])
            param_name = []
            param_value = []
            for i in range(n_param):
                if len(parameter_grid[i][1]) != n_value:
                    raise ValueError('The number of value of parameters should be the same as each other!')
                param_name.append(parameter_grid[i][0])
                param_value.append(parameter_grid[i][1])

            for i_param_value in range(n_value):

                param_start_time = time.time()
                grid_search_tuple_list = []
                param_info = ''
                for i_param in range(n_param):
                    param_name_i = param_name[i_param]
                    param_value_i = param_value[i_param][i_param_value]
                    param_info += ' ' + utils.get_simple_param_name(param_name_i) + '-' + str(param_value_i)
                    grid_search_tuple_list.append((param_name_i, param_value_i))

                for i in range(n_epoch):

                    train_seed = random.randint(0, 500)
                    cv_seed = random.randint(0, 500)
                    epoch_start_time = time.time()
                    train_args['csv_idx'] = 'idx-' + str(i + 1)

                    print('======================================================')
                    print('Parameter:' + param_info)
                    print('------------------------------------------------------')
                    print('Epoch: {}/{} | train_seed: {} | cv_seed: {}'.format(i + 1, n_epoch, train_seed, cv_seed))

                    # Training Model
                    if num_boost_round is not None:
                        train_function(train_seed, cv_seed, parameters=base_parameters,
                                       grid_search_tuple_list=grid_search_tuple_list, num_boost_round=num_boost_round)
                    else:
                        train_function(train_seed, cv_seed, parameters=base_parameters,
                                       grid_search_tuple_list=grid_search_tuple_list)

                    print('======================================================')
                    print('Auto Training Epoch Done!')
                    print('Train Seed: {}'.format(train_seed))
                    print('Cross Validation Seed: {}'.format(cv_seed))
                    print('Epoch Time: {}s'.format(time.time() - epoch_start_time))
                    print('======================================================')

                print('======================================================')
                print('One Parameter Done!')
                print('Parameter Time: {}s'.format(time.time() - param_start_time))
                print('======================================================')

            print('======================================================')
            print('All Parameter Done!')
            print('Grid Searching Time: {}s'.format(time.time() - gs_start_time))
            print('======================================================')

    def auto_train_boost_round(self, model_name=None, train_seed_list=None, cv_seed_list=None, n_epoch=1,
                               num_boost_round=None, epochs=None, parameter_grid_list=None, reduced_feature_list=None,
                               grid_search_n_cv=20, save_final_pred=False, base_parameters=None,
                               train_args=None, train_options=None):
        """
            Automatically Training by Boost Round or Epoch
        """

        def _random_int_list(start, stop, length):
            start, stop = (int(start), int(stop)) if start <= stop else (int(stop), int(start))
            length = int(abs(length)) if length else 0
            random_list = []
            for _ in range(length):
                random_list.append(random.randint(start, stop))
            return random_list

        if train_seed_list is None:
            train_seed_list = _random_int_list(500, 1000, n_epoch)
        else:
            n_epoch = len(train_seed_list)
        if cv_seed_list is None:
            cv_seed_list = _random_int_list(500, 1000, n_epoch)
        else:
            n_epoch = len(train_seed_list)

        # Get Train Function
        train_options['save_final_pred'] = save_final_pred
        train_function = self.get_train_function('auto_train_boost_round', model_name,
                                                 grid_search_n_cv=grid_search_n_cv,
                                                 reduced_feature_list=reduced_feature_list, train_args=train_args,
                                                 train_options=train_options)

        for parameter_grid in parameter_grid_list:

            gs_start_time = time.time()

            print('======================================================')
            print('Auto Train by Boost Round...')
            print('======================================================')

            n_param = len(parameter_grid)
            n_value = len(parameter_grid[0][1])
            param_name = []
            param_value = []
            for i in range(n_param):
                if len(parameter_grid[i][1]) != n_value:
                    raise ValueError('The number of value of parameters should be the same as each other!')
                param_name.append(parameter_grid[i][0])
                param_value.append(parameter_grid[i][1])

            for i_param_value in range(n_value):

                param_start_time = time.time()
                grid_search_tuple_list = []
                param_info = ''
                for i_param in range(n_param):
                    param_name_i = param_name[i_param]
                    param_value_i = param_value[i_param][i_param_value]
                    param_info += ' ' + utils.get_simple_param_name(param_name_i) + '-' + str(param_value_i)
                    grid_search_tuple_list.append((param_name_i, param_value_i))

                for i, (train_seed, cv_seed) in enumerate(zip(train_seed_list, cv_seed_list)):

                    epoch_start_time = time.time()
                    train_args['csv_idx'] = 'idx-' + str(i + 1)

                    print('======================================================')
                    print('Parameter:' + param_info)
                    print('------------------------------------------------------')
                    print('Epoch: {}/{} | train_seed: {} | cv_seed: {}'.format(i + 1, n_epoch, train_seed, cv_seed))

                    # Training Model
                    if num_boost_round is not None:
                        train_function(train_seed, cv_seed, parameters=base_parameters,
                                       grid_search_tuple_list=grid_search_tuple_list, num_boost_round=num_boost_round)
                    elif epochs is not None:
                        train_function(train_seed, cv_seed, parameters=base_parameters,
                                       grid_search_tuple_list=grid_search_tuple_list, epochs=epochs)
                    else:
                        train_function(train_seed, cv_seed, parameters=base_parameters,
                                       grid_search_tuple_list=grid_search_tuple_list)

                    print('======================================================')
                    print('Auto Training Epoch Done!')
                    print('Train Seed: {}'.format(train_seed))
                    print('Cross Validation Seed: {}'.format(cv_seed))
                    print('Epoch Time: {}s'.format(time.time() - epoch_start_time))
                    print('======================================================')

                print('======================================================')
                print('One Parameter Done!')
                print('Parameter Time: {}s'.format(time.time() - param_start_time))
                print('======================================================')

            print('======================================================')
            print('All Parameter Done!')
            print('Grid Searching Time: {}s'.format(time.time() - gs_start_time))
            print('======================================================')

    def auto_train(self, model_name=None, reduced_feature_list=None, n_epoch=1,
                   stack_final_epochs=None, base_parameters=None, train_args=None, train_options=None):
        """
            Automatically training a model for many times
        """

        # Get Train Function
        train_function = \
            self.get_train_function('auto_train', model_name, reduced_feature_list=reduced_feature_list,
                                    train_args=train_args, train_options=train_options)

        for i in range(n_epoch):

            train_seed = random.randint(0, 500)
            cv_seed = random.randint(0, 500)
            train_args['csv_idx'] = 'idx-' + str(i + 1)
            epoch_start_time = time.time()

            print('======================================================')
            print('Auto Training Epoch {}/{}...'.format(i + 1, n_epoch))

            if model_name == 'stack_t':
                train_function(train_seed, cv_seed)
                train_function_s = \
                    self.get_train_function('auto_train', 'stack_lgb', reduced_feature_list=reduced_feature_list,
                                            train_args=train_args, train_options=train_options)

                for ii in range(stack_final_epochs):
                    t_seed = random.randint(0, 500)
                    c_seed = random.randint(0, 500)
                    train_args['idx'] = 'auto_{}_epoch_{}'.format(i + 1, ii + 1)
                    train_function_s(t_seed, c_seed, auto_idx=i + 1, parameters=base_parameters)
            else:
                train_function(train_seed, cv_seed, parameters=base_parameters)

            print('======================================================')
            print('Auto Training Epoch Done!')
            print('Train Seed: {}'.format(train_seed))
            print('Cross Validation Seed: {}'.format(cv_seed))
            print('Epoch Time: {}s'.format(time.time() - epoch_start_time))
            print('======================================================')


if __name__ == "__main__":

    pass