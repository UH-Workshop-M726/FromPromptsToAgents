import json
import os
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP
mcp = FastMCP("Robotics Hardware Agent")

def load_data(filename):
    """Helper to load your local JSON data files."""
    base_path = os.path.dirname(os.path.abspath(__file__))
    # Assuming files are in a 'data' folder as per your request
    file_path = os.path.join(base_path, "data", filename)
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

@mcp.tool()
def suggest_actuator(required_force_n: float, task_type: str = "") -> str:
    """Finds an actuator (gripper, pump, etc.) from the catalog that meets the force requirement."""
    actuators = load_data("actuators.json")
    suitable = []
    
    for act in actuators:
        # Check grip force for grippers
        spec_force = act.get("specifications", {}).get("grip_force_n", 0)
        # Check if the task matches (e.g., 'food handling', 'mixing')
        task_match = any(task_type.lower() in s.lower() for s in act.get("suitable_for", [])) if task_type else True
        
        if spec_force >= required_force_n and task_match:
            suitable.append(f"{act['name']} ({act['type']}): {act['description']}")

    if not suitable:
        return f"No standard actuator found for {required_force_n}N. Consider the Adaptive Finger Gripper (AF-2D) for high-force requirements."
    
    return "Recommended Actuators:\n" + "\n".join(suitable)

@mcp.tool()
def suggest_manipulator(payload_kg: float, task: str) -> str:
    """Suggests a robotic arm or manipulator based on payload and task."""
    components = load_data("components.json")
    arms = [c for c in components if c["category"] == "manipulator"]
    
    suitable = [
        f"{a['name']}: {a['description']} (Payload: {a['specifications']['payload_kg']}kg)"
        for a in arms if a["specifications"]["payload_kg"] >= payload_kg
    ]
    
    return "Recommended Manipulators:\n" + "\n".join(suitable) if suitable else "No suitable arm found."

@mcp.tool()
def suggest_sensors(task: str) -> str:
    """Finds sensors suitable for tasks like 'temperature', 'safety', or 'navigation'."""
    sensors = load_data("sensors.json")
    suitable = [
        f"{s['name']}: {s['description']}"
        for s in sensors if any(task.lower() in sub.lower() for sub in s.get("suitable_for", []))
    ]
    
    return "Recommended Sensors:\n" + "\n".join(suitable) if suitable else "No specific sensors found for this task."

if __name__ == "__main__":
    mcp.run()