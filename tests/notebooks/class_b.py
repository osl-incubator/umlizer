import dataclasses
from class_a import ClassA

@dataclasses.dataclass
class ClassB(ClassA):
    ba : str = None
    bb : int = 0
        
    def print_content(self):
        print(self.__dict__)
        
