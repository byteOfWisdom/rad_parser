import os
from sys import argv
import struct
import math
import numpy as np
from typing import Callable, Generator


def read_bytes(filename: str) -> bytes:
    filesize = os.path.getsize(filename)
    with open(filename, 'rb') as file_handle:
        return file_handle.read(filesize)


def chunks(iterable : list, chunk_size: int) -> Generator[list, None, None]:
    for i in range(0, len(iterable) // chunk_size):
        start = i * chunk_size
        yield iterable[start : start + chunk_size]


def parse_slice(data: bytes, slice: int, function: Callable) -> (any, bytes):
    this = data[0: slice]
    leftover = data[slice:]
    return function(this), leftover


def zero_terminated(raw_str: str) -> str:
    res = ''
    for char in raw_str:
        if char != '\x00':
            res += char
    return res


def parse_measurement(data: bytes) -> dict:
    result = {}

    parse_long_int = lambda x : struct.unpack('<L', x)[0]
    parse_4b_float = lambda x : struct.unpack('<f', x)[0]
    parse_dimension = lambda x : zero_terminated(struct.unpack('8s', x)[0].decode('latin-1'))
    parse_date =  lambda x : struct.unpack('7s', x)[0].decode('latin-1')

    result["secs_of_month"], data = parse_slice(data, 4, parse_long_int)
    result["value"], data = parse_slice(data, 4, parse_4b_float)
    result["dimension"], data = parse_slice(data, 8, parse_dimension)
    result["alarm"], data = parse_slice(data, 4, parse_long_int)
    result["status"], data = parse_slice(data, 4, parse_long_int)
    result["interval"], data = parse_slice(data, 4, parse_long_int)
    result["date"], data = parse_slice(data, 7, parse_date)
    result["time"], data = parse_slice(data, 7, parse_date)

    #if len(data) != 2:
        #return None

    return result


def parse_c1(data: bytes, len: int) -> dict:
    result = {}

    parse_long_int = lambda x : struct.unpack('<L', x)[0]
    parse_4b_float = lambda x : struct.unpack('<f', x)[0]
    parse_dimension = lambda x : zero_terminated(struct.unpack('8s', x)[0].decode('latin-1'))
    parse_date =  lambda x : struct.unpack('7s', x)[0].decode('latin-1')

    result["secs_of_month"], data = parse_slice(data, 4, parse_long_int)
    result["value"], data = parse_slice(data, 4, parse_4b_float)
    _, data = parse_slice(data, len - 44, lambda _: None)
    result["dimension"], data = parse_slice(data, 8, parse_dimension)
    result["alarm"], data = parse_slice(data, 4, parse_long_int)
    result["status"], data = parse_slice(data, 4, parse_long_int)
    result["interval"], data = parse_slice(data, 4, parse_long_int)
    result["date"], data = parse_slice(data, 7, parse_date)
    result["time"], data = parse_slice(data, 7, parse_date)

    #if len(data) != 2:
        #return None

    return result



def convert_to_uSv(value: float, dim: str) -> float:
    if dim == 'Sv/h':
        return value * 1e6
    if dim == 'mSv/h':
        return value * 1e3
    print("found unknown unit: " + dim)
    return math.nan


def parse_file(filename: str) -> dict:
    data = read_bytes(filename)
    valid_padding = lambda x: x[42] == 32 and x[43] == 32 and x[44] != 32

    before_trim = len(data)

    while (not valid_padding(data)) and (not len(data) % 44 == 0):
        data = data[1:]

    measurements = list(chunks(data, 44))
    data_points = [parse_measurement(m) for m in measurements]

    bulk_data = {
        'secs': [],
        'value': [],
        'dimension': 'µSv/h', # just gonna do all values in this unit
        'alarm': [],
        'status': [],
        'interval': [],
        'date': [],
        'time': []
        }

    for point in data_points:
        bulk_data['secs'].append(point['secs_of_month'])

        if point['dimension'] == 'µSv/h':
            bulk_data['value'].append(point['value'])
        else:
            bulk_data['value'].append(convert_to_uSv(point['value'], point['dimension']))

        bulk_data['alarm'].append(point['alarm'])
        bulk_data['status'].append(point['status'])
        bulk_data['interval'].append(point['interval'])
        bulk_data['date'].append(point['date'])
        bulk_data['time'].append(point['time'])

    for key in bulk_data:
        if isinstance(bulk_data[key], list):
            bulk_data[key] = np.array(bulk_data[key])

    return bulk_data


def datetime_to_secs(day: int, hour: int, minute: int, secs: int) -> int:
    return day * 24 * 60 * 60 + hour * 60 * 60 + minute * 60 + secs


if __name__ == "__main__":
    data = parse_file(argv[1])

    print("secs, value, dimension, alarm, status, interval, date, time")

    for i in range(len(data['value'])):
        print(f"{data["secs"][i]}, {data["value"][i]}, {data["dimension"]}, {data["alarm"][i]}, {data["status"][i]}, {data["interval"][i]}, {data["date"][i]}, {data["time"][i]}")
