def saw (t):
        q, r = divmod (t, 1)
        if r < 0.5:
                return 2*r
        else:
                return 1-2*(r-0.5)

def sine (t):
        import math
        return (1 + math.sin (t * 2 * math.pi))/2

def constant (t):
        return 1

def third (t):
        q, r = divmod (t, 1)
        if r < 0.333:
                return 1
        return 0
