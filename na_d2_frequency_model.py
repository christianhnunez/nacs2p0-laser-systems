"""
NaCs 2.0 Na D2 frequency model, with EOM positive sidebands.

Frequency convention
--------------------
All optical frequencies are plotted as MHz offsets from the sodium D2 center
of gravity, with the sodium ground F=2 level taken as zero.

Lock convention:
    NaRFA raw + Lock_SPAO = F=2 -> F'=3

Therefore:
    NaRFA raw = (F=2 -> F'=3) - Lock_SPAO.

EOM convention:
    EOMs create sidebands, not a replacement carrier. For the bookkeeping page
    we show the carrier output and the positive-frequency EOM sideband because
    that is the repump sideband used to address the F=1 ground manifold.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

APP_TITLE = "NaCs 2.0 Sodium D2 System"

# -----------------------------------------------------------------------------
# Sodium D2 constants in MHz, from Steck sodium D-line data.
# We use F=2 in the 3^2S_1/2 ground manifold as the zero of energy.
# -----------------------------------------------------------------------------
D2_CENTER_THz = 508.848_716_2
D2_WAVELENGTH_NM = 589.158_326_4
D2_LINEWIDTH_MHZ = 9.7946

GROUND_SPLITTING_MHZ = 1_771.626_128_8
GROUND_ENERGY_MHZ = {
    2: 0.0,
    1: -GROUND_SPLITTING_MHZ,
}

# Visual-only compression constants for the level diagram. Calculations remain
# true MHz values; only the plotted y coordinate is compressed.
GROUND_GAP_VISUAL_MHZ = 260.0
OPTICAL_GAP_VISUAL_MHZ = 620.0

# Excited 3^2P_3/2 hyperfine energies relative to the D2 center of gravity.
# Computed from A = 18.534 MHz and B = 2.724 MHz for I = J = 3/2.
EXCITED_ENERGY_MHZ = {
    0: -66.0975,
    1: -50.2875,
    2: -15.9435,
    3: +42.3825,
}

BEAM_COLORS = {
    "NaRFA": "black",
    "LockRef": "dimgray",
    "Na2DMOT": "tab:green",
    "Na2DMOT +EOM": "mediumseagreen",
    "Na3DMOT": "tab:blue",
    "Na3DMOT +EOM": "cornflowerblue",
    "NaPush": "tab:red",
    "NaPush +EOM": "orangered",
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
    "lock_SPAO_MHz": 168.0,
    "na2dmot_DPAO_MHz": 74.5,
    "na2dmot_EOM_pos_MHz": 1730.0,
    "na3dmot_push_EOM_pos_MHz": 1720.0,
    "na3dmot_DPAO_MHz": 79.0,
    "napush_DPAO_MHz": 90.0,
}

AOMS = {
    "lock_SPAO_MHz": AOM("lock_SPAO_MHz", "Lock SPAO", passes=1, order=+1),
    "na2dmot_DPAO_MHz": AOM("na2dmot_DPAO_MHz", "Na 2D MOT DPAO", passes=2, order=+1),
    "na3dmot_DPAO_MHz": AOM("na3dmot_DPAO_MHz", "Na 3D MOT DPAO", passes=2, order=+1),
    "napush_DPAO_MHz": AOM("napush_DPAO_MHz", "Na Push DPAO", passes=2, order=+1),
}

EOMS = {
    "na2dmot_EOM_pos_MHz": EOM("na2dmot_EOM_pos_MHz", "2D MOT EOM", sideband_order=+1),
    "na3dmot_push_EOM_pos_MHz": EOM("na3dmot_push_EOM_pos_MHz", "3D MOT / Push EOM", sideband_order=+1),
}

# Directed graph edges for the Na D2 optical system. NaRFA is the root/raw rail.
# The EOM sideband entries are separate plotted frequency components of the same
# physical output beams.
FREQUENCY_GRAPH_EDGES = {
    "LockRef": FrequencyEdge("NaRFA", ("lock_SPAO_MHz",)),
    "Na2DMOT": FrequencyEdge("NaRFA", ("na2dmot_DPAO_MHz",)),
    "Na2DMOT +EOM": FrequencyEdge("NaRFA", ("na2dmot_DPAO_MHz", "na2dmot_EOM_pos_MHz")),
    "Na3DMOT": FrequencyEdge("NaRFA", ("na3dmot_DPAO_MHz",)),
    "Na3DMOT +EOM": FrequencyEdge("NaRFA", ("na3dmot_push_EOM_pos_MHz", "na3dmot_DPAO_MHz")),
    "NaPush": FrequencyEdge("NaRFA", ("napush_DPAO_MHz",)),
    "NaPush +EOM": FrequencyEdge("NaRFA", ("na3dmot_push_EOM_pos_MHz", "napush_DPAO_MHz")),
}

BEAM_ORDER = [
    "NaRFA",
    "LockRef",
    "Na2DMOT",
    "Na2DMOT +EOM",
    "Na3DMOT",
    "Na3DMOT +EOM",
    "NaPush",
    "NaPush +EOM",
]

FINAL_OUTPUT_BEAMS = [
    "NaRFA",
    "Na2DMOT",
    "Na2DMOT +EOM",
    "Na3DMOT",
    "Na3DMOT +EOM",
    "NaPush",
    "NaPush +EOM",
]

CARRIER_BEAMS = ["NaRFA", "Na2DMOT", "Na3DMOT", "NaPush"]
EOM_SIDEBAND_BEAMS = ["Na2DMOT +EOM", "Na3DMOT +EOM", "NaPush +EOM"]


def all_d2_transitions() -> List[Transition]:
    out: List[Transition] = []
    for g in (1, 2):
        for e in (0, 1, 2, 3):
            out.append(Transition(g, e, EXCITED_ENERGY_MHZ[e] - GROUND_ENERGY_MHZ[g]))
    return out


TRANSITIONS = all_d2_transitions()


def transition_frequency(g: int, e: int) -> float:
    return EXCITED_ENERGY_MHZ[e] - GROUND_ENERGY_MHZ[g]


# Atomic lock reference: Na D2 cycling transition.
LOCK_F2_TO_F3P_MHZ = transition_frequency(2, 3)


class NaD2FrequencyModel:
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
        return self.component_shift_mhz("lock_SPAO_MHz")

    def narfa_raw_axis_frequency_mhz(self) -> float:
        """Return the raw NaRFA optical offset on the D2 axis."""
        return LOCK_F2_TO_F3P_MHZ - self.lock_shift_mhz()

    def beam_shift_from_narfa(self, node: str) -> float:
        if node == "NaRFA":
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
        if node == "NaRFA":
            return ["NaRFA"]
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
