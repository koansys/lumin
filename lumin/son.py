from pymongo.son_manipulator import SONManipulator

import colander

SENTINEL = {u'_type': u'colander.null'}

class ColanderNullTransformer(SONManipulator):
    """Added to the db at load time in (at the time of this writing)
    run:get_root
    This allows MongoDB to store and retrieve colander.null sentinals for
    unknown values.
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
            if isinstance(v, dict) and v != SENTINEL:
                for (key, value) in v.items():
                    if isinstance(value, dict):
                        self.recursive_in(value)

    def recursive_out(self, subson):
        for (k, v) in subson.items():
            if isinstance(v, dict):
                if v == SENTINEL:
                    subson[k] = colander.null
                self.recursive_out(v)
