# -*- coding: utf-8 -*-
"""
This Python Toolbox (`.pyt`) provides a geoprocessing tool for ArcGIS Pro
that reads a GPX file and uploads the tracks and waypoints to existing
hosted feature services in ArcGIS Online.

To use this toolbox:
1. Ensure the `arcgis` and `gpxpy` libraries are installed in your
   ArcGIS Pro Python environment.
   Open the Python Package Manager in ArcGIS Pro or use the `proenv`
   command prompt to run: `pip install arcgis gpxpy`
2. In ArcGIS Pro, add this `.pyt` file to your project.
3. The "GPX to ArcGIS Online" tool will appear and you can run it.
"""

import arcpy
import os
import gpxpy
from arcgis.gis import GIS
from arcgis.features import FeatureLayer

class Toolbox(object):
    """Defines the geoprocessing toolbox for GPX uploading."""
    def __init__(self):
        """Define the toolbox properties."""
        self.label = "GPX Uploader Tools"
        self.alias = "gpxuploader"
        # List of tool classes associated with this toolbox
        self.tools = [GPXUploaderTool]

class GPXUploaderTool(object):
    """
    Geoprocessing tool to upload GPX data to ArcGIS Online.
    """
    def __init__(self):
        """Defines the tool properties and a flag for custom credentials."""
        self.label = "GPX to ArcGIS Online"
        self.description = "Transforms and appends tracks and waypoints from a Garmin GPX file to existing ArcGIS Online hosted feature services."
        self.canRunInBackground = False
        self.gis = None

    def getParameterInfo(self):
        """Defines the parameters for the tool's dialog box."""
        
        # Define the input GPX file parameter and then set its filter
        in_gpx_file_param = arcpy.Parameter(
            displayName="Input GPX File",
            name="in_gpx_file",
            datatype="DEFile",
            parameterType="Required",
            direction="Input"
        )
        in_gpx_file_param.filter.list = ['gpx']

        # Define the URL parameter and then set its default value
        arcgis_online_url_param = arcpy.Parameter(
            displayName="ArcGIS Online URL",
            name="arcgis_online_url",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
        )
        arcgis_online_url_param.defaultValue = "https://www.arcgis.com"
        
        # Define the password parameter and then set its string_type
        arcgis_password_param = arcpy.Parameter(
            displayName="ArcGIS Online Password",
            name="arcgis_password",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        # Set as "Password" so it is not saved or displayed in the history
        arcgis_password_param.string_type = "Password"

        # Define the waypoints URL parameter and then set its default value
        waypoints_layer_url_param = arcpy.Parameter(
            displayName="Waypoints Layer URL",
            name="waypoints_layer_url",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        waypoints_layer_url_param.defaultValue = "https://services.arcgis.com/xxxxxxxxxxxx/arcgis/rest/services/MyTracks/FeatureServer/0"

        # Define the tracks URL parameter and then set its default value
        tracks_layer_url_param = arcpy.Parameter(
            displayName="Tracks Layer URL",
            name="tracks_layer_url",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        tracks_layer_url_param.defaultValue = "https://services.arcgis.com/xxxxxxxxxxxx/arcgis/rest/services/MyTracks/FeatureServer/1"
        
        # Add the new parameter for Project Number
        project_number_param = arcpy.Parameter(
            displayName="Project Number",
            name="project_number",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )

        # Add the new parameter for Surveyor
        surveyor_param = arcpy.Parameter(
            displayName="Surveyor",
            name="surveyor",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )

        params = [
            in_gpx_file_param,
            arcgis_online_url_param,
            arcpy.Parameter(
                displayName="ArcGIS Online Username",
                name="arcgis_username",
                datatype="GPString",
                parameterType="Required",
                direction="Input"
            ),
            arcgis_password_param,
            waypoints_layer_url_param,
            tracks_layer_url_param,
            project_number_param,
            surveyor_param
        ]
        return params

    def authenticate_and_connect(self, url, username, password):
        """Connects to ArcGIS Online and returns the GIS object."""
        try:
            arcpy.AddMessage("Connecting to ArcGIS Online...")
            gis = GIS(url, username=username, password=password)
            arcpy.AddMessage("Successfully connected to ArcGIS Online.")
            return gis
        except Exception as e:
            arcpy.AddError(f"Error connecting to ArcGIS Online: {e}")
            raise

    def get_feature_layers(self, gis_obj, waypoint_url, tracks_url):
        """Gets the feature layers from the provided URLs."""
        try:
            arcpy.AddMessage("Getting feature layers...")
            waypoint_fl = FeatureLayer(waypoint_url, gis=gis_obj)
            tracks_fl = FeatureLayer(tracks_url, gis=gis_obj)
            arcpy.AddMessage("Successfully accessed feature layers.")
            return waypoint_fl, tracks_fl
        except Exception as e:
            arcpy.AddError(f"Error accessing feature layers: {e}")
            raise

    def parse_gpx_file(self, file_path, project_number, surveyor):
        """
        Parses a GPX file and extracts waypoints and tracks,
        adding the Project Number and Surveyor to each feature's attributes.
        """
        arcpy.AddMessage(f"Parsing GPX file: {file_path}")
        waypoints_to_add = []
        tracks_to_add = []

        try:
            with open(file_path, 'r', encoding='utf-8') as gpx_file:
                gpx = gpxpy.parse(gpx_file)

            # Process Waypoints
            for waypoint in gpx.waypoints:
                waypoints_to_add.append({
                    "geometry": {
                        "x": waypoint.longitude,
                        "y": waypoint.latitude,
                        "spatialReference": {"wkid": 4326}
                    },
                    "attributes": {
                        "name": waypoint.name if waypoint.name else "Unnamed Waypoint",
                        "description": waypoint.description if waypoint.description else "No description",
                        "Project_Number": project_number, # New field
                        "Surveyor": surveyor # New field
                    }
                })

            # Process Tracks
            for track in gpx.tracks:
                for segment in track.segments:
                    if len(segment.points) > 1:
                        line_geometry = {
                            "spatialReference": {"wkid": 4326},
                            "paths": []
                        }
                        path = []
                        for point in segment.points:
                            path.append([point.longitude, point.latitude])
                        line_geometry["paths"].append(path)

                        tracks_to_add.append({
                            "geometry": line_geometry,
                            "attributes": {
                                "name": track.name if track.name else "Unnamed Track",
                                "description": track.description if track.description else "No description",
                                "Project_Number": project_number, # New field
                                "Surveyor": surveyor # New field
                            }
                        })

            arcpy.AddMessage(f"GPX parsing complete. Found {len(waypoints_to_add)} waypoints and {len(tracks_to_add)} tracks.")
            return waypoints_to_add, tracks_to_add

        except Exception as e:
            arcpy.AddError(f"Error parsing GPX file: {e}")
            raise

    def append_features_to_service(self, feature_layer, features_to_add):
        """Appends a list of features to the specified feature layer."""
        if not features_to_add:
            arcpy.AddMessage(f"No features to append to {feature_layer.properties.name}.")
            return

        arcpy.AddMessage(f"Appending {len(features_to_add)} features to {feature_layer.properties.name}...")
        try:
            result = feature_layer.edit_features(adds=features_to_add)

            # Check for successful appends
            add_results = result.get('addResults', [])
            success_count = sum(1 for res in add_results if res.get('success'))

            arcpy.AddMessage(f"Successfully appended {success_count} features.")
            if len(add_results) != success_count:
                arcpy.AddWarning("Some features failed to append. Check the geoprocessing history for details.")

        except Exception as e:
            arcpy.AddError(f"Error appending features to {feature_layer.properties.name}: {e}")
            raise

    def execute(self, parameters, messages):
        """The main execution function of the tool."""
        # Retrieve the parameter values from the tool dialog
        gpx_file_path = parameters[0].valueAsText
        arcgis_online_url = parameters[1].valueAsText
        arcgis_username = parameters[2].valueAsText
        arcgis_password = parameters[3].valueAsText
        waypoints_layer_url = parameters[4].valueAsText
        tracks_layer_url = parameters[5].valueAsText
        project_number = parameters[6].valueAsText
        surveyor = parameters[7].valueAsText
        
        # 1. Connect to ArcGIS Online
        try:
            gis = self.authenticate_and_connect(arcgis_online_url, arcgis_username, arcgis_password)
        except Exception:
            return

        # 2. Get feature layers
        try:
            waypoint_layer, tracks_layer = self.get_feature_layers(gis, waypoints_layer_url, tracks_layer_url)
        except Exception:
            return

        # 3. Parse GPX file
        if not os.path.exists(gpx_file_path):
            arcpy.AddError(f"Error: The specified GPX file does not exist at '{gpx_file_path}'")
            return

        try:
            waypoints, tracks = self.parse_gpx_file(gpx_file_path, project_number, surveyor)
        except Exception:
            return

        # 4. Append features to hosted feature services
        try:
            self.append_features_to_service(waypoint_layer, waypoints)
            self.append_features_to_service(tracks_layer, tracks)
        except Exception:
            return

        arcpy.AddMessage("\nProcess complete. Data has been uploaded to ArcGIS Online.")
