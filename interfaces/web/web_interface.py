"""
Web Interface Module
Web-based interface for AI System using Flask.
"""

import os
import json
from typing import Optional, Dict, Any, List, Union
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import numpy as np

from core.logger import logger
from core.config import config


# Initialize Flask app
app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates",
)

# Configuration
app.config["UPLOAD_FOLDER"] = os.path.join(config.path.data_dir, "uploads")
app.config["ALLOWED_EXTENSIONS"] = {"csv", "json", "txt", "png", "jpg", "jpeg"}
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload size

# Ensure upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# Global model registry
MODEL_REGISTRY = {}


def allowed_file(filename: str) -> bool:
    """Check if a file has an allowed extension."""
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


@app.route("/")
def index():
    """Main page."""
    return render_template("index.html")


@app.route("/train")
def train_page():
    """Training page."""
    return render_template("train.html")


@app.route("/predict")
def predict_page():
    """Prediction page."""
    return render_template("predict.html")


@app.route("/explain")
def explain_page():
    """Explanation page."""
    return render_template("explain.html")


@app.route("/api/models", methods=["GET"])
def list_models():
    """List all available models."""
    models = [
        {
            "name": name,
            "type": type(model).__name__,
        }
        for name, model in MODEL_REGISTRY.items()
    ]
    return jsonify({"models": models, "count": len(models)})


@app.route("/api/train", methods=["POST"])
def train_model():
    """Train a model."""
    try:
        data = request.get_json()
        model_type = data.get("model_type")
        model_name = data.get("model_name", "default_model")

        if not model_type:
            return jsonify({"error": "model_type is required"}), 400

        # For now, just store the model name
        MODEL_REGISTRY[model_name] = {"type": model_type}

        logger.info(f"Trained model: {model_name} ({model_type})")
        return jsonify({
            "status": "success",
            "model_name": model_name,
            "model_type": model_type,
        })

    except Exception as e:
        logger.error(f"Training failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/predict", methods=["POST"])
