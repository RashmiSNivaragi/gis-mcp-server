# Utility to get layer URL and JSON by layer name
import requests
from arcgis.gis import GIS

def get_layer_url_and_json(layer_name: str, org_id: str = "V6ZHFr6zdgNZuVG0") -> dict:
    """
    Given a service name and a layer name, returns the layer URL and its JSON definition.
    """
    feature_server_url = f"https://services.arcgis.com/{org_id}/ArcGIS/rest/services/{layer_name}/FeatureServer"
    try:
        # Get all layers metadata
        resp = requests.get(feature_server_url, params={"f": "json"})
        resp.raise_for_status()
        data = resp.json()
        layers = data.get("layers", [])
        # Find the layer by name
        for lyr in layers:
            if lyr.get("name") == layer_name:
                layer_id = lyr.get("id")
                layer_url = f"{feature_server_url}/{layer_id}"
                # Get the layer JSON
                lyr_resp = requests.get(layer_url, params={"f": "json"})
                lyr_resp.raise_for_status()
                layer_json = lyr_resp.json()
                return {
                    "status": "success",
                    "layer_url": layer_url,
                    "layer_json": layer_json
                }
        return {
            "status": "error",
            "message": f"Layer '{layer_name}' not found in service.",
            "feature_server_url": feature_server_url
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get layer '{layer_name}' from service.",
            "error": str(e),
            "feature_server_url": feature_server_url
        }

def search_feature_layer_by_title(layer_name: str, org_url: str = 'https://wwww.arcgis.com', username: str = 'udaya.kumar_sitetrackernew', password: str = 'Uday1991#') -> dict:
    """
    Searches ArcGIS Online for a feature layer by title and returns the first match's URL and metadata.
    """
    try:
        if org_url and username and password:
            gis = GIS(org_url, username, password)
        else:
            gis = GIS()  # anonymous connection

        search_results = gis.content.search(f'title: {layer_name}', 'Feature Layer')
        print(f"Search results for layer '{layer_name}': {search_results}")
        if not search_results:
            return {"status": "error", "message": f"No feature layer found with title '{layer_name}'."}

        item = search_results[0]
        layers = item.layers
        layer_urls = [layer.url for layer in layers]
        return {
            "status": "success",
            "item_title": item.title,
            "item_id": item.id,
            "layer_urls": layer_urls,
            "item_url": item.url,
            "item_type": item.type,
            "item_metadata": item.get_data()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Utility to list all layers in a given ArcGIS FeatureServer service
def list_arcgis_layers(service_name: str, org_id: str = "V6ZHFr6zdgNZuVG0") -> dict:
    """
    Lists all layers in the given ArcGIS FeatureServer service using the arcgis Python package.
    """
    feature_server_url = f"https://services.arcgis.com/{org_id}/ArcGIS/rest/services/{service_name}/FeatureServer"
    try:
        # Anonymous GIS connection (for public services)
        gis = GIS()
        fs = gis.content.get(feature_server_url)
        if not fs:
            # Try as FeatureLayerCollection
            from arcgis.features import FeatureLayerCollection
            fs = FeatureLayerCollection(feature_server_url, gis)
        layers = []
        if hasattr(fs, 'layers'):
            for lyr in fs.layers:
                layers.append({
                    "id": lyr.properties.id,
                    "name": lyr.properties.name,
                    "type": lyr.properties.type
                })
        return {
            "status": "success",
            "layers": layers,
            "feature_server_url": feature_server_url
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to list layers for service '{service_name}'.",
            "error": str(e),
            "feature_server_url": feature_server_url
        }
