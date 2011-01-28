import unittest


class TestConlanderNullTransformer(unittest.TestCase):
    def _makeOne(self):
        from lumin.son import ColanderNullTransformer
        tformer = ColanderNullTransformer()
        return tformer

    def test_one_in(self):
        import colander
        from lumin.son import SENTINEL
        doc = {'test' : colander.null}
        tf = self._makeOne()
        result = tf.transform_incoming(doc, None)
        self.failUnlessEqual(result['test'], SENTINEL)
        self.failIfEqual(result['test'], colander.null)

    def test_two_in(self):
        import colander
        from lumin.son import SENTINEL
        doc = {'test' : { 'test' : colander.null}}
        tf = self._makeOne()
        result = tf.transform_incoming(doc, None)
        self.failUnlessEqual(result['test']['test'], SENTINEL)
        self.failIfEqual(result['test']['test'], colander.null)

    def test_three_in(self):
        import colander
        from lumin.son import SENTINEL
        doc = {'test' : {'test' : { 'test' : colander.null}}}
        tf = self._makeOne()
        result = tf.transform_incoming(doc, None)
        self.failUnlessEqual(result['test']['test']['test'], SENTINEL)
        self.failIfEqual(result['test']['test']['test'], colander.null)

    def test_many_in(self):
        import colander
        from lumin.son import SENTINEL
        doc = {'one' : {'foo' : { 'bar' : colander.null}},
               'two' : { 'foo' : colander.null},
               'three'  : { 'foo' : { 'bar' : { 'baz' : {'spam' : colander.null}}}},
               'four' : {'foo' : colander.null},
               'five' : colander.null}
        tf = self._makeOne()
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
        doc = {'test' : SENTINEL}
        tf = self._makeOne()
        result = tf.transform_outgoing(doc, None)
        self.failUnlessEqual(result['test'],colander.null)
        self.failIfEqual(result['test'], SENTINEL)

    def test_two_out(self):
        import colander
        from lumin.son import SENTINEL
        doc = {'test' : {'test' : SENTINEL}}
        tf = self._makeOne()
        result = tf.transform_outgoing(doc, None)
        self.failUnlessEqual(result['test']['test'],colander.null)
        self.failIfEqual(result['test']['test'], SENTINEL)

    def test_three_out(self):
        import colander
        from lumin.son import SENTINEL
        doc = {'test' : {'test' : {'test' : SENTINEL}}}
        tf = self._makeOne()
        result = tf.transform_outgoing(doc, None)
        self.failUnlessEqual(result['test']['test']['test'],colander.null)
        self.failIfEqual(result['test']['test']['test'], SENTINEL)

    def test_many_out(self):
        import colander
        from lumin.son import SENTINEL
        doc = {'five' : {u'_type': u'colander.null'},
               'four': {'foo': {u'_type': u'colander.null'}},
               'three': {'foo': {'bar': {'baz': {'spam': {u'_type': u'colander.null'}}}}},
               'two': {'foo': {u'_type': u'colander.null'}},
               'one': {'foo': {'bar': {u'_type': u'colander.null'}}}}
        tf = self._makeOne()
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

