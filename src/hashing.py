from hashlib import sha256 as _sha2


def bitstring(b: bytes, nbits: int) -> str:
    num_bytes = (nbits + 8) // 8

    return ''.join((
        '1' if byte >> (7 - i) & 1 else '0'

        for nb, byte in zip(
            range(1, num_bytes + 1),
            b[:num_bytes]
        )

        for i in range(8 if nb < num_bytes else nbits % 8)
    ))


def compare_digests(x: bytes, y: bytes, nbits: int):
    num_bytes = nbits // 8

    for bx, by in zip(
            x[:num_bytes],
            y[:num_bytes]
    ):
        if bx != by:
            return False

    if nbits % 8:
        x, y = x[num_bytes], y[num_bytes]

        for bx, by in (
            (
                x >> (7 - i) & 1,
                y >> (7 - i) & 1
            )
            for i in range(0, nbits % 8)
        ):
            if bx != by:
                return False

    return True


def sha256(s: str, nbits: int) -> str:
    return bitstring(
        _sha2(s.encode('utf-8')).digest(),
        nbits
    )
