import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import plotly.express as px
import plotly.graph_objects as go

class RatioOptimizer:
    """
    Machine Learning model for predicting optimal student-teacher ratios 
    based on subject difficulty, teacher experience, and other factors.
    """
    
    def __init__(self):
        """Initialize the ML model"""
        # Create a pipeline with preprocessing and model
        self.pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', RandomForestRegressor(
                n_estimators=100, 
                max_depth=10,
                min_samples_split=5,
                random_state=42
            ))
        ])
        
        # Store feature names for later use
        self.feature_names = [
            'subject_difficulty',
            'teacher_experience',
            'subject_importance',
            'student_proficiency',
            'resource_availability'
        ]
        
        # Store training data
        self.X_train = None
        self.y_train = None
        self.X_test = None
        self.y_test = None
        self.trained = False
        
        # Store synthetic data for exploration
        self.synthetic_data = None
    
    def generate_synthetic_data(self, n_samples=200):
        """
        Generate synthetic data for training the model.
        In a real-world application, this would be replaced with actual historical data.
        """
        # Set random seed for reproducibility
        np.random.seed(42)
        
        # Generate features
        subject_difficulty = np.random.uniform(1, 10, n_samples)  # 1-10 scale
        teacher_experience = np.random.uniform(1, 30, n_samples)  # 1-30 years
        subject_importance = np.random.uniform(1, 10, n_samples)  # 1-10 scale
        student_proficiency = np.random.uniform(1, 10, n_samples)  # 1-10 scale
        resource_availability = np.random.uniform(1, 10, n_samples)  # 1-10 scale
        
        # Create feature matrix
        X = np.column_stack([
            subject_difficulty,
            teacher_experience,
            subject_importance,
            student_proficiency,
            resource_availability
        ])
        
        # Generate target variable with some noise
        # Formula: More difficult subjects and less experienced teachers need lower ratios
        # Higher student proficiency and resource availability allow for higher ratios
        y = (
            15  # Base ratio
            - 0.7 * subject_difficulty  # Harder subjects need lower ratios
            + 0.2 * teacher_experience  # More experienced teachers can handle higher ratios
            - 0.3 * subject_importance  # More important subjects need more attention (lower ratios)
            + 0.4 * student_proficiency  # Higher proficiency allows higher ratios
            + 0.3 * resource_availability  # More resources allow higher ratios
            + np.random.normal(0, 1, n_samples)  # Add noise
        )
        
        # Ensure ratios are within reasonable bounds (5 to 25)
        y = np.clip(y, 5, 25)
        
        # Create DataFrame for easier manipulation
        data = pd.DataFrame({
            'subject_difficulty': subject_difficulty,
            'teacher_experience': teacher_experience,
            'subject_importance': subject_importance,
            'student_proficiency': student_proficiency,
            'resource_availability': resource_availability,
            'optimal_ratio': y
        })
        
        self.synthetic_data = data
        return data
    
    def train(self, data=None):
        """
        Train the ML model.
        If no data is provided, synthetic data will be used.
        
        Args:
            data: Optional pandas DataFrame with training data
        
        Returns:
            Dictionary with training metrics
        """
        # Generate or use provided data
        if data is None:
            data = self.generate_synthetic_data()
        
        # Split features and target
        X = data[self.feature_names].values
        y = data['optimal_ratio'].values
        
        # Split into training and testing sets
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train the model
        self.pipeline.fit(self.X_train, self.y_train)
        
        # Evaluate the model
        train_pred = self.pipeline.predict(self.X_train)
        test_pred = self.pipeline.predict(self.X_test)
        
        train_mse = mean_squared_error(self.y_train, train_pred)
        test_mse = mean_squared_error(self.y_test, test_pred)
        train_r2 = r2_score(self.y_train, train_pred)
        test_r2 = r2_score(self.y_test, test_pred)
        
        self.trained = True
        
        return {
            'train_mse': train_mse,
            'test_mse': test_mse,
            'train_r2': train_r2,
            'test_r2': test_r2
        }
    
    def predict(self, inputs):
        """
        Predict optimal ratios based on inputs.
        
        Args:
            inputs: Dictionary or DataFrame with feature values
        
        Returns:
            Predicted optimal ratio
        """
        if not self.trained:
            self.train()
        
        # Convert inputs to numpy array
        if isinstance(inputs, dict):
            # Extract features in the correct order
            features = np.array([
                inputs.get('subject_difficulty', 5),
                inputs.get('teacher_experience', 10),
                inputs.get('subject_importance', 5),
                inputs.get('student_proficiency', 5),
                inputs.get('resource_availability', 5)
            ]).reshape(1, -1)
        elif isinstance(inputs, pd.DataFrame):
            features = inputs[self.feature_names].values
        else:
            raise ValueError("Inputs must be a dictionary or DataFrame")
        
        # Make prediction
        predicted_ratio = self.pipeline.predict(features)
        
        if isinstance(inputs, dict):
            return predicted_ratio[0]
        else:
            return predicted_ratio
    
    def create_feature_importance_chart(self):
        """
        Create a chart showing feature importance.
        
        Returns:
            Plotly figure object
        """
        if not self.trained:
            self.train()
        
        # Get feature importances from random forest
        importances = self.pipeline.named_steps['model'].feature_importances_
        
        # Create DataFrame for plotting
        importance_df = pd.DataFrame({
            'Feature': self.feature_names,
            'Importance': importances
        })
        
        # Sort by importance
        importance_df = importance_df.sort_values('Importance', ascending=False)
        
        # Create bar chart
        fig = px.bar(
            importance_df, 
            x='Importance', 
            y='Feature',
            orientation='h',
            title='Feature Importance in Optimal Ratio Prediction',
            color='Importance',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            yaxis=dict(title=''),
            xaxis=dict(title='Relative Importance'),
            height=400
        )
        
        return fig
    
    def create_3d_relationship_plot(self, feature1='teacher_experience', 
                                    feature2='subject_difficulty', 
                                    feature3='optimal_ratio'):
        """
        Create a 3D plot showing the relationship between two features and the target.
        
        Args:
            feature1: First feature to plot
            feature2: Second feature to plot
            feature3: Third feature (usually the target)
            
        Returns:
            Plotly figure object
        """
        if self.synthetic_data is None:
            self.generate_synthetic_data()
        
        # Create 3D scatter plot
        if self.synthetic_data is not None:
            fig = px.scatter_3d(
                self.synthetic_data, 
                x=feature1,
                y=feature2,
                z=feature3,
                color=feature3,
                color_continuous_scale='Viridis',
                opacity=0.7,
                title=f'3D Relationship: {feature1.replace("_", " ").title()} vs. {feature2.replace("_", " ").title()} vs. {feature3.replace("_", " ").title()}'
            )
        else:
            # Create an empty figure with message if we can't generate data
            fig = go.Figure()
            fig.add_annotation(
                x=0.5, y=0.5, z=0.5,
                text="Unable to generate visualization data",
                showarrow=False,
                font=dict(size=14)
            )
        
        # Update layout
        fig.update_layout(
            scene=dict(
                xaxis_title=feature1.replace('_', ' ').title(),
                yaxis_title=feature2.replace('_', ' ').title(),
                zaxis_title=feature3.replace('_', ' ').title()
            ),
            height=700
        )
        
        return fig
    
    def create_what_if_analysis(self, base_inputs, feature, range_min, range_max, steps=20):
        """
        Create a what-if analysis chart showing how changes in one feature 
        affect the predicted optimal ratio.
        
        Args:
            base_inputs: Dictionary with base feature values
            feature: Feature to vary
            range_min: Minimum value for the feature
            range_max: Maximum value for the feature
            steps: Number of steps in the range
            
        Returns:
            Plotly figure object
        """
        if not self.trained:
            self.train()
        
        # Create range of values for the feature
        feature_values = np.linspace(range_min, range_max, steps)
        predictions = []
        
        # Make predictions for each value
        for value in feature_values:
            # Create copy of base inputs and update the feature value
            inputs = base_inputs.copy()
            inputs[feature] = value
            
            # Make prediction
            pred = self.predict(inputs)
            predictions.append(pred)
        
        # Create trace for predictions
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=feature_values,
            y=predictions,
            mode='lines+markers',
            line=dict(width=3, color='royalblue'),
            marker=dict(size=8, color='royalblue'),
            name='Predicted Ratio'
        ))
        
        # Add reference line for current value
        current_value = base_inputs.get(feature, (range_min + range_max) / 2)
        current_pred = self.predict(base_inputs)
        
        fig.add_trace(go.Scatter(
            x=[current_value, current_value],
            y=[min(predictions) - 1, max(predictions) + 1],
            mode='lines',
            line=dict(dash='dash', color='red', width=2),
            name='Current Value'
        ))
        
        # Add point for current prediction
        fig.add_trace(go.Scatter(
            x=[current_value],
            y=[current_pred],
            mode='markers',
            marker=dict(size=12, color='red', symbol='star'),
            name='Current Prediction'
        ))
        
        # Update layout
        fig.update_layout(
            title=f'What-If Analysis: Impact of {feature.replace("_", " ").title()} on Optimal Ratio',
            xaxis_title=feature.replace('_', ' ').title(),
            yaxis_title='Predicted Optimal Ratio',
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig