from __future__ import annotations

import io

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from matplotlib import rcParams
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch, Circle, Rectangle

from na_d1_frequency_model import (
    AOMS,
    EOMS,
    APP_TITLE,
    BEAM_COLORS,
    BEAM_ORDER,
    D1_CENTER_THz,
    D1_LINEWIDTH_MHZ,
    D1_WAVELENGTH_NM,
    DEFAULT_RF,
    EXCITED_ENERGY_MHZ,
    FINAL_OUTPUT_BEAMS,
    FREQUENCY_GRAPH_EDGES,
    GROUND_GAP_VISUAL_MHZ,
    GROUND_SPLITTING_MHZ,
    GROUND_ENERGY_MHZ,
    LOCK_F2_TO_F1P_MHZ,
    OPTICAL_GAP_VISUAL_MHZ,
    NaD1FrequencyModel,
)

st.set_page_config(page_title=APP_TITLE, layout="wide")

rcParams["svg.fonttype"] = "path"
rcParams["font.family"] = "DejaVu Sans"

st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
    [data-testid="stSidebar"], [data-testid="stSidebarContent"],
    [data-testid="stMainBlockContainer"] {
        background-color: #ffffff !important;
        color: #111111 !important;
    }

    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: #111111;
    }

    [data-testid="stMetric"], [data-testid="stDataFrame"], [data-testid="stCodeBlock"] {
        background-color: #ffffff !important;
        color: #111111 !important;
    }

    /* Force BaseWeb widgets used by Streamlit selectbox/button/text inputs to light mode. */
    div[data-baseweb="select"] > div,
    div[data-baseweb="popover"],
    div[data-baseweb="menu"],
    ul[role="listbox"],
    li[role="option"] {
        background-color: #f3f3f3 !important;
        color: #111111 !important;
        border-color: #cfcfcf !important;
    }
    div[data-baseweb="select"] svg,
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div {
        color: #111111 !important;
        fill: #111111 !important;
    }
    button[kind="secondary"], button[data-testid="baseButton-secondary"] {
        background-color: #f3f3f3 !important;
        color: #111111 !important;
        border: 1px solid #cfcfcf !important;
    }
    button[kind="secondary"] p, button[data-testid="baseButton-secondary"] p {
        color: #111111 !important;
    }
    input, textarea, select, div[data-baseweb="input"] input {
        background-color: #f3f3f3 !important;
        color: #111111 !important;
        border-color: #cfcfcf !important;
    }
    div[data-baseweb="input"] > div {
        background-color: #f3f3f3 !important;
        color: #111111 !important;
        border-color: #cfcfcf !important;
    }
    [data-testid="stTextInput"] input,
    [data-testid="stTextInput"] div[data-baseweb="base-input"],
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background-color: #f3f3f3 !important;
        color: #111111 !important;
        border-color: #cfcfcf !important;
    }
    .stTabs [data-baseweb="tab-list"], .stTabs [data-baseweb="tab"] {
        background-color: #ffffff !important;
        color: #111111 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

LIGHT_PANEL_BG = "#ffffff"
LIGHT_GRID = "#d0d0d0"


def figure_to_svg(fig: Figure) -> str:
    """Convert a Matplotlib figure to raw SVG."""
    buf = io.StringIO()
    fig.savefig(
        buf,
        format="svg",
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        metadata={"Date": None},
    )
    return buf.getvalue()


def show_plot_stack(figures: list[Figure]) -> None:
    """Show multiple SVG figures in one responsive component."""
    svgs = [figure_to_svg(fig) for fig in figures]
    total_height_px = 1120
    html = f"""
    <html>
    <head>
    <style>
      html, body {{ margin: 0; padding: 0; background: white; overflow: hidden; }}
      .plot-wrap {{ width: 100%; background: white; }}
      .plot-wrap svg {{ width: 100%; height: auto; display: block; }}
    </style>
    </head>
    <body>
      <div class="plot-wrap">{svgs[0]}</div>
      <div class="plot-wrap" style="margin-top: 18px;">{svgs[1]}</div>
    </body>
    </html>
    """
    components.html(html, height=total_height_px, scrolling=False)


def pretty_rf_label(key: str) -> str:
    label = key.replace("_MHz", "").replace("_pos", " +SB").replace("_", " ")
    if key in AOMS:
        aom = AOMS[key]
        label += f" ({aom.type_label}, {aom.order_label})"
    elif key in EOMS:
        label += " (EOM positive sideband)"
    return label


def component_short_label(component: str | None) -> str:
    if component is None:
        return "route"
    if component in AOMS:
        return AOMS[component].type_label
    if component in EOMS:
        return EOMS[component].type_label
    return str(component)


def components_label(model: NaD1FrequencyModel, components: tuple[str, ...]) -> str:
    parts: list[str] = []
    for component in components:
        rf_mhz = model.rf_values[component]
        shift_mhz = model.component_shift_mhz(component)
        if component in AOMS:
            aom = AOMS[component]
            parts.append(f"{aom.multiplier:+d} x {rf_mhz:.3g} = {shift_mhz:+.1f} MHz")
        elif component in EOMS:
            eom = EOMS[component]
            parts.append(f"{eom.type_label}: {shift_mhz:+.1f} MHz")
        else:
            parts.append(f"{shift_mhz:+.1f} MHz")
    return "\n".join(parts) if parts else "route"


def edge_label(model: NaD1FrequencyModel, components: tuple[str, ...] | str | None) -> str:
    if components is None:
        return "route"
    if isinstance(components, str):
        components = (components,)
    return components_label(model, components)


def aom_short_label(component: str | None) -> str:
    return component_short_label(component)


def make_level_figure(model: NaD1FrequencyModel, selected_beam: str) -> Figure:
    fig = Figure(figsize=(10.8, 6.4), dpi=180, facecolor=LIGHT_PANEL_BG)
    ax = fig.add_subplot(111, facecolor=LIGHT_PANEL_BG)
    ax.set_title("Na D1 level diagram", fontsize=15)
    ax.set_ylabel("Frequency [MHz]", fontsize=13)
    ax.set_xlabel("")

    label_box = dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="none", alpha=0.90)
    level_box = dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.95)

    beams = model.beam_axis_frequencies()
    ground_plot_energy = {2: 0.0, 1: -GROUND_GAP_VISUAL_MHZ}
    excited_reference_actual = min(EXCITED_ENERGY_MHZ.values())
    excited_plot_energy = {
        fp: OPTICAL_GAP_VISUAL_MHZ + (val - excited_reference_actual)
        for fp, val in EXCITED_ENERGY_MHZ.items()
    }

    x_positions = {beam: 0.8 + 0.92 * i for i, beam in enumerate(BEAM_ORDER)}
    xmin = min(x_positions.values()) - 0.65
    xmax = max(x_positions.values()) + 0.65
    level_label_x = xmax + 0.36

    for f in (2, 1):
        y = ground_plot_energy[f]
        ax.hlines(y, xmin, xmax, color="0.12", linewidth=2.6, zorder=1)
        ax.text(
            level_label_x,
            y,
            rf"$3^2\mathrm{{S}}_{{1/2}};\ F={f}$",
            ha="left",
            va="center",
            fontsize=12,
            color="0.12",
            bbox=level_box,
            zorder=8,
            clip_on=False,
        )

    for fp in (1, 2):
        y = excited_plot_energy[fp]
        ax.hlines(y, xmin, xmax, color="0.22", linewidth=2.0, zorder=1)
        ax.text(
            level_label_x,
            y,
            rf"$3^2\mathrm{{P}}_{{1/2}};\ F'={fp}$",
            ha="left",
            va="center",
            fontsize=12,
            color="0.22",
            bbox=level_box,
            zorder=8,
            clip_on=False,
        )

    ax.text(
        xmin + 0.05,
        0.5 * (ground_plot_energy[2] + excited_plot_energy[1]),
        "compressed\nlevel gaps",
        ha="left",
        va="center",
        fontsize=8,
        color="0.35",
        bbox=label_box,
        zorder=8,
    )
    ax.text(
        xmin + 0.05,
        0.5 * (ground_plot_energy[1] + ground_plot_energy[2]),
        f"true F=1 to F=2 gap = {GROUND_SPLITTING_MHZ:.3f} MHz",
        ha="left",
        va="center",
        fontsize=8,
        color="0.35",
        bbox=label_box,
        zorder=8,
    )

    for beam in BEAM_ORDER:
        x = x_positions[beam]
        optical_offset = beams[beam]
        ground_f, excited_f, det = model.nearest_transition_for_frequency(optical_offset)
        y0 = ground_plot_energy[ground_f]
        target_y = excited_plot_energy[excited_f]
        y1 = target_y + det
        color = BEAM_COLORS.get(beam, "tab:blue")
        lw = 3.1 if beam == selected_beam else 1.9
        mutation = 16 if beam == selected_beam else 11
        alpha = 0.92

        ax.add_patch(
            FancyArrowPatch(
                (x, y0),
                (x, y1),
                arrowstyle="-|>",
                mutation_scale=mutation,
                linewidth=lw,
                color=color,
                alpha=alpha,
                shrinkA=0,
                shrinkB=0,
            )
        )
        ax.plot([x], [y0], marker="o", color=color, markersize=4.5, zorder=5)
        ax.plot([x], [y1], marker="o", color=color, markersize=7 if beam == selected_beam else 5, zorder=6)
        ax.plot([x - 0.14, x + 0.14], [target_y, target_y], color=color, linewidth=1.2, alpha=0.45)
        ax.plot([x + 0.14, x + 0.14], [target_y, y1], color=color, linewidth=1.0, alpha=0.35)

        name = beam
        label = f"{name}\nF={ground_f} → F′={excited_f}\n{det:+.1f} MHz"
        va = "bottom" if y1 >= y0 else "top"
        stagger = {0: -110, 1: 92, 2: -170}[BEAM_ORDER.index(beam) % 3]
        ax.text(
            x,
            y1 + stagger,
            label,
            ha="center",
            va=va,
            fontsize=7.2,
            color=color,
            bbox=label_box,
            zorder=10,
            linespacing=1.05,
        )

    ax.set_xticks([x_positions[b] for b in BEAM_ORDER])
    ax.set_xticklabels([b for b in BEAM_ORDER], rotation=28, ha="right", fontsize=8)

    all_y = list(ground_plot_energy.values()) + list(excited_plot_energy.values())
    for optical_offset in beams.values():
        _gf, ef, det = model.nearest_transition_for_frequency(optical_offset)
        all_y.append(excited_plot_energy[ef] + det)
    ymin, ymax = min(all_y), max(all_y)
    pad = max(360.0, 0.08 * (ymax - ymin))
    ax.set_ylim(ymin - pad, ymax + pad)
    ax.set_xlim(xmin, xmax + 1.85)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)
    ax.tick_params(axis="both", direction="out")
    fig.tight_layout()
    return fig


