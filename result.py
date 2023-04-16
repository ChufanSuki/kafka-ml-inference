from middleware import draw_rectangle_on_image
import requests
import base64
from pydantic import BaseModel, Field

class Result:
    def __init__(self) -> None:
        pass

class Position:
    def __init__(self, left, top, width, height) -> None:
        self.left = left
        self.top = top
        self.width = width
        self.height = height

    def as_dict(self):
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height
        }
    
class ImageClassificationResult(Result):
    def __init__(self, base64_str, class_name, score) -> None:
        super().__init__()
        self.base64_str = base64_str
        self.class_name = class_name
        self.score = score
        
    def as_dict(self):
        return {
            "base64_str": self.base64_str,
            "class_name": self.class_name,
            "score": self.score
        }

class ObjectDetectionResult(Result):
    def __init__(self, num, base64_str) -> None:
        super().__init__()
        self.num = num
        self.base64_str = base64_str
        self.class_name = []
        self.score = []
        self.position = []
    
    def as_dict(self):
        dict = {
            "base64_str": self.base64_str,
            "class_name": [],
            "score": [],
            "position": [] 
        }
        for i in range(self.num):
            dict["class_name"].append(self.class_name[i])
            dict["score"].append(self.score[i])
            dict["position"].append(self.position[i].as_dict())
        return dict
    
    def add_to_result(self, class_name, score, position: Position):
        self.class_name.append(class_name)
        self.score.append(score)
        self.position.append(position)
        
    def draw_rectangle_on_image(self):
        for i in range(self.num):
            self.base64_str = draw_rectangle_on_image(self.base64_str, self.position[i])

class ImageSegmentationResult(Result):
    def __init__(self, segmentation_list_path) -> None:
        super().__init__()
        png_url = "http://10.14.42.236:30260/imageSegmentation/image/" + segmentation_list_path

        # Send a GET request to the PNG URL and get the content
        response = requests.get(png_url)
        png_content = response.content

        # Encode the PNG content as a base64 string
        self.png_base64 = base64.b64encode(png_content).decode('utf-8')

    def as_dict(self):
        return {
            "png_base64": self.png_base64
        }