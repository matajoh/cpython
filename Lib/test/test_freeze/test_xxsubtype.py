import unittest

try:
    import xxsubtype
except ImportError:
    xxsubtype = None

class xxsubtypelib(unittest.TestCase):

    @unittest.skipIf(xxsubtype is None, "requires xxsubtype module")
    def test_spamdict_setstate(self):
        import xxsubtype as spam
        a = spam.spamlist()

        freeze(a)

        with self.assertRaises(NotWritableError):
            a.setstate(17)

    @unittest.skipIf(xxsubtype is None, "requires xxsubtype module")
    def test_spamdict_setstate(self):
        import xxsubtype as spam
        a = spam.spamdict()

        freeze(a)

        with self.assertRaises(NotWritableError):
            a.setstate(17)
