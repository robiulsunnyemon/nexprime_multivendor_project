from fastapi import FastAPI, File, UploadFile
from typing import List, Optional, Union, Annotated
from fastapi.testclient import TestClient

app = FastAPI()

@app.patch("/test")
def test_endpoint(
    images: Annotated[Optional[List[Union[UploadFile, str]]], File()] = None
):
    return {"types": [type(i).__name__ for i in images] if images else None}

client = TestClient(app)
print("Empty string:", client.patch("/test", data={"images": ""}).json())
print("Missing:", client.patch("/test").json())
print("File:", client.patch("/test", files=[("images", ("test.jpg", b"123"))]).json())
