import os
import io
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from PIL import Image
import google.generativeai as genai

app = FastAPI()

# Enable CORS for the application
# This is crucial if the API is accessed from web interfaces or different domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Fetch API key from Environment Variables
# Crucial for deployment on platforms like Render or Heroku
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", ""))

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

@app.get("/")
async def root():
    '''
    Root endpoint for health check and verification of deployment.
    '''
    print("Root endpoint hit")
    return {
        "status": "online",
        "message": "SmartCropAdvisory Gemini API is running successfully!",
        "version": "1.0.1"
    }

@app.get("/health")
async def health_check():
    '''
    Dedicated health check endpoint.
    '''
    return {"status": "healthy", "timestamp": os.getenv("RENDER_SERVICE_ID", "local")}

@app.post("/predict")
async def predict_disease(file: UploadFile = File(...)):
    '''
    Endpoint utilizing Google Gemini Vision for analyzing crop disease from image bytes.
    Automatically handles ANY crop type using Multi-modal Generative AI natively.
    '''
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY environment variable not set on the server.")
    
    try:
        # 1. Read the file into memory
        contents = await file.read()
        
        # 2. Convert to PIL Image which Gemini accepts natively
        img = Image.open(io.BytesIO(contents))
        
        # 3. Setup Gemini Model
        # Using 1.5-flash as it's perfectly optimized for multimodal rapid logic
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 4. Prompt Engineering for JSON response matching Retrofit Model structure
        prompt = """
        You are an expert plant pathologist and agronomist. 
        Analyze the provided image of a plant leaf and determine if it has any disease.
        IMPORTANT: Your response MUST be valid JSON data and nothing else. Do not use markdown backticks like ```json.
        The JSON must strictly have the following three keys:
        - "disease": String (Name of the plant and the disease e.g. 'Apple Scab', or 'Healthy Tomato')
        - "confidence": String (A percentage like '95%')
        - "solution": String (A brief actionable step for the farmer to treat the disease)
        """
        
        # 5. Inference (Pass the text prompt and the image)
        response = model.generate_content([prompt, img])
        
        # 6. Parse and Clean response (Gemini sometimes returns markdown json blocks)
        res_text = response.text.replace("```json", "").replace("```", "").strip()
        
        # Deserialize into native dict so FastAPI can return Application/JSON natively
        result_json = json.loads(res_text)
        
        return result_json
        
    except Exception as e:
        print(f"Error occurred: {e}")
        # Fallback payload in case model fails to process or return valid JSON
        return {
            "disease": "Unable to identify",
            "confidence": "0%",
            "solution": "An error occurred with image diagnosis. Try uploading a clearer picture."
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app_host = "0.0.0.0"
    uvicorn.run(app, host=app_host, port=port)
