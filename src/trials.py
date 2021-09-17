from __future__ import annotations
import random
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Optional, Generator, Tuple
from pickle import Pickler, Unpickler
from hashing import *


class Trial:
    _COLLISION_MASTER: Dict[  # Unique messages so that other trials don't reuse the same strings
        str,   # The source message of a sample
        Trial  # The trial instance using it
    ] = OrderedDict()

    _PRE_IMAGE_MASTER: Dict[  # Unique digests so that other trials don't reuse the same values
        bytes,  # The pre-image digest
        Trial   # The trial instance using it
    ] = OrderedDict()

    _BIT_SIZES = (8, 10, 12, 14, 16, 18, 20, 22)
    _NUM_SAMPLES = 50

    _FILENAME_TEMPLATE = "hash-attack-trial-{num_bits:d}bits.pkl"
    _ASCII_STRING_LEN = 14
    _ASCII_SEGMENT_BOUNDS = (
        ('a', 'z'),
        ('A', 'Z'),
        ('0', '9')
    )
    _ASCII_BOUNDS = (
        min(*(
            ord(first) for first, _ in _ASCII_SEGMENT_BOUNDS
        )),
        max(*(
            ord(last) for _, last in _ASCII_SEGMENT_BOUNDS
        )) + 1
    )
    _ASCII_SEGMENTS = tuple(
        ''.join((
            chr(n) for n in range(
                ord(first),
                ord(last) + 1
            )
        ))
        for first, last in _ASCII_SEGMENT_BOUNDS
    )

    @classmethod
    def _random_ascii(cls) -> str:
        chars: List[Optional[str]] = [None] * cls._ASCII_STRING_LEN
        for index, c in enumerate(chars):
            while c is None or True not in (c in s for s in cls._ASCII_SEGMENTS):
                c = chr(random.randrange(*cls._ASCII_BOUNDS))
            chars[index] = c
        return ''.join(chars)

    @classmethod
    def _random_digest(cls) -> bytes:
        return bytes((random.randrange(0, 256) for _ in range(32)))

    @classmethod
    def open_directory(cls, results_dir: Path) -> Generator[Trial]:
        print(f"loading previous results from directory {results_dir}")

        for num_bits in cls._BIT_SIZES:
            path = results_dir.joinpath(cls._FILENAME_TEMPLATE.format(num_bits=num_bits))
            try:
                with open(path, 'rb') as fp:
                    print(f"found pickled trial results {path}")
                    yield Unpickler(fp).load()
            except FileNotFoundError:
                print(f"did not find a file {path}, creating new trial for bit size {num_bits}")

                digest = None
                while digest is None or digest in cls._PRE_IMAGE_MASTER:
                    digest = cls._random_digest()

                yield Trial(num_bits, digest)

    def __init__(self, bits: int, pre_image: bytes):
        self.num_bits = bits
        self.collision_results: Dict[
            str,      # Source message A, used as key here to ensure uniqueness / avoid redundancy
            Tuple[    # Sample results:
                str,  # Source message B
                int,  # Number of iterations
            ]
        ] = OrderedDict()
        self.pre_image_digest: bytes = pre_image
        self._PRE_IMAGE_MASTER[pre_image] = self
        self.pre_image_results: List[
            Tuple[    # Sample results:
                str,  # The source message
                int   # Number of iterations
            ]
        ] = []

    def __setstate__(self, state):
        num_bits, pre_image_digest = (state[key] for key in ("num_bits", "pre_image_digest"))
        print(f"unpickling trial with {num_bits} bit size")
        self.__init__(num_bits, pre_image_digest)

        for a, b in state['collision_results'].items():
            self.collision_results[a] = b
            self._COLLISION_MASTER[a] = self
        print(f"found {len(self.collision_results)} completed collision samples")

        self.pre_image_results = list(state['pre_image_results'])
        print(f"and {len(self.pre_image_results)} pre-image samples")

    def _dump(self, direct: Path):
        with open(
                direct.joinpath(self._FILENAME_TEMPLATE.format(num_bits=self.num_bits)),
                'wb'
        ) as fp:
            Pickler(fp).dump(self)

    def run_collision(self, results_dir: Path):
        num_tests = self._NUM_SAMPLES - len(self.collision_results)
        if num_tests == 0:
            print(f"all collision samples for bit size {self.num_bits} are complete; no new tests will be run")
            return

        while len(self.collision_results) < self._NUM_SAMPLES:
            print(f"running collision experiment {len(self.collision_results):02d} with {self.num_bits} bit size")

            m = None
            while m is None or m in self._COLLISION_MASTER:
                m = self._random_ascii()
            print(f"source message is {m}")

            num_iter = 0
            a, b = sha256(m, self.num_bits), None

            while b is None or sha256(b, self.num_bits) != a:
                b = self._random_ascii()
                num_iter += 1
            print(f"completed in {num_iter} iterations")

            self.collision_results[m] = (b, num_iter)
            self._COLLISION_MASTER[m] = self
            self._dump(results_dir)
        print(f"completed {num_tests} collision samples, this trial is complete")

    def run_pre_image(self, results_dir: Path):
        num_tests = self._NUM_SAMPLES - len(self.pre_image_results)
        if num_tests == 0:
            print(f"all pre-image samples for bit size {self.num_bits} are complete; no new tests will be run")
            return

        while len(self.pre_image_results) < self._NUM_SAMPLES:
            print(f"running pre-image experiment {len(self.pre_image_results):02d} with {self.num_bits} bit size")

            num_iter = 0
            a, b = bitstring(self.pre_image_digest, self.num_bits), None

            while b is None or sha256(b, self.num_bits) != a:
                b = self._random_ascii()
                num_iter += 1
            print(f"completed in {num_iter} iterations")

            self.pre_image_results.append((b, num_iter))
            self._dump(results_dir)
        print(f"completed {num_tests} pre-image samples, this trial is complete")


__all__ = [
    'Trial'
]
