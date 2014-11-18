import math

class PhysState(object):
    def __init__(self, pos, velocity):
        self.pos = pos
        self.velocity = velocity

class PhysDerivatives(object):
    def __init__(self, dx, dv):
        self.dx = dx
        self.dv = dv


class Vector(object):
    @staticmethod
    def almostEqual(d1, d2, epsilon=10**-10):
        return (abs(d2 - d1) < epsilon)
    
    def __init__(self, x, y):
        #ensure type is always the same
        self.x = float(x)
        self.y = float(y)

    def __eq__(self, other):
        if(isinstance(other, Vector)):
            return (Vector.almostEqual(self.x, other.x) and 
                    Vector.almostEqual(self.y, other.y))
        else:
            return False

    def __add__(self, other):
        if(isinstance(other, Vector)):
            return Vector(self.x + other.x, self.y + other.y)
        else:
            return NotImplemented

    def __radd__(self, other):
        return self + other

    def __mul__(self, other):
        if(isinstance(other, Vector)):
            return (self.x * other.x) + (self.y * other.y)
        elif(isinstance(other, int) or isinstance(other, float)):
            return Vector(self.x * other, self.y * other)
        else:
            return NotImplemented

    def __rmul__(self, other):
        return self * other

    def __str__(self):
        return "Vector(%f, %f)" % (self.x, self.y)

    def __repr__(self):
        return str(self)

    def __sub__(self, other):
        return self + (-1) * other

    def __div__(self, other):
        if(isinstance(other, int)):
            other = float(other)
        if(isinstance(other, float)):
            return Vector(self.x/other, self.y/other)
        else:
            return NotImplemented

    def __iadd__(self, other):
        if(isinstance(other, Vector)):
            self.x += other.x
            self.y += other.y
            return self
        else:
            return NotImplemented

    def __imul__(self, other):
        if(isinstance(other, float) or isinstance(other, int)):
            self.x *= other
            self.y *= other
            return self
        else:
            return NotImplemented

    def getMag(self):
        return math.sqrt(self*self)

    def projOnto(self, u):
        return ((self*u/float(u*u)) * u)

    def getXY(self):
        return (self.x, self.y)

def testVectorClass():
    print "Testing Vector Class...",
    #equality
    assert(Vector(3, 4) == Vector(3, 4))
    assert(Vector(0, 0) == Vector(0, 0))
    assert(Vector(6, 8) != Vector(3, 4))

    #addition
    assert(Vector(3, 4) + Vector(2, 5) == Vector(5, 9))
    assert(Vector(-3, 2) + Vector(3, -2) == Vector(0, 0))

    #subtraction
    assert(Vector(3, 4) - Vector(2, 7) == Vector(1, -3))
    assert(Vector(3, 4) - Vector(2, 7) != Vector(2, 7) - Vector(3, 4))

    #multiplication
    assert(Vector(3, 4) * 3 == Vector(9, 12))
    assert(Vector(2, 3) * -2 == 2 * Vector(-2, -3))

    #multiplication of two vectors is dot product
    assert(Vector(3, 4) * Vector(2, 5) == 26)
    assert(Vector(-1, 3) * Vector(3, 1) == 0)

    #get magnitude
    assert(Vector(3, 4).getMag() == 5)

    #projections main vector is what you are projecting
    #argument is the vector to project onto
    assert(Vector(4, 3).projOnto(Vector(1, 0)) == Vector(4, 0))
    assert(Vector(1, 1).projOnto(Vector(3, 4)) == Vector(21/25.0, 28/25.0))

    assert(Vector(6, 3) / 3 == Vector(2, 1))

    vector = Vector(1, 1)
    vector += Vector(1, 2)
    assert(vector == Vector(2, 3))

    vector *= 5
    assert(vector == Vector(10, 15))

    assert((10, 15) == vector.getXY())
    print "...passed!"
