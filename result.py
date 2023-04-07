class Result:
    def __init__(self) -> None:
        pass
    
class ImageClassificationResult(Result):
    def __init__(self, base64_str, class_name, score) -> None:
        super().__init__()
        self.base64_str = base64_str
        self.class_name = class_name
        self.score = score

class ObjectDetectionResult(Result):
    def __init__(self, base64_str, location) -> None:
        super().__init__()
        self.base64_str = base64_str
        self.location = location 