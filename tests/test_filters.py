import audiogen.filters as filters

# These tests are mainly to ensure compatibility with the results from the old library.
# You shold be able to run them there and get the same results.

def test_iir():
    A = [1,2,3,4,5,6,7,8]
    B = [3,4,5,6,7,8,9,0]
    gen = iter([1,1,1,1,0,0,0,0])

    iir = filters.iir(A, B)
    actual = [x for x in iir(gen)]
    expected = [0, 0, 0, 0, 0, 0, 0, 0, 1, 6, 28, 123, 531, 2286, 9837, 42327]
    assert actual == expected

def test_band_pass():
    gen = iter([100, 34000, 43443, 12353, 2, 0, 753433])
    iir = filters.band_pass(144390, 12000)
    expected = [0, 0, 52.688293116819665, 17902.3438880653, 18874.545528302602, -13883.70233086756, -20033.72890440749, -3847.0694654327, 397859.57936680166]
    actual = [x for x in iir(gen)]
    assert actual == expected

def test_band_stop():
    gen = iter([100, 34, 556, 3, 2.3, 4.4, 94, 23])
    iir = filters.band_stop(144390, 12500)
    actual = [x for x in iir(gen)]
    expected = [0, 0, 46.3726269592332, 27.687549172077397, 306.67952232206255, 80.60763062938622, 248.80292325755013, -9.308218554722806, 40.1221045661752, 24.277103322517064]
    print(actual)
    assert actual == expected