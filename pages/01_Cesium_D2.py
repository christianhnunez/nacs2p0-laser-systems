from __future__ import annotations

import io
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from matplotlib import rcParams
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch, Circle, Rectangle

from cs_frequency_model import (
    AOMS,
    APP_TITLE,
    BEAM_COLORS,
    BEAM_ORDER,
    D2_CENTER_THz,
    D2_LINEWIDTH_MHZ,
    D2_WAVELENGTH_NM,
    DEFAULT_RF,
    EXCITED_ENERGY_MHZ,
    FREQUENCY_GRAPH_EDGES,
    GROUND_GAP_VISUAL_MHZ,
    GROUND_SPLITTING_MHZ,
    GROUND_ENERGY_MHZ,
    LOCK_CO_23_MHZ,
    OPTICAL_GAP_VISUAL_MHZ,
    CsFrequencyModel,
)

st.set_page_config(page_title=APP_TITLE, layout="wide")

# Keep Matplotlib output as real SVG text where possible instead of converting
# every character to a filled path. This makes browser-rendered plots sharper
# on large/high-DPI lab displays.
rcParams["svg.fonttype"] = "path"
rcParams["font.family"] = "DejaVu Sans"

# Force a light-looking Streamlit UI even when the browser or OS is in dark mode.
# For a deployed app, the most complete version of this is also to add
# .streamlit/config.toml with [theme] base = "light".  This CSS keeps the
# single-file replacement workflow simple for local testing.
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
    """Convert a Matplotlib figure to raw SVG with text kept as SVG text."""
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
    """Show multiple SVG figures in one responsive component.

    Keeping both plots inside one HTML component prevents Streamlit from giving
    each plot an independently fixed-height iframe. The SVGs fill the available
    width, preserve their aspect ratios, and stay adjacent during window resize.
    """
    svgs = [figure_to_svg(fig) for fig in figures]
    total_height_px = 1180
    html = f"""
    <!doctype html>
    <html>
      <head>
        <style>
          html, body {{
            margin: 0;
            padding: 0;
            background: #ffffff;
            overflow: hidden;
          }}
          .plot-stack {{
            width: 100%;
            max-width: 100%;
            background: #ffffff;
            margin: 0;
            padding: 0;
            line-height: 0;
          }}
          .plot-frame {{
            width: 100%;
            margin: 0 0 14px 0;
            padding: 0;
            background: #ffffff;
            line-height: 0;
          }}
          .plot-frame svg {{
            width: 100%;
            height: auto;
            display: block;
            background: #ffffff;
          }}
        </style>
      </head>
      <body>
        <div class="plot-stack">
          <div class="plot-frame">{svgs[0]}</div>
          <div class="plot-frame">{svgs[1]}</div>
        </div>
      </body>
    </html>
    """
    components.html(html, height=total_height_px, scrolling=False)

def pretty_rf_label(key: str) -> str:
    label = key.replace("_MHz", "").replace("_", " ")
    if key in AOMS:
        aom = AOMS[key]
        label += f" ({aom.type_label}, {aom.order_label})"
    return label


def edge_label(model: CsFrequencyModel, component: str | None) -> str:
    if component is None:
        return "route"
    if component in AOMS:
        aom = AOMS[component]
        rf_mhz = model.rf_values[component]
        shift_mhz = model.component_shift_mhz(component)
        return f"{aom.multiplier:+d} x {rf_mhz:.3g} = {shift_mhz:+.1f} MHz"
    return f"{model.component_shift_mhz(component):+.1f} MHz"


def aom_short_label(component: str | None) -> str:
    if component in AOMS:
        return AOMS[component].type_label
    return str(component)


