from typing import Dict, List


def _normalize_data(self, plots_data: List[Dict]) -> List[Dict]:
    """Normalize different data structures into a standard format."""
    normalized_data = []
    for plot in plots_data:
        if "land_data" in plot:
            normalized_data.append(plot)
        elif "plot_info" in plot:
            normalized_data.append(
                {
                    "land_data": {
                        "plot_id": plot["plot_info"]["plot_number"],
                        "size": plot["plot_info"]["area"],
                        "type": (
                            "Acres"
                            if plot["plot_info"]["metric"] == "Acres"
                            else "Unknown"
                        ),
                        "location": f"{plot["plot_info"]["region"]}, {plot["plot_info"]["district"]} - {plot["plot_info"]["locality"]}",
                        "owners": plot["plot_info"].get("owners", []),
                        "site_plan": {
                            "gps_processed_data_summary": {
                                "point_list": [
                                    {
                                        "latitude": p["latitude"],
                                        "longitude": p["longitude"],
                                    }
                                    for p in plot["point_list"]
                                ]
                            }
                        },
                    }
                }
            )

    return normalized_data
