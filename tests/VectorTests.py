#!/usr/bin/env python

from hydra import *
import unittest


class ThatStruct(Struct):

    data = uint16_t(0x55AA)
    indicator = uint8_t(0xFA)
    alignment = Pad()


class VectorTests(unittest.TestCase):
    def setUp(self):
        HydraSettings.push()
        HydraSettings.endian = LittleEndian

    def tearDown(self):
        HydraSettings.pop()

    def test_array_default_type(self):
        array = Array(3)

        self.assertEqual(array.format([0] * 3), b'\x00\x00\x00')
        self.assertEqual(array.format([1] * 5), b'\x01\x01\x01')
        self.assertEqual(array.format([2] * 2), b'\x02\x02\x00')
        self.assertEqual(array.format([1, 2, 3]), b'\x01\x02\x03')

        self.assertEqual(array.parse('\x00\x00\x00'), [0, 0, 0])

    def test_array_custom_type(self):
        array = Array(2, uint16_t)
        data = [0xDEAF, 0xCAFE]
        self.assertEqual(array.format(data), b'\xAF\xDE\xFE\xCA')
        self.assertEqual(array.format(data, {'endian': BigEndian}), b'\xDE\xAF\xCA\xFE')

        HydraSettings.endian = BigEndian
        array = Array(3, int16_t)
        data = [-2, 100, 200]
        self.assertEqual(array.format(data), b'\xFF\xFE\x00\x64\x00\xC8')

    def test_struct_array(self):
        array = Array(2, ThatStruct)
        data = [ThatStruct(indicator=0), ThatStruct()]
        self.assertEqual(array.format(data), b'\xAA\x55\x00\x00\xAA\x55\xFA\x00')


if __name__ == '__main__':
    unittest.main()