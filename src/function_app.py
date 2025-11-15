import json
import logging

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


class ToolProperty:
    def __init__(self, property_name: str, property_type: str, description: str):
        self.propertyName = property_name
        self.propertyType = property_type
        self.description = description

    def to_dict(self):
        return {
            "propertyName": self.propertyName,
            "propertyType": self.propertyType,
            "description": self.description,
        }


# Define the tool properties for package checking
tool_properties_package_check_object = [
    ToolProperty("length", "number", "The length of the package in inches."),
    ToolProperty("width", "number", "The width of the package in inches."),
    ToolProperty("height", "number", "The height of the package in inches."),
    ToolProperty("weight", "number", "The weight of the package in grams."),
]

# Convert the tool properties to JSON
tool_properties_package_check_json = json.dumps([prop.to_dict() for prop in tool_properties_package_check_object])


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="check_package_oversized",
    description="Check if a package is oversized based on dimensions and weight.",
    toolProperties=tool_properties_package_check_json,
)
def check_package_oversized(context) -> str:
    """
    Check if a package is oversized based on dimensions and weight criteria.
    
    Oversized criteria:
    - Weight >= 5000 grams
    - Any single dimension (length, width, height) > 60 inches
    - Total dimensions (length + width + height) > 150 inches

    Args:
        context: The trigger context containing package dimensions and weight.

    Returns:
        str: JSON string with oversized status and reasoning.
    """
    try:
        # Parse the context to get the package dimensions and weight
        content = json.loads(context)
        args = content.get("arguments", {})
        
        length = args.get("length", 0)
        width = args.get("width", 0)
        height = args.get("height", 0)
        weight = args.get("weight", 0)
        
        # Convert to numbers if they're strings
        try:
            length = float(length)
            width = float(width)
            height = float(height)
            weight = float(weight)
        except (ValueError, TypeError):
            return json.dumps({
                "oversized": False,
                "error": "Invalid input: All dimensions and weight must be numeric values."
            })
        
        # Check oversized criteria
        reasons = []
        is_oversized = False
        
        # Check weight
        if weight >= 5000:
            is_oversized = True
            reasons.append(f"Weight ({weight}) is >= 5000 grams")
        
        # Check individual dimensions
        if length > 60:
            is_oversized = True
            reasons.append(f"Length ({length}) is > 60 inches")
        
        if width > 60:
            is_oversized = True
            reasons.append(f"Width ({width}) is > 60 inches")
            
        if height > 60:
            is_oversized = True
            reasons.append(f"Height ({height}) is > 60 inches")
        
        # Check total dimensions
        total_dimensions = length + width + height
        if total_dimensions > 150:
            is_oversized = True
            reasons.append(f"Total dimensions ({total_dimensions}) is > 150 inches")
        
        # Prepare response
        result = {
            "oversized": is_oversized,
            "length": length,
            "width": width,
            "height": height,
            "weight": weight,
            "total_dimensions": total_dimensions,
            "reasoning": reasons if is_oversized else ["Package meets all size and weight requirements"]
        }
        
        logging.info(f"Package check result: {result}")
        return json.dumps(result)
        
    except json.JSONDecodeError:
        return json.dumps({
            "oversized": False,
            "error": "Invalid JSON format in context"
        })
    except Exception as e:
        logging.error(f"Error checking package: {str(e)}")
        return json.dumps({
            "oversized": False,
            "error": f"Error processing package check: {str(e)}"
        })