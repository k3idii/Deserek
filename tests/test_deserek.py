from deserek import do_unserialize, do_serialize  # adjust imports based on your code structure

def test_roundtrip():
    original = b'\xac\xed\x00\x05t\x00\x04test'  # example serialized string
    obj = do_unserialize(original)
    reserialized = do_serialize(obj)
    assert reserialized == original