def make_graph_figure(model: NaD1FrequencyModel, selected_beam: str) -> Figure:
    fig = Figure(figsize=(10.8, 4.45), dpi=180, facecolor=LIGHT_PANEL_BG)
    ax = fig.add_subplot(111, facecolor=LIGHT_PANEL_BG)
    ax.set_title("Na D1 laser system directed graph", fontsize=13)
    ax.set_axis_off()
    ax.set_xlim(-0.2, 11.2)
    ax.set_ylim(-0.75, 6.85)

    label_box = dict(boxstyle="round,pad=0.16", facecolor="white", edgecolor="none", alpha=0.9)

    def node_color(node: str) -> str:
        return BEAM_COLORS.get(node, "black")

    def rectangle_node(x: float, y: float, w: float, h: float, text: str, edge: str = "black", face: str = "white", lw: float = 1.6, fontsize: float = 8.3) -> None:
        rect = Rectangle((x - 0.5 * w, y - 0.5 * h), w, h, linewidth=lw, edgecolor=edge, facecolor=face, zorder=4)
        ax.add_patch(rect)
        ax.text(x, y, text, ha="center", va="center", fontsize=fontsize, fontweight="bold", color=edge, zorder=5)

    def output_port(x: float, y: float, name: str, color: str) -> None:
        circ = Circle((x, y), 0.14, linewidth=1.9, edgecolor=color, facecolor="white", zorder=6)
        ax.add_patch(circ)
        ax.text(x + 0.22, y, name, ha="left", va="center", fontsize=8.2, fontweight="bold", color=color, zorder=7, bbox=dict(boxstyle="round,pad=0.08", facecolor="white", edgecolor="none", alpha=0.9))

    def arrow(x1: float, y1: float, x2: float, y2: float, color: str, lw: float = 1.7, ms: float = 10.5) -> None:
        arr = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=ms, linewidth=lw, color=color, shrinkA=0, shrinkB=0, zorder=3)
        ax.add_patch(arr)

    def line(x1: float, y1: float, x2: float, y2: float, color: str, lw: float = 1.7, alpha: float = 1.0) -> None:
        ax.plot([x1, x2], [y1, y2], color=color, linewidth=lw, alpha=alpha, zorder=2)

    def label(x: float, y: float, text: str, color: str, fontsize: float = 7.0, ha: str = "center", va: str = "center") -> None:
        ax.text(x, y, text, ha=ha, va=va, fontsize=fontsize, color=color, bbox=label_box, zorder=8)

    # Source and common raw RF-amplified optical rail.
    rectangle_node(0.95, 3.25, 1.28, 0.54, "NaD1RFA", edge="black", face="#f6f6f6", lw=1.7)
    bus_x = 2.85
    line(1.60, 3.25, bus_x, 3.25, "0.25", lw=2.0)
    line(bus_x, 1.05, bus_x, 5.75, "0.25", lw=2.2, alpha=0.88)
    ax.text(bus_x - 0.62, 2.25, "NaD1RFA\ncommon rail", ha="center", va="center", fontsize=7.2, color="0.25", bbox=label_box, zorder=8)

    # Wavemeter pickoff: no frequency shift.
    wav_color = node_color("NaD1Wavemeter")
    y = 1.55
    line(bus_x, y, 4.15, y, wav_color, lw=1.8, alpha=0.85)
    arrow(4.15, y, 4.45, y, wav_color, lw=1.8, ms=10)
    label(3.75, y + 0.24, "route", wav_color, fontsize=6.8)
    output_port(4.70, y, "NaD1Wavemeter", wav_color)

    # Lock path: NaD1RFA -> NaD1Lock_SPAO -> NaD1Lock.
    lock_components = FREQUENCY_GRAPH_EDGES["NaD1Lock"].components
    lock_color = node_color("NaD1Lock")
    y = 5.35
    line(bus_x, y, 4.05, y, lock_color, lw=1.8, alpha=0.82)
    arrow(4.05, y, 4.35, y, lock_color, lw=1.8, ms=10)
    label(4.05, y + 0.28, edge_label(model, lock_components), lock_color, fontsize=6.8)
    rectangle_node(4.90, y, 0.86, 0.46, component_short_label(lock_components[0]), edge=lock_color, face="white", lw=1.7)
    arrow(5.35, y, 6.10, y, lock_color, lw=1.8, ms=10)
    output_port(6.32, y, "NaD1Lock", lock_color)
    ax.text(7.28, y + 0.34, "locked to F=2 -> F'=1", ha="left", va="center", fontsize=8.0, fontweight="bold", color=lock_color, bbox=label_box, zorder=8)

    # Cooling/repump path: one shared Cool DPAO creates the carrier output.
    # The repump output is a +1 EOM sideband derived from the light after that same DPAO.
    cool_color = node_color("NaD1Cool")
    repump_color = node_color("NaD1Repump")
    cool_comp = ("nad1cool_DPAO_MHz",)
    eom_comp = ("nad1repump_EOM_pos_MHz",)

    y_cool = 3.55
    line(bus_x, y_cool, 4.15, y_cool, cool_color, lw=1.9)
    arrow(4.15, y_cool, 4.38, y_cool, cool_color, lw=1.9)
    label(4.05, y_cool + 0.27, edge_label(model, cool_comp), cool_color, fontsize=6.8)
    rectangle_node(4.92, y_cool, 0.86, 0.46, "DPAO", edge=cool_color, face="white", lw=1.7)

    # A short post-DPAO rail makes it clear that the carrier and the EOM sideband
    # are two optical frequency components derived after the same cooling shifter.
    post_x = 5.65
    line(5.37, y_cool, post_x, y_cool, cool_color, lw=1.9)
    line(post_x, y_cool - 0.95, post_x, y_cool + 0.35, "0.35", lw=1.6, alpha=0.85)
    ax.text(post_x - 0.36, y_cool - 0.32, "post-DPAO\nlight", ha="center", va="center", fontsize=6.8, color="0.35", bbox=label_box, zorder=8)

    # Carrier output branch.
    line(post_x, y_cool + 0.28, 6.28, y_cool + 0.28, cool_color, lw=1.8)
    arrow(6.28, y_cool + 0.28, 6.55, y_cool + 0.28, cool_color, lw=1.8)
    output_port(6.78, y_cool + 0.28, "NaD1Cool carrier", cool_color)

    # EOM sideband output branch, intentionally drawn below the carrier so the EOM
    # does not look like it comes after the NaD1Cool output port.
    y_repump = y_cool - 0.90
    line(post_x, y_repump, 6.28, y_repump, repump_color, lw=1.8)
    arrow(6.28, y_repump, 6.55, y_repump, repump_color, lw=1.8)
    label(6.25, y_repump + 0.30, edge_label(model, eom_comp), repump_color, fontsize=6.8)
    rectangle_node(7.10, y_repump, 0.92, 0.46, "EOM +SB", edge=repump_color, face="white", lw=1.7)
    arrow(7.58, y_repump, 8.50, y_repump, repump_color, lw=1.8)
    output_port(8.72, y_repump, "NaD1Repump", repump_color)

    path = " -> ".join(model.graph_path(selected_beam))
    ax.text(-0.12, -0.55, f"Selected path: {path}", fontsize=8.2, ha="left", va="bottom", bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="0.85", alpha=0.92), clip_on=False, zorder=10)

    fig.subplots_adjust(left=0.035, right=0.985, top=0.88, bottom=0.16)
    return fig


