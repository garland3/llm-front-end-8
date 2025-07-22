#!/usr/bin/env python3
"""
Linear Regression MCP Server
Provides linear regression analysis and prediction tools.
"""
import json
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("LinearRegression")

@dataclass
class RegressionResult:
    slope: float
    intercept: float
    r_squared: float
    predictions: Optional[List[float]] = None

class LinearRegressionModel:
    def __init__(self):
        self.slope = None
        self.intercept = None
        self.r_squared = None
        self.x_data = None
        self.y_data = None
    
    def fit(self, x: List[float], y: List[float]) -> RegressionResult:
        """Fit linear regression model to data."""
        if len(x) != len(y):
            raise ValueError("X and Y data must have the same length")
        if len(x) < 2:
            raise ValueError("Need at least 2 data points for regression")
        
        x_array = np.array(x)
        y_array = np.array(y)
        
        # Calculate slope and intercept using least squares
        n = len(x)
        sum_x = np.sum(x_array)
        sum_y = np.sum(y_array)
        sum_xy = np.sum(x_array * y_array)
        sum_x_squared = np.sum(x_array ** 2)
        
        # Calculate slope (m) and intercept (b) for y = mx + b
        denominator = n * sum_x_squared - sum_x ** 2
        if abs(denominator) < 1e-10:
            raise ValueError("Cannot perform regression: all X values are the same")
        
        self.slope = (n * sum_xy - sum_x * sum_y) / denominator
        self.intercept = (sum_y - self.slope * sum_x) / n
        
        # Calculate R-squared
        y_mean = np.mean(y_array)
        ss_tot = np.sum((y_array - y_mean) ** 2)
        y_pred = self.slope * x_array + self.intercept
        ss_res = np.sum((y_array - y_pred) ** 2)
        
        self.r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
        
        self.x_data = x
        self.y_data = y
        
        return RegressionResult(
            slope=self.slope,
            intercept=self.intercept,
            r_squared=self.r_squared
        )
    
    def predict(self, x_values: List[float]) -> List[float]:
        """Make predictions using the fitted model."""
        if self.slope is None or self.intercept is None:
            raise ValueError("Model must be fitted before making predictions")
        
        return [self.slope * x + self.intercept for x in x_values]

# Global model instance
model = LinearRegressionModel()

