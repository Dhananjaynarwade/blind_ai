import numpy as np
import json
import os
from datetime import datetime
import time

class AdaptiveLearningModel:
    """
    Adaptive learning model that improves navigation over time based on user behavior
    and feedback.
    """
    
    def __init__(self, user_id=None, data_file="adaptive_learning_data.json"):
        """
        Initialize the adaptive learning model
        
        Args:
            user_id: ID of the current user for personalized learning
            data_file: File to store learning data
        """
        self.user_id = user_id
        self.data_file = data_file
        self.learning_data = self._load_data()
        
        # Default learning parameters
        self.default_params = {
            "path_adjustment_weight": 0.3,      # How much to adjust path finding based on history
            "obstacle_confidence_threshold": 0.6, # Confidence threshold for obstacle detection
            "direction_verbosity": 0.7,         # How detailed directions should be (0-1)
            "walking_pace": 1.0,                # Normal walking pace factor
            "navigation_frequency": 5.0,        # Seconds between navigation updates
            "max_warning_distance": 3.0,        # Maximum distance for obstacle warnings (meters)
        }
        
        # Initialize user data if not exists
        if user_id and user_id not in self.learning_data["users"]:
            self.learning_data["users"][user_id] = {
                "parameters": self.default_params.copy(),
                "navigation_history": [],
                "feedback_history": [],
                "object_recognition_history": [],
                "created_at": datetime.now().isoformat(),
                "interaction_count": 0
            }
            self._save_data()
    
    def _load_data(self):
        """Load learning data from file, or create default if not exists"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading learning data: {e}")
        
        # Default data structure
        return {
            "global_stats": {
                "total_navigations": 0,
                "successful_navigations": 0,
                "object_detection_stats": {},
                "last_updated": datetime.now().isoformat()
            },
            "users": {},
            "object_recognition": {
                "difficult_objects": {
                    "glass_door": {"adjustment_factor": 1.2},
                    "low_object": {"adjustment_factor": 1.3},
                    "reflective_surface": {"adjustment_factor": 1.4}
                }
            }
        }
    
    def _save_data(self):
        """Save learning data to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.data_file) or '.', exist_ok=True)
            
            # Update timestamp
            self.learning_data["global_stats"]["last_updated"] = datetime.now().isoformat()
            
            with open(self.data_file, 'w') as f:
                json.dump(self.learning_data, f, indent=2)
        except Exception as e:
            print(f"Error saving learning data: {e}")
    
    def get_adjusted_parameters(self):
        """
        Get learning parameters adjusted for current user
        
        Returns:
            parameters: Dictionary of adjusted parameters
        """
        if not self.user_id or self.user_id not in self.learning_data["users"]:
            return self.default_params.copy()
        
        return self.learning_data["users"][self.user_id]["parameters"]
    
    def record_navigation_session(self, start_point, end_point, path_taken, obstacles_avoided, 
                                  duration, successful=True):
        """
        Record a navigation session for learning
        
        Args:
            start_point: Starting coordinates
            end_point: Ending coordinates
            path_taken: List of coordinates in the path
            obstacles_avoided: List of obstacles avoided
            duration: Duration of navigation in seconds
            successful: Whether navigation was successful
        """
        if not self.user_id:
            return
        
        # Record navigation data
        navigation_data = {
            "timestamp": datetime.now().isoformat(),
            "start_point": start_point,
            "end_point": end_point,
            "path_length": len(path_taken),
            "obstacles_avoided": obstacles_avoided,
            "duration": duration,
            "successful": successful
        }
        
        # Update user data
        user_data = self.learning_data["users"][self.user_id]
        user_data["navigation_history"].append(navigation_data)
        user_data["interaction_count"] += 1
        
        # Limit history size to avoid file bloat
        if len(user_data["navigation_history"]) > 100:
            user_data["navigation_history"] = user_data["navigation_history"][-100:]
        
        # Update global stats
        self.learning_data["global_stats"]["total_navigations"] += 1
        if successful:
            self.learning_data["global_stats"]["successful_navigations"] += 1
        
        # Save data
        self._save_data()
        
        # Apply learning to adjust parameters
        self._update_learning_parameters()
    
    def record_object_detection(self, object_class, confidence, was_correct):
        """
        Record object detection results for learning
        
        Args:
            object_class: Class of detected object
            confidence: Detection confidence (0-1)
            was_correct: Whether detection was correct (based on user feedback)
        """
        if not self.user_id:
            return
        
        # Record detection data
        detection_data = {
            "timestamp": datetime.now().isoformat(),
            "object_class": object_class,
            "confidence": confidence,
            "was_correct": was_correct
        }
        
        # Update user data
        user_data = self.learning_data["users"][self.user_id]
        user_data["object_recognition_history"].append(detection_data)
        
        # Limit history size
        if len(user_data["object_recognition_history"]) > 200:
            user_data["object_recognition_history"] = user_data["object_recognition_history"][-200:]
        
        # Update global stats
        global_stats = self.learning_data["global_stats"]
        if object_class not in global_stats["object_detection_stats"]:
            global_stats["object_detection_stats"][object_class] = {
                "total": 0,
                "correct": 0
            }
        
        global_stats["object_detection_stats"][object_class]["total"] += 1
        if was_correct:
            global_stats["object_detection_stats"][object_class]["correct"] += 1
        
        # Save data
        self._save_data()
        
        # Apply learning
        self._update_detection_thresholds()
    
    def record_user_feedback(self, direction_type, was_helpful, context=None):
        """
        Record user feedback on navigation directions
        
        Args:
            direction_type: Type of direction (e.g., 'turn', 'obstacle_warning')
            was_helpful: Whether direction was helpful (True/False)
            context: Additional context about the situation
        """
        if not self.user_id:
            return
        
        # Record feedback data
        feedback_data = {
            "timestamp": datetime.now().isoformat(),
            "direction_type": direction_type,
            "was_helpful": was_helpful,
            "context": context or {}
        }
        
        # Update user data
        user_data = self.learning_data["users"][self.user_id]
        user_data["feedback_history"].append(feedback_data)
        
        # Limit history size
        if len(user_data["feedback_history"]) > 100:
            user_data["feedback_history"] = user_data["feedback_history"][-100:]
        
        # Save data
        self._save_data()
        
        # Apply learning
        self._adjust_direction_verbosity(direction_type, was_helpful)
    
    def _update_learning_parameters(self):
        """Update learning parameters based on navigation history"""
        if not self.user_id:
            return
        
        user_data = self.learning_data["users"][self.user_id]
        history = user_data["navigation_history"]
        params = user_data["parameters"]
        
        # Need multiple sessions to start learning
        if len(history) < 3:
            return
            
        # Calculate walking pace based on recent successful navigations
        successful_navigations = [n for n in history[-10:] if n["successful"]]
        if successful_navigations:
            avg_duration = sum(n["duration"] for n in successful_navigations) / len(successful_navigations)
            avg_path_length = sum(n["path_length"] for n in successful_navigations) / len(successful_navigations)
            
            if avg_path_length > 0:
                # Pace is relative to distance covered per time
                new_pace = avg_path_length / max(avg_duration, 1)
                # Smooth adjustment
                params["walking_pace"] = 0.8 * params["walking_pace"] + 0.2 * new_pace
        
        # Adjust navigation frequency based on obstacle density
        avg_obstacles = sum(len(n["obstacles_avoided"]) for n in history[-5:]) / 5
        if avg_obstacles > 5:
            # More frequent updates in complex environments
            params["navigation_frequency"] = max(2.0, params["navigation_frequency"] * 0.9)
        else:
            # Less frequent updates in simple environments
            params["navigation_frequency"] = min(8.0, params["navigation_frequency"] * 1.1)
        
        # Save updated parameters
        self._save_data()
    
    def _update_detection_thresholds(self):
        """Update object detection thresholds based on history"""
        if not self.user_id:
            return
        
        user_data = self.learning_data["users"][self.user_id]
        history = user_data["object_recognition_history"]
        params = user_data["parameters"]
        
        # Need enough samples to adjust
        if len(history) < 10:
            return
        
        # Calculate detection accuracy trends
        recent_history = history[-20:]
        accuracy = sum(1 for h in recent_history if h["was_correct"]) / len(recent_history)
        
        # Adjust threshold based on accuracy
        if accuracy < 0.7:
            # Increase threshold to reduce false positives
            params["obstacle_confidence_threshold"] = min(0.85, params["obstacle_confidence_threshold"] + 0.02)
        elif accuracy > 0.9:
            # Decrease threshold to reduce false negatives
            params["obstacle_confidence_threshold"] = max(0.5, params["obstacle_confidence_threshold"] - 0.01)
        
        # Save updated parameters
        self._save_data()
    
    def _adjust_direction_verbosity(self, direction_type, was_helpful):
        """Adjust direction verbosity based on user feedback"""
        if not self.user_id:
            return
        
        user_data = self.learning_data["users"][self.user_id]
        params = user_data["parameters"]
        
        # Adjust verbosity
        if was_helpful:
            # If directions are helpful, slightly increase verbosity
            params["direction_verbosity"] = min(1.0, params["direction_verbosity"] + 0.02)
        else:
            # If directions are not helpful, decrease verbosity
            params["direction_verbosity"] = max(0.3, params["direction_verbosity"] - 0.05)
        
        # Save updated parameters
        self._save_data()
    
    def get_learning_progress(self):
        """
        Get learning progress statistics
        
        Returns:
            progress: Dictionary with learning progress stats
        """
        if not self.user_id or self.user_id not in self.learning_data["users"]:
            return {
                "progress_percentage": 0,
                "interaction_count": 0,
                "adapted_parameters": [],
                "accuracy": {}
            }
        
        user_data = self.learning_data["users"][self.user_id]
        
        # Calculate progress as a percentage (maxes out at ~250 interactions)
        interaction_count = user_data["interaction_count"]
        progress_percentage = min(100, int((interaction_count / 250) * 100))
        
        # Identify adapted parameters (different from defaults)
        adapted_parameters = []
        for param, value in user_data["parameters"].items():
            if abs(value - self.default_params[param]) > 0.01:
                adapted_parameters.append({
                    "name": param,
                    "value": value,
                    "default": self.default_params[param],
                    "change_percentage": int(((value / self.default_params[param]) - 1) * 100)
                })
        
        # Calculate recognition accuracy
        accuracy = {}
        for object_class, stats in self.learning_data["global_stats"]["object_detection_stats"].items():
            if stats["total"] > 0:
                accuracy[object_class] = round((stats["correct"] / stats["total"]) * 100)
        
        return {
            "progress_percentage": progress_percentage,
            "interaction_count": interaction_count,
            "adapted_parameters": adapted_parameters,
            "accuracy": accuracy
        }
    
    def reset_learning(self):
        """Reset learning data for current user"""
        if not self.user_id or self.user_id not in self.learning_data["users"]:
            return False
        
        # Reset user parameters to defaults
        self.learning_data["users"][self.user_id]["parameters"] = self.default_params.copy()
        self.learning_data["users"][self.user_id]["navigation_history"] = []
        self.learning_data["users"][self.user_id]["feedback_history"] = []
        self.learning_data["users"][self.user_id]["object_recognition_history"] = []
        self.learning_data["users"][self.user_id]["interaction_count"] = 0
        
        # Save data
        self._save_data()
        return True

# Singleton instance
adaptive_learning_model = AdaptiveLearningModel() 