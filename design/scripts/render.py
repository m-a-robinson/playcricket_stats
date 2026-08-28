"""
Render the ELPMCC design templates (design/templates/*.html) to PNG/PDF.

Demo mode (no arguments) renders all three templates against real figures
pulled from a locally-built SQLite store (see README "Basic usage") --
the memorable 2010 Failsworth Macedonia match, Ian Wade's career record,
and the 30-Aug-2025 Heywood result -- as a preview of the look, not a
finished data pipeline. A real pipeline would query sqlite_queries.py /
playcricket_scorecard.py directly into these same template variable
shapes (see the `demo_*()` functions below for the shape each template
expects) rather than hand-writing the dicts.

Usage:
    python3 design/scripts/render.py
"""
import argparse
from pathlib import Path

import jinja2
from playwright.sync_api import sync_playwright

DESIGN_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = DESIGN_DIR / "templates"
PREVIEWS_DIR = DESIGN_DIR / "previews"
CHROMIUM_PATH = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATES_DIR))


def render_html(template_name: str, context: dict) -> str:
    return env.get_template(template_name).render(**context)


def screenshot(html: str, out_png: Path, width: int, height: int, scale: float = 2.0):
    out_png.parent.mkdir(parents=True, exist_ok=True)
    tmp_html = out_png.with_suffix(".render.html")
    tmp_html.write_text(html)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROMIUM_PATH)
        page = browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=scale,
        )
        page.goto(tmp_html.as_uri())
        page.screenshot(path=str(out_png))
        browser.close()
    tmp_html.unlink()


def pdf(html: str, out_pdf: Path, page_format: str = "A4"):
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    tmp_html = out_pdf.with_suffix(".render.html")
    tmp_html.write_text(html)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROMIUM_PATH)
        page = browser.new_page()
        page.goto(tmp_html.as_uri())
        page.pdf(path=str(out_pdf), format=page_format, print_background=True)
        browser.close()
    tmp_html.unlink()


# ---------------------------------------------------------------------------
# Demo data -- pulled from a full.sqlite built per README "Basic usage",
# with play_cricket + cricketstatz + the scorebook source ingested and
# Ian Wade's three split identities merged per reconcile/decisions.yaml.
# ---------------------------------------------------------------------------

def demo_scorecard_context() -> dict:
    return {
        "match": {
            "title": "East Lancs Paper Mill CC v Failsworth Macedonia CC",
            "date": "11 July 2010",
            "venue": "Away",
            "competition": "League",
            "result": "East Lancs Paper Mill CC won by 236 runs",
            "totals": [
                {"name": "East Lancs Paper Mill", "score": "384-6 dec", "overs": "39.3"},
                {"name": "Failsworth Macedonia", "score": "148 all out", "overs": "29.1"},
            ],
            "innings": [
                {
                    "team": "East Lancs Paper Mill",
                    "score": "384-6 dec",
                    "batting": [
                        {"name": "A McCheyne", "how_out": "c", "runs": 0, "fours": 0, "sixes": 0, "featured": False},
                        {"name": "J Shiels", "how_out": "lbw", "runs": 9, "fours": 0, "sixes": 0, "featured": False},
                        {"name": "G Greaves", "how_out": "c", "runs": 170, "fours": 0, "sixes": 0, "featured": True},
                        {"name": "Ian Wade", "how_out": "b", "runs": 163, "fours": 0, "sixes": 0, "featured": True},
                        {"name": "G Wade", "how_out": "b", "runs": 2, "fours": 0, "sixes": 0, "featured": False},
                        {"name": "M Hay", "how_out": "not out", "runs": 0, "fours": 0, "sixes": 0, "featured": False},
                        {"name": "C Holt", "how_out": "b", "runs": 0, "fours": 0, "sixes": 0, "featured": False},
                        {"name": "S Keyworth", "how_out": "not out", "runs": 0, "fours": 0, "sixes": 0, "featured": False},
                    ],
                    "extras": "Extras 40 (b10 lb6 w24)  ·  Total 384-6 dec off 39.3 overs",
                },
                {
                    "team": "Failsworth Macedonia",
                    "score": "148 all out",
                    "batting": [
                        {"name": "A Shenton", "how_out": "c", "runs": 24, "fours": 5, "sixes": 0, "featured": False},
                        {"name": "L Maddocks", "how_out": "c", "runs": 51, "fours": 8, "sixes": 1, "featured": True},
                        {"name": "J Cassidy", "how_out": "run out", "runs": 0, "fours": 0, "sixes": 0, "featured": False},
                        {"name": "M Chambers", "how_out": "c", "runs": 24, "fours": 3, "sixes": 0, "featured": False},
                        {"name": "R Bellfield", "how_out": "b", "runs": 2, "fours": 2, "sixes": 0, "featured": False},
                        {"name": "L Phelan", "how_out": "c", "runs": 11, "fours": 1, "sixes": 0, "featured": False},
                        {"name": "D Rigney", "how_out": "c", "runs": 4, "fours": 1, "sixes": 0, "featured": False},
                        {"name": "D Marriott", "how_out": "c", "runs": 10, "fours": 1, "sixes": 1, "featured": False},
                    ],
                    "extras": "Extras 22 (b9 lb1 w12)  ·  Total 148 all out off 29.1 overs",
                },
            ],
            "highlight": (
                "<b>Gavin Greaves (170) and Ian Wade (163)</b> put on 339 for the "
                "3rd wicket &mdash; the record stand this archive has found so far."
            ),
        }
    }


