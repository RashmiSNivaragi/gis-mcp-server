import os
import json
import requests
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from arcgis_utils import list_arcgis_layers, get_layer_url_and_json, search_feature_layer_by_title

# Create a FastAPI application instance
app = FastAPI(
    title="MCP Server for ArcGIS",
    description="An API that uses an LLM to call ArcGIS tools."
)

# Endpoint to get layer URL and JSON by service and layer name
@app.get("/api/arcgis_layer_info/{layer_name}")
async def get_arcgis_layer_info(layer_name: str):
    """
    Returns the ArcGIS layer URL and JSON for a given layer name.
    """
    return get_layer_url_and_json(layer_name)

# --- 2. DEFINE THE API SERVER (FastAPI) ---

# Define the main API endpoint
@app.get("/api/arcgis_layers/{layer_name}")
async def get_arcgis_layers(layer_name: str):
    """
    Returns all layers in the given ArcGIS FeatureServer service.
    """
    return list_arcgis_layers(layer_name)

# --- 1. CONFIGURE THE AI MODEL AND TOOLS ---

# Configure the Gemini API key from environment variables
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    raise ValueError("GOOGLE_API_KEY environment variable not set.")

# This is the tool function from our previous example.
# It acts as a wrapper for your Salesforce Apex API call.
def load_arcGIS_layer(layer_name: str) -> dict:
    """
    Calls ArcGIS to load a specific geographic layer onto a map.

    Args:
        layer_name: The name of the layer to be loaded, for example, 'Bozeman'.
    """
    print(f"TOOL EXECUTED: Getting ArcGIS layer info for '{layer_name}'...")
    # Assume the service name is the same as the layer name for this use case
    # If you have a different mapping, adjust accordingly
    from arcgis_utils import search_feature_layer_by_title
    result = search_feature_layer_by_title(layer_name)
    print(f"Result from search_feature_layer_by_title: {result}")
    # from arcgis_utils import get_layer_url_and_json
    # result = get_layer_url_and_json(layer_name)
    if result["status"] == "success":
        return {
            "status": "success",
            "message": f"Layer '{layer_name}' data loaded from ArcGIS.",
            "layer_name": layer_name,
            "layer_url": result["item_url"]
        }
    else:
        return result

# Initialize the Generative Model with your tool
model = genai.GenerativeModel(
    model_name='gemini-2.5-pro',
    tools=[load_arcGIS_layer]
)
chat = model.start_chat()

# --- 2. DEFINE THE API SERVER (FastAPI) ---

# Create a FastAPI application instance
app = FastAPI(
    title="MCP Server for ArcGIS",
    description="An API that uses an LLM to call ArcGIS tools."
)

# Define the structure of the incoming request body
class ChatRequest(BaseModel):
    prompt: str

# Define the main API endpoint
@app.post("/api/chat")
async def handle_chat(request: ChatRequest):
    """
    Receives a user prompt, processes it with the LLM, and executes tool calls.
    """
    try:
        print(f"Received prompt: '{request.prompt}'")
        # Send the prompt to the Gemini model
        response = chat.send_message(request.prompt)
        function_call = response.candidates[0].content.parts[0].function_call

        if not function_call:
            # If the model just wants to chat, return its text response
            return {"type": "text", "data": response.text}

        # If the model wants to call a tool:
        tool_name = function_call.name
        tool_args = dict(function_call.args)
        
        print(f"LLM wants to call tool: {tool_name} with args: {tool_args}")
        
        if tool_name == "load_arcGIS_layer":
            # Execute the function and get the result
            tool_response = load_arcGIS_layer(**tool_args)
            return {"type": "tool_response", "data": tool_response}
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool requested: {tool_name}")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))