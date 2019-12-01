import dataclass


@dataclasses.dataclass
class ClassBase:
    a : str = None
    b : int = 0
        
    def print_content(self):
        print(self.__dict__)
        