def make_level_figure(model: CsFrequencyModel, selected_beam: str) -> Figure:
    fig = Figure(figsize=(10.2, 6.0), dpi=180, facecolor=LIGHT_PANEL_BG)
    ax = fig.add_subplot(111, facecolor=LIGHT_PANEL_BG)
    ax.set_title("Cs D2 level diagram", fontsize=15)
    ax.set_ylabel("Frequency [MHz]", fontsize=13)
    ax.set_xlabel("")
    #ax.grid(True, axis="y", alpha=0.18, color=LIGHT_GRID)

    label_box = dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="none", alpha=0.88)
    level_box = dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.94)

    beams = model.beam_axis_frequencies()
    ground_plot_energy = {4: 0.0, 3: -GROUND_GAP_VISUAL_MHZ}
    excited_reference_actual = min(EXCITED_ENERGY_MHZ.values())
    excited_plot_energy = {
        fp: OPTICAL_GAP_VISUAL_MHZ + (val - excited_reference_actual)
        for fp, val in EXCITED_ENERGY_MHZ.items()
    }

    x_positions = {beam: 0.8 + 1.18 * i for i, beam in enumerate(BEAM_ORDER)}
    xmin = min(x_positions.values()) - 0.60
    xmax = max(x_positions.values()) + 0.60
    level_label_x = xmax + 0.34

    for f in (4, 3):
        y = ground_plot_energy[f]
        ax.hlines(y, xmin, xmax, color="0.12", linewidth=2.6, zorder=1)
        ax.text(
            level_label_x,
            y,
            rf"$6^2\mathrm{{S}}_{{1/2}};\ F={f}$",
            ha="left",
            va="center",
            fontsize=12,
            color="0.12",
            bbox=level_box,
            zorder=8,
            clip_on=False,
        )

    for fp in (2, 3, 4, 5):
        y = excited_plot_energy[fp]
        ax.hlines(y, xmin, xmax, color="0.22", linewidth=2.0, zorder=1)
        ax.text(
            level_label_x,
            y,
            rf"$6^2\mathrm{{P}}_{{3/2}};\ F'={fp}$",
            ha="left",
            va="center",
            fontsize=12,
            color="0.22",
            bbox=level_box,
            zorder=8,
            clip_on=False,
        )

    ax.text(xmin + 0.05, 0.5 * (ground_plot_energy[4] + excited_plot_energy[2]),
            "compressed\nlevel gaps", ha="left", va="center", fontsize=8, color="0.35",
            bbox=label_box, zorder=8)
    ax.text(xmin + 0.05, 0.5 * (ground_plot_energy[3] + ground_plot_energy[4]),
            f"true F=3 to F=4 gap = {GROUND_SPLITTING_MHZ:.3f} MHz",
            ha="left", va="center", fontsize=8, color="0.35", bbox=label_box, zorder=8)

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

        ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle="-|>", mutation_scale=mutation,
                                     linewidth=lw, color=color, alpha=0.92, shrinkA=0, shrinkB=0))
        ax.plot([x], [y0], marker="o", color=color, markersize=4.5, zorder=5)
        ax.plot([x], [y1], marker="o", color=color, markersize=7 if beam == selected_beam else 5, zorder=6)
        ax.plot([x - 0.14, x + 0.14], [target_y, target_y], color=color, linewidth=1.2, alpha=0.45)
        ax.plot([x + 0.14, x + 0.14], [target_y, y1], color=color, linewidth=1.0, alpha=0.35)

        label = f"{beam}\nF={ground_f} → F′={excited_f}\n{det:+.1f} MHz"
        va = "bottom" if y1 >= y0 else "top"
        stagger = {0: 132, 1: 42, 2: 222}[BEAM_ORDER.index(beam) % 3]
        if beam in ("CsDBR1", "OP"):
            stagger = -96
            va = "top"
        ax.text(x, y1 + stagger, label, ha="center", va=va, fontsize=7.8, color=color,
                bbox=label_box, zorder=10, linespacing=1.05)

    ax.set_xticks([x_positions[b] for b in BEAM_ORDER])
    ax.set_xticklabels(BEAM_ORDER, rotation=35, ha="right")

    all_y = list(ground_plot_energy.values()) + list(excited_plot_energy.values())
    for optical_offset in beams.values():
        _gf, ef, det = model.nearest_transition_for_frequency(optical_offset)
        all_y.append(excited_plot_energy[ef] + det)
    ymin, ymax = min(all_y), max(all_y)
    pad = max(450.0, 0.06 * (ymax - ymin))
    ax.set_ylim(ymin - pad, ymax + pad)
    ax.set_xlim(xmin, xmax + 1.75)
   
   # Clean level-diagram frame: keep only physical-looking x/y axes.
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)
    ax.tick_params(axis="both", direction="out")

    fig.tight_layout()

    return fig


