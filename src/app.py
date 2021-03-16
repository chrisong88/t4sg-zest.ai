from flask import Flask, request, session, jsonify, redirect, render_template
from flask_cors import CORS

# Needed for surgeo route
import pandas as pd 
import surgeo
import pickle
#import zrp_predict
import json

import warnings
import pandas as pd
import numpy as np
warnings.filterwarnings(action='once')
import datetime as dt
import os, re, sys
from sklearn.preprocessing import MultiLabelBinarizer, OrdinalEncoder
from category_encoders import TargetEncoder
from xgboost import XGBClassifier
import zrp_predict
from zrp_predict import ZRPFeatureEngineering, Basic_PreProcessor


app = Flask(__name__)
CORS(app)

@app.route('/hello')
def say_hello_world():
    return {'result': "Flask says Hello World"}

@app.route('/surgeo', methods=["GET"])
def run_surgeo():
    # TO-DO: @KAYLA
    # Build out a public facing API that responds to a get request with the surname and zip code as query arguments. 
    # The API should return the probabilities of each race prediction as a JSON object.
    # Example of return object: {'AAPI': .56, 'Hispanic': .32, ..., 'White': .10}

    surname = request.args.get('surname')
    zipcode = request.args.get('zipcode')
    surname_series = pd.Series([surname])
    zip_series = pd.Series([zipcode]) 

    sg = surgeo.SurgeoModel()
    sg_results = sg.get_probabilities(surname_series, zip_series)

    sg_json = pd.DataFrame.to_json(sg_results)
    return(sg_json)

    # END OF SURGEO API; END OF TO-DO @KAYLA

@app.route('/zrp', methods=["GET"])
def zrp():
    # TO-DO: @RAKESH
    # Build out a public facing API that responds to a get request with the full name, address, age, and gender as a query arguments. 
    # The API should return the probabilities of each race prediction as a JSON object.
    # Example of return object: {'AAPI': .56, 'Hispanic': .32, ..., 'White': .10}
    # Required fields: 'Name_First', 'Name_Last', 'Name_Middle', 'Zipcode', 'Precinct_Split','Gender', 'County_Code','Congressional_District', 'Senate_District', 'House_District', 'Birth_Date'

    # As part of this, you should add any relevant pickle files that you might want to call to the directory "picklefiles".
    # These files will be stored on the server and your API will be able to call them in order to make predictions.
    # Currently, there's just one file in the picklefiles folder: the pickled Florida predictor that was sent over by Kasey, but feel free to add more.
    # Also, if you're having trouble accessing a picklefile in the picklefiles folder, DM Chris. It may be a problem with how the Dockerfile is set up
    # and how it copies the picklefile folder over to the container.

    zipcode = request.args.get('zipcode')
    last_name = request.args.get('last_name')
    first_name = request.args.get('first_name')
    middle_name = request.args.get('middle_name')
    precinct_split = request.args.get('precinct_split')
    gender = request.args.get('gender')
    county_code = request.args.get('county_code')
    congressional_district = request.args.get('congressional_district')
    senate_district = request.args.get('senate_district')
    house_district = request.args.get('house_district')
    birth_date = request.args.get('birth_date')

    data = {'Name_First': [str(first_name)], 'Name_Last': [str(last_name)], 'Name_Middle': [str(middle_name)], 'Zipcode': [int(zipcode)], 'Precinct_Split': [str(precinct_split)], 'Gender': [str(gender)], 'County_Code': [str(county_code)], 'Congressional_District':[float(congressional_district)], 'Senate_District': [float(senate_district)], 'House_District': [float(house_district)], 'Birth_Date': [str(birth_date)]}
    #data = {'Name_First': ['George'], 'Name_Last': ['Chambers'], 'Name_Middle': ['William'], 'Zipcode': [34293], 'Precinct_Split': ['NaN'], 'Gender': ['M'], 'County_Code': ['SAR'], 'Congressional_District':[17.0], 'Senate_District': [23.0], 'House_District': [74.0], 'Birth_Date': ['12/02/1951']}
    sample = pd.DataFrame(data)
    preds = generatePredictions(sample)

    preds_data = {'American Indian': preds[0], 'Asian Pacific Islander': preds[1], 'Black': preds[2], 'Hispanic': preds[3], 'White': preds[4], 'Other': preds[5], 'Multi': preds[6]}
    json_preds = json.dumps(preds_data)
    return json_preds
    
    # END OF ZRP API; END OF TO-DO @RAKESH


## CHANGE
class Basic_PreProcessor():
    '''This class is used to execute general ZRP preprocessing. This is an example class requiring access to the proxy_fe.py script & functions. 
    ''' 

    def __init__(self):
        pass
    def fit(self):
        pass
    def transform(self, data):
        from proxy_fe import fl_address_clean
        from proxy_fe import lower_case
        from proxy_fe import handle_compounds
        
