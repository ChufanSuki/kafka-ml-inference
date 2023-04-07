class Result:
    def __init__(self) -> None:
        pass

class Location:
    def __init__(self, left, top, width, height) -> None:
        self.left = left
        self.top = top
        self.width = width
        self.height = height
    
class ImageClassificationResult(Result):
    def __init__(self, base64_str, class_name, score) -> None:
        super().__init__()
        self.base64_str = base64_str
        self.class_name = class_name
        self.score = score

class ObjectDetectionResult(Result):
    def __init__(self, num) -> None:
        super().__init__()
        self.num = num
        self.base64_str = [None * num]
        self.class_name = [None * num]
        self.score = [None * num]
        self.location = [None * num]
    
    def add_to_result(self, base64_str, class_name, score, location: Location):
        self.base64_str.append(base64_str)
        self.class_name.append(class_name)
        self.score.append(score)
        self.location.append(location)