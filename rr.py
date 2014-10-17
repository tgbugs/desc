# thinking space for request/response pairing

class Request:
    def __init__(self, type_uuid_list, property_id_xyzt, current_rel_id):
        self.type_uuid_list = type_uuid_list
        self.prop_x, self.prop_y, self.prop_z, self.prop_t = property_id_xyzt  #FIXME
        self.current_rel_id = current_rel_id


class Response:
    def __new__(cls, bam, collision, ui_data):
        positions, uuids, bounds = collision
        data_tuple = (bam, (positions, uuids, bounds) , ui_data)
        return data_tuple


