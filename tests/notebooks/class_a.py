import dataclasses


@dataclasses.dataclass
class ClassA:
    aa : str = None
    ab : int = 0
        
    def print_content(self):
        print(self.__dict__)
        
