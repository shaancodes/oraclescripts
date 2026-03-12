import numpy as np

def rowsum(matrix):
    """
    :param matrix (list): A list of lists where each inner list represents a row.
    :returns: (list) A list containing the sum of each row.
    """
    np_matrix = np.array(matrix)
    row_sums = np.sum(np_matrix, axis=1)
    return row_sums.tolist()

print(rowsum([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])) 
