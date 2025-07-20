from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import easyocr
import io
import re
import numpy as np

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

YOUR_EMAIL = "yourmail"

reader = easyocr.Reader(['en'], gpu=False)

@app.post("/captcha")
async def solve_captcha(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image_bytes = io.BytesIO(contents)
        image = Image.open(image_bytes).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        result = reader.readtext(np.array(image), detail=0)
        full_text = " ".join(result)
        print("OCR Text:", full_text)
    except Exception:
        raise HTTPException(status_code=500, detail="OCR failed")

    numbers = re.findall(r'\d{8}', full_text)
    if len(numbers) < 2:
        raise HTTPException(status_code=400, detail="Not enough 8-digit numbers found")

    try:
        num1, num2 = int(numbers[0]), int(numbers[1])
        product = num1 * num2
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to compute product")

    return JSONResponse(content={"answer": product, "email": YOUR_EMAIL})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("2_captcha:app", host="0.0.0.0", port=8002, reload=True)
