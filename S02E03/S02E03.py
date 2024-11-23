import openai
import os
import dotenv
import requests
import cv2
import base64
from io import BytesIO

dotenv.load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
personal_api_key = os.getenv('PERSONAL_API_KEY')

def encode_image_to_base64(image_path):
    import base64
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Initialize OpenAI client
client = openai.OpenAI(api_key=openai_api_key)

# Get base64 encoded image
def generate_image(description: str):
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=description,
            size="1024x1024",
            quality="standard",
            n=1
        )
        # Response contains a URL to the generated image
        image_url = response.data[0].url
        
        # Download the image
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            # Save the image locally
            with open("generated_image.png", "wb") as f:
                f.write(image_response.content)
            
            # Read and display with OpenCV
            image = cv2.imread("generated_image.png")
            cv2.imshow("Generated Image", image)
            cv2.waitKey(0)  # Wait for a key press
            cv2.destroyAllWindows()
            
            return image_url
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

desc_url = f'https://centrala.ag3nts.org/data/{personal_api_key}/robotid.json'

prompt = requests.get(desc_url).json()
print(prompt['description'])

response = client.images.generate(
  model="dall-e-3",
  prompt=prompt['description'],
  size="1024x1024",
  quality="standard",
  n=1,
)

image_url = response.data[0].url

answer_url = "https://centrala.ag3nts.org/report"
answer_json = {
    "task": "robotid",
    "apikey": personal_api_key,
    "answer": image_url
}

image = requests.get(image_url)
answer_response = requests.post(answer_url, json=answer_json)
print(answer_response.request.body)  # Displays the request body

# Assuming `login_response` is the response object from the login request
print("Status Code:", answer_response.status_code)  # Displays the status code (e.g., 200)
print("Response Body:", answer_response.text.encode('utf-8').decode('unicode-escape'))       # Displays the response content as a string

print("save image")
image_bytes = (BytesIO(image.content))
with open("S02E03/generated_image.png", "wb") as f:
    f.write(image.content)
# cv2.imshow("Generated Image", image)
# cv2.waitKey(0)  # Wait for a key press
# cv2.destroyAllWindows()
