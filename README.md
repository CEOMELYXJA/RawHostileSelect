# RawHostileSelect

**A visual laboratory for exploring how communication protocols evolve in a simulated hostile network.**

In Package Arena, each protocol is a way to protect a message. A package carries a sentence, a color code, or a short sequence through a simulated network. The arena shows the original and reconstructed contents, so you can see whether the message arrived intact, changed, became unreadable, or was lost. The packages and characters are visual metaphors, and the animation displays a sample of recorded trials.

Visit the [project website](https://ceomelyxja.github.io/RawHostileSelect/) or read the [full guide](README_V3.md).

## Run the Windows app

1. Download the [standalone Windows package](https://github.com/CEOMELYXJA/RawHostileSelect/releases/latest/download/RawHostileSelect-Windows.zip).
2. Extract the ZIP completely and open the `RawHostileSelect` folder.
3. Double-click `START THE APP.bat`.

The package includes Python, Tcl/Tk, and NumPy for compatible 64-bit Windows 10 and 11 systems. Keep its files together. The website introduces the project; it does not run the Python simulation in the browser.

## What the controls mean

- **Box designs / population:** the number of protocol candidates tested in each round. A design can send multiple messages.
- **Rounds / generations:** repeated stages of selection and variation. Nested boxes are a metaphor for recorded lineage; the model does not simulate physical nested packages.
- **Magic number / seed:** a number used to reproduce the same random draws with the same settings and program version.
- **Main-screen dashboard:** select a design to page through its actual operations, messages and changed bits. The dashboard summarizes the current round. A changed bit belongs to the encoded packet, not necessarily to a letter; the specific bit is chosen randomly by the simulated disturbance.
- **Package history:** review each recorded message at departure and arrival, by round. It remains available after a run while the app is open; Restart clears it. Export JSON and reopen it as a replay if you want to keep a run after closing the app.

## Run from source

The source download does not include the standalone runtime or dependencies. Install Python 3 with Tcl/Tk and pip, open a terminal in the extracted folder, and install the project dependency locally:

```bat
py -3 -m pip install -r requirements.txt --target .deps
```

Double-click `START_RawHostileSelect.bat` or run the app from the same folder:

```bat
set "PYTHONPATH=%CD%\.deps;%PYTHONPATH%"
py -3 app.py
```

The original v2 text-mode command remains available:

```bat
py -3 hostile_protocol_evolution.py --generations 20 --pop 36 --hostile medium
```

## Understanding the results

Version 4 evaluates multiple objectives: delivery, exact reconstruction, efficiency and resilience. Resilience is measured in separate extreme trials. Efficiency is a calculated score based on successfully reconstructed original bytes, transmitted bytes and simulated latency; it is not real network throughput. `FRAGMENT` has no effect on bytes in this model, and a checksum can miss errors. Delivery does not guarantee that a message is intact.

Results describe this simulation and its assumptions, not a physical network. Small samples can vary, and v2 scores are not directly comparable with the v3/v4 metrics. The [full guide](README_V3.md) describes the measurements, exports, replay and limitations.

## Project history and future ideas

- Genetic programming with operation trees and mutation/crossover.
- Multi-objective selection, Pareto fronts and structural niches.
- Future ideas include non-classical memory architectures, adversary co-evolution and agents without an explicit message concept.

## License

MIT. See [LICENSE](LICENSE).
