from __future__ import unicode_literals
import unittest


class TestConlanderNullTransformer(unittest.TestCase):
    def _make_one(self):
        from lumin.son import ColanderNullTransformer
        tformer = ColanderNullTransformer()
        return tformer

    def test_one_in(self):
        import colander
        from lumin.son import SENTINEL
        doc = {'test': colander.null}
        tf = self._make_one()
        result = tf.transform_incoming(doc, None)
        self.failUnlessEqual(result['test'], SENTINEL)
        self.failIfEqual(result['test'], colander.null)

    def test_two_in(self):
        import colander
        from lumin.son import SENTINEL
        doc = {'test': {'test': colander.null}}
        tf = self._make_one()
        result = tf.transform_incoming(doc, None)
        self.failUnlessEqual(result['test']['test'], SENTINEL)
        self.failIfEqual(result['test']['test'], colander.null)

    def test_three_in(self):
        import colander
        from lumin.son import SENTINEL
        doc = {'test': {'test': {'test': colander.null}}}
        tf = self._make_one()
        result = tf.transform_incoming(doc, None)
        self.failUnlessEqual(result['test']['test']['test'], SENTINEL)
        self.failIfEqual(result['test']['test']['test'], colander.null)

    def test_many_in(self):
        import colander
        from lumin.son import SENTINEL
        doc = {'one': {'foo': {'bar': colander.null}},
               'two': {'foo': colander.null},
               'three': {'foo': {'bar': {'baz': {'spam': colander.null}}}},
               'four': {'foo': colander.null},
               'five': colander.null}
        tf = self._make_one()
        result = tf.transform_incoming(doc, None)
        self.failUnlessEqual(result['one']['foo']['bar'], SENTINEL)
        self.failUnlessEqual(result['two']['foo'], SENTINEL)
        self.failUnlessEqual(result['three']['foo']['bar']['baz']['spam'], SENTINEL)
        self.failUnlessEqual(result['four']['foo'], SENTINEL)
        self.failUnlessEqual(result['five'], SENTINEL)
        self.failIfEqual(result['one']['foo']['bar'], colander.null)
        self.failIfEqual(result['two']['foo'], colander.null)
        self.failIfEqual(result['three']['foo']['bar']['baz']['spam'], colander.null)
        self.failIfEqual(result['four']['foo'], colander.null)
        self.failIfEqual(result['five'], colander.null)

    def test_one_out(self):
        import colander
        from lumin.son import SENTINEL
        doc = {'test': SENTINEL}
        tf = self._make_one()
        result = tf.transform_outgoing(doc, None)
        self.failUnlessEqual(result['test'], colander.null)
        self.failIfEqual(result['test'], SENTINEL)

    def test_two_out(self):
        import colander
        from lumin.son import SENTINEL
        doc = {'test': {'test': SENTINEL}}
        tf = self._make_one()
        result = tf.transform_outgoing(doc, None)

        self.failUnlessEqual(result['test']['test'],    colander.null)
        self.failIfEqual(result['test']['test'], SENTINEL)

    def test_three_out(self):
        import colander
        from lumin.son import SENTINEL
        doc = {'test': {'test': {'test': SENTINEL}}}
        tf = self._make_one()
        result = tf.transform_outgoing(doc, None)

        self.failUnlessEqual(result['test']['test']['test'],    colander.null)
        self.failIfEqual(result['test']['test']['test'], SENTINEL)

    def test_many_out(self):
        import colander
        from lumin.son import SENTINEL
        doc = {'five': {'_type': 'colander.null'},
               'four': {'foo': {'_type': 'colander.null'}},
               'three': {'foo': {'bar': {'baz': {'spam': {'_type': 'colander.null'}}}}},
               'two': {'foo': {'_type': 'colander.null'}},
               'one': {'foo': {'bar': {'_type': 'colander.null'}}}}
        tf = self._make_one()
        result = tf.transform_outgoing(doc, None)
        self.failUnlessEqual(result['one']['foo']['bar'], colander.null)
        self.failUnlessEqual(result['two']['foo'], colander.null)
        self.failUnlessEqual(result['three']['foo']['bar']['baz']['spam'], colander.null)
        self.failUnlessEqual(result['four']['foo'], colander.null)
        self.failUnlessEqual(result['five'], colander.null)
        self.failIfEqual(result['one']['foo']['bar'], SENTINEL)
        self.failIfEqual(result['two']['foo'], SENTINEL)
        self.failIfEqual(result['three']['foo']['bar']['baz']['spam'], SENTINEL)
        self.failIfEqual(result['four']['foo'], SENTINEL)
        self.failIfEqual(result['five'], SENTINEL)


