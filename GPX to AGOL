import arcpy
import os

def append_gpx_to_agol(gpx_file_path, target_feature_service_url):
    """
    Converts a GPX file's tracks and waypoints into feature classes and
    appends them to an existing ArcGIS Online feature service.

    Args:
        gpx_file_path (str): The full path to the input GPX file.
        target_feature_service_url (str): The URL of the target hosted
                                          feature service layer to append to.
    """
    try:
        # Check if the GPX file exists
        if not arcpy.Exists(gpx_file_path):
            print(f"Error: The GPX file '{gpx_file_path}' does not exist.")
            return

        # Set up environment variables
        arcpy.env.overwriteOutput = True
        
        # Create a temporary geodatabase for intermediate feature classes
        temp_gdb_path = os.path.join(arcpy.env.scratchFolder, "temp.gdb")
        if not arcpy.Exists(temp_gdb_path):
            arcpy.CreateFileGDB_management(arcpy.env.scratchFolder, "temp.gdb")

        print(f"Converting GPX file '{os.path.basename(gpx_file_path)}' to features...")
        
        # Use the GPX To Features tool to convert waypoints and tracks
        arcpy.conversion.GPXToFeatures(
            in_gpx_file=gpx_file_path,
            output_waypoints=os.path.join(temp_gdb_path, "gpx_waypoints"),
            output_tracks=os.path.join(temp_gdb_path, "gpx_tracks")
        )

        print("GPX conversion successful. Appending data to ArcGIS Online...")

        # Append the new waypoints (points) to the target feature service
        # Assumes the target URL points to the points layer
        print("Appending waypoints...")
        arcpy.management.Append(
            inputs=os.path.join(temp_gdb_path, "gpx_waypoints"),
            target=target_feature_service_url,
            schema_type="NO_TEST"
        )

        print("Waypoints appended successfully!")
        
        # You can add similar logic here to handle appending tracks (lines) if needed
        # For example:
        # print("Appending tracks...")
        # arcpy.management.Append(
        #     inputs=os.path.join(temp_gdb_path, "gpx_tracks"),
        #     target="YOUR_TRACKS_AGOL_URL",
        #     schema_type="NO_TEST"
        # )
        
        print("Workflow completed.")

    except arcpy.ExecuteError:
        print("ArcPy error occurred:")
        print(arcpy.GetMessages(2))
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- Example Usage ---
# Replace these with your actual file path and ArcGIS Online feature service URL
# The URL should point to the specific layer, e.g., .../FeatureServer/0 for the first layer
# gpx_file = r"C:\Data\Garmin\my_hike.gpx"
# agol_points_url = r"https://services.arcgis.com/your_org_id/arcgis/rest/services/My_Feature_Service/FeatureServer/0"

# Call the function with your parameters
# append_gpx_to_agol(gpx_file, agol_points_url)