def parse_sidebar_float(raw: str, label: str, *, min_value: float | None = None) -> float:
    try:
        value = float(raw.strip())
    except ValueError:
        st.sidebar.error(f"{label} must be a number. Keeping its default value.")
        return float(DEFAULT_RF[label])
    if min_value is not None and value < min_value:
        st.sidebar.error(f"{label} must be >= {min_value:g}. Keeping its default value.")
        return float(DEFAULT_RF[label])
    return value


def build_model_from_sidebar() -> tuple[NaD1FrequencyModel, str]:
    st.sidebar.markdown("### Na D1 Frequency Settings")
    st.sidebar.caption(
        "Sodium D1 frequency graph. NaD1RFA is shifted by NaD1Lock_SPAO and the shifted light "
        "is locked exactly to F = 2 --> F' = 1. The repump output is the positive EOM sideband "
        "after the NaD1Cool DPAO."
    )

    selected_beam = st.sidebar.selectbox(
        "Selected beam",
        BEAM_ORDER,
        index=BEAM_ORDER.index("NaD1Cool"),
    )

    if "na_d1_rf_values" not in st.session_state:
        st.session_state.na_d1_rf_values = DEFAULT_RF.copy()

    if st.sidebar.button("Reset RF defaults"):
        st.session_state.na_d1_rf_values = DEFAULT_RF.copy()

    rf_values = {}
    st.sidebar.subheader("RF inputs")
    for key, default in DEFAULT_RF.items():
        current_value = float(st.session_state.na_d1_rf_values.get(key, default))
        raw = st.sidebar.text_input(
            pretty_rf_label(key),
            value=f"{current_value:.9g}",
            key=f"na_d1_rf_{key}",
        )
        rf_values[key] = parse_sidebar_float(raw, key, min_value=0.0)

    st.session_state.na_d1_rf_values = rf_values.copy()
    return NaD1FrequencyModel(rf_values), selected_beam


