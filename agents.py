import asyncio
import os
import sys
import traceback
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import llm_client 

async def run_agent_with_mcp(server_script, system_prompt, user_message):
    
    # 1. Get absolute path to ensure the script is found
    base_path = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(base_path, server_script)
    
    # Verify file existence before attempting to run
    if not os.path.exists(script_path):
        return f"Error: The server script '{server_script}' was not found at {script_path}."

    # 2. Use sys.executable to maintain the same Python environment/venv
    server_params = StdioServerParameters(
        command=sys.executable, 
        args=[script_path],
        env=os.environ.copy() # Pass environment variables
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection to the MCP server
                await session.initialize()
                
                # Call the LLM (ensure llm_client.chat is compatible with your setup)
                return llm_client.chat([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ])
    except Exception as e:
        # Log the full error to the terminal for debugging
        print(f"--- MCP Server Error ({server_script}) ---")
        traceback.print_exc()
        return f"Failed to communicate with {server_script}: {str(e)}"

async def run_robotic_chef_pipeline(user_query, status_callback=None):
    """
    Orchestrates the two-agent pipeline.
    """
    # --- Agent 1: Culinary Analyst ---
    if status_callback: 
        status_callback("Agent 1: Analyzing budget and nutritional constraints...")
    
    agent_1_system = (
        "You are a Culinary Analyst. Use 'fit_budget' and 'get_nutrition' tools "
        "to find the best meal. Provide a breakdown of physical motions required "
        "for a robot (e.g., 'requires 20N vertical force for chopping')."
    )
    
    food_analysis = await run_agent_with_mcp("recipe_mcp_server.py", agent_1_system, user_query)
    
    # Check if Agent 1 returned an error string
    if "Error:" in food_analysis or "Failed to" in food_analysis:
        return {"food_analysis": food_analysis, "robot_design": "Pipeline halted due to Agent 1 error."}

    # --- Agent 2: Robotics Engineer ---
    if status_callback: 
        status_callback("Agent 2: Designing hardware and selecting actuators...")
    
    agent_2_system = (
        "You are a Robotics Engineer. Review the food analysis and suggest "
        "specific robotic hardware (servos, sensors, end-effectors) "
        "to accomplish the tasks described."
    )
    
    robot_design = await run_agent_with_mcp(
        "robotics_mcp_server.py", 
        agent_2_system, 
        f"Analyze this culinary requirement and design the hardware: {food_analysis}"
    )
    
    return {
        "food_analysis": food_analysis, 
        "robot_design": robot_design
    }

