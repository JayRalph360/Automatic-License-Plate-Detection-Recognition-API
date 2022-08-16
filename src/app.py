import io
import os
import sys

import cv2
import numpy as np
import pytesseract
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from PIL import Image

from helpers import get_plate, load_model, preprocess_image

sys.path.append(os.path.abspath(os.path.join("..", "config")))


app = FastAPI(
    title="AVNPR API",
    description="""Automatic Vehicle Number Plate Recognition API.""",
        docs_url=None,
    redoc_url=None
)

templates = Jinja2Templates(directory="templates")

favicon_path = "./images/favicon.ico"


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)


@app.get("/running")
async def running():
    note = """
    AVNPR API 📚
    Automatic Vehicle License Plate Recognition API!
    Note: add "/redoc" to get the complete documentation.
    """
    return note


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("ocr.html", {"request": request})


@app.post("/ocr_parser")
async def get_ocr(request: Request, file: UploadFile = File(...)):
    # write a function to save the uploaded file and return the file name
    if request.method == "POST":
        form = await request.form()
        if form["file"]:

            files = form["file"]
            contents = io.BytesIO(await files.read())
            file_bytes = np.asarray(bytearray(contents.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            cv2.imwrite("./images/image.jpg", img)
            try:
                vehicle, LpImg, cor = get_plate("./images/image.jpg")
                value = np.array(LpImg[0], dtype=np.float32)
                pred_img = Image.fromarray((value * 255).astype(np.uint8)).convert("RGB")
                pred_img.save("./images/newimage.jpg")

                image = Image.open("./images/newimage.jpg")

                # Extracting text from image
                custom_config = r"-l eng --oem 3 --psm 6"
                text = pytesseract.image_to_string(image, config=custom_config)

                # Remove symbol if any
                characters_to_remove = "!()@—*“>+-/,'|£#%$&^_~"
                new_string = text
                for character in characters_to_remove:
                    new_string = new_string.replace(character, "")

                # Converting string into list to dislay extracted text in seperate line
                new_string = new_string.split("\n")
                return templates.TemplateResponse(
                    "ocr.html", {"request": request, "sumary": new_string[0]}
                )
            except AssertionError:
                vals = "No License Plate Found"
                return templates.TemplateResponse(
                    "ocr.html", {"request": request, "sumary": vals }
                )
