import sys
import io
import itertools
import errno
import struct
from io import BytesIO
import wave
import hashlib
import pytest
import audiogen.noise as noise
from audiogen import util as util
from audiogen import sampler as sampler
from audiogen import generators as generators


PYTHON_MAJOR_VERSION = sys.version_info[0]

def test_file_is_seekable():
    f = open('audiogen/filters.py')
    assert sampler.file_is_seekable(f)

    # grr test is fine on linux. broken os os x.
    # f = open('/dev/tty')
    # assert not sampler.file_is_seekable(f)

    class safenotell(object):
        def tell(self):
            raise IOError(errno.ESPIPE, 'you should be expecting this')
    assert not sampler.file_is_seekable(safenotell())

    class badnotell(object):
        def tell(self):
            raise IOError(errno.ETIMEDOUT, 'you should expect this too')
    with pytest.raises(IOError):
        sampler.file_is_seekable(badnotell())

def _collect(gen, num_samples):
    count = 0
    while count < num_samples:
        yield next(gen)
        count += 1
    return

def test_sample():
    gen = generators.beep()
    samples = sampler.sample(gen)
    actual = [x for x in _collect(samples, 10)]
    expected = [b'\x00\x00', b'\x04\x00', b'\x12\x00', b')\x00', b'I\x00', b'r\x00', b'\xa3\x00', b'\xdc\x00', b'\x1d\x01', b'e\x01']
    assert actual == expected

def test_sample_all():
    gens = [generators.beep(frequency=440), generators.beep(frequency=875)]
    sampler_list = sampler.sample_all(gens)
    actual0 = [x for x in _collect(sampler_list[0], 10)]
    actual1 = [x for x in _collect(sampler_list[1], 10)]
    expected0 = [b'\x00\x00', b'\x04\x00', b'\x12\x00', b')\x00', b'I\x00', b'r\x00', b'\xa3\x00', b'\xdc\x00', b'\x1d\x01', b'e\x01']
    expected1 = [b'\x00\x00', b'\x08\x00', b'$\x00', b'Q\x00', b'\x8e\x00', b'\xd9\x00', b'0\x01', b'\x90\x01', b'\xf5\x01', b'\\\x02']
    assert actual0 != actual1
    assert actual0 == expected0
    assert actual1 == expected1

def test_interleave():
    gen = sampler.interleave([iter('abcde'), iter('fghij')])
    actual = [x for x in gen]
    expected = ['af', 'bg', 'ch', 'di', 'ej']
    print(actual)
    assert actual == expected

# this test shows that the way buffer was implemented will not work
# (wrong assumptions about islice -- that buffer_size argument is something else)
def test_islice_assumptions():
    b = b'abcdefghijklmnopqrstuvwxyz'

    slicer = itertools.islice(iter(b), 2)
    with pytest.raises(AssertionError):
        assert next(slicer) == b'ab'

    slicer = itertools.islice(iter(b), None, None, 2)
    with pytest.raises(AssertionError):
        assert next(slicer) == b'ab'

    # this was essentially the code behind the python 2 imple of buffer.
    # it doesn't work in python 3.
    chunker = iter(lambda: b"".join(itertools.islice(iter(b), 2)), b"")
    if PYTHON_MAJOR_VERSION > 2:
        with pytest.raises(TypeError):
            assert next(chunker) == b'ab'
    else:
        assert next(chunker) == b'ab'

def test_buffer():
    # 32 bytes. 4 chunks of 8 bytes
    test_str = b'abcdefgh' + b'ijklmnop' + b'qrstuvwx' + b'yzabcdef' + b'ghi'
    chunk_gen = sampler.buffer(test_str, buffer_size=8)
    chunks = [x for x in chunk_gen]
    assert len(chunks) == 5
    assert chunks[0] == b'abcdefgh'
    assert chunks[1] == b'ijklmnop'
    assert chunks[2] == b'qrstuvwx'
    assert chunks[3] == b'yzabcdef'
    assert chunks[4] == b'ghi'

def test_wav_samples():
    gens = [generators.beep(frequency=440), generators.beep(frequency=875)]
    wav_samples = sampler.wav_samples(gens)
    actual = [x for x in _collect(wav_samples, 10)]
    expected = [b'\x00\x00\x00\x00', b'\x04\x00\x08\x00', b'\x12\x00$\x00', b')\x00Q\x00', b'I\x00\x8e\x00', b'r\x00\xd9\x00', b'\xa3\x000\x01', b'\xdc\x00\x90\x01', b'\x1d\x01\xf5\x01', b'e\x01\\\x02']
    assert actual == expected

    sav_samples = sampler.wav_samples(gens, raw_samples=True)
    actual = [x for x in _collect(wav_samples, 10)]
    expected = [b'\xb4\x01\xc2\x02', b'\x08\x02"\x03', b'a\x02y\x03', b'\xbf\x02\xc3\x03', b'!\x03\xfd\x03', b'\x85\x03#\x04', b'\xeb\x033\x04', b'R\x04*\x04', b'\xb9\x04\x06\x04', b' \x05\xc5\x03']
    assert actual == expected

def test_bytes_and_struct_interactions():
    f = BytesIO()
    setattr(f, 'mode', 'wb')
    f.write(b'abc')
    f.write(struct.pack('<L4s4sLHHLLHH4s',
    3632, b'WAVE', b'fmt ', 16,
    0x0001, 0, 0, 0,
    0, 0, b'data'))

def test_wave_module_patched():
    f = BytesIO()
    setattr(f, 'mode', 'wb')
    assert not isinstance(f, str)
    w = wave.open(f, 'wb')
    assert isinstance(w, wave.Wave_write)
    w.setparams((1, 2, 44100, 0, "NONE", "no compression"))
    w.setnframes((0x7FFFFFFF - 36) / w.getnchannels() / w.getsampwidth())
    w._ensure_header_written(0)

    # returns true in python 2. unsure about 3.
    # dunno which version of python this is borked in...
    assert sampler.wave_module_patched()

def test_write_wav():
    f = BytesIO()
    setattr(f, 'mode', 'wb')
    assert sampler.file_is_seekable(f)

    # we want 1 second of data from each.
    num_seconds = 1
    channels = [
        generators.beep(frequency=440, seconds=num_seconds),
        generators.beep(frequency=875, seconds=num_seconds)
    ]

    sampler.write_wav(f, channels)
    # f.flush()
    assert not f.closed

    # its about 176kb of data. hash it.
    md5 = hashlib.md5()
    szbuf = 65536

    # reset the bytes io and read it.
    f.seek(0)
    while True:
        data = f.read(szbuf)
        if not data:
            break
        md5.update(data)
    print(md5.hexdigest())
    assert md5.hexdigest() == '8a59f916eebe2401072334596656625a'

    f.close()

def test_play():
    num_seconds = 1
    channels = [
        generators.beep(frequency=440, seconds=num_seconds),
        generators.beep(frequency=875, seconds=num_seconds)
    ]
    if sampler.pyaudio_loaded:
        sampler.play(channels)





