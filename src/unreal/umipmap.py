"""Mipmap class for texture asset with PS5 format support"""
from .archive import (ArchiveBase, Int32, Uint32, Uint16, Buffer,
                      SerializableBase)
from .data_resource import LegacyDataResource


class PS5DataResource:
    """Minimal data resource for PS5 mipmap format."""
    def __init__(self):
        self.bulk_type = None
        self.data_size = 0
        self.offset = 0
        self.has_wrong_offset = False
        self.has_64bit_size = False

    def update(self, data_size, has_uexp_bulk):
        self.data_size = data_size
        self.offset = 0

    def has_uexp_bulk(self):
        return False

    def has_no_bulk(self):
        return False

    def has_ubulk_bulk(self):
        return True

    def has_uptnl_bulk(self):
        return False

    def get_type_str(self):
        return "UBULK"

    def rewrite_offset(self, ar, new_offset):
        self.offset = new_offset


class Umipmap(SerializableBase):
    """A mipmap (FTexture2DMipMap) with PS5 format support."""

    def __init__(self):
        self.depth = 1
        self.data_resource = None
        self._ps5_data_offset = 0
        self._ps5_fields = {}

    def init_data_resource(self, uasset):
        self.data_resource = PS5DataResource()

    def update(self, data, size, depth, has_uexp_bulk):
        self.data = data
        self.width = size[0]
        self.height = size[1]
        self.depth = depth
        self.pixel_num = self.width * self.height * self.depth
        self.data_resource.update(len(data), has_uexp_bulk)

    def serialize(self, ar: ArchiveBase):
        is_ps5 = len(ar.args) > 2 and ar.args[2]
        if ar.is_reading:
            if is_ps5:
                self._serialize_read(ar)
            else:
                self._serialize_read_standard(ar)
        else:
            if is_ps5:
                self._serialize_write(ar)
            else:
                self._serialize_write_standard(ar)

    def _serialize_read(self, ar: ArchiveBase):
        mip_type = Uint32.read(ar)

        if mip_type == 2:
            self._ps5_fields['type'] = 2
            self._ps5_fields['f1'] = Uint32.read(ar)
            self._ps5_fields['f2'] = Uint32.read(ar)
            self._ps5_fields['tag'] = Uint32.read(ar)
            self._ps5_fields['data_size'] = Uint32.read(ar)
            self._ps5_fields['data_size2'] = Uint32.read(ar)
            self._ps5_fields['f6'] = Uint32.read(ar)
            self._ps5_fields['f7'] = Uint32.read(ar)
            self.width = Uint32.read(ar)
            self.height = Uint32.read(ar)
            self.depth = 1
            self.pixel_num = self.width * self.height * self.depth

            self.data_resource = PS5DataResource()
            self.data_resource.data_size = self._ps5_fields['data_size']
            self.data_resource.offset = 0
            self._ps5_data_offset = 0
            self.has_data = True

        elif mip_type == 1:
            self._ps5_fields['type'] = 1
            self._ps5_fields['f1'] = Uint32.read(ar)
            self._ps5_fields['tag'] = Uint32.read(ar)
            self._ps5_fields['data_size'] = Uint32.read(ar)
            self._ps5_fields['data_size2'] = Uint32.read(ar)
            self._ps5_fields['offset_or_flag'] = Uint32.read(ar)
            self._ps5_fields['f6'] = Uint32.read(ar)
            self.width = Uint32.read(ar)
            self.height = Uint32.read(ar)
            self.depth = 1
            self.pixel_num = self.width * self.height * self.depth

            self.data_resource = PS5DataResource()
            self.data_resource.data_size = self._ps5_fields['data_size']
            self._ps5_data_offset = self._ps5_fields['offset_or_flag']
            self.has_data = self.width > 0 and self.height > 0
            if not self.has_data:
                self.data = b""

        else:
            # Empty/dummy mip (type=0 or unknown): 36 bytes total
            self._ps5_fields['type'] = 0
            for i in range(8):
                self._ps5_fields[f'pad{i}'] = Uint32.read(ar)
            self.width = 0
            self.height = 0
            self.depth = 1
            self.pixel_num = 0
            self.has_data = False
            self.data = b""
            self.data_resource = PS5DataResource()
            self.data_resource.data_size = 0

    def _serialize_write(self, ar: ArchiveBase):
        ps5 = self._ps5_fields

        if ps5.get('type') == 2:
            Uint32.write(ar, 2)
            Uint32.write(ar, ps5.get('f1', 11))
            Uint32.write(ar, ps5.get('f2', 1))
            Uint32.write(ar, ps5.get('tag', 0x10501))
            Uint32.write(ar, self.data_resource.data_size if self.data_resource else ps5.get('data_size', 0))
            Uint32.write(ar, self.data_resource.data_size if self.data_resource else ps5.get('data_size2', 0))
            Uint32.write(ar, ps5.get('f6', 0))
            Uint32.write(ar, ps5.get('f7', 0))
            Uint32.write(ar, self.width)
            Uint32.write(ar, self.height)
        elif ps5.get('type') == 1:
            Uint32.write(ar, 1)
            Uint32.write(ar, ps5.get('f1', 1))
            Uint32.write(ar, ps5.get('tag', 0x10501))
            Uint32.write(ar, self.data_resource.data_size if self.data_resource else ps5.get('data_size', 0))
            Uint32.write(ar, self.data_resource.data_size if self.data_resource else ps5.get('data_size2', 0))
            Uint32.write(ar, ps5.get('offset_or_flag', 0))
            Uint32.write(ar, ps5.get('f6', 0))
            Uint32.write(ar, self.width)
            Uint32.write(ar, self.height)
        else:
            # type 0: 36 bytes total
            Uint32.write(ar, 0)
            for _ in range(8):
                Uint32.write(ar, 0)

    def _serialize_read_standard(self, ar: ArchiveBase):
        """Standard UE format (LegacyDataResource)."""
        offset = ar.args[0]
        data_resources = ar.args[1]

        if ar.version <= "4.27":
            bCooked = Uint32.read(ar)
            if bCooked != 1:
                print(f"offset: {ar.tell() - 4}")
                print(f"expected: 1")
                print(f"actual: {bCooked}")
                ar.raise_error("Unexpected value for bCooked.")

        if ar.version <= "5.1":
            self.data_resource = LegacyDataResource()
            ar << (LegacyDataResource, self, "data_resource", offset)
        else:
            if ar.is_writing:
                self.data_resource_id = len(data_resources)
                data_resources.append(self.data_resource)
            ar << (Int32, self, "data_resource_id")
            if ar.is_reading:
                self.data_resource = data_resources[self.data_resource_id]

        if self.has_uexp_bulk():
            ar << (Buffer, self, "data", self.data_resource.data_size)

        int_type = Uint16 if ar.version == "borderlands3" else Uint32
        ar << (int_type, self, "width")
        ar << (int_type, self, "height")
        if ar.version >= "4.20":
            ar << (int_type, self, "depth")
        self.pixel_num = self.width * self.height * self.depth
        self.has_data = True

    def _serialize_write_standard(self, ar: ArchiveBase):
        offset = ar.args[0]
        data_resources = ar.args[1]

        if ar.version <= "4.27":
            Uint32.write(ar, 1)  # bCooked

        if ar.version <= "5.1":
            ar << (LegacyDataResource, self, "data_resource", offset)
        else:
            if ar.is_writing:
                self.data_resource_id = len(data_resources)
                data_resources.append(self.data_resource)
            ar << (Int32, self, "data_resource_id")

        if self.has_uexp_bulk():
            ar << (Buffer, self, "data", self.data_resource.data_size)

        int_type = Uint16 if ar.version == "borderlands3" else Uint32
        ar << (int_type, self, "width")
        ar << (int_type, self, "height")
        if ar.version >= "4.20":
            ar << (int_type, self, "depth")
        if not getattr(self, 'has_data', True):
            return
        if self.data_resource.data_size <= 0:
            return
        ubulk_ar << (Buffer, self, "data", self.data_resource.data_size)

    def rewrite_offset(self, ar, new_offset):
        pass

    def print(self, padding=2):
        pad = " " * padding
        if self.data_resource:
            print(pad + f"bulk type: {self.data_resource.get_type_str()}")
            print(pad + f"data size: {self.get_data_size()}")
        print(pad + f"width: {self.width}")
        print(pad + f"height: {self.height}")
        if self.depth > 1:
            print(pad + f"depth: {self.depth}")

    def has_uexp_bulk(self):
        if self.data_resource:
            return self.data_resource.has_uexp_bulk()
        return False

    def has_no_bulk(self):
        if self.data_resource:
            return self.data_resource.has_no_bulk()
        return False

    def has_ubulk_bulk(self):
        if self.data_resource:
            return self.data_resource.has_ubulk_bulk()
        return getattr(self, 'has_data', True) and self.data_resource and self.data_resource.data_size > 0

    def has_uptnl_bulk(self):
        if self.data_resource:
            return self.data_resource.has_uptnl_bulk()
        return False

    def has_wrong_offset(self):
        if self.data_resource:
            return self.data_resource.has_wrong_offset
        return False

    def get_data_size(self):
        if self.data_resource:
            return self.data_resource.data_size
        return 0

    def serialize_ubulk(self, ubulk_ar, uptnl_ar):
        if not getattr(self, 'has_data', True):
            return
        if self.data_resource is None or self.data_resource.data_size <= 0:
            return
        if self.has_uptnl_bulk():
            uptnl_ar << (Buffer, self, "data", self.data_resource.data_size)
        elif self.has_ubulk_bulk():
            ubulk_ar << (Buffer, self, "data", self.data_resource.data_size)

    def rewrite_offset(self, ar, new_offset):
        if self.data_resource:
            self.data_resource.rewrite_offset(ar, new_offset)