def predict():
    """Make a prediction."""
    try:
        data = request.get_json()
        model_name = data.get("model_name")
        input_data = data.get("data")

        if not model_name:
            return jsonify({"error": "model_name is required"}), 400

        if not input_data:
            return jsonify({"error": "data is required"}), 400

        if model_name not in MODEL_REGISTRY:
            return jsonify({"error": f"Model {model_name} not found"}), 404

        # For now, return a mock prediction
        prediction = {
            "model": model_name,
            "input": input_data,
            "output": np.random.rand(10).tolist(),  # Mock prediction
        }

        logger.info(f"Made prediction with model: {model_name}")
        return jsonify(prediction)

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/explain", methods=["POST"])
def explain():
    """Generate explanation for a prediction."""
    try:
        data = request.get_json()
        model_name = data.get("model_name")
        input_data = data.get("data")
        method = data.get("method", "lime")

        if not model_name:
            return jsonify({"error": "model_name is required"}), 400

        if not input_data:
            return jsonify({"error": "data is required"}), 400

        if model_name not in MODEL_REGISTRY:
            return jsonify({"error": f"Model {model_name} not found"}), 404

        # For now, return a mock explanation
        explanation = {
            "model": model_name,
            "method": method,
            "input": input_data,
            "feature_importance": [
                {"feature": f"feature_{i}", "importance": float(np.random.rand())}
                for i in range(5)
            ],
        }

        logger.info(f"Generated explanation for model: {model_name} using {method}")
        return jsonify(explanation)

    except Exception as e:
        logger.error(f"Explanation failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Upload a file."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            logger.info(f"File uploaded: {filename}")
            return jsonify({
                "status": "success",
                "filename": filename,
                "filepath": filepath,
            })

        return jsonify({"error": "File type not allowed"}), 400

    except Exception as e:
        logger.error(f"File upload failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/static/<path:filename>")
def static_files(filename: str):
    """Serve static files."""
    return send_from_directory(app.static_folder, filename)


@app.route("/templates/<path:filename>")
def template_files(filename: str):
    """Serve template files."""
    return send_from_directory(app.template_folder, filename)


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500


def create_web_interface():
    """Create and configure the web interface."""
    # Create static and templates directories if they don't exist
    os.makedirs("static", exist_ok=True)
    os.makedirs("templates", exist_ok=True)

    # Create basic HTML templates
    _create_html_templates()

    return app


def _create_html_templates():
    """Create basic HTML templates for the web interface."""
    # Index template
    index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI System - Home</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f0f0f0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background-color: #4a90d9;
            color: white;
            padding: 20px;
            text-align: center;
        }
        nav {
            background-color: #333;
            padding: 10px;
        }
        nav a {
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            margin: 0 5px;
            border-radius: 5px;
        }
        nav a:hover {
            background-color: #555;
        }
        .content {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        footer {
            text-align: center;
            padding: 20px;
            color: #666;
        }
    </style>
</head>
<body>
    <header>
        <h1>AI System</h1>
        <p>Machine Learning Platform</p>
    </header>
    <nav>
        <a href="/">Home</a>
        <a href="/train">Train</a>
        <a href="/predict">Predict</a>
        <a href="/explain">Explain</a>
    </nav>
    <div class="container">
        <div class="content">
            <h2>Welcome to AI System</h2>
            <p>This is a comprehensive platform for training, evaluating, and deploying machine learning models.</p>
            <h3>Features:</h3>
            <ul>
                <li>Support for multiple model types (Machine Learning and Deep Learning)</li>
                <li>Data preprocessing and augmentation</li>
                <li>Model training and evaluation</li>
                <li>Prediction and explanation</li>
                <li>REST API for model serving</li>
                <li>CLI and GUI interfaces</li>
            </ul>
        </div>
    </div>
    <footer>
        <p>AI System v1.0.0</p>
    </footer>
</body>
</html>
    """

    # Train template
    train_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI System - Train Model</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f0f0f0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background-color: #4a90d9;
            color: white;
            padding: 20px;
            text-align: center;
        }
        nav {
            background-color: #333;
            padding: 10px;
        }
        nav a {
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            margin: 0 5px;
            border-radius: 5px;
        }
        nav a:hover {
            background-color: #555;
        }
        .content {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input, select, textarea {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            background-color: #4a90d9;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #3a7bc8;
        }
        #training-log {
            height: 300px;
            overflow-y: auto;
            background-color: #f9f9f9;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-top: 20px;
        }
        footer {
            text-align: center;
            padding: 20px;
            color: #666;
        }
    </style>
</head>
<body>
    <header>
        <h1>AI System</h1>
        <p>Train Model</p>
    </header>
    <nav>
        <a href="/">Home</a>
        <a href="/train">Train</a>
        <a href="/predict">Predict</a>
        <a href="/explain">Explain</a>
    </nav>
    <div class="container">
        <div class="content">
            <h2>Train a Model</h2>
            <form id="train-form">
                <div class="form-group">
                    <label for="model-name">Model Name:</label>
                    <input type="text" id="model-name" name="model_name" value="my_model" required>
                </div>
                <div class="form-group">
                    <label for="model-type">Model Type:</label>
                    <select id="model-type" name="model_type" required>
                        <option value="linear_regression">Linear Regression</option>
                        <option value="random_forest">Random Forest</option>
                        <option value="kmeans">K-Means</option>
                        <option value="simple_nn">Neural Network</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="data-file">Data File:</label>
                    <input type="file" id="data-file" name="data_file" accept=".csv,.json" required>
                </div>
                <div class="form-group">
                    <label for="target-column">Target Column:</label>
                    <input type="text" id="target-column" name="target_column" value="target" required>
                </div>
                <div class="form-group">
                    <label for="epochs">Epochs:</label>
                    <input type="number" id="epochs" name="epochs" value="10" min="1">
                </div>
                <div class="form-group">
                    <label for="batch-size">Batch Size:</label>
                    <input type="number" id="batch-size" name="batch_size" value="32" min="1">
                </div>
                <div class="form-group">
                    <label for="learning-rate">Learning Rate:</label>
                    <input type="number" id="learning-rate" name="learning_rate" value="0.001" step="0.0001">
                </div>
                <button type="button" onclick="startTraining()">Start Training</button>
            </form>
            <div id="training-log"></div>
        </div>
    </div>
    <footer>
        <p>AI System v1.0.0</p>
    </footer>
    <script>
        function startTraining() {
            const modelName = document.getElementById('model-name').value;
            const modelType = document.getElementById('model-type').value;
            const targetColumn = document.getElementById('target-column').value;
            const epochs = document.getElementById('epochs').value;
            const batchSize = document.getElementById('batch-size').value;
            const learningRate = document.getElementById('learning-rate').value;

            const logDiv = document.getElementById('training-log');
            logDiv.innerHTML += 'Starting training...\\n';

            fetch('/api/train', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model_name: modelName,
                    model_type: modelType,
                    target_column: targetColumn,
                    epochs: parseInt(epochs),
                    batch_size: parseInt(batchSize),
                    learning_rate: parseFloat(learningRate),
                }),
            })
            .then(response => response.json())
            .then(data => {
                logDiv.innerHTML += JSON.stringify(data, null, 2) + '\\n';
            })
            .catch(error => {
                logDiv.innerHTML += 'Error: ' + error + '\\n';
            });
        }
    </script>
</body>
</html>
    """

    # Predict template
    predict_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI System - Predict</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f0f0f0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background-color: #4a90d9;
            color: white;
            padding: 20px;
            text-align: center;
        }
        nav {
            background-color: #333;
            padding: 10px;
        }
        nav a {
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            margin: 0 5px;
            border-radius: 5px;
        }
        nav a:hover {
            background-color: #555;
        }
        .content {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input, select, textarea {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            background-color: #4a90d9;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #3a7bc8;
        }
        #prediction-results {
            background-color: #f9f9f9;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-top: 20px;
            white-space: pre-wrap;
        }
        footer {
            text-align: center;
            padding: 20px;
            color: #666;
        }
    </style>
