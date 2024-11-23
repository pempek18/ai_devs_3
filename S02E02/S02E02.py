import openai
import os
import dotenv

dotenv.load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')

def encode_image_to_base64(image_path):
    import base64
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Initialize OpenAI client
client = openai.OpenAI(api_key=openai_api_key)

# Get base64 encoded image
def analyze_city_image(image_path: str):
    base64_image = encode_image_to_base64(image_path)

    # Create message with image
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You get a image of city and need to response with a name of the city."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    },
                    {
                        "type": "text", 
                        "text": "What city is on this image?"
                    }
                ]
            }
        ],
        max_tokens=300
    )
    return response.choices[0].message.content

# Process all PNG files in current directory
def process_all_png_files():
    results = {}
    for file in os.listdir('S02E02'):
        if file.endswith('.png'):
            try:
                city_name = analyze_city_image(f'S02E02/{file}')
                results[file] = city_name
                print(f"Analyzed {file}: {city_name}")
            except Exception as e:
                print(f"Error processing {file}: {str(e)}")
    return results

if __name__ == "__main__":
    results = process_all_png_files()
    print("\nFinal Results:")
    for file, city in results.items():
        print(f"{file}: {city}")

