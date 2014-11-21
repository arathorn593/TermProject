from physics import *

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

    assert(Vector.zero() == Vector(0, 0))
    print "...passed!"

def testPhysEnvironmentClass():
    print "testing Physenvironment Class...",
    grav = 10
    screenConv = 100
    x0 = 0
    y0 = 250

    environment = PhysEnvironment(grav, screenConv, x0, y0)

    #object at 1, 1.5 in meters
    position = Vector(1, 1.5)

    assert(environment.getScreenXY(position) == (100, 100))

    screenPos = Vector(150, 175)
    assert(environment.getVect(screenPos) == (1.5, .75))
    print "...Passed!"

testVectorClass()
testPhysEnvironmentClass()