def main() -> None:
    model, selected_beam = build_model_from_sidebar()

    st.title(APP_TITLE)
    st.write(
        "Interactive Na D1 frequency bookkeeping for the NaCs 2.0 sodium system. "
        "The lock path shifts NaD1RFA by NaD1Lock_SPAO and pins that shifted light to F = 2 → F′ = 1. "
        "NaD1Repump is the positive EOM sideband after the NaD1Cool DPAO."
    )

    shifts = model.beam_shifts_from_narfa()
    axis_freqs = model.beam_axis_frequencies()
    detuning_rows = model.detuning_table(selected_beam)
    nearest_label, nearest_det = min(detuning_rows, key=lambda item: abs(item[1]))

    c1, c2, c3 = st.columns(3)
    c1.metric("Selected beam", selected_beam)
    c2.metric("Nearest detuning", f"{nearest_det:+.6f} MHz", nearest_label)
    c3.metric("Raw NaD1RFA from lock", f"{axis_freqs['NaD1RFA'] - LOCK_F2_TO_F1P_MHZ:+.3f} MHz", "relative to F=2 → F′=1")

    tab_plot, tab_tables, tab_model = st.tabs(["Plots", "Tables", "Model notes"])

    with tab_plot:
        show_plot_stack([
            make_level_figure(model, selected_beam),
            make_graph_figure(model, selected_beam),
        ])

    with tab_tables:
        st.subheader("Detunings from selected beam")
        df_det = pd.DataFrame(detuning_rows, columns=["Transition", "Detuning [MHz]"])
        df_det["abs detuning [MHz]"] = df_det["Detuning [MHz]"].abs()
        st.dataframe(
            df_det.sort_values("abs detuning [MHz]").drop(columns=["abs detuning [MHz]"]),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Computed beam shifts")
        df_shifts = pd.DataFrame(
            {
                "Beam": BEAM_ORDER,
                "Output/component": ["raw rail" if b == "NaD1RFA" else ("wavemeter pickoff" if b == "NaD1Wavemeter" else ("lock path" if b == "NaD1Lock" else ("repump sideband" if b == "NaD1Repump" else "cooling output"))) for b in BEAM_ORDER],
                "Shift from NaRFA [MHz]": [shifts[b] for b in BEAM_ORDER],
                "D1-axis frequency [MHz]": [axis_freqs[b] for b in BEAM_ORDER],
                "Detuning from F=2 -> F'=1 [MHz]": [axis_freqs[b] - LOCK_F2_TO_F1P_MHZ for b in BEAM_ORDER],
                "Path": [" -> ".join(model.graph_path(b)) for b in BEAM_ORDER],
            }
        )
        st.dataframe(df_shifts, use_container_width=True, hide_index=True)

    with tab_model:
        st.subheader("Lock point and D1 constants")
        st.code(
            f"D1 frequency = {D1_CENTER_THz:.7f} THz\n"
            f"lambda = {D1_WAVELENGTH_NM:.7f} nm\n"
            f"Gamma/2pi = {D1_LINEWIDTH_MHZ:.4f} MHz\n"
            f"ground split = {GROUND_SPLITTING_MHZ:.7f} MHz\n"
            f"lock reference = F=2 -> F'=1\n"
            f"lock transition plot frequency = {LOCK_F2_TO_F1P_MHZ:+.6f} MHz\n"
            f"NaD1RFA raw plot frequency = {model.narfa_raw_axis_frequency_mhz():+.6f} MHz\n"
            f"default NaD1RFA detuning from F=2 -> F'=1 = {-DEFAULT_RF['nad1lock_SPAO_MHz']:+.3f} MHz\n"
            f"NaD1 cool DPAO = {DEFAULT_RF['nad1cool_DPAO_MHz']:.3f} MHz\n"
            f"NaD1 repump EOM positive sideband = {DEFAULT_RF['nad1repump_EOM_pos_MHz']:.3f} MHz",
            language="text",
        )

        st.subheader("AOM metadata")
        aom_df = pd.DataFrame(
            [
                {
                    "key": key,
                    "label": aom.label,
                    "passes": aom.passes,
                    "order": aom.order,
                    "multiplier": aom.multiplier,
                }
                for key, aom in AOMS.items()
            ]
        )
        st.dataframe(aom_df, use_container_width=True, hide_index=True)

        st.subheader("EOM metadata")
        eom_df = pd.DataFrame(
            [
                {
                    "key": key,
                    "label": eom.label,
                    "sideband shown": "+1",
                    "multiplier": eom.multiplier,
                }
                for key, eom in EOMS.items()
            ]
        )
        st.dataframe(eom_df, use_container_width=True, hide_index=True)

        st.subheader("Directed frequency graph edges")
        edge_df = pd.DataFrame(
            [
                {"child node": child, "parent node": edge.parent, "components": " + ".join(edge.components) if edge.components else "route only"}
                for child, edge in FREQUENCY_GRAPH_EDGES.items()
            ]
        )
        st.dataframe(edge_df, use_container_width=True, hide_index=True)

        st.info(
            "To change this Na D1 system, edit na_d1_frequency_model.py: update DEFAULT_RF, "
            "AOMS, EOMS, FREQUENCY_GRAPH_EDGES, and BEAM_COLORS. The current lock convention keeps "
            "NaD1Lock exactly on F=2 -> F'=1 and moves the raw NaD1RFA frequency accordingly. "
            "NaD1Repump is the positive EOM sideband after the NaD1Cool DPAO."
        )


if __name__ == "__main__":
    main()
