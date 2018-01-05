
import math, unittest
import time
from datetime import datetime
from simple_steem_client.serializer import twos, Serializer

def hs(s):
  return bytes(s, "utf8")

def hx(x):
  return bytes.fromhex(x)

def b(x):
  return bytes(x)

# PublicKey fixture for testing
pk_bytes = bytes.fromhex(
  "3AF1E1EFA4D1E1AD5CB9E3967E98E901DAFCD37C44CF0BFB6C216997F5EE51DF" + 
  "E4ACAC3E6F139E0C7DB2BD736824F51392BDA176965A1C59EB9C3C5FF9E85D7A"
)

class PublicKey:
  def format(self, compressed=False):
    return bytes.fromhex("80") + bytes(pk_bytes) 

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

  def setUp(self):
    self.s = Serializer()    

  def test_uint8(self):   
    self.assertEqual(self.s.uint8(0x01), 1)
    self.assertEqual(self.s.uint8(0xff), 1)
    self.assertEqual(self.s.flush(), hx('01ff'))
 
  def test_uint16(self):
    self.assertEqual(self.s.uint16(0x0001), 2)
    self.assertEqual(self.s.uint16(0xfffe), 2)
    self.assertEqual(self.s.flush(), hx('0100feff'))

  def test_uint32(self):
    self.assertEqual(self.s.uint32(0x00000001), 4)
    self.assertEqual(self.s.uint32(0xfffffffe), 4)
    self.assertEqual(self.s.flush(), hx('01000000feffffff'))

  def test_uint64(self):
    self.assertEqual(self.s.uint64(0x0000000000000001), 8)
    self.assertEqual(self.s.uint64(0xfffffffffffffffe), 8)
    self.assertEqual(self.s.flush(), hx('0100000000000000feffffffffffffff'))

  def test_int8(self):
    self.assertEqual(self.s.int8(127), 1)   
    self.assertEqual(self.s.int8(-128), 1)
    self.assertEqual(self.s.flush(), hx('7f80'))
 
  def test_int16(self):
    self.assertEqual(self.s.int16(32767), 2)
    self.assertEqual(self.s.int16(-32768), 2)
    self.assertEqual(self.s.flush(), hx('ff7f0080'))

  def test_int32(self):
    self.assertEqual(self.s.int32(2147483647), 4)
    self.assertEqual(self.s.int32(-2147483648), 4)
    self.assertEqual(self.s.flush(), hx('ffffff7f00000080'))

  def test_int64(self):
    self.assertEqual(self.s.int64(9223372036854775807), 8)
    self.assertEqual(self.s.int64(-9223372036854775808), 8)
    self.assertEqual(self.s.flush(), hx('ffffffffffffff7f0000000000000080'))

  def test_binary64(self):
    self.assertEqual(self.s.binary64(math.inf), 8)
    self.assertEqual(self.s.binary64(-math.inf), 8)
    self.assertEqual(self.s.binary64(math.nan), 8)
    self.assertEqual(self.s.binary64(1.1945305291614955e+103), 8)
    self.assertEqual(self.s.binary64(3.141592653589793), 8)
    self.assertEqual(self.s.binary64(-1.8797162599773979e+230), 8)

    data = self.s.flush()

    self.assertEqual(len(data), 48)
    self.assertEqual(data[0:8], hx('000000000000f07f'))
    self.assertEqual(data[8:16], hx('000000000000f0ff'))
    self.assertEqual(data[16:24], hx('000000000000f87f'))
    self.assertEqual(data[24:32], hx('5555555555555555'))
    self.assertEqual(data[32:40], hx('182d4454fb210940'))
    self.assertEqual(data[40:48], hx('feedfacecafebeef'))

  def test_uvarint(self):
    self.assertEqual(self.s.uvarint(127), 1)
    self.assertEqual(self.s.uvarint(128), 2)
    self.assertEqual(self.s.uvarint(16383), 2)
    self.assertEqual(self.s.uvarint(16384), 3)
    self.assertEqual(self.s.uvarint(2097151), 3)
    self.assertEqual(self.s.uvarint(2097152), 4)

    data = self.s.flush()

    self.assertEqual(len(data), 15)
    self.assertEqual(data[0:1], hx('7f'))
    self.assertEqual(data[1:3], hx('8001'))
    self.assertEqual(data[3:5], hx('ff7f'))
    self.assertEqual(data[5:8], hx('808001'))
    self.assertEqual(data[8:11], hx('ffff7f'))
    self.assertEqual(data[11:15], hx('80808001'))

  def test_svarint(self):
    self.assertEqual(self.s.svarint(-65), 2)
    self.assertEqual(self.s.svarint(-64), 1)
    self.assertEqual(self.s.svarint(-1), 1)
    self.assertEqual(self.s.svarint(0), 1)
    self.assertEqual(self.s.svarint(1), 1)
    self.assertEqual(self.s.svarint(63), 1)
    self.assertEqual(self.s.svarint(64), 2)

    data = self.s.flush()

    self.assertEqual(len(data), 9)
    self.assertEqual(data[0:2], hx('8101'))
    self.assertEqual(data[2:3], hx('7f'))  
    self.assertEqual(data[3:4], hx('01'))
    self.assertEqual(data[4:5], hx('00'))
    self.assertEqual(data[5:6], hx('02'))
    self.assertEqual(data[6:7], hx('7e'))
    self.assertEqual(data[7:9], hx('8001'))

  def test_boolean(self):
    self.assertEqual(self.s.boolean(True), 1)
    self.assertEqual(self.s.boolean(False), 1)
    self.assertEqual(self.s.flush(), hx('0100'))

  def test_raw_bytes(self):
    self.assertEqual(self.s.raw_bytes(bytes(0)), 0)
    self.assertEqual(self.s.raw_bytes(bytes.fromhex("010203")), 3)
    self.assertEqual(self.s.flush(), hx("010203"))
    
  def test_raw_string(self):
    self.assertEqual(self.s.raw_string(""), 0)
    self.assertEqual(self.s.raw_string("foobar"), 6)  
    self.assertEqual(self.s.flush(), hs("foobar"))

  def test_string(self):
    long_string = "".join(["t" for i in range(0, 128)])
    long_bytearray = bytearray(bytes.fromhex("8001") + bytearray(long_string, "utf8"))
  
    self.assertEqual(self.s.string(""), 1)
    self.assertEqual(self.s.string("hello"), 6)
    self.assertEqual(self.s.string(long_string), 130)

    data = self.s.flush()

    self.assertEqual(len(data), 137)
    self.assertEqual(data[0:1], hx("00"))
    self.assertEqual(data[1:7], bytearray("\x05hello", "utf8"))
    self.assertEqual(data[7:137], long_bytearray)

  def test_time_point_sec(self):
    y2k38_struct = time.gmtime(2147483647)
    y2k38_aftermath_datetime = datetime.utcfromtimestamp(2147483648)

    self.assertEqual(self.s.time_point_sec(y2k38_struct), 4)
    self.assertEqual(self.s.time_point_sec(y2k38_aftermath_datetime), 4)
    self.assertEqual(self.s.flush(), hx("ffffff7f00000080"))

  def test_array(self):
    self.assertEqual(self.s.array([], 'int8'), 1)
    self.assertEqual(self.s.array([127, -128], 'int8'), 3)
    self.assertEqual(self.s.flush(), hx("00027f80"))

  def test_map(self):
    self.assertEqual(self.s.map({}, 'string', 'string'), 1)
    self.assertEqual(self.s.map({"foo":"bar", "baz":"quux"}, 'string', 'string'), 18)

    data = self.s.flush()
 
    self.assertEqual(len(data), 19)  
    self.assertEqual(data[0:1], hx("00"))
    self.assertEqual(data[1:2], hx("02"))
    self.assertEqual(data[2:3], hx("03"))
    self.assertEqual(data[3:6], hs("foo"))
    self.assertEqual(data[6:7], hx("03"))
    self.assertEqual(data[7:10], hs("bar"))
    self.assertEqual(data[10:11], hx("03"))
    self.assertEqual(data[11:14], hs("baz"))
    self.assertEqual(data[14:15], hx("04"))
    self.assertEqual(data[15:19], hs("quux"))

  def test_optional(self):
    self.assertEqual(self.s.optional(None, 'string'), 1)
    self.assertEqual(self.s.optional("foo", 'string'), 5)
    self.assertEqual(self.s.flush(), hx("000103") + hs("foo"))

  def test_field(self):
    class Thing:
      def __init__(self):
        self.foo = 'bar'

    t = Thing()

    self.assertEqual(self.s.field(t, 'foo', 'string'), 4)
    self.assertEqual(self.s.field(t, 'nope', lambda s, v: self.s.optional(v, 'string')), 1)

    data = self.s.flush()
    self.assertEqual(len(data), 5)

    self.assertEqual(data[0:1], hx("03"))
    self.assertEqual(data[1:4], hs("bar"))
    self.assertEqual(data[4:5], hx("00"))

  def test_fields(self):
    class Thing:
      def __init__(self):
        self.foo = 'bar'
        self.baz = 9
        self.quux = True

    t = Thing()

    fields = (
      ("foo", "string"),
      ("baz", "uint8"),
      ("quux", lambda s, v: self.s.optional(v, "boolean"))
    )

    self.assertEqual(self.s.fields(t, fields), 7)

    data = self.s.flush()

    self.assertEqual(len(data), 7)
    self.assertEqual(data, hx("03") + hs("bar") + hx("090101"))

  def test_public_key(self):
    self.assertEqual(self.s.public_key(PublicKey()), 64)

    data = self.s.flush()

    self.assertEqual(len(data), 64)
    self.assertEqual(data, pk_bytes)

  def test_static_variant(self):
    snake = ["reptile", {"slither_speed" : 5, "slimy" : False}]
    horse = ["mammal", {"gallop_speed" : 9, "dappled" : True}]
    frog = ["amphibian", {"hop_speed" : 4, "slimy" : True}]

    variants = (
      (
        "mammal",
        lambda s, v: self.s.fields(v, (
          ( "gallop_speed", "uint16" ),
          ( "dappled", "boolean")
        ))
      ),
      (
        "reptile",
        lambda s, v: self.s.fields(v, (
          ( "slither_speed", "uint8" ),
          ( "slimy", "boolean" )
        ))
      ),
      (
        "amphibian",
        lambda s, v: self.s.fields(v, (
          ( "hop_speed", "uint8" ),
          ( "slimy", "boolean" )
        ))
      )
    )

    self.assertEqual(self.s.static_variant(frog, variants), 3)
    self.assertEqual(self.s.static_variant(snake, variants), 3)
    self.assertEqual(self.s.static_variant(horse, variants), 4)

    data = self.s.flush()

    self.assertEqual(len(data), 10)
    self.assertEqual(data[0:3], hx("020401"))
    self.assertEqual(data[3:6], hx("010500"))
    self.assertEqual(data[6:10], hx("00090001"))

  def test_void(self):
    self.assertEqual(self.s.void(None), 0)

    self.assertEqual(self.s.flush(), bytes([]))

    with self.assertRaises(AssertionError):
      self.s.void("hello")
    with self.assertRaises(AssertionError):
      self.s.void(0)

  def test_asset(self):
    print("TODO:  (Re-)implement test_asset()")

  def test_authority(self):
    self.assertEqual(self.s.authority({
      "weight_threshold": 65535,
      "account_auths": [
        ("goldibex", 65535)
      ],
      "key_auths": [
        (PublicKey(), 32768)
      ]
    }), 83)

    data = self.s.flush()

    self.assertEqual(len(data), 83)
    self.assertEqual(data[0:4], hx("ffff0000"))
    self.assertEqual(data[4:16], hx("0108") + hs("goldibex") + hx("ffff"))
    self.assertEqual(data[16:83], hx("01") + pk_bytes + hx("0080"))

  def test_beneficiary(self):
    self.assertEqual(self.s.beneficiary({
      "account": "goldibex",
      "weight": 1
    }), 11)

    self.assertEqual(self.s.flush(), hx("08") + hs("goldibex") + hx("0100"))

  def test_price(self):
    self.assertEqual(self.s.price(
      {"base": "0.010 STEEM", "quote" : "0.000010 VESTS"}
      ), 32)

    data = self.s.flush()

    self.assertEqual(len(data), 32)
    self.assertEqual(data[0:16], hx("0a0000000000000003") + hs("STEEM") + hx("0000"))
    self.assertEqual(data[16:32], hx("0a0000000000000006") + hs("VESTS") + hx("0000"))

  def test_signed_block_header(self):
    y2k38_struct = time.gmtime(2147483647)
    thirty_two_bytes = bytes.fromhex("000102030405060708090a0b0c0d0e0f000102030405060708090a0b0c0d0e0f")

    self.assertEqual(self.s.signed_block_header({
      "transaction_merkle_root": thirty_two_bytes,
      "extensions": [],
      "witness_signature": thirty_two_bytes,
      "previous": thirty_two_bytes,
      "timestamp": y2k38_struct,
      "witness": "goldibex"
    }), 110)

    data = self.s.flush()

    self.assertEqual(len(data), 110)
    self.assertEqual(data[0:32], thirty_two_bytes)
    self.assertEqual(data[32:36], hx("ffffff7f"))
    self.assertEqual(data[36:37], hx("08"))
    self.assertEqual(data[37:45], hs("goldibex"))
    self.assertEqual(data[45:77], thirty_two_bytes)
    self.assertEqual(data[77:78], hx("00"))
    self.assertEqual(data[78:110], thirty_two_bytes)

  def test_chain_properties(self):
    self.assertEqual(self.s.chain_properties({
      "account_creation_fee":"0.010 STEEM",
      "maximum_block_size": 16777215,
      "sbd_interest_rate": 9
    }), 22)

    data = self.s.flush()

    self.assertEqual(len(data), 22)
    self.assertEqual(data[0:16], hx("0a0000000000000003") + hs("STEEM") + hx("0000"))
    self.assertEqual(data[16:22], hx("ffffff000900"))

  def test_operation(self):
    self.assertEqual(self.s.operation([
      "account_witness_vote",
      {
        "account": "goldibex",
        "witness": "ned",
        "approve": False
      }]), 15)

    self.assertEqual(self.s.flush(), hx("0c08") + hs("goldibex") + hx("03") + hs("ned") + hx("00"))

  def test_transaction(self):
    y2k38_struct = time.gmtime(2147483647)

    self.assertEqual(self.s.transaction({
      "operations": [[
        "account_witness_vote",
        {
        "account": "goldibex",
        "witness": "ned",
        "approve": False
        }]],
      "ref_block_num": 65535,
      "ref_block_prefix": 65535,
      "expiration": y2k38_struct,
      "extensions": []
    }), 27)

    data = self.s.flush()

    self.assertEqual(data[0:2], hx("ffff"))
    self.assertEqual(data[2:6], hx("ffff0000"))
    self.assertEqual(data[6:10], hx("ffffff7f"))
    self.assertEqual(data[10:11], hx("01"))
    self.assertEqual(data[11:26], hx("0c08") + hs("goldibex") + hx("03") + hs("ned") + hx("00"))
    self.assertEqual(data[26:27], hx("00"))

  def test_extensions(self):
    ext_variants = (
      ("users", lambda s2, v: s2.array(v, "string")),
      ("extended", "boolean")
    )

    self.assertEqual(self.s.extensions(
      [["extended", True],
       ["users", ["goldibex", "ned"]]],
      ext_variants), 18)

    self.assertEqual(self.s.flush(), hx("020101000208") + hs("goldibex") + hx("03") + hs("ned"))

  def test_comment_options_operation(self):
    # we test this operation specifically because it has extensions
    self.assertEqual(self.s.operation([
      "comment_options", {
      "author": "goldibex",
      "permlink": "https://example.com",
      "max_accepted_payout": "0.010 STEEM",
      "percent_steem_dollars": 100,
      "allow_votes": True,
      "allow_curation_rewards": True,
      "extensions": [["beneficiaries",
        [{
          "account": "goldibex",
          "weight": 2
        }, {
          "account": "ned",
          "weight": 1
        }]]]
    }]), 72)

    data = self.s.flush()

    self.assertEqual(len(data), 72)
    self.assertEqual(data[0:2], hx("1208"))
    self.assertEqual(data[2:10], hs("goldibex"))
    self.assertEqual(data[10:11], hx("13"))
    self.assertEqual(data[11:30], hs("https://example.com"))
    self.assertEqual(data[30:46], hx("0a0000000000000003") + hs("STEEM") + hx("0000"))
    self.assertEqual(data[46:50], hx("64000000"))
    self.assertEqual(data[50:51], hx("01"))
    self.assertEqual(data[51:52], hx("01"))
    self.assertEqual(data[52:72], hx("01000208") + hs("goldibex") + hx("0200") + hx("03") + hs("ned") + hx("0100"))