#         # create id
#         data["applicant_id"] =  data.index
        
        data_fl_co_all_sample_clean = data.copy()

        # clean address information
        data_fl_co_all_sample_clean['Zipcode'] = data_fl_co_all_sample_clean['Zipcode'].astype(str).str.extract(r"(^\d{5})").astype(str)

        # handle dashes and spaces
        data_fl_co_all_sample_clean['Name_Last'] = data_fl_co_all_sample_clean['Name_Last'].str.replace('-', ' ') # replace dashes with spaces
        data_fl_co_all_sample_clean['Name_Last'] = data_fl_co_all_sample_clean['Name_Last'].str.replace(' +', ' ') # replace double spaces with single spaces

        # handle casing
        data_fl_co_all_sample_clean = lower_case(data_fl_co_all_sample_clean, ['Name_Last', 'Name_First', 'Name_Middle']) 

        # compound names (row indicies are not preserved!)
        # data_fl_co_all_sample_clean = handle_compounds(data_fl_co_all_sample_clean)
        return(data_fl_co_all_sample_clean)


class ZRPFeatureEngineering():
    '''This class is used to execute general ZRP feature engineering.''' 
    
    def __init__(self):
        
        # label encode via target
        self.label_encoded_columns = ['Name_First', 'Name_Last', 'Name_Middle', 'Zipcode', 'Precinct_Split']
  
        # ordinal encoding
        self.ordinal_encoded_columns = ['Gender', 'County_Code']
        self.oe = OrdinalEncoder()

        # numerical columns (categories, but let the tree figure it out...)
        self.numerical_columns =  ['Congressional_District', 'Senate_District', 'House_District']
        
        # dates
        self.date_columns = ['Birth_Date']


    def _process_target(self, y):                
        y_unique = y.unique()
        y_unique.sort()
        self.n_classes = len(y_unique)

        census_code_mapping = {1: 'AI', 2: 'API', 3: 'Black', 4: 'Hispanic', 5: 'White', 6: 'Other', 7: 'Multi', 9: 'Unknown'}

        # handle multi-labeled output
        self.mlb = MultiLabelBinarizer(classes = y_unique)
        self.mlb_columns = [census_code_mapping[x] for x in y_unique]
        
        self.mlb.fit(y.values.reshape(-1,1))
        y_ohe = pd.DataFrame(self.mlb.transform(y.values.reshape(-1,1)), columns=self.mlb_columns)

        self.le = {}
        for i in range(self.n_classes):
            self.le[i] = TargetEncoder()

        return y_ohe
    
    def fit(self, X, y):
        
        X = X.reset_index(drop=True)
        y = y.reset_index(drop=True)        
        
        y_ohe = self._process_target(y)
        
        # fit label encoded columns
        for i in range(self.n_classes):
            self.le[i].fit(X[self.label_encoded_columns], y_ohe.iloc[:,i])

        # fit ordinal columns
        self.oe.fit(X[self.ordinal_encoded_columns]) 
        

        return self
    
    def transform(self, X):

        X = X.reset_index(drop=True)
        
        # handle missing gender
        X[['Gender']] = X[['Gender']].replace(to_replace='nan', value='U')
        
        # transform X
        X_date_convert = X[self.date_columns].apply(pd.to_datetime, errors='coerce')
        X_date_convert = X_date_convert[self.date_columns].apply(lambda x: getattr(pd.DatetimeIndex(x),'year'))
  
        X_fe = pd.concat([self.le[i].transform(X[self.label_encoded_columns]) for i in range(self.n_classes)],
                         axis=1, sort=False
                        )

        X_fe = pd.concat([X_fe,
                          pd.DataFrame(self.oe.transform(X[self.ordinal_encoded_columns])),
                          X_date_convert[self.date_columns],
                          X[self.numerical_columns]
                         ], axis=1, sort=False)
    
        label_encoded_colname = []
        for label in self.mlb_columns:
            for col in self.label_encoded_columns:
                label_encoded_colname.append(label+'_'+col)

        X_fe.columns = label_encoded_colname + self.ordinal_encoded_columns + self.date_columns + self.numerical_columns

        return X_fe

def generatePredictions(data):
    bpp = Basic_PreProcessor()
    sample_data_transform_0 = bpp.transform(data)
    zrp_fe = pd.read_pickle(r'/code/picklefiles/zrp_feature_engineering.obj')
    sample_data_transform_1 = zrp_fe.transform(sample_data_transform_0)
    zrp_model = pd.read_pickle(r'/code/picklefiles/clf-all-fl-30pct-sample.obj')
    zrp_result_probs = np.round(zrp_model.predict_proba(sample_data_transform_1),3)
    return zrp_result_probs