</head>
<body>
    <header>
        <h1>AI System</h1>
        <p>Make Predictions</p>
    </header>
    <nav>
        <a href="/">Home</a>
        <a href="/train">Train</a>
        <a href="/predict">Predict</a>
        <a href="/explain">Explain</a>
    </nav>
    <div class="container">
        <div class="content">
            <h2>Make a Prediction</h2>
            <form id="predict-form">
                <div class="form-group">
                    <label for="model-name">Model:</label>
                    <select id="model-name" name="model_name" required>
                        <option value="">Select a model...</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="input-data">Input Data (JSON):</label>
                    <textarea id="input-data" name="input_data" rows="5" required>{"features": [1.0, 2.0, 3.0, 4.0]}</textarea>
                </div>
                <button type="button" onclick="makePrediction()">Make Prediction</button>
            </form>
            <div id="prediction-results"></div>
        </div>
    </div>
    <footer>
        <p>AI System v1.0.0</p>
    </footer>
    <script>
        // Load models on page load
        fetch('/api/models')
            .then(response => response.json())
            .then(data => {
                const modelSelect = document.getElementById('model-name');
                data.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.name;
                    option.textContent = model.name + ' (' + model.type + ') ';
                    modelSelect.appendChild(option);
                });
            });

        function makePrediction() {
            const modelName = document.getElementById('model-name').value;
            const inputData = document.getElementById('input-data').value;

            const resultsDiv = document.getElementById('prediction-results');
            resultsDiv.innerHTML = 'Making prediction...\\n';

            try {
                const data = JSON.parse(inputData);

                fetch('/api/predict', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        model_name: modelName,
                        data: data,
                    }),
                })
                .then(response => response.json())
                .then(data => {
                    resultsDiv.innerHTML = JSON.stringify(data, null, 2);
                })
                .catch(error => {
                    resultsDiv.innerHTML = 'Error: ' + error;
                });
            } catch (error) {
                resultsDiv.innerHTML = 'Invalid JSON: ' + error;
            }
        }
    </script>
