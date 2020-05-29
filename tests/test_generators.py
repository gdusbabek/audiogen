import sys
import math
import audiogen.generators as generators
from audiogen import sampler as sampler
from audiogen import util as util

ORIGINAL_FRAME_RATE = getattr(sampler, 'FRAME_RATE', 44100)
PYTHON_MAJOR_VERSION = sys.version_info[0]

# def setup_module(module):
#     # we force the frame rate to 1 sample/sec in order to make
#     # testing a little easier.
#     setattr(sampler, 'FRAME_RATE', 1)
#     assert ORIGINAL_FRAME_RATE == 44100

# def teardown_module(module):
#     setattr(sampler, 'FRAME_RATE', ORIGINAL_FRAME_RATE)
#     assert sampler.FRAME_RATE == 44100

# NOTE: The generators here generate 44.1k samples per second.
#       In order to make testing stomachable, I'm comparing the
#       sums of the results.


def test_beep():
    num_seconds = 2
    samples = [x for x in generators.beep(seconds=num_seconds)]
    assert len(samples) == sampler.FRAME_RATE * num_seconds
    actual = sum(samples)
    expected = -3.1143206503242427e-12
    assert actual == expected

def test_fixed_tone():
    num_seconds = 0.2
    samples = [x for x in util.crop(generators.tone(), seconds=num_seconds)]
    assert len(samples) == sampler.FRAME_RATE * num_seconds
    actual = sum(samples)
    expected = 10.518189618991757
    assert actual == expected

def test_variable_tone():
    # set up the variation function
    def variation():
        count = 0
        while True:
            yield count % 10
            count += 1
    assert hasattr(variation(), 'next')

    num_seconds = 0.2
    samples = [x for x in util.crop(generators.tone(frequency=variation()), seconds=num_seconds)]
    assert len(samples) == sampler.FRAME_RATE * num_seconds
    actual = sum(samples)
    expected = 299.2509532216738
    assert actual == expected

def test_synth():
    num_seconds = 2
    samples = [x for x in util.crop(generators.synth(400, 90), seconds=num_seconds)]
    assert len(samples) == 2 * sampler.FRAME_RATE
    actual = sum(samples)
    expected = 1361.8180138781925
    assert actual == expected

def test_silence():
    num_seconds = 5
    samples = [x for x in generators.silence(seconds=num_seconds)]
    assert len(samples) == num_seconds * sampler.FRAME_RATE
    actual = sum(samples)
    expected = 0
    assert actual == expected
