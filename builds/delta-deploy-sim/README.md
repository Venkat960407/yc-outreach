# Sending only what changed: delta updates for robots on flaky links

A small experiment I did after reading about Agency Tool Company's ATC Deploy. A robot in the field
already has the old software image, and the new build only differs in a few places. How few bytes
do you really need to send, and how much does resuming after a dropped connection matter?

```
pip install numpy
python delta.py     # about a minute
```

## The setup

- **A synthetic 97 MB "image":** 600 files, mostly random binary blobs plus repetitive config text.
- **The new build** has 6 small in-place edits, 3 small insertions near the start of files (which
  shift every byte after them), and 2 new files.
- **Three ways to send it:**
  1. **Full image:** send everything.
  2. **Fixed 64 KiB blocks:** send only the blocks the robot doesn't already have.
  3. **Content-defined chunks:** cut chunk boundaries wherever a rolling hash of the content hits
     a pattern (gear hash, as in FastCDC, average about 80 KiB). Boundaries move with the
     content, so an insertion only changes the chunks right around it.
- **A flaky field link:** 2 Mbit/s that drops at random, with 5 s to reconnect. After a drop the
  transfer either restarts from zero or resumes at the last finished chunk.

Checks: chunks always reassemble to the exact image, and an unchanged image needs 0 bytes of data.

## Results

| method | bytes to send | vs full image |
|---|---|---|
| full image | 97.0 MB | 100% |
| fixed 64 KiB blocks | 91.8 MB | 94.6% |
| content-defined chunks | 1.6 MB | **1.6%** |

Time to deliver on the flaky 2 Mbit/s link:

| payload | link drops every | restart from zero | resume at chunk |
|---|---|---|---|
| full image | 600 s | 6.5 min | 6.5 min |
| full image | 120 s | 22.2 min | 6.7 min |
| full image | 30 s | never (over 6 h) | 7.7 min |
| content-defined delta | any of the above | 0.1 min | 0.1 min |

## What I took from it

- **Fixed blocks barely help.** Three 37-byte insertions near the start of files shifted almost
  everything after them, so 95% of the blocks looked new. Content-defined chunking only resent
  1.6%.
- **Resuming matters as much as the delta itself on bad links.** Restarting from zero never
  finished when the link dropped every 30 seconds, while resuming finished in under 8 minutes.
- **Together, the update dropped from "never" to about 6 seconds.** Small payloads also slip
  between drops, which is why the delta row barely changes as the link gets worse.

Simplifications: synthetic files (real binaries change more after recompiling, which makes deltas
bigger), no compression, and a simple drop model. Next I'd try real container layers from two
builds of the same robot software.

Built with help from Claude.
