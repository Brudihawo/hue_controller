"""Utility Functions for hue_controller."""


# TODO: Fix this so it uses the index instead of the element.
# TODO: Also fix where get_next is used.
def get_next(lst, elem):
    """Get subsequent element of list.

    Parameters
    ----------
        lst : List in which to find next element
        elem: Element in array to get next element

    Returns
    -------
        None
            If element is last in lst
        Element
            Next element in list (else)
    """
    try:
        return lst[lst.index(elem) + 1]
    except IndexError:
        return None
    except ValueError:
        return None


def map_linear(x, orig_min, orig_max, tar_min, tar_max):
    """Map x from range [orig_min, orig_max] to [tar_min, tar_max].

    Parameters
    ----------
        x : numeric
            Value to map.
        orig_min : numeric
                   Lower boundary of origin range.
        orig_max : numeric
                   Upper boundary of origin range.
        tar_min : numeric
                  Lower boundary of target range.
        tar_max : numeric
                  Upper boundary of target range.

    Returns
    -------
        int
            Mapped x in new target range
    """
    return (x - orig_min) / (orig_min - orig_max) * (tar_min - tar_max) + tar_min


def cutoff_val(x, lower, upper):
    """Cut off values exceeding upper and lower boundary.

    Parameters
    ----------
        x : numeric
            Value to cut off.
        lower : numeric
                Lower boundary.
        upper : numeric
                Upper boundary.

    Returns
    -------
        numeric
            lower if x < lower, upper if x > upper, else x.
    """
    if x < lower:
        return lower
    if x > upper:
        return upper
    return x
