import sys
import itertools
import pytest
import logging
from audiogen import util as util
from audiogen import sampler as sampler

ORIGINAL_FRAME_RATE = getattr(sampler, 'FRAME_RATE', 44100)
PYTHON_MAJOR_VERSION = sys.version_info[0]

def setup_module(module):
    # we force the frame rate to 1 sample/sec in order to make
    # testing a little easier.
    setattr(sampler, 'FRAME_RATE', 1)
    assert ORIGINAL_FRAME_RATE == 44100

def teardown_module(module):
    setattr(sampler, 'FRAME_RATE', ORIGINAL_FRAME_RATE)
    assert sampler.FRAME_RATE == 44100

@pytest.fixture
def number_gen():
    def fn(num):
        i = 0
        while i < num:
            yield i
            i += 1
    return fn

if not hasattr(util, 'can_next'):
    def can_next(thing):
        if sys.version_info[0] > 2:
            try:
                # next(iter(thing))
                next(thing)
                return True
            except TypeError as e:
                return False
            except StopIteration as e:
                # it was an empty iterable.
                return True
        else:
            return hasattr(thing, 'next')
    util.can_next = can_next

def test_can_next_type_assumptions():
    assert util.can_next(1) == False
    assert util.can_next((1,2,3)) == False
    assert util.can_next(iter((1,2,3))) == True
    assert util.can_next([1,2,3]) == False
    assert util.can_next(iter([1,2,3])) == True

    def gen_func(num):
        i = 0
        while i < num:
            yield i
            i += 1

    assert util.can_next(gen_func(5)) == True

def test_can_next_idempotence(number_gen):
    assert len([x for x in number_gen(10)]) == 10
    assert len([x for x in number_gen(10)]) == 10

    gen = number_gen(10)
    assert util.can_next(gen)
    assert len([x for x in gen]) == 10

def test_tuple_iterable():
     t = (1,2,3)
     assert len(t) == 3
     assert len([x for x in t]) == 3

     # new implementation of can_next hinges on this fact:
     assert not hasattr(t, 'next')

def test_cropper(number_gen):
    cropper = lambda gen: itertools.islice(gen, 0, 5)
    actual = [x for x in util.crop(number_gen(10), seconds=1, cropper=cropper)]
    expected = [x for x in range(5)]
    assert actual == expected

    actual = [x for x in util.crop(number_gen(10), seconds=1)]
    assert actual == [0]

    actual = [x for x in util.crop(number_gen(10), seconds=2)]
    assert actual == [0, 1]

def test_crop_with_fades(number_gen):
    actual = [x for x in util.crop_with_fades(number_gen(10), 5, fade_in=2, fade_out=2)]
    expected = [0.0, 0.5, 2, 3.0, 2.0]
    assert actual == expected

def test_crop_with_fade_out(number_gen):
    actual = [x for x in util.crop_with_fade_out(number_gen(10), seconds=5, fade=2)]
    expected = [0, 1, 2, 3.0, 2.0]
    assert actual == expected

def test_crop_at_zero_crossing():
    samples = [2,3,4,5,3,1,3,6,0,5,4,3]
    actual = [x for x in util.crop_at_zero_crossing(samples, seconds=10, error=0.1)]
    expected = [2, 3, 4, 5, 3, 1, 3, 6, 0, 5]
    print(actual)
    assert actual == expected

def test_normalize(number_gen):
    actual = [x for x in util.normalize(number_gen(10))]
    expected = [-1.0, -0.9921875, -0.984375, -0.9765625, -0.96875, -0.9609375, -0.953125, -0.9453125, -0.9375, -0.9296875]
    assert actual == expected

def test_hard_clip(number_gen):
    actual = [x for x in util.hard_clip(number_gen(10), min=2, max=8)]
    expected = [2, 2, 2, 3, 4, 5, 6, 7, 8, 8]
    assert actual == expected

def test_vector_reduce():
    v0 = (1,2,3)
    v1 = (4,5,6)
    v2 = (7,8,9)

    expected = [12, 15, 18]
    actual = [x for x in util.vector_reduce(lambda a,b:a+b, [iter(v0), iter(v1), iter(v2)])]
    assert actual == expected

    actual = [x for x in util.vector_reduce1(lambda a,b:a+b, [iter(v0), iter(v1), iter(v2)])]
    assert actual == expected

def test_sum(number_gen):
    actual = [x for x in util.sum(number_gen(10), number_gen(10), number_gen(10))]
    expected = [0, 3, 6, 9, 12, 15, 18, 21, 24, 27]
    assert actual == expected

def test_volume(number_gen):
    # no change
    actual = [x for x in util.volume(number_gen(10))]
    expected = [float(x) for x in range(10)]
    assert actual == expected

    # constant change
    actual = [x for x in util.volume(number_gen(10), 5)]
    expected = [0.0, 1.7782794100389228, 3.5565588200778455, 5.334838230116768, 7.113117640155691, 8.891397050194614, 10.669676460233536, 12.447955870272459, 14.226235280311382, 16.004514690350305]
    assert actual == expected

    # variable change
    actual = [x for x in util.volume(number_gen(10), number_gen(10))]
    expected = [0.0, 1.1220184543019633, 2.5178508235883346, 4.237612633868263, 6.339572769844454, 8.891397050194614, 11.971573889813277, 15.671047969978376, 20.09509145207664, 25.36544638138008]
    assert actual == expected

    # incongruent variable change.
    actual = [x for x in util.volume(number_gen(10), number_gen(5))]
    expected = [0.0, 1.1220184543019633, 2.5178508235883346, 4.237612633868263, 6.339572769844454]
    assert actual == expected

def test_clip(number_gen):
    # simple limit
    actual = [x for x in util.clip(number_gen(10), 5)]
    expected = [0, 1, 2, 3, 4, 5, 5.0, 5.0, 5.0, 5.0]
    assert actual == expected

    # generator limit
    clip_gen = iter([x/2 for x in number_gen(10)])
    actual = [x for x in util.clip(number_gen(10), clip_gen)]

    # old version is giving this. I'm pretty sure it's a bug because it's
    # using inteteger division and not floating point.
    python2_expected = [0, 0.0, 1.0, 1.0, 2.0, 2.0, 3.0, 3.0, 4.0, 4.0]
    python3_expected = [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
    expected = python3_expected if PYTHON_MAJOR_VERSION > 2 else python2_expected
    assert actual == expected

    # incongruent limit
    clip_gen = iter([x/2 for x in number_gen(5)])
    actual = [x for x in util.clip(number_gen(10), clip_gen)]
    python2_expected = [0, 0.0, 1.0, 1.0, 2.0]
    python3_expected = [0, 0.5, 1.0, 1.5, 2.0]
    expected = python3_expected if PYTHON_MAJOR_VERSION > 2 else python2_expected
    assert actual == expected

def test_envelope(number_gen):
    # constant factor
    actual = [x for x in util.envelope(number_gen(10), 2)]
    expected = [2*x for x in range(10)]
    assert actual == expected

    # generator should cause square factor
    square_gen = number_gen(10)
    actual = [x for x in util.envelope(number_gen(10), square_gen)]
    expected = [x*x for x in range(10)]
    assert actual == expected

    # incongruent square factor
    square_gen = number_gen(5)
    actual = [x for x in util.envelope(number_gen(10), square_gen)]
    expected = [x*x for x in range(5)]
    assert actual == expected