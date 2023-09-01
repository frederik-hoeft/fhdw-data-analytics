from typing import List

# This is a wrapper class for the binary search algorithm.
class BinarySearchWrapper:
    __data: List[int]
    __invocations: int = 0

    # The constructor takes in a list of integers and stores it in the private
    # data member.
    def __init__(self, data: List[int]) -> None:
        # set the private data member
        self.__data = data
        # sort the list
        self.__data.sort()

    # This method returns the index of the value in the list, or -1 if the value
    # is not in the list.
    def index_of_value_or_one_below(self, value: int) -> int:
        # call the private binary search method
        self.__invocations += 1
        return self.__binary_search_modified(value, 0, len(self.__data) - 1)

    def position_of_value_or_one_below(self, value: int) -> int:
        return self.index_of_value_or_one_below(value) + 1
    
    # This is the private binary search method. It takes in the value to search
    # for, the start index, and the end index. It returns the index of the value
    # in the list, or the closest index below if the value is not in the list.
    def __binary_search_modified(self, value: int, start: int, end: int) -> int:
        # if the start index is greater than the end index, then the value is
        # not in the list
        if start > end:
            # return the index of the value one below the value
            return end
        # calculate the middle index
        mid: int = (start + end) // 2
        # if the value is at the middle index, return the middle index
        if self.__data[mid] == value:
            return mid
        # if the value is less than the value at the middle index, search the
        # left half of the list
        elif self.__data[mid] > value:
            # the end index is now the middle index minus one
            return self.__binary_search_modified(value, start, mid - 1)
        else:
            # the start index is now the middle index plus one
            return self.__binary_search_modified(value, mid + 1, end)
    
    def print_invocations(self) -> None:
        print(f'BinarySearchWrapper invocations: {self.__invocations}')