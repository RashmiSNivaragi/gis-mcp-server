import os
import json
import requests
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from arcgis_utils import search_feature_layer_by_title

# Create a FastAPI application instance
app = FastAPI(
    title="MCP Server for import layear from ArcGIS and create Sitetracker Layer",
    description="An API that uses an LLM to call ArcGIS tools and create Sitetracker Layer"
)

# Tool function to create Sitetracker Layer based on ArcGIS layer
def create_sitetracker_layer(layer_name: str) -> dict:
    """
    Creates a new Sitetracker Layer based on the ArcGIS layer name.
    This function simulates calling the Salesforce Apex method 'createSitetrackerMapLayer'.

    Args:
        layer_name: The name of the ArcGIS layer to create a Sitetracker Layer for.
    """
    print(f"TOOL EXECUTED: Creating Sitetracker Layer for '{layer_name}'...")
    
    try:
        # In a real implementation, you would make a call to your Salesforce org
        # using the Salesforce REST API to invoke the Apex method
        # For example:
        # POST to: https://your-org.salesforce.com/services/apexrest/StUserAssistant/createLayer
        # with body: {"layerName": layer_name}
        
        # Return the layer name that should be created in Sitetracker
        # The actual creation will be handled by your Apex code
        sitetracker_layer_name = f"{layer_name}"
        
        response = {
            "status": "success",
            "sitetracker_layer_name": sitetracker_layer_name,
            "message": f"Ready to create Sitetracker Layer: '{sitetracker_layer_name}'"
        }
        return response
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create Sitetracker Layer for '{layer_name}': {str(e)}"
        }

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
    #from arcgis_utils import search_feature_layer_by_title
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

# Initialize the Generative Model with your tools
model = genai.GenerativeModel(
    model_name='gemini-2.5-pro',
    tools=[load_arcGIS_layer, create_sitetracker_layer]
)
chat = model.start_chat()

# --- 2. DEFINE THE API SERVER (FastAPI) ---

# Create a FastAPI application instance
app = FastAPI(
    title="MCP Server for import layear from ArcGIS and create Sitetracker Layer",
    description="An API that uses an LLM to call ArcGIS tools and create Sitetracker Layer"
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
        elif tool_name == "create_sitetracker_layer":
            # Execute the function and get the result
            tool_response = create_sitetracker_layer(**tool_args)
            return {"type": "tool_response", "data": tool_response}
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool requested: {tool_name}")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))