class TestDecimalTransformer(unittest.TestCase):
    def _make_one(self):
        from lumin.son import DecimalTransformer
        tformer = DecimalTransformer()
        return tformer

    def _make_decimal(self, val):
        from decimal import Decimal
        return Decimal(str(val))

    def test_one_in(self):
        d = self._make_decimal('10.234')
        doc = {'test': d}
        tf = self._make_one()
        result = tf.transform_incoming(doc, None)
        self.failUnlessEqual(result['test'],
            {"_type": "decimal", "value": '10.234'})
        self.failIfEqual(result['test'], d)

    def test_two_in(self):
        d = self._make_decimal('10.234')
        doc = {'test': {'test': d}}
        tf = self._make_one()
        result = tf.transform_incoming(doc, None)
        self.failUnlessEqual(result['test']['test'],
            {"_type": "decimal", "value": '10.234'})
        self.failIfEqual(result['test']['test'], d)

    def test_three_in(self):
        d = self._make_decimal('1.234')
        doc = {'test': {'test': {'test': d}}}
        tf = self._make_one()
        result = tf.transform_incoming(doc, None)
        self.failUnlessEqual(result['test']['test']['test'],
            {"_type": "decimal", "value": '1.234'})
        self.failIfEqual(result['test']['test']['test'], d)

    def test_threeplus_in(self):
        d = self._make_decimal('1.234')
        d2 = self._make_decimal('9.99')
        doc = {'test': {'test': {'test': d}}, 'foo': d2}
        tf = self._make_one()
        result = tf.transform_incoming(doc, None)
        self.failUnlessEqual(result['test']['test']['test'],
            {"_type": "decimal", "value": '1.234'})
        self.failUnlessEqual(result['foo'],
            {"_type": "decimal", "value": '9.99'})
        self.failIfEqual(result['test']['test']['test'], d)
        self.failIfEqual(result['foo'], d2)

    def test_five_in(self):
        d = self._make_decimal('1.234')
        doc = {'test': {'test': {'test': {'test': {'test': d}}}}}
        tf = self._make_one()
        result = tf.transform_incoming(doc, None)
        self.failUnlessEqual(
            result['test']['test']['test']['test']['test'],
                {"_type": "decimal", "value": '1.234'})
        self.failIfEqual(result['test']['test']['test'], d)

    def test_many_in(self):
        d1 = self._make_decimal('1.1')
        d2 = self._make_decimal('2.2')
        d3 = self._make_decimal('3.3')
        d4 = self._make_decimal('4.4')
        d5 = self._make_decimal('5.5')
        doc = {'one': {'foo': {'bar': d1}},
               'two': {'foo': d2},
               'three': {'foo': {'bar': {'baz': {'spam': d3}}}},
               'four': {'foo': d4},
               'five': d5}
        tf = self._make_one()
        result = tf.transform_incoming(doc, None)
        self.failUnlessEqual(result['one']['foo']['bar'],
            {"_type": "decimal", "value": "1.1"})
        self.failUnlessEqual(result['two']['foo'],
            {"_type": "decimal", "value": "2.2"})
        self.failUnlessEqual(result['three']['foo']['bar']['baz']['spam'],
            {"_type": "decimal", "value": "3.3"})
        self.failUnlessEqual(result['four']['foo'],
            {"_type": "decimal", "value": "4.4"})
        self.failUnlessEqual(result['five'],
            {"_type": "decimal", "value": "5.5"})
        self.failIfEqual(result['one']['foo']['bar'], d1)
        self.failIfEqual(result['two']['foo'], d2)
        self.failIfEqual(result['three']['foo']['bar']['baz']['spam'],
            d3)
        self.failIfEqual(result['four']['foo'], d4)
        self.failIfEqual(result['five'], d5)

    def test_one_out(self):
        doc = {'test': {"_type": "decimal", "value": "1.1"}}
        tf = self._make_one()
        result = tf.transform_outgoing(doc, None)
        self.failUnlessEqual(result['test'], self._make_decimal('1.1'))

    def test_two_out(self):
        doc = {'test': {'test': {"_type": "decimal", "value": "1.1"}}}
        tf = self._make_one()
        result = tf.transform_outgoing(doc, None)

        self.failUnlessEqual(result['test']['test'],
            self._make_decimal('1.1'))
        self.failIfEqual(result['test']['test'],
            {"_type": "decimal", "value": "1.1"})

    def test_three_out(self):
        doc = {'test': {'test': {'test': {
            "_type": "decimal", "value": "1.1"}}}}
        tf = self._make_one()
        result = tf.transform_outgoing(doc, None)

        self.failUnlessEqual(result['test']['test']['test'],
            self._make_decimal('1.1'))
        self.failIfEqual(result['test']['test']['test'],
            {"_type": "decimal", "value": "1.1"})

    def test_many_out(self):
        doc = {
            'five': {'_type': 'decimal', 'value': '5.5'},
            'four': {'foo': {'_type': 'decimal', 'value': '4.4'}},
            'one': {'foo': {'bar': {
                                '_type': 'decimal', 'value': '1.1'}}},
            'three': {'foo': {'bar': {'baz': {
                            'spam': {'_type': 'decimal', 'value': '3.3'}
                            }}}},
            'two': {'foo': {'_type': 'decimal', 'value': '2.2'}}}
        tf = self._make_one()
        result = tf.transform_outgoing(doc, None)
        self.failUnlessEqual(result['one']['foo']['bar'],
            self._make_decimal('1.1'))
        self.failUnlessEqual(result['two']['foo'],
            self._make_decimal('2.2'))
        self.failUnlessEqual(
            result['three']['foo']['bar']['baz']['spam'],
            self._make_decimal('3.3'))
        self.failUnlessEqual(result['four']['foo'],
            self._make_decimal('4.4'))
        self.failUnlessEqual(result['five'], self._make_decimal('5.5'))


