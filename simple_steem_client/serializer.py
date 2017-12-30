import math
import time
import datetime
import calendar
import types

NIF_FLOAT_64 = 0xfff0000000000000
INF_FLOAT_64 = 0x7ff0000000000000
NAN_FLOAT_64 = 0x7ff8000000000000

UINT8_MAX    = 0xFF
UINT16_MAX   = 0xFFFF
UINT32_MAX   = 0xFFFFFFFF
UINT64_MAX   = 0xFFFFFFFFFFFFFFFF

BINARY64_RANGE = 2**53

def twos(v, width):
  assert(width in (1,2,4,8))
  if v >= 0:
    return v

  abs_v = abs(v)
  if width == 1:
    return UINT8_MAX-abs_v+1
  elif width == 2:
    return UINT16_MAX-abs_v+1
  elif width == 4:
    return UINT32_MAX-abs_v+1
  elif width == 8:
    return UINT64_MAX-abs_v+1

class Serializer:
  def __init__(self, size=65536):
    self._data = bytearray(size)
    self._pos = 0

  def _get_serializer_fn(self, name_or_lambda):
    if type(name_or_lambda) is types.FunctionType:
      return lambda v: name_or_lambda(self, v)
    else:
      return getattr(self, name_or_lambda)

  def _write_byte(self, value):
    self._data[self._pos] = value
    self._pos += 1
    return 1

  def int8(self, value):
    return self.uint8(twos(value, 1))

  def int16(self, value):
    return self.uint16(twos(value, 2))

  def int32(self, value):
    return self.uint32(twos(value, 4))

  def int64(self, value):
    return self.uint64(twos(value, 8)) 

  def uint8(self, value):
    return self._write_byte(value)

  def uint16(self, value):
    return self.uint8(value & 0xff) + self.uint8((value >> 8) & 0xff) 

  def uint32(self, value):
    return self.uint16(value & 0xffff) + self.uint16((value >> 16) & 0xffff) 

  def uint64(self, value):
    return self.uint32(value & 0xffffffff) + self.uint32((value >> 32) & 0xffffffff)

  def binary64(self, value): 
    if math.isinf(value) and value < 0:
      encoded_value = NIF_FLOAT_64
    elif math.isinf(value):
      encoded_value = INF_FLOAT_64
    elif math.isnan(value):
      encoded_value = NAN_FLOAT_64
    else:
      # frontmost bit: sign, next 11 bits: exponent, next 52 bits: mantissa
      (mantissa_frac, exponent) = math.frexp(value)
      mantissa = int(abs(mantissa_frac) * BINARY64_RANGE)
      sign = 1 if value < 0 else 0
      # convert exponent offset to IEEE-754 standard
      exponent += 1022
      encoded_value = (sign << 63) | ((exponent & 0x7ff) << 52) | (mantissa & 0xfffffffffffff)
    return self.uint64(encoded_value)

  def uvarint(self, value):
    assert(value >= 0)
    count = 0
    while value > 127:
      self._write_byte(0x80 | (value & 0x7f))
      value = value >> 7
      count += 1 
    self._write_byte(value & 0x7f)
    return count + 1

  def svarint(self, value):
    return self.uvarint((value << 1) ^ (value >> 63))

  def boolean(self, value):
    assert(value in (True, False))
    encoded_value = 1 if value is True else 0
    return self.uint8(encoded_value)

  def raw_bytes(self, value):
    l = len(value)
    self._data[self._pos:self._pos+l] = value
    self._pos += l
    return l

  def raw_string(self, value):    
    return self.raw_bytes(bytes(value, "utf8"))

  def string(self, value):
    return self.uvarint(len(value)) + self.raw_string(value)

  def time_point_sec(self, value):
    if type(value) is time.struct_time:
      return self.uint32(calendar.timegm(value))
    elif type(value) is datetime.datetime:
      return self.time_point_sec(value.timetuple())
    else:
      raise ArgumentError("Cannot serialize to time_point_sec")

  def array(self, value, itemtype):
    bytes_written = self.uvarint(len(value))
    item_serializer = self._get_serializer_fn(itemtype)
    for item in value:
      bytes_written += item_serializer(item)
    return bytes_written
     
  def map(self, value, keytype, valuetype):
    bytes_written = self.uvarint(len(value))
    key_serializer = self._get_serializer_fn(keytype)
    value_serializer = self._get_serializer_fn(valuetype)

    for k, v in value.items():
      bytes_written += key_serializer(k) + value_serializer(v)
    return bytes_written

  def optional(self, value, underlyingtype):
    underlying_serializer = self._get_serializer_fn(underlyingtype)
    if value is None:
      return self.uint8(0)
    else:
      return self.uint8(1) + underlying_serializer(value)

  def field(self, value, name, fieldtype):
    field_val = getattr(value, name, None)
    return self._get_serializer_fn(fieldtype)(field_val)

  def fields(self, value, pairs):
    return sum([ self.field(value, name, fieldtype) for (name, fieldtype) in pairs ])

  def public_key(self, value):
    pass

  def static_variant(self, value, typetuple):
    pass

  def void(self, value):
    assert(value is None)
    return 0

  def asset(self, value):
    symbol = getattr(value, "symbol")
    assert(len(symbol) < 8)
    encoded_symbol = bytearray(7)
    encoded_symbol[0:len(symbol)] = symbol.encode("utf8")

    return self.fields(value, (
      ( "amount", "int64" ),
      ( "precision", "int8" ),
    )) + self.raw_bytes(encoded_symbol)

  def authority(self, value):
    return self.fields(value, (
      ( "weight_threshold", "uint32" ),
      ( "account_auths", lambda s, v: s.map(v, "string", "uint16") ),
      ( "key_auths", lambda s, v: s.map(v, "public_key", "uint16") )
    ))

  def beneficiary(self, value):
    return self.fields(value, (
      ( "account", "string" ),
      ( "weight", "uint16" )
    ))

  def price(self, value):
    return self.fields(value, (
      ( "base", "asset" ),
      ( "quote", "asset" )
    ))

  def signed_block_header(self, value):
    return self.fields(value, (
      ( "previous", "raw_bytes" ),
      ( "timestamp", "time_point_sec" ),
      ( "witness", "string" ),
      ( "transaction_merkle_root", "raw_bytes" ),
      ( "extensions", lambda s, v: s.array(v, "void") ),
      ( "witness_signature", "raw_bytes" )
    ))

  def chain_properties(self, value):
    return self.fields(value, (
      ( "account_creation_fee", "asset" ),
      ( "maximum_block_size", "uint32" ),
      ( "sbd_interest_rate", "uint16" )
    ))

  def operation(self, value):
    raise NotImplementedError()

  def transaction(self, value):
    return self.fields(value, (
      ( "ref_block_num", "uint16" ),
      ( "ref_block_prefix", "uint32" ),
      ( "expiration", "time_point_sec" ),
      ( "operations", lambda s, v: s.array(v, "operation") ),
      ( "extensions", lambda s, v: s.array(v, "string") )
    ))
