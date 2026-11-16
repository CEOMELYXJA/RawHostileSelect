# RawHostileSelect — Package Arena

Version 4 represents messages as little boxes travelling through a simulated network. Try a sentence, color, code, or a mix; see what was sent and what was actually reconstructed; and follow results across rounds.

- **Population**: number of box designs (protocols) tested in each round. Each design may send several messages.
- **Generations**: number of rounds. Selected designs can give rise to other designs in the next round. Nested boxes are a visual metaphor, not a physical structure simulated by the model.
- **Seed**: a number that repeats the same random draws with the same settings and program version.
- **At the end**: a box can arrive intact, arrive with a changed or unreadable message, or get lost. Corrupted bytes may no longer form valid UTF-8 text; no replacement sentence is invented.

The arena is a local interface for exploring RawHostileSelect's Python engine. The GitHub Pages website describes the project; it does not execute Python in the browser. The `hostile_protocol_evolution.py` script and its existing command remain available.

### Installation on Windows 10 or 11

To use the self-contained v4 package on **64-bit** Windows 10 or 11, extract the ZIP completely, open the `RawHostileSelect` folder, then double-click `START THE APP.bat`. Keep all its files together. This package includes Python, Tkinter and NumPy; no separate installation is needed on a compatible Windows computer. The [project website](https://ceomelyxja.github.io/RawHostileSelect/) shows the available download.

For a **source-code copy downloaded from GitHub**, the runtime and local dependencies are not included:

1. Download the complete repository from GitHub using **Code → Download ZIP**, then extract it to a folder. Keep all the files together.
2. Install Python 3 from [python.org](https://www.python.org/downloads/windows/) if needed. Include Tcl/Tk and pip in the installation; add Python to PATH if the option is offered.
3. Open a terminal in the extracted folder and install the dependency:

   ```bat
   py -3 -m pip install -r requirements.txt --target .deps
   ```

   If `py` is unavailable, try `python -m pip install -r requirements.txt --target .deps`. This folder keeps the dependency beside the project. The launcher can also use an existing NumPy installation or, when available, the computer's Codex runtime.
4. Double-click `START_RawHostileSelect.bat`. The launcher checks for Python, Tkinter and NumPy, then opens `app.py`. If it encounters an error, it keeps the window open with guidance.

Alternatively, open a terminal in the folder and run the following if NumPy is installed in `.deps`:

```bat
set "PYTHONPATH=%CD%\.deps;%PYTHONPATH%"
py -3 app.py
```

The original text-mode command remains `py -3 hostile_protocol_evolution.py --generations 20 --pop 36 --hostile medium` (after setting `PYTHONPATH` as above if necessary).

### About the results

On the main screen, select a P… design to see its recipe. Use the buttons to move through its operations, messages and changed bits without scrolling the entire page. The dashboard summarizes the current round. The displayed bits belong to the encoded packet; the program explains the recorded noise or corruption, while the choice of a particular bit is random. Large result sets remain accessible through pages and detailed views.

The layout was verified at 1,380 × 900 pixels and larger; smaller screens may not have enough room for every panel.

The **PACKAGE HISTORY** button opens a list of messages by round: choose a package to review its contents at departure and arrival. History remains available after the test while the app is open, and **RESTART** clears it. To keep it after closing the app, export JSON and reopen that file as a replay.

The application can run evolution one generation at a time, display a sample of recorded transmissions, selections, eliminations, mutations and crossovers, export results as JSON or CSV, and reopen a JSON replay. The simulation runs in the background. The arena uses visual metaphors: it does not simulate physical characters. The animation shows only a sample of recorded events.

A protocol's details include a clickable tree, explanations in English, and recorded parents and history. Choose a trial and click an operation to see before-and-after byte traces when available. These excerpts are limited to 64 bytes and clearly identified as such. Older replays without traces show that the information is unavailable instead of inventing an example. The dashboard includes the Pareto front, niches, complexity, latency, losses, and bytes sent.

Results describe the computer model and its assumptions, not tests of a physical network. Each protocol is evaluated on a small number of messages, so values can vary considerably. Versions 3 and 4 use different definitions from version 2: **their scores are not directly comparable**. In v4, changing message type or length also changes the experiment; compare trials with the same settings.

In v4:

- **Delivery**: packets received divided by attempts.
- **Integrity**: messages reconstructed exactly divided by attempts.
- **Resilience**: fraction of messages reconstructed exactly in separate extreme trials.
- **Efficiency**: sum of the original bytes of exactly reconstructed messages, divided by bytes actually sent, multiplied by `1 / (1 + average latency of received packets / 40)`. This is a calculated model score, not actual throughput; it is zero when no bytes were sent or no latency was measured.

Latency is expressed in simulated units. In this model, `FRAGMENT` is a neutral operation; a checksum can miss some errors. Delivery does not guarantee exact reconstruction.

This first version does not yet include every requested feature. Animations are educational representations of a sample of events; they do not demonstrate performance on a real network.
