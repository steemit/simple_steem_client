
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

  def test_uint8(self):
    s = Serializer()
    
    self.assertEqual(s.uint8(0x01), 1)
    self.assertEqual(s.uint8(0xff), 1)

    self.assertEqual(s._pos, 2)
    self.assertEqual(b(s._data[0:2]), hx('01ff'))
 
  def test_uint16(self):
    s = Serializer()

    self.assertEqual(s.uint16(0x0001), 2)
    self.assertEqual(s.uint16(0xfffe), 2)

    self.assertEqual(s._pos, 4)
    self.assertEqual(b(s._data[0:4]), hx('0100feff'))

  def test_uint32(self):
    s = Serializer()
    
    self.assertEqual(s.uint32(0x00000001), 4)
    self.assertEqual(s.uint32(0xfffffffe), 4)

    self.assertEqual(s._pos, 8)
    self.assertEqual(b(s._data[0:8]), hx('01000000feffffff'))

  def test_uint64(self):
    s = Serializer()

    self.assertEqual(s.uint64(0x0000000000000001), 8)
    self.assertEqual(s.uint64(0xfffffffffffffffe), 8)

    self.assertEqual(s._pos, 16)
    self.assertEqual(b(s._data[0:16]), hx('0100000000000000feffffffffffffff'))

  def test_int8(self):
    s = Serializer()
 
    self.assertEqual(s.int8(127), 1)   
    self.assertEqual(s.int8(-128), 1)

    self.assertEqual(s._pos, 2)
    self.assertEqual(b(s._data[0:2]), hx('7f80'))
 
  def test_int16(self):
    s = Serializer()

    self.assertEqual(s.int16(32767), 2)
    self.assertEqual(s.int16(-32768), 2)

    self.assertEqual(s._pos, 4)
    self.assertEqual(b(s._data[0:4]), hx('ff7f0080'))

  def test_int32(self):
    s = Serializer()
    
    self.assertEqual(s.int32(2147483647), 4)
    self.assertEqual(s.int32(-2147483648), 4)

    self.assertEqual(s._pos, 8)
    self.assertEqual(b(s._data[0:8]), hx('ffffff7f00000080'))

  def test_int64(self):
    s = Serializer()

    self.assertEqual(s.int64(9223372036854775807), 8)
    self.assertEqual(s.int64(-9223372036854775808), 8)

    self.assertEqual(s._pos, 16)
    self.assertEqual(b(s._data[0:16]), hx('ffffffffffffff7f0000000000000080'))

  def test_binary64(self):
    s = Serializer()

    self.assertEqual(s.binary64(math.inf), 8)
    self.assertEqual(s.binary64(-math.inf), 8)
    self.assertEqual(s.binary64(math.nan), 8)
    self.assertEqual(s.binary64(1.1945305291614955e+103), 8)
    self.assertEqual(s.binary64(3.141592653589793), 8)
    self.assertEqual(s.binary64(-1.8797162599773979e+230), 8)
    self.assertEqual(s._pos, 48)

    self.assertEqual(b(s._data[0:8]), hx('000000000000f07f'))
    self.assertEqual(b(s._data[8:16]), hx('000000000000f0ff'))
    self.assertEqual(b(s._data[16:24]), hx('000000000000f87f'))
    self.assertEqual(b(s._data[24:32]), hx('5555555555555555'))
    self.assertEqual(b(s._data[32:40]), hx('182d4454fb210940'))
    self.assertEqual(b(s._data[40:48]), hx('feedfacecafebeef'))

  def test_uvarint(self):
    s = Serializer()

    self.assertEqual(s.uvarint(127), 1)
    self.assertEqual(s.uvarint(128), 2)
    self.assertEqual(s.uvarint(16383), 2)
    self.assertEqual(s.uvarint(16384), 3)
    self.assertEqual(s.uvarint(2097151), 3)
    self.assertEqual(s.uvarint(2097152), 4)
    self.assertEqual(s._pos, 15)

    self.assertEqual(b(s._data[0:1]), hx('7f'))
    self.assertEqual(b(s._data[1:3]), hx('8001'))
    self.assertEqual(b(s._data[3:5]), hx('ff7f'))
    self.assertEqual(b(s._data[5:8]), hx('808001'))
    self.assertEqual(b(s._data[8:11]), hx('ffff7f'))
    self.assertEqual(b(s._data[11:15]), hx('80808001'))

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

    self.assertEqual(b(s._data[0:2]), hx('8101'))
    self.assertEqual(b(s._data[2:3]), hx('7f'))  
    self.assertEqual(b(s._data[3:4]), hx('01'))
    self.assertEqual(b(s._data[4:5]), hx('00'))
    self.assertEqual(b(s._data[5:6]), hx('02'))
    self.assertEqual(b(s._data[6:7]), hx('7e'))
    self.assertEqual(b(s._data[7:9]), hx('8001'))

  def test_boolean(self):
    s = Serializer()

    self.assertEqual(s.boolean(True), 1)
    self.assertEqual(s.boolean(False), 1)
    self.assertEqual(s._pos, 2)

    self.assertEqual(b(s._data[0:1]), hx('01'))
    self.assertEqual(b(s._data[1:2]), hx('00'))

  def test_raw_bytes(self):
    s = Serializer()

    self.assertEqual(s.raw_bytes(bytes(0)), 0)
    self.assertEqual(s.raw_bytes(bytes.fromhex("010203")), 3)
    self.assertEqual(s._pos, 3)
    
    self.assertEqual(b(s._data[0:3]), bytes.fromhex("010203"))
    
  def test_raw_string(self):
    s = Serializer()

    self.assertEqual(s.raw_string(""), 0)
    self.assertEqual(s.raw_string("foobar"), 6)
    self.assertEqual(s._pos, 6)
    
    self.assertEqual(b(s._data[0:6]), bytearray("foobar", "utf8"))

  def test_string(self):
    s = Serializer()
    
    long_string = "".join(["t" for i in range(0, 128)])
    long_bytearray = bytearray(bytes.fromhex("8001") + bytearray(long_string, "utf8"))
  
    self.assertEqual(s.string(""), 1)
    self.assertEqual(s.string("hello"), 6)
    self.assertEqual(s.string(long_string), 130)
    self.assertEqual(s._pos, 137)

    self.assertEqual(b(s._data[0:1]), hx("00"))
    self.assertEqual(b(s._data[1:7]), bytearray("\x05hello", "utf8"))
    self.assertEqual(b(s._data[7:137]), long_bytearray)

  def test_time_point_sec(self):
    s = Serializer()

    y2k38_struct = time.gmtime(2147483647)
    y2k38_aftermath_datetime = datetime.utcfromtimestamp(2147483648)

    self.assertEqual(s.time_point_sec(y2k38_struct), 4)
    self.assertEqual(s.time_point_sec(y2k38_aftermath_datetime), 4)
    self.assertEqual(s._pos, 8)
 
    self.assertEqual(b(s._data[0:4]), hx("ffffff7f"))
    self.assertEqual(b(s._data[4:8]), hx("00000080"))

  def test_array(self):
    s = Serializer()

    self.assertEqual(s.array([], 'int8'), 1)
    self.assertEqual(s.array([127, -128], 'int8'), 3)
    self.assertEqual(s._pos, 4)
   
    self.assertEqual(b(s._data[0:1]), hx("00"))
    self.assertEqual(b(s._data[1:4]), hx("027f80"))

  def test_map(self):
    s = Serializer()

    self.assertEqual(s.map({}, 'string', 'string'), 1)
    self.assertEqual(s.map({"foo":"bar", "baz":"quux"}, 'string', 'string'), 18)
    self.assertEqual(s._pos, 19)
   
    self.assertEqual(b(s._data[0:1]), hx("00"))
    self.assertEqual(b(s._data[1:2]), hx("02"))
    self.assertEqual(b(s._data[2:3]), hx("03"))
    self.assertEqual(b(s._data[3:6]), bytearray("foo", "utf8"))
    self.assertEqual(b(s._data[6:7]), hx("03"))
    self.assertEqual(b(s._data[7:10]), bytearray("bar", "utf8"))
    self.assertEqual(b(s._data[10:11]), hx("03"))
    self.assertEqual(b(s._data[11:14]), bytearray("baz", "utf8"))
    self.assertEqual(b(s._data[14:15]), hx("04"))
    self.assertEqual(b(s._data[15:19]), bytearray("quux", "utf8"))

  def test_optional(self):
    s = Serializer()

    self.assertEqual(s.optional(None, 'string'), 1)
    self.assertEqual(s.optional("foo", 'string'), 5)
    self.assertEqual(s._pos, 6)

    self.assertEqual(b(s._data[0:1]), hx("00"))  
    self.assertEqual(b(s._data[1:3]), hx("0103"))
    self.assertEqual(b(s._data[3:6]), bytearray("foo", "utf8"))

  def test_field(self):
    s = Serializer()

    class Thing:
      def __init__(self):
        self.foo = 'bar'

    t = Thing()

    self.assertEqual(s.field(t, 'foo', 'string'), 4)
    self.assertEqual(s.field(t, 'nope', lambda s, v: s.optional(v, 'string')), 1)
    self.assertEqual(s._pos, 5)

    self.assertEqual(b(s._data[0:1]), hx("03"))
    self.assertEqual(b(s._data[1:4]), bytearray("bar", "utf8"))
    self.assertEqual(b(s._data[4:5]), hx("00"))

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

    self.assertEqual(b(s._data[0:1]), hx("03"))
    self.assertEqual(b(s._data[1:4]), bytearray("bar", "utf8"))
    self.assertEqual(b(s._data[4:5]), hx("09"))
    self.assertEqual(b(s._data[5:7]), hx("0101"))

  def test_public_key(self):
    s = Serializer()

    self.assertEqual(s.public_key(PublicKey()), 64)
    self.assertEqual(s._pos, 64)
 
    self.assertEqual(b(s._data[0:64]), pk_bytes)

  def test_static_variant(self):
    s = Serializer()

    class Snake:
      animal_type = "reptile"
      slither_speed = 5
      slimy = False
    
    class Horse:
      animal_type = "mammal"
      gallop_speed = 9
      dappled = True

    class Frog:
      animal_type = "amphibian"
      hop_speed = 4
      slimy = True

    variants = (
      (
        "mammal",
        lambda s, v: s.fields(v, (
          ( "gallop_speed", "uint16" ),
          ( "dappled", "boolean")
        ))
      ),
      (
        "reptile",
        lambda s, v: s.fields(v, (
          ( "slither_speed", "uint8" ),
          ( "slimy", "boolean" )
        ))
      ),
      (
        "amphibian",
        lambda s, v: s.fields(v, (
          ( "hop_speed", "uint8" ),
          ( "slimy", "boolean" ) 
        ))
      ) 
    )

    self.assertEqual(s.static_variant(Frog(), "animal_type", variants), 3)
    self.assertEqual(s.static_variant(Snake(), "animal_type", variants), 3)
    self.assertEqual(s.static_variant(Horse(), "animal_type", variants), 4)
    self.assertEqual(s._pos, 10)

    self.assertEqual(b(s._data[0:3]), hx("020401"))
    self.assertEqual(b(s._data[3:6]), hx("010500"))
    self.assertEqual(b(s._data[6:10]), hx("00090001"))

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

    self.assertEqual(b(s._data[0:9]), hx("ffffffffffffff7f05"))
    self.assertEqual(b(s._data[9:16]), bytearray("STEEM\0\0", "ascii"))

    class BogoAsset(Asset):
      symbol = "TOO_LONG_SYMBOL"

    with self.assertRaises(AssertionError):
      s.asset(BogoAsset())

  def test_authority(self):
    s = Serializer()

    self.assertEqual(s.authority({
      "weight_threshold": 65535,
      "account_auths": [
        ("goldibex", 65535)
      ],
      "key_auths": [
        (PublicKey(), 32768)
      ]
    }), 83)

    self.assertEqual(b(s._data[0:4]), hx("ffff0000"))
    self.assertEqual(b(s._data[4:16]), hx("0108") + hs("goldibex") + hx("ffff"))
    self.assertEqual(b(s._data[16:83]), hx("01") + pk_bytes + hx("0080"))

  def test_beneficiary(self):
    s = Serializer()

    self.assertEqual(s.beneficiary({
      "account": "goldibex",
      "weight": 1        
    }), 11)

    self.assertEqual(b(s._data[0:11]), hx("08") + hs("goldibex") + hx("0100"))
  
  def test_price(self):
    s = Serializer()

    self.assertEqual(s.price({
      "base": {
        "amount": 10,
        "precision": 3,
        "symbol": "STEEM"
      },
      "quote": {
        "amount": 10,
        "precision": 3,
        "symbol": "VESTS"
      } 
    }), 32)

    self.assertEqual(b(s._data[0:16]), hx("0a0000000000000003") + hs("STEEM") + hx("0000"))
    self.assertEqual(b(s._data[16:32]), hx("0a0000000000000003") + hs("VESTS") + hx("0000"))

  def test_signed_block_header(self):
    s = Serializer()

    y2k38_struct = time.gmtime(2147483647)
    thirty_two_bytes = bytes.fromhex("000102030405060708090a0b0c0d0e0f000102030405060708090a0b0c0d0e0f")

    self.assertEqual(s.signed_block_header({
      "transaction_merkle_root": thirty_two_bytes,
      "extensions": [],
      "witness_signature": thirty_two_bytes,
      "previous": thirty_two_bytes,
      "timestamp": y2k38_struct,
      "witness": "goldibex"
    }), 1+4+9+96)

    self.assertEqual(b(s._data[0:32]), thirty_two_bytes)
    self.assertEqual(b(s._data[32:36]), hx("ffffff7f"))
    self.assertEqual(b(s._data[36:37]), hx("08"))
    self.assertEqual(b(s._data[37:45]), hs("goldibex"))
    self.assertEqual(b(s._data[45:77]), thirty_two_bytes)
    self.assertEqual(b(s._data[77:78]), hx("00"))
    self.assertEqual(b(s._data[78:110]), thirty_two_bytes)

  def test_chain_properties(self):
    s = Serializer()

    self.assertEqual(s.chain_properties({
      "account_creation_fee":{
        "amount": 10,
        "precision": 3,
        "symbol": "STEEM"
      },
      "maximum_block_size": 16777215,
      "sbd_interest_rate": 9
    }), 22)

    self.assertEqual(b(s._data[0:16]), hx("0a0000000000000003") + hs("STEEM") + hx("0000"))
    self.assertEqual(b(s._data[16:22]), hx("ffffff000900"))

  def test_operation(self):
    s = Serializer()

    self.assertEqual(s.operation({
      "type": "account_witness_vote",
      "account": "goldibex",
      "witness": "ned",
      "approve": False
    }), 15)

    self.assertEqual(s.flush(), hx("0c08") + hs("goldibex") + hx("03") + hs("ned") + hx("00"))

  def test_transaction(self):
    s = Serializer()

    y2k38_struct = time.gmtime(2147483647)

    self.assertEqual(s.transaction({
      "operations": [{
        "type": "account_witness_vote",
        "account": "goldibex",
        "witness": "ned",
        "approve": False
      }],
      "ref_block_num": 65535,
      "ref_block_prefix": 65535,
      "expiration": y2k38_struct,
      "extensions": []
    }), 27)

    self.assertEqual(b(s._data[0:2]), hx("ffff"))
    self.assertEqual(b(s._data[2:6]), hx("ffff0000"))
    self.assertEqual(b(s._data[6:10]), hx("ffffff7f"))
    self.assertEqual(b(s._data[10:11]), hx("01"))
    self.assertEqual(b(s._data[11:26]), hx("0c08") + hs("goldibex") + hx("03") + hs("ned") + hx("00"))
    self.assertEqual(b(s._data[26:27]), hx("00"))

  def test_extensions(self):
    s = Serializer()

    ext_variants = (
      ("users", lambda s2, v: s2.array(v, "string")),
      ("extended", "boolean")
    )

    self.assertEqual(s.extensions([{
      "extension": "extended",
      "extended": True
    }, {
      "extension": "users",
      "users": [
        "goldibex",
        "ned"
      ]
    }], ext_variants), 18)

    self.assertEqual(s.flush(), hx("020101000208") + hs("goldibex") + hx("03") + hs("ned"))

  def test_comment_options_operation(self):
    # we test this one specifically because it actually has extensions
    s = Serializer()

    self.assertEqual(s.operation({
      "type": "comment_options",
      "author": "goldibex",
      "permlink": "https://example.com",
      "max_accepted_payout": {
        "amount": 10,
        "precision": 3,
        "symbol": "STEEM"
      },
      "percent_steem_dollars": 100,
      "allow_votes": True,
      "allow_curation_rewards": True,
      "extensions": [{
        "extension": "beneficiaries",
        "beneficiaries": [{
          "account": "goldibex",
          "weight": 2
        }, {
          "account": "ned",
          "weight": 1
        }]
      }]
    }), 72)
    
    data = s.flush()
    
    self.assertEqual(data[0:2], hx("1208"))
    self.assertEqual(data[2:10], hs("goldibex"))
    self.assertEqual(data[10:11], hx("13"))
    self.assertEqual(data[11:30], hs("https://example.com"))
    self.assertEqual(data[30:46], hx("0a0000000000000003") + hs("STEEM") + hx("0000"))
    self.assertEqual(data[46:50], hx("64000000"))
    self.assertEqual(data[50:51], hx("01"))
    self.assertEqual(data[51:52], hx("01"))
    self.assertEqual(data[52:72], hx("01000208") + hs("goldibex") + hx("0200") + hx("03") + hs("ned") + hx("0100"))