def make_graph_figure(model: CsFrequencyModel, selected_beam: str) -> Figure:
    fig = Figure(figsize=(10.2, 3.45), dpi=180, facecolor=LIGHT_PANEL_BG)
    ax = fig.add_subplot(111, facecolor=LIGHT_PANEL_BG)
    ax.set_title("Laser system directed graph", fontsize=13)
    ax.set_axis_off()
    ax.set_xlim(-0.2, 10.2)
    ax.set_ylim(-0.55, 7.1)
    label_box = dict(boxstyle="round,pad=0.16", facecolor="white", edgecolor="none", alpha=0.9)

    def node_color(node: str) -> str:
        return BEAM_COLORS.get(node, "black")

    def rectangle_node(x: float, y: float, w: float, h: float, text: str,
                       edge: str = "black", face: str = "white", lw: float = 1.6,
                       fontsize: float = 8.8) -> None:
        rect = Rectangle((x - 0.5 * w, y - 0.5 * h), w, h,
                         linewidth=lw, edgecolor=edge, facecolor=face, zorder=4)
        ax.add_patch(rect)
        ax.text(x, y, text, ha="center", va="center", fontsize=fontsize,
                fontweight="bold", color=edge, zorder=5)

    def output_port(x: float, y: float, name: str, color: str) -> None:
        circ = Circle((x, y), 0.15, linewidth=2.0, edgecolor=color, facecolor="white", zorder=6)
        ax.add_patch(circ)
        ax.text(x + 0.24, y, name, ha="left", va="center", fontsize=9.0,
                fontweight="bold", color=color, zorder=7,
                bbox=dict(boxstyle="round,pad=0.08", facecolor="white", edgecolor="none", alpha=0.9))

    def arrow(x1: float, y1: float, x2: float, y2: float, color: str,
              lw: float = 1.8, ms: float = 11.5) -> None:
        arr = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=ms,
                              linewidth=lw, color=color, shrinkA=0, shrinkB=0, zorder=3)
        ax.add_patch(arr)

    def line(x1: float, y1: float, x2: float, y2: float, color: str,
             lw: float = 1.7, alpha: float = 1.0) -> None:
        ax.plot([x1, x2], [y1, y2], color=color, linewidth=lw, alpha=alpha, zorder=2)

    def label(x: float, y: float, text: str, color: str, fontsize: float = 7.6,
              ha: str = "center", va: str = "center") -> None:
        ax.text(x, y, text, ha=ha, va=va, fontsize=fontsize, color=color, bbox=label_box, zorder=8)

    rectangle_node(0.85, 5.55, 1.15, 0.52, "CsDBR1", edge="black", face="#f6f6f6", lw=1.7)
    rectangle_node(0.85, 2.15, 1.15, 0.52, "CsDBR2", edge="black", face="#f6f6f6", lw=1.7)
    rectangle_node(2.55, 2.15, 1.20, 0.50, "CsTA", edge="0.55", face="#f8f8f8", lw=1.5)

    beat_edge = FREQUENCY_GRAPH_EDGES["CsDBR2"]
    line(0.85, 5.29, 0.85, 2.52, "0.45", lw=1.7, alpha=0.9)
    arrow(0.85, 2.52, 0.85, 2.41, "0.45", lw=1.7, ms=10)
    label(0.98, 3.75, f"beat {edge_label(model, beat_edge.component)}", "0.45", fontsize=7.4, ha="left")
    arrow(1.43, 2.15, 1.95, 2.15, "0.45", lw=2.0)

    source_branches = {
        "Repump": {"y": 6.35, "component": FREQUENCY_GRAPH_EDGES["Repump"].component},
        "OP": {"y": 5.10, "component": FREQUENCY_GRAPH_EDGES["OP"].component},
    }
    for child, cfg in source_branches.items():
        y = cfg["y"]
        comp = cfg["component"]
        color = node_color(child)
        line(1.43, 5.55, 1.80, 5.55, color, lw=1.9)
        line(1.80, 5.55, 1.80, y, color, lw=1.9)
        arrow(1.80, y, 2.70, y, color, lw=1.9)
        label(2.18, y + 0.24, edge_label(model, comp), color, fontsize=7.2)
        rectangle_node(3.35, y, 0.86, 0.46, aom_short_label(comp), edge=color, face="white", lw=1.7)
        arrow(3.80, y, 4.55, y, color, lw=1.9)
        output_port(4.75, y, child, color)

    bus_x = 4.25
    line(3.15, 2.15, bus_x, 2.15, "0.45", lw=2.0)
    line(bus_x, 0.55, bus_x, 4.55, "0.25", lw=2.2, alpha=0.88)
    ax.text(bus_x - 0.58, 3.08, "CsTA common rail", ha="center", va="center", fontsize=7.5,
            color="0.25", bbox=label_box, zorder=8)

    ta_branches = {
        "SMALL_BEAM": {"y": 4.35, "component": FREQUENCY_GRAPH_EDGES["SMALL_BEAM"].component},
        "PUSH": {"y": 3.45, "component": FREQUENCY_GRAPH_EDGES["PUSH"].component},
        "3DMOT": {"y": 2.55, "component": FREQUENCY_GRAPH_EDGES["3DMOT"].component},
        "2DMOT": {"y": 1.65, "component": FREQUENCY_GRAPH_EDGES["2DMOT"].component},
        "dRSC": {"y": 0.75, "component": FREQUENCY_GRAPH_EDGES["dRSC"].component},
    }
    for child, cfg in ta_branches.items():
        y = cfg["y"]
        comp = cfg["component"]
        color = node_color(child)
        line(bus_x, y, 5.45, y, color, lw=1.9)
        arrow(5.45, y, 5.65, y, color, lw=1.9)
        label(5.08, y + 0.22, edge_label(model, comp), color, fontsize=7.2)
        rectangle_node(6.25, y, 0.86, 0.46, aom_short_label(comp), edge=color, face="white", lw=1.7)
        arrow(6.70, y, 7.70, y, color, lw=1.9)
        output_port(7.92, y, child, color)

    path = " -> ".join(model.graph_path(selected_beam))
    ax.text(-0.12, -0.38, f"Selected path: {path}", fontsize=8.5, ha="left", va="bottom",
            bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="0.85", alpha=0.92),
            clip_on=False, zorder=10)
    fig.subplots_adjust(left=0.035, right=0.985, top=0.90, bottom=0.16)
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


