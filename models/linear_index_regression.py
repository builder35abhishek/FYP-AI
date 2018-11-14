from os import path
import time

import pandas as pd
from sklearn import linear_model
import numpy as np
from sklearn.metrics import mean_squared_error

from models.index_regression import IndexRegressionModel

class LinearIndexRegression(IndexRegressionModel):
    MODEL = "linear_index_regression"

    def __init__(self, model_options, input_options, stock_code, load=False, saved_model_dir=None, saved_model_path=None):
        IndexRegressionModel.__init__(self, model_options, input_options, stock_code)

        if not load or saved_model_dir is None:
            self.model = linear_model.LinearRegression()
        else:
            model_path = saved_model_path if saved_model_path is not None else self.get_saved_model_path(saved_model_dir)
            if model_path is not None:
                self.load_model(path.join(saved_model_dir, model_path), self.SKLEARN_MODEL)

    def train(self, xs, ys):
        self.model.fit(xs, ys)

    def predict(self, x):
        return self.model.predict(x).flatten()

    def save(self, saved_model_dir):
        # create the saved models directory
        self.create_model_dir(saved_model_dir)

        model_name = self.get_model_name()
        model_path = path.join(self.stock_code, self.get_model_type_hash())

        # save the model
        self.save_model(path.join(saved_model_dir, model_path, model_name), self.SKLEARN_MODEL)

        # load models data
        models_data = self.load_models_data(saved_model_dir)
        if models_data is None:
            models_data = {"models": {}, "modelTypes": {}}

        # update models data
        models_data = self.update_models_data(models_data, model_name, model_path)

        # save models data
        self.save_models_data(models_data, saved_model_dir)

    def update_models_data(self, models_data, model_name, model_path):
        if self.stock_code not in models_data["models"]:
            models_data["models"][self.stock_code] = {}

        model_type_hash = self.get_model_type_hash()

        if model_type_hash not in models_data["models"][self.stock_code]:
            models_data["models"][self.stock_code][model_type_hash] = []

        model_data = {}
        model_data["model_name"] = model_name
        model_data["model_path"] = model_path
        model_data["model"] = self.MODEL

        models_data["models"][self.stock_code][model_type_hash].append(model_data)

        if model_type_hash not in models_data["modelTypes"]:
            models_data["modelTypes"][model_type_hash] = self.get_model_type()

        return models_data

    def get_model_type(self):
        return {"model": self.MODEL, "modelOptions": self.model_options, "inputOptions": self.input_options}

    def get_model_type_hash(self):
        model_type = self.get_model_type()

        model_type_json_str = self.get_json_str(model_type)

        return self.hash_str(model_type_json_str)

    def get_model_name(self):
        model_name = []
        model_name.append(self.get_model_type_hash())
        model_name.append(str(int(time.time())))
        return "_".join(model_name) + ".model"

    def get_saved_model_path(self, saved_model_dir):
        models_data = self.load_models_data(saved_model_dir)
        if models_data is None:
            return None

        if self.stock_code not in models_data["models"]:
            return None

        model_type_hash = self.get_model_type_hash()

        if model_type_hash not in models_data["models"]:
            return None

        return models_data["models"][self.stock_code][model_type_hash][-1]["model_path"]

    def get_model_display_name(self):
        options_name = [str(self.model_options["n"]), "days", "change" if not self.model_options["use_stock_price"] else "price"]
        return "Linear Regression (%s)" % " ".join(options_name)

    def error(self, y_true, y_pred):
        return mean_squared_error(y_true, y_pred)

    @staticmethod
    def calculate_average_mean_squared_error(model_options, input_options, stock_code, iteration_limit, data_dir):

        stock_prices = pd.read_csv (data_dir + '\\stock_prices\\' + stock_code + '.csv')
        cleaned_prices = stock_prices

        i = 0
        n = input_options["config"][0]["n"]
        error_sum = 0

        listX = np.arange(n, 0, -1).reshape(-1, 1)

        for i in range(iteration_limit):
            # create model
            m = LinearIndexRegression(model_options, input_options, stock_code)

            # prepare d1 to d10     
            listY = cleaned_prices[input_options["column"]][i + 1:i + 1 + n].values

            m.train(listX, listY)
            
            predict_n = input_options["config"][0]["predict_n"] if "predict_n" in input_options["config"][0] else 1        
            x = np.arange(input_options["config"][0]["n"], input_options["config"][0]["n"] + predict_n).reshape(-1, 1)
            y_pred = m.predict(x)
            print(y_pred, cleaned_prices[input_options["column"]][i:i + y_pred.shape[0]].values)

            error_sum += m.error(cleaned_prices[input_options["column"]][i:i + y_pred.shape[0]].values, y_pred)
            
        return error_sum/iteration_limit

    def get_all_models(stock_code, saved_model_dir, last_price):
        models_data = Model.load_models_data(saved_model_dir)
        if models_data is None:
            return None

        if stock_code not in models_data["models"]:
            return None

        models = []
        for model_type in models_data["models"][stock_code]:
            models.append(LinearIndexRegression(
                models_data["modelTypes"][model_type]["modelOptions"],
                models_data["modelTypes"][model_type]["inputOptions"],
                stock_code,
                load=True,
                saved_model_dir=saved_model_dir,
                saved_model_path=models_data["models"][stock_code][model_type][-1]["model_path"]))

        return models
