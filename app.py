from flask import Flask, request, jsonify, render_template
from flask_restful import Resource, Api
import pickle
import pandas as pd
import numpy as np

app = Flask(__name__)
api = Api(app)

print("Loading model...")
with open('best_model.pkl', 'rb') as f:
    model = pickle.load(f)

with open('scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

with open('feature_names.pkl', 'rb') as f:
    feature_names = pickle.load(f)

print(f"   Model type: Logistic Regression")
print(f"   Features: {len(feature_names)}")
print(f"   Classes: {model.classes_}")

class WinePrediction(Resource):
    """
    POST /api/predict
    Predict wine quality based on chemical properties
    """
    def post(self):
        try:
            
            data = request.get_json()

            if not data:
                return {
                    'status': 'error',
                    'message': 'No data provided'
                }, 400
            
            missing_features = [f for f in feature_names if f not in data]
            if missing_features:
                return {
                    'status': 'error',
                    'message': f'Missing Features: {missing_features}'
                }, 400
            
            input_df = pd.DataFrame([data])
            input_df = input_df[feature_names]

            input_scaled = scaler.transform(input_df)

            prediction = model.predict(input_scaled)[0]
            probabilities = model.predict_proba(input_scaled)[0]

            classes = model.classes_

            response = {
                'status': 'success',
                'prediction': str(prediction),
                'confidence': float(max(probabilities)),
                'probabilities': {
                    str(classes[0]): float(probabilities[0]),
                    str(classes[1]): float(probabilities[1]),
                    str(classes[2]): float(probabilities[2])
                },
                'input_features': data
            }

            return response, 200
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }, 500
        
class FeatureInfo(Resource):
    """
    GET /api/features
    Returns list of required features for prediction
    """
    
    def get(self):
        return {
            'status': 'success',
            'features': feature_names,
            'count': len(feature_names),
            'description': 'Chemical properties required for wine quality prediction'
        }, 200
    
class ModelInfo(Resource):
    """
    GET /api/model
    Returns information about the trained model
    """
    def get(self):
        return {
            'status': 'success',
            'model_type': 'Logistic Regression',
            'classes': list(model.classes_),
            'n_features': len(feature_names),
            'features': feature_names,
            'requires_scaling': True,
            'scaler_type': 'StandardScaler'
        }, 200

class HealthCheck(Resource):
    """
    GET /api/health
    Health check endpoint
    """
    def get(self):
        return {
            'status': 'healthy',
            'service': 'Wine Quality Prediction API',
            'model_loaded': model is not None,
            'scaler_loaded': scaler is not None,
            'features_loaded': feature_names is not None
        }, 200

class SampleData(Resource):
    """
    GET /api/samples
    Returns preset wine samples and feature ranges for UI
    """
    def get(self):
        try:
            from sklearn.datasets import load_wine

            wine = load_wine()

            sklearn_to_model = {
                'alcohol': 'Alcohol',
                'malic_acid': 'Malic_Acid',
                'ash': 'Ash',
                'alcalinity_of_ash': 'Ash_Alcanity',
                'magnesium': 'Magnesium',
                'total_phenols': 'Total_Phenols',
                'flavanoids': 'Flavanoids',
                'nonflavanoid_phenols': 'Nonflavanoid_Phenols',
                'proanthocyanins': 'Proanthocyanins',
                'color_intensity': 'Color_Intensity',
                'hue': 'Hue',
                'od280/od315_of_diluted_wines': 'OD280',
                'proline': 'Proline'
            }

            df = pd.DataFrame(wine.data, columns=wine.feature_names)
            df['target'] = wine.target

            np.random.seed(42)
            class_0_indices = np.where(df['target'] == 0)[0]
            class_1_indices = np.where(df['target'] == 1)[0]
            class_2_indices = np.where(df['target'] == 2)[0]

            selected_indices = (
                list(np.random.choice(class_0_indices, 4, replace=False)) +
                list(np.random.choice(class_1_indices, 3, replace=False)) +
                list(np.random.choice(class_2_indices, 3, replace=False))
            )

            presets = []
            class_names = ['High', 'Medium', 'Low']

            for i, idx in enumerate(selected_indices, 1):
                row = df.iloc[idx]
                features = {}
                for sklearn_name, model_name in sklearn_to_model.items():
                    features[model_name] = float(row[sklearn_name])

                presets.append({
                    'id': i,
                    'name': f'Wine Sample {i}',
                    'description': f'{class_names[int(row["target"])]} quality profile',
                    'expectedClass': class_names[int(row['target'])],
                    'features': features
                })

            feature_ranges = {}
            for sklearn_name, model_name in sklearn_to_model.items():
                col_data = df[sklearn_name]
                feature_ranges[model_name] = {
                    'min': float(col_data.min()),
                    'max': float(col_data.max()),
                    'mean': float(col_data.mean()),
                    'std': float(col_data.std())
                }

            return {
                'status': 'success',
                'presets': presets,
                'featureRanges': feature_ranges,
                'totalSamples': len(presets)
            }, 200

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }, 500

# API Routes
api.add_resource(WinePrediction, '/api/predict')
api.add_resource(FeatureInfo, '/api/features')
api.add_resource(ModelInfo, '/api/model')
api.add_resource(HealthCheck, '/api/health')
api.add_resource(SampleData, '/api/samples')

@app.route('/')
def home():
    """Serve the main HTML interface"""
    return render_template('index.html', features=feature_names)

@app.route('/guide')
def guide():
    """Serve the user guide page"""
    return render_template('guide.html')


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found',
        'available_endpoints': [
            'GET /',
            'GET /guide',
            'GET /api/health',
            'GET /api/model',
            'GET /api/features',
            'GET /api/samples',
            'POST /api/predict'
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("WINE QUALITY PREDICTION API")
    print("="*60)
    print("\nRESTful API Endpoints:")
    print("  GET    /                - Web interface")
    print("  GET    /api/health      - Health check")
    print("  GET    /api/model       - Model information")
    print("  GET    /api/features    - Feature list")
    print("  GET    /api/samples     - Get sample data")
    print("  POST   /api/predict     - Make prediction")
    print("\n" + "="*60)
    print("Server running at: http://localhost:5000")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)