def demo_career_context() -> dict:
    return {
        "player": {
            "name": "Ian Wade",
            "summary": "East Lancs Paper Mill CC · 1st &amp; 2nd XI · batting all-rounder",
            "tiles": [
                {"value": "264", "label": "Games"},
                {"value": "5,948", "label": "Runs"},
                {"value": "27.92", "label": "Average"},
                {"value": "188", "label": "Highest score"},
                {"value": "8", "label": "Hundreds"},
                {"value": "26", "label": "Fifties"},
                {"value": "183", "label": "Wickets"},
                {"value": "120", "label": "Catches"},
            ],
            "batting": {
                "innings": 248, "not_outs": 35, "runs": 5948,
                "average": 27.92, "highest": "188", "fifties": 26, "hundreds": 8,
            },
            "bowling": {
                "wickets": 183, "average": 15.08, "best": "8-13", "five_fors": 8,
            },
            "fielding": {"catches": 120, "run_outs": 13},
            "milestones": [
                {"headline": "188", "detail": "highest first-team score (Play-Cricket era)"},
                {"headline": "163", "detail": "v Failsworth Macedonia, 11 Jul 2010 — 339-run 3rd-wicket stand with Gavin Greaves (170)"},
                {"headline": "8 centuries, 26 half-centuries", "detail": "across 248 recorded innings"},
                {"headline": "183 wickets at 15.08", "detail": "including 8 five-wicket hauls"},
            ],
            "note": "Scorecard-only totals from the fully-reconciled store (all six sources merged per reconcile/decisions.yaml). Excludes NMCL season-aggregate residuals (+400 runs 2003, +403 2012, +518 2013, +6 wickets 2010 — see root README) not yet folded in by career(); cross-checked against a manually-compiled career line and found a small unresolved gap on runs/games (see README).",
        }
    }


def demo_social_context() -> dict:
    return {
        "card": {
            "competition": "Saturday league · 1st XI",
            "result_tag": "Won by 8 wickets",
            "headline": "ELPM blow away Heywood inside 26 overs",
            "date": "30 August 2025",
            "venue": "Home",
            "scores": [
                {"name": "Heywood CC", "score": "72 all out"},
                {"name": "East Lancs Paper Mill", "score": "75-2"},
            ],
            "performances": [
                {"name": "Louis Birmingham", "stat": "5-35", "detail": "10 overs, 2 maidens"},
                {"name": "Ian Wade", "stat": "43* (21)", "detail": "3 fours, 4 sixes"},
            ],
        }
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=["scorecard", "career", "social"], default=None)
    args = parser.parse_args()

    jobs = []
    if args.only in (None, "scorecard"):
        jobs.append(("scorecard_poster.html", demo_scorecard_context(), "scorecard_poster", "A4", None))
    if args.only in (None, "career"):
        jobs.append(("career_stats.html", demo_career_context(), "career_stats", "A4", None))
    if args.only in (None, "social"):
        jobs.append(("social_card.html", demo_social_context(), "social_card", None, (1080, 1080)))

    for template_name, context, out_stem, page_format, viewport in jobs:
        html = render_html(template_name, context)
        if page_format:
            out_pdf = PREVIEWS_DIR / f"{out_stem}.pdf"
            pdf(html, out_pdf, page_format=page_format)
            print(f"Wrote {out_pdf}")
            out_png = PREVIEWS_DIR / f"{out_stem}.png"
            screenshot(html, out_png, width=794, height=1123, scale=2.0)
            print(f"Wrote {out_png}")
        else:
            width, height = viewport
            out_png = PREVIEWS_DIR / f"{out_stem}.png"
            screenshot(html, out_png, width=width, height=height, scale=1.0)
            print(f"Wrote {out_png}")


if __name__ == "__main__":
    main()
