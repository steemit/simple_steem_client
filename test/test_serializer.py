
import math, unittest
import time
from datetime import datetime
from simple_steem_client.serializer import twos, Serializer

class TestTwos(unittest.TestCase):

  def test_8bit(self):
    self.assertEqual(twos(0, 1), 0)
    self.assertEqual(twos(-1, 1), 255)
    self.assertEqual(twos(-128, 1), 128)
    self.assertEqual(twos(127, 1), 127)

  def test_16bit(self):
    self.assertEqual(twos(0, 2), 0)
    self.assertEqual(twos(-1, 2), 65535)
    self.assertEqual(twos(-32768, 2), 32768)
    self.assertEqual(twos(32767, 2), 32767)

  def test_32bit(self):
    self.assertEqual(twos(0, 4), 0)
    self.assertEqual(twos(-1, 4), 4294967295)
    self.assertEqual(twos(-2147483648, 4), 2147483648)
    self.assertEqual(twos(2147483647, 4), 2147483647)

  def test_64bit(self):
    self.assertEqual(twos(0, 8), 0)
    self.assertEqual(twos(-1, 8), 18446744073709551615)
    self.assertEqual(twos(-9223372036854775808, 8), 9223372036854775808)
    self.assertEqual(twos(9223372036854775807, 8), 9223372036854775807)

  def test_invalid_width(self):
    with self.assertRaises(AssertionError):
      twos(0, 0)
    with self.assertRaises(AssertionError):
      twos(0, 5)


