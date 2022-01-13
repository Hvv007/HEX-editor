import pytest
from src.PyHex import PyHex
from src.HexFile import HexFile
from src.Application import Application


@pytest.fixture
def empty_file():
    empty_file = HexFile('test_files/empty_file.txt', 16)
    empty_file.start()
    return empty_file


@pytest.fixture
def filled_file():
    file = HexFile('test_files/test_file.txt', 16)
    file.start()
    return file


def test_empty_file_length(empty_file):
    assert not empty_file.hex_array and not empty_file.content_array


def test_non_empty_file(filled_file):
    assert filled_file.content_array and filled_file.hex_array


def test_from_byte_to_ascii(empty_file):
    empty_file.hex_array = ['41', '42', '43', '44', '45']
    decoded_ascii = empty_file.decode_hex()
    decoded_string = ''
    for element in decoded_ascii:
        decoded_string += element
    assert decoded_string == 'ABCDE'
