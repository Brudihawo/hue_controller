#!/usr/bin/python

def get_next(arr, elem):
  """Gets element after elem in arr
  Args:
    arr: Array
    elem: Element in array to get next element
  Returns:
    Next element of array after elem if it is present, else returns None
  """
  try:
    return arr[arr.index(elem) + 1]
  except IndexError:
    return None
  
def map_linear(x, orig_min, orig_max, tar_min, tar_max):
  """Maps x from range [orig_min, orig_max] to [tar_min, tar_max]
  Args:
    x: Parameter to Maps
    orig_min: Low end of origin range
    orig_max: High end of origin range
    tar_min: Low end of target range
    tar_max: High end of target range
  Returns:
    Mapped x in new target range
  """
  return (x - orig_min) / (orig_min - orig_max) * (tar_min - tar_max) + tar_min

def cutoff_val(x, lower, upper):
  """Cuts off values exceeding upper and lower boundary
  Args:
    x: Value to cut off
    lower: lower boundary
    upper: upper boundary
  
  Returns:
    lower if x < lower, upper if x > upper, else x
  """
  if x < lower:
    return lower
  elif x > upper:
    return upper
  else:
    return x
