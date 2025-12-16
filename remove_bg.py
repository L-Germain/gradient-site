from PIL import Image
import numpy as np

def remove_white_bg(input_path, output_path):
    img = Image.open(input_path).convert("RGBA")
    data = np.array(img)
    
    # Define white threshold (e.g. pixels > 240 in all channels)
    r, g, b, a = data.T
    white_areas = (r > 240) & (g > 240) & (b > 240)
    
    # Set alpha to 0 for white areas
    data[..., 3][white_areas.T] = 0
    
    # Save result
    result = Image.fromarray(data)
    result.save(output_path)
    print(f"Saved transparent logo to {output_path}")

try:
    remove_white_bg("gradient_site/assets/new_logo.jpg", "gradient_site/assets/logo_transparent.png")
except Exception as e:
    print(f"Error: {e}")