def build_model_from_sidebar() -> tuple[CsFrequencyModel, str]:
    st.sidebar.markdown("### NaCs 2.0 Frequency Settings")
    st.sidebar.caption(
        "Cesium D2 frequency graph. Enter AOM RF magnitudes in MHz; AOM +1/-1 order is encoded "
        "in the AOMs metadata near the top of cs_frequency_model.py. We assume CsDBR1 is locked "
        "to F = 3 --> F' = CO(2, 3)."
    )

    selected_beam = st.sidebar.selectbox(
        "Selected beam",
        BEAM_ORDER,
        index=BEAM_ORDER.index("2DMOT"),
    )

    if "rf_values" not in st.session_state:
        st.session_state.rf_values = DEFAULT_RF.copy()

    if st.sidebar.button("Reset RF defaults"):
        st.session_state.rf_values = DEFAULT_RF.copy()

    rf_values = {}
    st.sidebar.subheader("RF inputs")
    for key, default in DEFAULT_RF.items():
        # Use text inputs instead of st.number_input so Streamlit does not render the
        # built-in +/- steppers. f_CsREF is allowed to be general. AOM RFs are
        # magnitudes, so they must be non-negative; the +/- diffraction order is
        # encoded in the AOMS metadata.
        min_value = None if key == "f_CsREF_MHz" else 0.0
        current_value = float(st.session_state.rf_values.get(key, default))
        raw = st.sidebar.text_input(
            pretty_rf_label(key),
            value=f"{current_value:.9g}",
            key=f"rf_{key}",
        )
        rf_values[key] = parse_sidebar_float(raw, key, min_value=min_value)

    st.session_state.rf_values = rf_values.copy()
    return CsFrequencyModel(rf_values), selected_beam


