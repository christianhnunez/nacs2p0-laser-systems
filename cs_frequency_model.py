"""
NaCs 2.0 Cs System frequency model.

This file is intentionally GUI-independent. Both the Streamlit browser app and
any future desktop GUI can import the same AOM metadata and directed frequency
graph from here.

How to add a new output port
----------------------------
1. Add an RF magnitude to DEFAULT_RF if the new path has a new RF source.
2. Add an AOM entry to AOMS if the new component is an AOM.
3. Add one directed edge to FREQUENCY_GRAPH_EDGES.
4. Optionally add a color to BEAM_COLORS.

The graph rule is:

    shift(child) = shift(parent) + shift(component)

where component is either:
    None            : no frequency shift, just a routed optical path
    "CsDBR2_BEAT"  : the beat-lock offset from CsDBR1 to CsDBR2
    an AOM key      : e.g. "mot2d_DPAO_MHz"

AOM shift rule:

    Delta f_AOM = order * passes * f_RF

RF values are positive magnitudes. The selected +1/-1 diffraction order belongs
in AOMS metadata, not in DEFAULT_RF.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


APP_TITLE = "NaCs 2.0 Cs System"

# -----------------------------------------------------------------------------
# Cs D2 constants in MHz, from Steck's Cs D-line data.
# We use F=4 in the 6S1/2 ground manifold as the zero of energy.
# -----------------------------------------------------------------------------
D2_CENTER_THz = 351.725_718_50
D2_WAVELENGTH_NM = 852.347_275_82
D2_LINEWIDTH_MHZ = 5.2227
GROUND_SPLITTING_MHZ = 9_192.631_770

GROUND_ENERGY_MHZ = {
    4: 0.0,
    3: -GROUND_SPLITTING_MHZ,
}

# Visual-only compression constants for the level diagram. Calculations remain
# true MHz values; only the plotted y coordinate is compressed.
GROUND_GAP_VISUAL_MHZ = 850.0
OPTICAL_GAP_VISUAL_MHZ = 1_050.0

# Excited 6P3/2 levels on the same offset scale: transition frequencies from
# F=4 to F'=2,3,4,5 with the common D2 optical carrier subtracted. Adjacent
# excited-state splittings follow Steck Fig. 2.
EXCITED_ENERGY_MHZ = {
    2: -4_361.416_399_375,
    3: -4_210.206_399_375,
    4: -4_008.966_399_375,
    5: -3_757.966_399_375,
}

# Lab-specific lock offset. Leave at zero unless CsDBR1 has an intentional
# offset from the saturated-absorption crossover.
DBR1_LOCK_OFFSET_MHZ = 0.0

BEAM_COLORS = {
    "CsDBR1": "black",
    "CsDBR2": "dimgray",
    "CsTA": "tab:gray",
    "Repump": "tab:purple",
    "OP": "tab:orange",
    "SMALL_BEAM": "tab:cyan",
    "PUSH": "tab:red",
    "3DMOT": "tab:blue",
    "2DMOT": "tab:green",
    "dRSC": "tab:pink",
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
class FrequencyEdge:
    parent: str
    component: Optional[str]


# RF magnitudes in MHz. Do not encode the sign of the optical AOM order here.
DEFAULT_RF = {
    "f_CsREF_MHz": 100.0,
    "repump_DPAO_MHz": 134.973297,
    "OP_SPAO_MHz": 68.0,
    "small_beam_DPAO_MHz": 101.0,
    "push_DPAO_MHz": 97.0,
    "mot3d_DPAO_MHz": 101.0,
    "mot2d_DPAO_MHz": 96.0,
    "drsc_SPAO_MHz": 200.0,
}

# AOM metadata. Change order=+1/-1 here when your path uses the positive or
# negative first diffracted order.
AOMS = {
    "repump_DPAO_MHz": AOM("repump_DPAO_MHz", "Repump DPAO", passes=2, order=+1),
    "OP_SPAO_MHz": AOM("OP_SPAO_MHz", "OP SPAO", passes=1, order=-1),
    "small_beam_DPAO_MHz": AOM("small_beam_DPAO_MHz", "Small Beam DPAO", passes=2, order=+1),
    "push_DPAO_MHz": AOM("push_DPAO_MHz", "Push DPAO", passes=2, order=+1),
    "mot3d_DPAO_MHz": AOM("mot3d_DPAO_MHz", "3DMOT DPAO", passes=2, order=+1),
    "mot2d_DPAO_MHz": AOM("mot2d_DPAO_MHz", "2DMOT DPAO", passes=2, order=+1),
    "drsc_SPAO_MHz": AOM("drsc_SPAO_MHz", "dRSC SPAO", passes=1, order=-1),
}

# Directed graph edges for the current Cs optical system. CsDBR1 is the root.
FREQUENCY_GRAPH_EDGES = {
    "CsDBR2": FrequencyEdge("CsDBR1", "CsDBR2_BEAT"),
    "CsTA": FrequencyEdge("CsDBR2", None),
    "Repump": FrequencyEdge("CsDBR1", "repump_DPAO_MHz"),
    "OP": FrequencyEdge("CsDBR1", "OP_SPAO_MHz"),
    "SMALL_BEAM": FrequencyEdge("CsTA", "small_beam_DPAO_MHz"),
    "PUSH": FrequencyEdge("CsTA", "push_DPAO_MHz"),
    "3DMOT": FrequencyEdge("CsTA", "mot3d_DPAO_MHz"),
    "2DMOT": FrequencyEdge("CsTA", "mot2d_DPAO_MHz"),
    "dRSC": FrequencyEdge("CsTA", "drsc_SPAO_MHz"),
}

BEAM_ORDER = ["CsDBR1"] + list(FREQUENCY_GRAPH_EDGES.keys())


def all_d2_transitions() -> List[Transition]:
    out = []
    for g in (3, 4):
        for e in (2, 3, 4, 5):
            out.append(Transition(g, e, EXCITED_ENERGY_MHZ[e] - GROUND_ENERGY_MHZ[g]))
    return out


TRANSITIONS = all_d2_transitions()


def transition_frequency(g: int, e: int) -> float:
    return EXCITED_ENERGY_MHZ[e] - GROUND_ENERGY_MHZ[g]


# CsDBR1 lock: crossover halfway between F=3 -> F'=2 and F=3 -> F'=3.
LOCK_CO_23_MHZ = 0.5 * (transition_frequency(3, 2) + transition_frequency(3, 3)) + DBR1_LOCK_OFFSET_MHZ


def d2_axis_frequency_from_csdbd1_shift(shift_from_dbr1_mhz: float) -> float:
    """Return optical frequency on the F=4-zero offset scale."""
    return LOCK_CO_23_MHZ + shift_from_dbr1_mhz


class CsFrequencyModel:
    def __init__(self, rf_values: Dict[str, float]):
        self.rf_values = dict(rf_values)
        self._shift_cache: Dict[str, float] = {}

    def component_shift_mhz(self, component: Optional[str]) -> float:
        if component is None:
            return 0.0
        if component == "CsDBR2_BEAT":
            return -88.7454545454 * self.rf_values["f_CsREF_MHz"]
        if component in AOMS:
            aom = AOMS[component]
            return float(aom.multiplier) * self.rf_values[component]
        raise KeyError(f"Unknown frequency graph component: {component!r}")

    def beat_offset_mhz(self) -> float:
        return self.component_shift_mhz("CsDBR2_BEAT")

    def beam_shift_from_dbr1(self, node: str) -> float:
        if node == "CsDBR1":
            return 0.0
        if node in self._shift_cache:
            return self._shift_cache[node]
        if node not in FREQUENCY_GRAPH_EDGES:
            raise KeyError(f"Unknown frequency graph node: {node!r}")
        edge = FREQUENCY_GRAPH_EDGES[node]
        shift = self.beam_shift_from_dbr1(edge.parent) + self.component_shift_mhz(edge.component)
        self._shift_cache[node] = shift
        return shift

    def beam_shifts_from_dbr1(self) -> Dict[str, float]:
        return {beam: self.beam_shift_from_dbr1(beam) for beam in BEAM_ORDER}

    def beam_axis_frequencies(self) -> Dict[str, float]:
        return {beam: d2_axis_frequency_from_csdbd1_shift(shift)
                for beam, shift in self.beam_shifts_from_dbr1().items()}

    def detuning_table(self, beam: str) -> List[Tuple[str, float]]:
        f = self.beam_axis_frequencies()[beam]
        return [(tr.label, f - tr.frequency_mhz) for tr in TRANSITIONS]

    def graph_path(self, node: str) -> List[str]:
        if node == "CsDBR1":
            return ["CsDBR1"]
        if node not in FREQUENCY_GRAPH_EDGES:
            raise KeyError(f"Unknown frequency graph node: {node!r}")
        edge = FREQUENCY_GRAPH_EDGES[node]
        part = node if edge.component is None else f"{edge.component} -> {node}"
        return self.graph_path(edge.parent) + [part]

    def nearest_transition_for_frequency(self, optical_offset_mhz: float) -> Tuple[int, int, float]:
        best = None
        for tr in TRANSITIONS:
            det = optical_offset_mhz - tr.frequency_mhz
            score = abs(det)
            if best is None or score < best[0]:
                best = (score, tr.ground_f, tr.excited_f, det)
        assert best is not None
        return best[1], best[2], best[3]
