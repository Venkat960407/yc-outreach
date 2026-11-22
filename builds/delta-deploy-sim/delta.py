"""How few bytes can you send to update software on a robot in the field?

A robot already has the old software image. A new build differs in a few places: some files
edited, a few bytes inserted early in a file (which shifts everything after it), a dependency
bumped. This script compares how much has to go over the network:

  1. full image: send everything (what a fresh download does)
  2. fixed-size blocks: split both images into 64 KiB blocks, send blocks the robot doesn't have
  3. content-defined chunks: split where a rolling hash of the content hits a pattern
     (a "gear" hash, as in FastCDC), so an insertion only changes the chunks around it

Then it adds a flaky link (drops every so often) and compares restarting the transfer from zero
against resuming at the last finished chunk.

The images are synthetic (random "binary" files plus repetitive "config" text), so the absolute
numbers are made up, but the comparison between methods is the point.

Usage:
  python delta.py
"""
import hashlib
import numpy as np

RNG = np.random.default_rng(0)
GEAR = RNG.integers(0, 2**63, 256, dtype=np.uint64)


def make_image(n_files=600, rng=RNG):
    files = []
    for i in range(n_files):
        if rng.random() < 0.7:
            size = int(rng.lognormal(11.6, 1.2))                        # binaries/libraries
            files.append(rng.integers(0, 256, size, dtype=np.uint8).tobytes())
        else:
            line = f"param_{i} = {rng.integers(1000)}\n".encode()
            files.append(line * int(rng.integers(50, 2000)))            # configs/text
    return files


def change(files, rng, n_edit=6, n_insert=3, n_new=2):
    files = list(files)
    for i in rng.choice(len(files), n_edit, replace=False):              # in-place edits
        b = bytearray(files[i])
        if len(b) > 100:
            p = int(rng.integers(0, len(b) - 50))
            b[p:p + 50] = rng.integers(0, 256, 50, dtype=np.uint8).tobytes()
        files[i] = bytes(b)
    for i in rng.choice(len(files), n_insert, replace=False):            # insertions shift data
        b = files[i]
        p = int(rng.integers(0, max(len(b) // 10, 1)))                  # near the start of the file
        files[i] = b[:p] + rng.integers(0, 256, 37, dtype=np.uint8).tobytes() + b[p:]
    for _ in range(n_new):
        files.append(rng.integers(0, 256, int(rng.lognormal(11, 1)), dtype=np.uint8).tobytes())
    return files


def fixed_chunks(data, size=64 * 1024):
    return [data[i:i + size] for i in range(0, len(data), size)]


def gear_hashes(arr):
    """Gear rolling hash at every byte: h_i = sum_{k<64} GEAR[b_{i-k}] << k (mod 2^64).
    Bytes more than 64 back have been shifted out, so this vectorizes over the 64 terms."""
    g = GEAR[arr]
    h = np.zeros(len(arr), dtype=np.uint64)
    with np.errstate(over="ignore"):
        for k in range(64):
            h[k:] += g[:len(arr) - k] << np.uint64(k)
    return h


def cdc_chunks(data, avg_bits=16, min_size=16 * 1024, max_size=256 * 1024):
    """Gear-hash content-defined chunking (as in FastCDC): cut where the top bits of the hash are
    zero, with a minimum and maximum chunk size."""
    arr = np.frombuffer(data, dtype=np.uint8)
    mask = np.uint64(((1 << avg_bits) - 1) << (64 - avg_bits))
    cands = []
    win = 8 * 1024 * 1024
    for s in range(0, len(arr), win):
        lo = max(0, s - 63)
        h = gear_hashes(arr[lo:s + win])
        idx = np.nonzero((h & mask) == 0)[0] + lo
        cands.append(idx[idx >= s])
    cands = np.concatenate(cands) if cands else np.array([], int)
    chunks, start, ci = [], 0, 0
    n = len(arr)
    while start < n:
        ci = np.searchsorted(cands, start + min_size - 1, side="left")
        if ci < len(cands) and cands[ci] - start + 1 <= max_size:
            end = cands[ci] + 1
        else:
            end = min(start + max_size, n)
        chunks.append(data[start:end]); start = end
    return chunks


def delta_bytes(old, new, chunker):
    have = {hashlib.sha256(c).digest() for c in chunker(old)}
    new_chunks = chunker(new)
    send = [c for c in new_chunks if hashlib.sha256(c).digest() not in have]
    # plus the list of chunk hashes the robot needs to rebuild the image
    return sum(len(c) for c in send) + 32 * len(new_chunks), send


def flaky_transfer(chunks, mbps, drop_every_s, resume, rng):
    """Seconds to deliver all chunks over a link that drops at random (exponential gaps)."""
    rate = mbps * 1e6 / 8
    t, k = 0.0, 0
    next_drop = rng.exponential(drop_every_s)
    sent_in_session = 0.0
    while k < len(chunks):
        dt = len(chunks[k]) / rate
        if t + dt > next_drop:                    # link drops mid-chunk
            t = next_drop + 5.0                   # 5 s to reconnect
            next_drop = t + rng.exponential(drop_every_s)
            if not resume:
                k = 0
            continue
        t += dt
        k += 1
        if t > 6 * 3600:
            return np.inf
    return t


def main():
    rng = np.random.default_rng(1)
    old_files = make_image()
    new_files = change(old_files, rng)
    old, new = b"".join(old_files), b"".join(new_files)
    MB = 1e6
    print(f"image size: {len(new) / MB:.0f} MB, changed: 6 edits, 3 small insertions, 2 new files\n")
    full = len(new)
    fx, fx_chunks = delta_bytes(old, new, fixed_chunks)
    cd, cd_chunks = delta_bytes(old, new, cdc_chunks)
    print(f"{'method':>24} | {'bytes to send':>13} | {'vs full image':>13}")
    for name, b in (("full image", full), ("fixed 64 KiB blocks", fx), ("content-defined chunks", cd)):
        print(f"{name:>24} | {b / MB:>10.1f} MB | {b / full:>12.1%}")

    print("\nTime to deliver over a 2 Mbit/s field link that drops on average every N seconds:")
    full_chunks = cdc_chunks(new)
    print(f"{'payload':>26} | {'drops every':>11} | {'restart from zero':>17} | {'resume at chunk':>15}")
    for label, chunks in (("full image", full_chunks), ("content-defined delta", cd_chunks)):
        for every in (600, 120, 30):
            r = [flaky_transfer(chunks, 2.0, every, False, np.random.default_rng(s)) for s in range(10)]
            q = [flaky_transfer(chunks, 2.0, every, True, np.random.default_rng(s)) for s in range(10)]
            fmt = lambda x: "never (>6 h)" if not np.isfinite(x) else f"{x / 60:.1f} min"
            print(f"{label:>26} | {every:>9} s | {fmt(np.median(r)):>17} | {fmt(np.median(q)):>15}")


if __name__ == "__main__":
    main()
