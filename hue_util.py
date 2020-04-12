#!/usr/bin/python

def get_next(lst, elem):
  """Gets element after elem in arr
  
  Args:
    lst: list
    elem: Element in array to get next element
  
  Returns:
    Next element of array after elem if it is present, else returns None
  """
  try:
    return lst[lst.index(elem) + 1]
  except IndexError:
    return None
  
def map_linear(x, orig_min, orig_max, tar_min, tar_max):
  """Maps x from range [orig_min, orig_max] to [tar_min, tar_max]
  
  Args:
    x (numeric): Value to map
    orig_min (numeric): Lower boundary of origin range
    orig_max (numeric): Upper boundary of origin range
    tar_min (numeric): Lower boundary of target range
    tar_max (numeric): Upper boundary of target range
  
  Returns:
    Mapped x in new target range
  """
  return (x - orig_min) / (orig_min - orig_max) * (tar_min - tar_max) + tar_min

def cutoff_val(x, lower, upper):
  """Cuts off values exceeding upper and lower boundary
  
  Args:
    x (numeric): Value to cut off
    lower (numeric): Lower boundary
    upper (numeric): Upper boundary
  
  Returns:
    lower if x < lower, upper if x > upper, else x
  """
  if x < lower:
    return lower
  elif x > upper:
    return upper
  else:
    return x
