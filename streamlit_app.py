import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Laser System Home",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Keep the landing page minimal and white, and hide Streamlit navigation chrome.
st.markdown(
    """
    <style>
    :root { color-scheme: light; }

    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background: #ffffff !important;
        color: #000000 !important;
    }

    [data-testid="stSidebar"],
    [data-testid="collapsedControl"],
    header[data-testid="stHeader"],
    footer {
        display: none !important;
    }

    .block-container {
        padding: 1.25rem 1.75rem 0.75rem 1.75rem !important;
        max-width: 1220px !important;
        margin: 0 auto !important;
    }

    /* Native Streamlit page links, styled to match the mockup buttons. */
    div[data-testid="stPageLink"] a {
        width: 258px !important;
        min-height: 58px !important;
        border: 2px solid #000000 !important;
        border-radius: 11px !important;
        background: #d4d4d4 !important;
        color: #000000 !important;
        text-decoration: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-sizing: border-box !important;
        font-size: 24px !important;
        font-weight: 750 !important;
        box-shadow: 0 2px 0 rgba(0,0,0,0.42) !important;
        transition: transform 140ms ease, filter 140ms ease, box-shadow 140ms ease !important;
    }

    div[data-testid="stPageLink"] a:hover {
        transform: translateY(-2px) !important;
        filter: brightness(1.045) !important;
        box-shadow: 0 5px 0 rgba(0,0,0,0.36) !important;
        color: #000000 !important;
    }

    div[data-testid="stPageLink"] a,
    div[data-testid="stPageLink"] a:visited,
    div[data-testid="stPageLink"] a:hover,
    div[data-testid="stPageLink"] a:active,
    div[data-testid="stPageLink"] a *,
    div[data-testid="stPageLink"] p,
    div[data-testid="stPageLink"] span {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    div[data-testid="stPageLink"] p {
        font-size: 24px !important;
        font-weight: 750 !important;
    }

    .nav-row {
        margin-top: -0.35rem;
    }

    @media (max-width: 900px) {
        .block-container {
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }
        div[data-testid="stPageLink"] a {
            width: 100% !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Put the moving-atom artwork in a Streamlit component instead of raw page markdown.
# This avoids the failure mode where the browser shows custom HTML/CSS as text.
components.html(
    """
    <!doctype html>
    <html>
    <head>
    <meta charset="utf-8" />
    <style>
        :root { color-scheme: light; }
        html, body {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: visible;
            background: #ffffff;
            color: #000000;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        .stage {
            position: relative;
            width: min(1180px, 100vw);
            height: 625px;
            margin: 0 auto;
            background: #ffffff;
        }

        .title {
            position: absolute;
            top: 10px;
            left: 4px;
            font-size: clamp(28px, 3vw, 36px);
            font-weight: 500;
            letter-spacing: -0.04em;
            white-space: nowrap;
        }

        .atom-group {
            position: absolute;
        }

        .na-group {
            width: 420px;
            height: 340px;
            left: calc(50% - 540px);
            top: 118px;
        }

        .cs-group {
            width: 590px;
            height: 450px;
            left: calc(50% - 55px);
            top: 74px;
        }

        .atom {
            position: absolute;
            border-radius: 50%;
            box-sizing: border-box;
            display: flex;
            align-items: center;
            justify-content: center;
            user-select: none;
        }

        .main-atom {
            z-index: 5;
            border: 4px solid #000000;
            font-weight: 500;
            letter-spacing: -0.04em;
            box-shadow: 0 10px 26px rgba(0,0,0,0.055);
        }

        .main-na {
            width: 106px;
            height: 106px;
            left: 170px;
            top: 118px;
            background: #ff8500;
            font-size: 39px;
        }

        .main-cs {
            width: 190px;
            height: 190px;
            left: 258px;
            top: 126px;
            background: #3fa2ff;
            font-size: 52px;
        }

        .satellite {
            z-index: 2;
            border: 4px solid rgba(120, 120, 120, 0.62);
            opacity: 0.80;
            filter: saturate(0.95);
            will-change: transform;
        }

        .na-satellite {
            width: 104px;
            height: 104px;
            background: rgba(255, 196, 150, 0.62);
        }

        .cs-satellite {
            width: 190px;
            height: 190px;
            background: rgba(166, 214, 255, 0.55);
        }

        .na-s1 { left: 52px;  top: 92px;  animation: naFloat1 4.2s ease-in-out infinite; }
        .na-s2 { left: 135px; top: 10px;  animation: naFloat2 4.6s ease-in-out infinite; }
        .na-s3 { left: 260px; top: 72px;  animation: naFloat3 4.3s ease-in-out infinite; }
        .na-s4 { left: 84px;  top: 214px; animation: naFloat4 4.9s ease-in-out infinite; }
        .na-s5 { left: 260px; top: 196px; animation: naFloat5 4.4s ease-in-out infinite; }

        .cs-s1 { left: 98px;  top: 36px;  animation: csFloat1 4.9s ease-in-out infinite; }
        .cs-s2 { left: 404px; top: 6px;   animation: csFloat2 5.1s ease-in-out infinite; }
        .cs-s3 { left: 142px; top: 238px; animation: csFloat3 5.0s ease-in-out infinite; }
        .cs-s4 { left: 386px; top: 220px; animation: csFloat4 5.4s ease-in-out infinite; }

        @keyframes naFloat1 {
            0%,100% { transform: translate(0,0) scale(1); }
            50% { transform: translate(-30px, 23px) scale(1.03); }
        }
        @keyframes naFloat2 {
            0%,100% { transform: translate(0,0) scale(1); }
            50% { transform: translate(25px, -33px) scale(0.97); }
        }
        @keyframes naFloat3 {
            0%,100% { transform: translate(0,0) scale(1); }
            50% { transform: translate(36px, 21px) scale(1.025); }
        }
        @keyframes naFloat4 {
            0%,100% { transform: translate(0,0) scale(1); }
            50% { transform: translate(-28px, 36px) scale(0.975); }
        }
        @keyframes naFloat5 {
            0%,100% { transform: translate(0,0) scale(1); }
            50% { transform: translate(31px, -28px) scale(1.025); }
        }

        @keyframes csFloat1 {
            0%,100% { transform: translate(0,0) scale(1); }
            50% { transform: translate(-37px, -25px) scale(1.022); }
        }
        @keyframes csFloat2 {
            0%,100% { transform: translate(0,0) scale(1); }
            50% { transform: translate(36px, -30px) scale(0.978); }
        }
        @keyframes csFloat3 {
            0%,100% { transform: translate(0,0) scale(1); }
            50% { transform: translate(-33px, 37px) scale(1.018); }
        }
        @keyframes csFloat4 {
            0%,100% { transform: translate(0,0) scale(1); }
            50% { transform: translate(38px, 30px) scale(0.982); }
        }

        @media (max-width: 900px) {
            .stage {
                height: 850px;
            }
            .title {
                left: 16px;
            }
            .na-group {
                left: calc(50% - 210px);
                top: 118px;
            }
            .cs-group {
                left: calc(50% - 295px);
                top: 410px;
            }
        }
    </style>
    </head>
    <body>
        <main class="stage" aria-label="NaCs 2.0 Laser Systems landing artwork">
            <div class="title">NaCs 2.0 Laser Systems</div>

            <section class="atom-group na-group" aria-label="Sodium atom graphic">
                <div class="atom satellite na-satellite na-s1"></div>
                <div class="atom satellite na-satellite na-s2"></div>
                <div class="atom satellite na-satellite na-s3"></div>
                <div class="atom satellite na-satellite na-s4"></div>
                <div class="atom satellite na-satellite na-s5"></div>
                <div class="atom main-atom main-na">Na</div>
            </section>

            <section class="atom-group cs-group" aria-label="Cesium atom graphic">
                <div class="atom satellite cs-satellite cs-s1"></div>
                <div class="atom satellite cs-satellite cs-s2"></div>
                <div class="atom satellite cs-satellite cs-s3"></div>
                <div class="atom satellite cs-satellite cs-s4"></div>
                <div class="atom main-atom main-cs">Cs</div>
            </section>
        </main>
    </body>
    </html>
    """,
    height=650,
    scrolling=False,
)

# Reliable native Streamlit navigation. The buttons sit below the artwork but are
# still centered under their corresponding species. This avoids custom JS routing.
st.markdown('<div class="nav-row">', unsafe_allow_html=True)
left_pad, na_col, middle_gap, cs_col, right_pad = st.columns([1.0, 1.35, 1.9, 1.35, 1.0])

with na_col:
    st.page_link("pages/03_Sodium_D1.py", label="Na D1 System")
    st.page_link("pages/02_Sodium_D2.py", label="Na D2 System")

with cs_col:
    st.page_link("pages/01_Cesium_D2.py", label="Cs D2 System")

st.markdown('</div>', unsafe_allow_html=True)
