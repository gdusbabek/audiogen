# coding=utf8

import sys
import audiogen.noise as noise
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

def test_stringness():
    assert isinstance('foo', str)

def _collect(gen, limit):
    ''' Collect a limit of things from a generator '''
    count = 0
    while count < limit:
        yield next(gen)
        count += 1
    return

def test_arcfour():
    gen = noise.arcfour('foobar')
    actual = [x for x in _collect(gen, 10)]
    expected = [111, 169, 16, 238, 246, 67, 179, 100, 142, 246]
    assert actual == expected

    gen = noise.arcfour([1,2,3,4,5])
    actual = [x for x in _collect(gen, 10)]
    expected = [178, 57, 99, 5, 240, 61, 192, 39, 204, 195]
    print(actual)
    assert actual == expected

def test_arcfour_drop():
    gen = noise.arcfour_drop('foobar')
    actual = [x for x in _collect(gen, 10)]
    expected = [207, 172, 67, 144, 212, 235, 238, 13, 218, 54]
    assert actual == expected

def test_white_noise():
    gen = noise.white_noise()
    actual = [x for x in _collect(gen, 10)]
    expected = [0.392364501953125, -0.226409912109375, 0.876861572265625, 0.501190185546875, 0.599700927734375, -0.35711669921875, -0.921356201171875, -0.807373046875, -0.17572021484375, 0.158660888671875]
    assert actual == expected

def test_white_noise_samples():
    gen = noise.white_noise_samples()
    actual = [x for x in _collect(gen, 10)]
    expected = ['\xb29', 'c\x05', '\xf0=', "\xc0'", '\xcc\xc3', 'RJ', '\n\x11', '\x18\xa8', 'i\x82', '\x94O']
    assert actual == expected

def test_red_noise():
    gen = noise.red_noise()
    actual = [x for x in _collect(gen, 10)]
    expected = [0.048828125, -0.0205078125, -0.048828125, -0.1689453125, -0.0595703125, -0.125, -0.0625, -0.1494140625, -0.0751953125, -0.009765625]
    print(actual)
    assert actual == expected