def main() -> None:
    model, selected_beam = build_model_from_sidebar()

    st.title(APP_TITLE)
    st.write(
        "Interactive Cs D2 frequency bookkeeping for the NaCs 2.0 cesium system. "
        "The directed graph and AOM orders live in `cs_frequency_model.py`; the sidebar controls only the RF magnitudes."
    )

    shifts = model.beam_shifts_from_dbr1()
    axis_freqs = model.beam_axis_frequencies()
    detuning_rows = model.detuning_table(selected_beam)
    nearest_label, nearest_det = min(detuning_rows, key=lambda item: abs(item[1]))

    c1, c2 = st.columns(2)
    c1.metric("Selected beam", selected_beam)
    c2.metric("Nearest detuning", f"{nearest_det:+.6f} MHz", nearest_label)

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
        st.dataframe(df_det.sort_values("abs detuning [MHz]").drop(columns=["abs detuning [MHz]"]),
                     use_container_width=True, hide_index=True)

        st.subheader("Computed beam shifts")
        df_shifts = pd.DataFrame({
            "Beam": BEAM_ORDER,
            "Shift from CsDBR1 [MHz]": [shifts[b] for b in BEAM_ORDER],
            "D2-axis frequency [MHz]": [axis_freqs[b] for b in BEAM_ORDER],
            "Path": [" -> ".join(model.graph_path(b)) for b in BEAM_ORDER],
        })
        st.dataframe(df_shifts, use_container_width=True, hide_index=True)

    with tab_model:
        st.subheader("Lock point and D2 constants")
        st.code(
            f"D2 frequency = {D2_CENTER_THz:.8f} THz\n"
            f"lambda = {D2_WAVELENGTH_NM:.8f} nm\n"
            f"Gamma/2pi = {D2_LINEWIDTH_MHZ:.4f} MHz\n"
            f"ground split = {GROUND_SPLITTING_MHZ:.6f} MHz\n"
            f"CsDBR1 lock = F=3 -> CO(2',3')\n"
            f"lock plot frequency = {LOCK_CO_23_MHZ:+.6f} MHz\n"
            f"CsDBR2 beat = -88.7454545454*f_CsREF = {model.beat_offset_mhz():+.6f} MHz",
            language="text",
        )
        st.subheader("AOM metadata")
        aom_df = pd.DataFrame([
            {
                "key": key,
                "label": aom.label,
                "passes": aom.passes,
                "order": aom.order,
                "multiplier": aom.multiplier,
            }
            for key, aom in AOMS.items()
        ])
        st.dataframe(aom_df, use_container_width=True, hide_index=True)

        st.subheader("Directed frequency graph edges")
        edge_df = pd.DataFrame([
            {"child node": child, "parent node": edge.parent, "component": edge.component or "route only"}
            for child, edge in FREQUENCY_GRAPH_EDGES.items()
        ])
        st.dataframe(edge_df, use_container_width=True, hide_index=True)

        st.info(
            "To add a new output port, edit cs_frequency_model.py: add any new RF magnitude to DEFAULT_RF, "
            "add AOM metadata if needed, then add one edge to FREQUENCY_GRAPH_EDGES."
        )


if __name__ == "__main__":
    main()