@mcp.tool
def fit_linear_regression(x_data: List[float], y_data: List[float]) -> Dict[str, Any]:
    """
    Fit a linear regression model to the provided data.
    
    Args:
        x_data: List of independent variable values
        y_data: List of dependent variable values
    
    Returns:
        Dictionary containing slope, intercept, and R-squared value
    """
    try:
        result = model.fit(x_data, y_data)
        
        return {
            "success": True,
            "slope": result.slope,
            "intercept": result.intercept,
            "r_squared": result.r_squared,
            "equation": f"y = {result.slope:.4f}x + {result.intercept:.4f}",
            "data_points": len(x_data),
            "fit_quality": _interpret_r_squared(result.r_squared)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool
def predict_values(x_values: List[float]) -> Dict[str, Any]:
    """
    Make predictions using the fitted linear regression model.
    
    Args:
        x_values: List of x values to predict y values for
    
    Returns:
        Dictionary containing predictions and model info
    """
    try:
        predictions = model.predict(x_values)
        
        return {
            "success": True,
            "predictions": predictions,
            "x_values": x_values,
            "model_info": {
                "slope": model.slope,
                "intercept": model.intercept,
                "r_squared": model.r_squared,
                "equation": f"y = {model.slope:.4f}x + {model.intercept:.4f}"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool
def analyze_data(x_data: List[float], y_data: List[float]) -> Dict[str, Any]:
    """
    Perform comprehensive linear regression analysis.
    
    Args:
        x_data: List of independent variable values
        y_data: List of dependent variable values
    
    Returns:
        Dictionary containing full analysis results
    """
    try:
        # Fit the model
        result = model.fit(x_data, y_data)
        
        # Calculate additional statistics
        x_array = np.array(x_data)
        y_array = np.array(y_data)
        
        x_mean = np.mean(x_array)
        y_mean = np.mean(y_array)
        x_std = np.std(x_array)
        y_std = np.std(y_array)
        
        # Calculate correlation coefficient
        correlation = np.corrcoef(x_array, y_array)[0, 1]
        
        # Calculate residuals
        predictions = model.predict(x_data)
        residuals = [y_data[i] - predictions[i] for i in range(len(y_data))]
        
        return {
            "success": True,
            "regression": {
                "slope": result.slope,
                "intercept": result.intercept,
                "r_squared": result.r_squared,
                "correlation": correlation,
                "equation": f"y = {result.slope:.4f}x + {result.intercept:.4f}"
            },
            "data_summary": {
                "n_points": len(x_data),
                "x_mean": x_mean,
                "y_mean": y_mean,
                "x_std": x_std,
                "y_std": y_std,
                "x_range": [float(min(x_array)), float(max(x_array))],
                "y_range": [float(min(y_array)), float(max(y_array))]
            },
            "residuals": {
                "values": residuals,
                "mean": np.mean(residuals),
                "std": np.std(residuals)
            },
            "interpretation": {
                "fit_quality": _interpret_r_squared(result.r_squared),
                "relationship_strength": _interpret_correlation(correlation),
                "slope_interpretation": _interpret_slope(result.slope)
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool
def get_model_info() -> Dict[str, Any]:
    """
    Get information about the currently fitted model.
    
    Returns:
        Dictionary containing current model parameters
    """
    if model.slope is None:
        return {
            "fitted": False,
            "message": "No model has been fitted yet"
        }
    
    return {
        "fitted": True,
        "slope": model.slope,
        "intercept": model.intercept,
        "r_squared": model.r_squared,
        "equation": f"y = {model.slope:.4f}x + {model.intercept:.4f}",
        "data_points": len(model.x_data) if model.x_data else 0,
        "fit_quality": _interpret_r_squared(model.r_squared)
    }

def _interpret_r_squared(r_squared: float) -> str:
    """Interpret R-squared value."""
    if r_squared >= 0.9:
        return "Excellent fit"
    elif r_squared >= 0.7:
        return "Good fit"
    elif r_squared >= 0.5:
        return "Moderate fit"
    elif r_squared >= 0.3:
        return "Weak fit"
    else:
        return "Poor fit"

def _interpret_correlation(correlation: float) -> str:
    """Interpret correlation coefficient."""
    abs_corr = abs(correlation)
    if abs_corr >= 0.9:
        strength = "Very strong"
    elif abs_corr >= 0.7:
        strength = "Strong"
    elif abs_corr >= 0.5:
        strength = "Moderate"
    elif abs_corr >= 0.3:
        strength = "Weak"
    else:
        strength = "Very weak"
    
    direction = "positive" if correlation > 0 else "negative"
    return f"{strength} {direction} correlation"

def _interpret_slope(slope: float) -> str:
    """Interpret slope value."""
    if slope > 0:
        return f"For each unit increase in X, Y increases by {slope:.4f} units"
    else:
        return f"For each unit increase in X, Y decreases by {abs(slope):.4f} units"

@mcp.resource("file://regression_guide")
def get_regression_guide() -> str:
    """Get a guide for using linear regression tools."""
    guide = {
        "description": "Linear Regression Analysis Tools",
        "tools": {
            "fit_linear_regression": "Fit a linear regression model to x,y data",
            "predict_values": "Make predictions using the fitted model",
            "analyze_data": "Comprehensive analysis including statistics and residuals",
            "get_model_info": "Get information about the current fitted model"
        },
        "workflow": [
            "1. Use fit_linear_regression or analyze_data with your x,y data",
            "2. Check the R-squared value to assess fit quality",
            "3. Use predict_values to make predictions for new x values",
            "4. Use get_model_info to review current model parameters"
        ],
        "interpretation": {
            "r_squared": "Closer to 1.0 indicates better fit",
            "slope": "Rate of change in Y per unit change in X",
            "intercept": "Y value when X equals zero"
        }
    }
    return json.dumps(guide, indent=2)

if __name__ == "__main__":
    mcp.run()