</body>
</html>
    """

    # Explain template
    explain_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI System - Explain</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f0f0f0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background-color: #4a90d9;
            color: white;
            padding: 20px;
            text-align: center;
        }
        nav {
            background-color: #333;
            padding: 10px;
        }
        nav a {
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            margin: 0 5px;
            border-radius: 5px;
        }
        nav a:hover {
            background-color: #555;
        }
        .content {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input, select, textarea {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            background-color: #4a90d9;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #3a7bc8;
        }
        #explanation-results {
            background-color: #f9f9f9;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-top: 20px;
            white-space: pre-wrap;
        }
        footer {
            text-align: center;
            padding: 20px;
            color: #666;
        }
    </style>
</head>
<body>
    <header>
        <h1>AI System</h1>
        <p>Explain Predictions</p>
    </header>
    <nav>
        <a href="/">Home</a>
        <a href="/train">Train</a>
        <a href="/predict">Predict</a>
        <a href="/explain">Explain</a>
    </nav>
    <div class="container">
        <div class="content">
            <h2>Generate Explanation</h2>
            <form id="explain-form">
                <div class="form-group">
                    <label for="model-name">Model:</label>
                    <select id="model-name" name="model_name" required>
                        <option value="">Select a model...</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="method">Explanation Method:</label>
                    <select id="method" name="method">
                        <option value="lime">LIME</option>
                        <option value="shap">SHAP</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="input-data">Input Data (JSON):</label>
                    <textarea id="input-data" name="input_data" rows="5" required>{"features": [1.0, 2.0, 3.0, 4.0]}</textarea>
                </div>
                <button type="button" onclick="generateExplanation()">Generate Explanation</button>
            </form>
            <div id="explanation-results"></div>
        </div>
    </div>
    <footer>
        <p>AI System v1.0.0</p>
    </footer>
    <script>
        // Load models on page load
        fetch('/api/models')
            .then(response => response.json())
            .then(data => {
                const modelSelect = document.getElementById('model-name');
                data.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.name;
                    option.textContent = model.name + ' (' + model.type + ') ';
                    modelSelect.appendChild(option);
                });
            });

        function generateExplanation() {
            const modelName = document.getElementById('model-name').value;
            const method = document.getElementById('method').value;
            const inputData = document.getElementById('input-data').value;

            const resultsDiv = document.getElementById('explanation-results');
            resultsDiv.innerHTML = 'Generating explanation...\\n';

            try {
                const data = JSON.parse(inputData);

                fetch('/api/explain', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        model_name: modelName,
                        data: data,
                        method: method,
                    }),
                })
                .then(response => response.json())
                .then(data => {
                    resultsDiv.innerHTML = JSON.stringify(data, null, 2);
                })
                .catch(error => {
                    resultsDiv.innerHTML = 'Error: ' + error;
                });
            } catch (error) {
                resultsDiv.innerHTML = 'Invalid JSON: ' + error;
            }
        }
    </script>
</body>
</html>
    """

    # Write templates
    with open("templates/index.html", "w") as f:
        f.write(index_html)

    with open("templates/train.html", "w") as f:
        f.write(train_html)

    with open("templates/predict.html", "w") as f:
        f.write(predict_html)

    with open("templates/explain.html", "w") as f:
        f.write(explain_html)

    logger.info("Created HTML templates for web interface")


def run_web_interface(
    host: str = "0.0.0.0",
    port: int = 5000,
    debug: bool = True,
) -> None:
    """
    Run the web interface.
    
    Args:
        host: Host address.
        port: Port number.
        debug: Whether to run in debug mode.
    """
    app = create_web_interface()
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_web_interface()
