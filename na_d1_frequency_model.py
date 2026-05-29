"""
NaCs 2.0 Na D1 frequency model.

Frequency convention
--------------------
All optical frequencies are plotted as MHz offsets from the sodium D1 center
frequency, with the sodium ground F=2 level taken as zero.

Lock convention:
    NaD1RFA raw + NaD1Lock_SPAO = F=2 -> F'=1 on the D1 line

Therefore:
    NaD1RFA raw = (F=2 -> F'=1) - NaD1Lock_SPAO.

Experimental graph
------------------
NaD1RFA -> NaD1Lock_SPAO (+1, single pass) -> NaD1Lock
NaD1RFA -> NaD1Cool_DPAO (+1, double pass) -> NaD1Cool
NaD1RFA -> NaD1Cool_DPAO -> NaD1Repump_EOM (+ sideband) -> NaD1Repump
NaD1RFA -> NaD1Wavemeter

How to change this model
------------------------
1. Add RF magnitudes to DEFAULT_RF.
2. Add AOM entries to AOMS and EOM entries to EOMS.
3. Add or modify FREQUENCY_GRAPH_EDGES.
4. Optionally add colors and BEAM_ORDER entries.

AOM shift rule:
    Delta f_AOM = order * passes * f_RF

EOM shift rule:
    Delta f_EOM = sideband_order * f_RF
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

APP_TITLE = "NaCs 2.0 Sodium D1 System"

# -----------------------------------------------------------------------------
# Sodium D1 constants in MHz, from Steck sodium D-line data.
# We use F=2 in the 3^2S_1/2 ground manifold as the zero of energy.
# -----------------------------------------------------------------------------
D1_CENTER_THz = 508.332_465_7
D1_WAVELENGTH_NM = 589.756_661_7
D1_LINEWIDTH_MHZ = 9.765

GROUND_SPLITTING_MHZ = 1_771.626_128_8
GROUND_ENERGY_MHZ = {
    2: 0.0,
    1: -GROUND_SPLITTING_MHZ,
}

# Visual-only compression constants for the level diagram. Calculations remain
# true MHz values; only the plotted y coordinate is compressed.
GROUND_GAP_VISUAL_MHZ = 260.0
OPTICAL_GAP_VISUAL_MHZ = 620.0

# Excited 3^2P_1/2 hyperfine energies relative to the D1 center frequency.
# The F'=1 to F'=2 splitting is 188.88 MHz, so the center-of-gravity offsets
# are approximately -118.05 MHz and +70.83 MHz.
EXCITED_ENERGY_MHZ = {
    1: -118.05,
    2: +70.83,
}

BEAM_COLORS = {
    "NaD1RFA": "black",
    "NaD1Wavemeter": "tab:gray",
    "NaD1Lock": "dimgray",
    "NaD1Cool": "tab:blue",
    "NaD1Repump": "tab:green",
}


@dataclass(frozen=True)
class Transition:
    ground_f: int
    excited_f: int
    frequency_mhz: float

    @property
    def label(self) -> str:
        return f"F={self.ground_f} -> F'={self.excited_f}"


@dataclass(frozen=True)
class AOM:
    key: str
    label: str
    passes: int
    order: int = +1

    @property
    def type_label(self) -> str:
        return "DPAO" if self.passes == 2 else "SPAO"

    @property
    def order_label(self) -> str:
        return "+1 order" if self.order > 0 else "-1 order"

    @property
    def multiplier(self) -> int:
        return self.order * self.passes


@dataclass(frozen=True)
class EOM:
    key: str
    label: str
    sideband_order: int = +1

    @property
    def type_label(self) -> str:
        return "EOM +SB" if self.sideband_order > 0 else "EOM -SB"

    @property
    def multiplier(self) -> int:
        return self.sideband_order


@dataclass(frozen=True)
class FrequencyEdge:
    parent: str
    components: Tuple[str, ...]


# RF magnitudes in MHz. The sign/order of the optical path is encoded in AOMS/EOMS.
DEFAULT_RF = {
    "nad1lock_SPAO_MHz": 200.0,
    "nad1cool_DPAO_MHz": 225.0,
    "nad1repump_EOM_pos_MHz": 1_771.0,
}

AOMS = {
    "nad1lock_SPAO_MHz": AOM("nad1lock_SPAO_MHz", "NaD1 Lock SPAO", passes=1, order=+1),
    "nad1cool_DPAO_MHz": AOM("nad1cool_DPAO_MHz", "NaD1 Cool DPAO", passes=2, order=+1),
}

EOMS = {
    "nad1repump_EOM_pos_MHz": EOM("nad1repump_EOM_pos_MHz", "NaD1 Repump EOM", sideband_order=+1),
}

# Directed graph edges for the Na D1 optical system. NaD1RFA is the root/raw rail.
FREQUENCY_GRAPH_EDGES = {
    "NaD1Lock": FrequencyEdge("NaD1RFA", ("nad1lock_SPAO_MHz",)),
    "NaD1Cool": FrequencyEdge("NaD1RFA", ("nad1cool_DPAO_MHz",)),
    "NaD1Repump": FrequencyEdge("NaD1RFA", ("nad1cool_DPAO_MHz", "nad1repump_EOM_pos_MHz")),
    "NaD1Wavemeter": FrequencyEdge("NaD1RFA", ()),
}

BEAM_ORDER = [
    "NaD1RFA",
    "NaD1Wavemeter",
    "NaD1Lock",
    "NaD1Cool",
    "NaD1Repump",
]

FINAL_OUTPUT_BEAMS = ["NaD1Wavemeter", "NaD1Lock", "NaD1Cool", "NaD1Repump"]
CARRIER_BEAMS = ["NaD1RFA", "NaD1Wavemeter", "NaD1Lock", "NaD1Cool"]
EOM_SIDEBAND_BEAMS = ["NaD1Repump"]


def all_d1_transitions() -> List[Transition]:
    out: List[Transition] = []
    for g in (1, 2):
        for e in (1, 2):
            out.append(Transition(g, e, EXCITED_ENERGY_MHZ[e] - GROUND_ENERGY_MHZ[g]))
    return out


TRANSITIONS = all_d1_transitions()


def transition_frequency(g: int, e: int) -> float:
    return EXCITED_ENERGY_MHZ[e] - GROUND_ENERGY_MHZ[g]


# Atomic lock reference: Na D1 F=2 -> F'=1.
LOCK_F2_TO_F1P_MHZ = transition_frequency(2, 1)
# Backward-compatible alias in case any helper still imports the older name.
LOCK_F2_TO_F2P_MHZ = transition_frequency(2, 2)


class NaD1FrequencyModel:
    def __init__(self, rf_values: Dict[str, float]):
        self.rf_values = dict(rf_values)
        self._shift_cache: Dict[str, float] = {}

    def component_shift_mhz(self, component: str | None) -> float:
        if component is None:
            return 0.0
        if component in AOMS:
            aom = AOMS[component]
            return float(aom.multiplier) * self.rf_values[component]
        if component in EOMS:
            eom = EOMS[component]
            return float(eom.multiplier) * self.rf_values[component]
        raise KeyError(f"Unknown frequency graph component: {component!r}")

    def components_shift_mhz(self, components: Tuple[str, ...]) -> float:
        return sum(self.component_shift_mhz(component) for component in components)

    def lock_shift_mhz(self) -> float:
        return self.component_shift_mhz("nad1lock_SPAO_MHz")

    def narfa_raw_axis_frequency_mhz(self) -> float:
        """Return the raw NaD1RFA optical offset on the D1 axis."""
        return LOCK_F2_TO_F1P_MHZ - self.lock_shift_mhz()

    def beam_shift_from_narfa(self, node: str) -> float:
        if node == "NaD1RFA":
            return 0.0
        if node in self._shift_cache:
            return self._shift_cache[node]
        if node not in FREQUENCY_GRAPH_EDGES:
            raise KeyError(f"Unknown frequency graph node: {node!r}")
        edge = FREQUENCY_GRAPH_EDGES[node]
        shift = self.beam_shift_from_narfa(edge.parent) + self.components_shift_mhz(edge.components)
        self._shift_cache[node] = shift
        return shift

    def beam_shifts_from_narfa(self) -> Dict[str, float]:
        return {beam: self.beam_shift_from_narfa(beam) for beam in BEAM_ORDER}

    def beam_axis_frequencies(self) -> Dict[str, float]:
        raw = self.narfa_raw_axis_frequency_mhz()
        return {beam: raw + shift for beam, shift in self.beam_shifts_from_narfa().items()}

    def detuning_table(self, beam: str) -> List[Tuple[str, float]]:
        f = self.beam_axis_frequencies()[beam]
        return [(tr.label, f - tr.frequency_mhz) for tr in TRANSITIONS]

    def graph_path(self, node: str) -> List[str]:
        if node == "NaD1RFA":
            return ["NaD1RFA"]
        if node not in FREQUENCY_GRAPH_EDGES:
            raise KeyError(f"Unknown frequency graph node: {node!r}")
        edge = FREQUENCY_GRAPH_EDGES[node]
        components = " + ".join(edge.components) if edge.components else "route"
        return self.graph_path(edge.parent) + [f"{components} -> {node}"]

    def nearest_transition_for_frequency(self, optical_offset_mhz: float) -> Tuple[int, int, float]:
        best = None
        for tr in TRANSITIONS:
            det = optical_offset_mhz - tr.frequency_mhz
            score = abs(det)
            if best is None or score < best[0]:
                best = (score, tr.ground_f, tr.excited_f, det)
        assert best is not None
        return best[1], best[2], best[3]