class TestSerializer(unittest.TestCase):

  def test_uint8(self):
    s = Serializer()
    
    self.assertEqual(s.uint8(0x01), 1)
    self.assertEqual(s.uint8(0xff), 1)

    self.assertEqual(s._pos, 2)
    self.assertEqual(s._data[0:2], bytearray.fromhex('01ff'))
 
  def test_uint16(self):
    s = Serializer()

    self.assertEqual(s.uint16(0x0001), 2)
    self.assertEqual(s.uint16(0xfffe), 2)

    self.assertEqual(s._pos, 4)
    self.assertEqual(s._data[0:4], bytearray.fromhex('0100feff'))

  def test_uint32(self):
    s = Serializer()
    
    self.assertEqual(s.uint32(0x00000001), 4)
    self.assertEqual(s.uint32(0xfffffffe), 4)

    self.assertEqual(s._pos, 8)
    self.assertEqual(s._data[0:8], bytearray.fromhex('01000000feffffff'))

  def test_uint64(self):
    s = Serializer()

    self.assertEqual(s.uint64(0x0000000000000001), 8)
    self.assertEqual(s.uint64(0xfffffffffffffffe), 8)

    self.assertEqual(s._pos, 16)
    self.assertEqual(s._data[0:16], bytearray.fromhex('0100000000000000feffffffffffffff'))

  def test_int8(self):
    s = Serializer()
 
    self.assertEqual(s.int8(127), 1)   
    self.assertEqual(s.int8(-128), 1)

    self.assertEqual(s._pos, 2)
    self.assertEqual(s._data[0:2], bytearray.fromhex('7f80'))
 
  def test_int16(self):
    s = Serializer()

    self.assertEqual(s.int16(32767), 2)
    self.assertEqual(s.int16(-32768), 2)

    self.assertEqual(s._pos, 4)
    self.assertEqual(s._data[0:4], bytearray.fromhex('ff7f0080'))

  def test_int32(self):
    s = Serializer()
    
    self.assertEqual(s.int32(2147483647), 4)
    self.assertEqual(s.int32(-2147483648), 4)

    self.assertEqual(s._pos, 8)
    self.assertEqual(s._data[0:8], bytearray.fromhex('ffffff7f00000080'))

  def test_int64(self):
    s = Serializer()

    self.assertEqual(s.int64(9223372036854775807), 8)
    self.assertEqual(s.int64(-9223372036854775808), 8)

    self.assertEqual(s._pos, 16)
    self.assertEqual(s._data[0:16], bytearray.fromhex('ffffffffffffff7f0000000000000080'))

  def test_binary64(self):
    s = Serializer()

    self.assertEqual(s.binary64(math.inf), 8)
    self.assertEqual(s.binary64(-math.inf), 8)
    self.assertEqual(s.binary64(math.nan), 8)
    self.assertEqual(s.binary64(1.1945305291614955e+103), 8)
    self.assertEqual(s.binary64(3.141592653589793), 8)
    self.assertEqual(s.binary64(-1.8797162599773979e+230), 8)
    self.assertEqual(s._pos, 48)

    self.assertEqual(s._data[0:8], bytearray.fromhex('000000000000f07f'))
    self.assertEqual(s._data[8:16], bytearray.fromhex('000000000000f0ff'))
    self.assertEqual(s._data[16:24], bytearray.fromhex('000000000000f87f'))
    self.assertEqual(s._data[24:32], bytearray.fromhex('5555555555555555'))
    self.assertEqual(s._data[32:40], bytearray.fromhex('182d4454fb210940'))
    self.assertEqual(s._data[40:48], bytearray.fromhex('feedfacecafebeef'))

  def test_uvarint(self):
    s = Serializer()

    self.assertEqual(s.uvarint(127), 1)
    self.assertEqual(s.uvarint(128), 2)
    self.assertEqual(s.uvarint(16383), 2)
    self.assertEqual(s.uvarint(16384), 3)
    self.assertEqual(s.uvarint(2097151), 3)
    self.assertEqual(s.uvarint(2097152), 4)
    self.assertEqual(s._pos, 15)

    self.assertEqual(s._data[0:1], bytearray.fromhex('7f'))
    self.assertEqual(s._data[1:3], bytearray.fromhex('8001'))
    self.assertEqual(s._data[3:5], bytearray.fromhex('ff7f'))
    self.assertEqual(s._data[5:8], bytearray.fromhex('808001'))
    self.assertEqual(s._data[8:11], bytearray.fromhex('ffff7f'))
    self.assertEqual(s._data[11:15], bytearray.fromhex('80808001'))

  def test_svarint(self):
    s = Serializer()

    self.assertEqual(s.svarint(-65), 2)
    self.assertEqual(s.svarint(-64), 1)
    self.assertEqual(s.svarint(-1), 1)
    self.assertEqual(s.svarint(0), 1)
    self.assertEqual(s.svarint(1), 1)
    self.assertEqual(s.svarint(63), 1)
    self.assertEqual(s.svarint(64), 2)
    self.assertEqual(s._pos, 9)

    self.assertEqual(s._data[0:2], bytearray.fromhex('8101'))
    self.assertEqual(s._data[2:3], bytearray.fromhex('7f'))  
    self.assertEqual(s._data[3:4], bytearray.fromhex('01'))
    self.assertEqual(s._data[4:5], bytearray.fromhex('00'))
    self.assertEqual(s._data[5:6], bytearray.fromhex('02'))
    self.assertEqual(s._data[6:7], bytearray.fromhex('7e'))
    self.assertEqual(s._data[7:9], bytearray.fromhex('8001'))

  def test_boolean(self):
    s = Serializer()

    self.assertEqual(s.boolean(True), 1)
    self.assertEqual(s.boolean(False), 1)
    self.assertEqual(s._pos, 2)

    self.assertEqual(s._data[0:1], bytearray.fromhex('01'))
    self.assertEqual(s._data[1:2], bytearray.fromhex('00'))

  def test_raw_bytes(self):
    s = Serializer()

    self.assertEqual(s.raw_bytes(bytes(0)), 0)
    self.assertEqual(s.raw_bytes(bytes.fromhex("010203")), 3)
    self.assertEqual(s._pos, 3)
    
    self.assertEqual(s._data[0:3], bytes.fromhex("010203"))
    
  def test_raw_string(self):
    s = Serializer()

    self.assertEqual(s.raw_string(""), 0)
    self.assertEqual(s.raw_string("foobar"), 6)
    self.assertEqual(s._pos, 6)
    
    self.assertEqual(s._data[0:6], bytearray("foobar", "utf8"))

  def test_string(self):
    s = Serializer()
    
    long_string = "".join(["t" for i in range(0, 128)])
    long_bytearray = bytearray(bytes.fromhex("8001") + bytearray(long_string, "utf8"))
  
    self.assertEqual(s.string(""), 1)
    self.assertEqual(s.string("hello"), 6)
    self.assertEqual(s.string(long_string), 130)
    self.assertEqual(s._pos, 137)

    self.assertEqual(s._data[0:1], bytearray.fromhex("00"))
    self.assertEqual(s._data[1:7], bytearray("\x05hello", "utf8"))
    self.assertEqual(s._data[7:137], long_bytearray)

  def test_time_point_sec(self):
    s = Serializer()

    y2k38_struct = time.gmtime(2147483647)
    y2k38_aftermath_datetime = datetime.utcfromtimestamp(2147483648)

    self.assertEqual(s.time_point_sec(y2k38_struct), 4)
    self.assertEqual(s.time_point_sec(y2k38_aftermath_datetime), 4)
    self.assertEqual(s._pos, 8)
 
    self.assertEqual(s._data[0:4], bytearray.fromhex("ffffff7f"))
    self.assertEqual(s._data[4:8], bytearray.fromhex("00000080"))

  def test_array(self):
    s = Serializer()

    self.assertEqual(s.array([], 'int8'), 1)
    self.assertEqual(s.array([127, -128], 'int8'), 3)
    self.assertEqual(s._pos, 4)
   
    self.assertEqual(s._data[0:1], bytearray.fromhex("00"))
    self.assertEqual(s._data[1:4], bytearray.fromhex("027f80"))

  def test_map(self):
    s = Serializer()

    self.assertEqual(s.map({}, 'string', 'string'), 1)
    self.assertEqual(s.map({"foo":"bar", "baz":"quux"}, 'string', 'string'), 18)
    self.assertEqual(s._pos, 19)
   
    self.assertEqual(s._data[0:1], bytearray.fromhex("00"))
    self.assertEqual(s._data[1:2], bytearray.fromhex("02"))
    self.assertEqual(s._data[2:3], bytearray.fromhex("03"))
    self.assertEqual(s._data[3:6], bytearray("foo", "utf8"))
    self.assertEqual(s._data[6:7], bytearray.fromhex("03"))
    self.assertEqual(s._data[7:10], bytearray("bar", "utf8"))
    self.assertEqual(s._data[10:11], bytearray.fromhex("03"))
    self.assertEqual(s._data[11:14], bytearray("baz", "utf8"))
    self.assertEqual(s._data[14:15], bytearray.fromhex("04"))
    self.assertEqual(s._data[15:19], bytearray("quux", "utf8"))

  def test_optional(self):
    s = Serializer()

    self.assertEqual(s.optional(None, 'string'), 1)
    self.assertEqual(s.optional("foo", 'string'), 5)
    self.assertEqual(s._pos, 6)

    self.assertEqual(s._data[0:1], bytearray.fromhex("00"))  
    self.assertEqual(s._data[1:3], bytearray.fromhex("0103"))
    self.assertEqual(s._data[3:6], bytearray("foo", "utf8"))

  def test_field(self):
    s = Serializer()

    class Thing:
      def __init__(self):
        self.foo = 'bar'

    t = Thing()

    self.assertEqual(s.field(t, 'foo', 'string'), 4)
    self.assertEqual(s.field(t, 'nope', lambda s, v: s.optional(v, 'string')), 1)
    self.assertEqual(s._pos, 5)

    self.assertEqual(s._data[0:1], bytearray.fromhex("03"))
    self.assertEqual(s._data[1:4], bytearray("bar", "utf8"))
    self.assertEqual(s._data[4:5], bytearray.fromhex("00"))

  def test_fields(self):
    s = Serializer()

    class Thing:
      def __init__(self):
        self.foo = 'bar'
        self.baz = 9
        self.quux = True

    t = Thing()

    fields = (
      ("foo", "string"),
      ("baz", "uint8"),
      ("quux", lambda s, v: s.optional(v, "boolean"))
    )

    self.assertEqual(s.fields(t, fields), 7)
    self.assertEqual(s._pos, 7)

    self.assertEqual(s._data[0:1], bytearray.fromhex("03"))
    self.assertEqual(s._data[1:4], bytearray("bar", "utf8"))
    self.assertEqual(s._data[4:5], bytearray.fromhex("09"))
    self.assertEqual(s._data[5:7], bytearray.fromhex("0101"))

  def test_void(self):
    s = Serializer()

    self.assertEqual(s.void(None), 0)
    self.assertEqual(s._pos, 0)

    with self.assertRaises(AssertionError):
      s.void("hello")
    with self.assertRaises(AssertionError):
      s.void(0)

  def test_asset(self):
    s = Serializer()

    class Asset:
      symbol = "STEEM"
      def __init__(self):
        self.amount = 2**63-1
        self.precision = 5

    self.assertEqual(s.asset(Asset()), 16)
    self.assertEqual(s._pos, 16)

    self.assertEqual(s._data[0:9], bytearray.fromhex("ffffffffffffff7f05"))
    self.assertEqual(s._data[9:16], bytearray("STEEM\0\0", "ascii"))

    class BogoAsset(Asset):
      symbol = "TOO_LONG_SYMBOL"

    with self.assertRaises(AssertionError):
      s.asset(BogoAsset())
