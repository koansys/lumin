from decimal import Decimal

from pymongo.son_manipulator import SONManipulator

import colander

SENTINEL = {u'_type': u'colander.null'}

class ColanderNullTransformer(SONManipulator):
    """Added to the db at load time, this allows MongoDB to store and
    retrieve colander.null sentinals for unknown values.
    """
    def transform_incoming(self, son, collection):
        for (k, v) in son.items():
            if v is colander.null:
                son[k] = SENTINEL
                continue
            if isinstance(v, dict):
                self.recursive_in(v)
        return son

    def transform_outgoing(self, son, collection):
        for (k, v) in son.items():
            if isinstance(v, dict):
                if v !=SENTINEL:
                    self.recursive_out(v)
                elif v == SENTINEL:
                    son[k] = colander.null
        return son

    def recursive_in(self, subson):
        for (k, v) in subson.items():
            if v is colander.null:
                subson[k] = SENTINEL
                continue
            if isinstance(v, dict):
                for (key, value) in v.items():
                    if value is colander.null:
                        v[key] = SENTINEL
                    if isinstance(value, dict):
                        self.recursive_in(value)

    def recursive_out(self, subson):
        for (k, v) in subson.items():
            if isinstance(v, dict):
                if v == SENTINEL:
                    subson[k] = colander.null
                self.recursive_out(v)


class DecimalTransform(SONManipulator):
    def transform_incoming(self, son, collection):
        for (k, v) in son.items():
            if isinstance(v, Decimal):
                son[k] = {'_type' : 'decimal', 'value' : unicode(v)}
            elif isinstance(v, dict):
                son[k] = self.transform_incoming(v, collection)
        return son

    def transform_outgoing(self, son, collection):
        for (k, v) in son.items():
            if isinstance(v, dict):
                if "_type" in v and v["_type"] == "decimal":
                   son[k] = Decimal(v['value'])
                else:
                   son[k] = self.transform_outgoing(v, collection)
        return son