class TestDeNull(unittest.TestCase):

    def test_denull(self):
        import colander
        from lumin.son import denull
        doc = {'one': {'foo': {'bar': colander.null}},
               'two': {'foo': colander.null},
               'three': {'foo': {'bar': {'baz': {'spam': colander.null}}}},
               'four': {'foo': colander.null},
               'five': colander.null}
        result = denull(doc)
        self.failUnlessEqual(result,
            {'five': '',
               'four': {'foo': ''},
               'three': {'foo': {'bar': {'baz': {'spam': ''}}}},
               'two': {'foo': ''},
               'one': {'foo': {'bar': ''}}})


class TestDeSentinel(unittest.TestCase):

    def test_desentinel(self):
        from lumin.son import SENTINEL
        from lumin.son import desentinel
        doc = {'five': SENTINEL,
               'four': {'foo': SENTINEL},
               'three': {'foo': {'bar': {'baz': {'spam': SENTINEL}}}},
               'two': {'foo': SENTINEL},
               'one': {'foo': {'bar': SENTINEL}}}
        result = desentinel(doc)
        self.failUnlessEqual(result,
            {'five': '',
               'four': {'foo': ''},
               'three': {'foo': {'bar': {'baz': {'spam': ''}}}},
               'two': {'foo': ''},
               'one': {'foo': {'bar': ''}}}
            )
