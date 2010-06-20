from pymongo.son_manipulator import SONManipulator

import colander

class ColanderNullTransformer(SONManipulator):
    """Added to the db at load time in (at the time of this writing)
    run:get_root
    This allows MongoDB to store and retrieve colander.null sentinals for
    unknown values.
    """
    def transform_incoming(self, son, collection):
        for (k, v) in son.items():
            if v is colander.null:
                son[k] = {'_type': 'colander.null'}
                continue
            if isinstance(v, dict):
                self.recursive_in(v)
        return son
    
    def transform_outgoing(self, son, collection):
        for (k, v) in son.items():
            if isinstance(v, dict):
                self.recursive_out(v)
        return son

    def recursive_in(self, subson):
        for (k, v) in subson.items():
            if v is colander.null:
                subson[k] = {'_type': 'colander.null'}
                continue
            if isinstance(v, dict):
                for (key, value) in v.items():
                    self.recursive_in(value)

    def recursive_out(self, subson):
        for (k, v) in subson.items():
            if isinstance(v, dict):
                if "_type" in v and v['_type'] == 'colander.null':
                    subson[k] = colander.null
                self.recursive_out(v)
