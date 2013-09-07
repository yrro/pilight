import math

def saw (t):
        q, r = divmod (t, 1)
        if r < 0.5:
                return 2*r
        else:
                return 1-2*(r-0.5)

def sine (t):
        return (1 + math.sin (t))/2
