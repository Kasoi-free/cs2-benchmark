"""ODS spreadsheet generation module."""
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

# ODS namespace constants
NS_TABLE = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
NS_TEXT = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
NS_OFFICE = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
NS_STYLE = "urn:oasis:names:tc:opendocument:xmlns:style:1.0"
NS_NUMBER = "urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0"
NS_CALC = "urn:oasis:names:tc:opendocument:xmlns:calculation:1.0"
NS_SVG = "http://www.w3.org/2000/svg"
NS_MANIFEST = "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
NS_FO = "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"

ET.register_namespace("office", NS_OFFICE)
ET.register_namespace("table", NS_TABLE)
ET.register_namespace("text", NS_TEXT)
ET.register_namespace("style", NS_STYLE)
ET.register_namespace("number", NS_NUMBER)
ET.register_namespace("calcext", NS_CALC)
ET.register_namespace("svg", NS_SVG)
ET.register_namespace("manifest", NS_MANIFEST)
ET.register_namespace("fo", NS_FO)


def ns(tag: str, namespace: str) -> str:
    return f"{{{namespace}}}{tag}"


def el(parent: ET.Element, tag: str, namespace: str, attrs: dict | None = None, text: str | None = None) -> ET.Element:
    e = ET.SubElement(parent, ns(tag, namespace))
    if attrs:
        for k, v in attrs.items():
            e.set(k, v)
    if text is not None:
        e.text = text
    return e


# --- Cell helpers ---

def _add_text_cell(parent: ET.Element, text: str, style: str | None = None) -> ET.Element:
    O, T, X = NS_OFFICE, NS_TABLE, NS_TEXT
    attrs = {ns("value-type", O): "string"}
    if style:
        attrs[ns("style-name", T)] = style
    cell = el(parent, "table-cell", T, attrs)
    el(cell, "p", X, text=text)
    return cell


def _add_num_cell(parent: ET.Element, text: str, value: float, style: str | None = None) -> ET.Element:
    O, T, X = NS_OFFICE, NS_TABLE, NS_TEXT
    attrs = {ns("value-type", O): "float", ns("value", O): str(value)}
    if style:
        attrs[ns("style-name", T)] = style
    cell = el(parent, "table-cell", T, attrs)
    el(cell, "p", X, text=text)
    return cell


def _add_pct_cell(parent: ET.Element, text: str, value: float, formula: str, style: str = "ce9") -> ET.Element:
    O, T, X = NS_OFFICE, NS_TABLE, NS_TEXT
    attrs = {
        ns("formula", T): formula,
        ns("value-type", O): "percentage",
        ns("value", O): str(value),
        ns("style-name", T): style,
    }
    cell = el(parent, "table-cell", T, attrs)
    el(cell, "p", X, text=text)
    return cell


def _add_empty_cell(parent: ET.Element, style: str | None = None, repeat: int = 1) -> ET.Element:
    O, T = NS_OFFICE, NS_TABLE
    attrs: dict[str, str] = {}
    if style:
        attrs[ns("style-name", T)] = style
    if repeat > 1:
        attrs[ns("number-columns-repeated", T)] = str(repeat)
    return el(parent, "table-cell", T, attrs)


# --- ODS State ---

class ODSState:
    """Holds accumulated benchmark results for incremental ODS writes."""

    def __init__(self, settings_list: list[dict], output_path: Path) -> None:
        self.settings_list = settings_list
        self.baseline: dict | None = None
        self.variants: dict[str, dict[str, dict]] = {}
        self.max_quality: dict | None = None
        self.output_path = output_path

    def update_baseline(self, data: dict) -> None:
        self.baseline = data

    def update_variant(self, name: str, variant: str, data: dict, baseline: dict | None) -> None:
        if name not in self.variants:
            self.variants[name] = {}
        self.variants[name][variant] = data

    def update_max_quality(self, data: dict, baseline: dict | None) -> None:
        self.max_quality = data


def init_ods(settings_list: list[dict], output_path: Path) -> ODSState:
    return ODSState(settings_list, output_path)


def update_ods_baseline(state: ODSState, data: dict) -> None:
    state.update_baseline(data)


def update_ods_variant(state: ODSState, name: str, variant: str, data: dict, baseline: dict | None) -> None:
    state.update_variant(name, variant, data, baseline)


def update_ods_max_quality(state: ODSState, data: dict, baseline: dict | None) -> None:
    state.update_max_quality(data, baseline)


# --- Styles ---

def _build_styles(auto_styles: Any = None) -> str:
    return """\
<style:style style:name="ce1" style:family="table-cell" style:parent-style-name="Default">
  <style:table-cell-properties style:wrap-option="wrap" style:vertical-align="automatic" />
</style:style>
<style:style style:name="ce2" style:family="table-cell" style:parent-style-name="Default">
  <style:table-cell-properties style:wrap-option="wrap" />
</style:style>
<style:style style:name="ce7" style:family="table-cell" style:parent-style-name="Default">
  <style:table-cell-properties style:wrap-option="wrap" />
  <style:text-properties style:font-weight="bold" />
</style:style>
<style:style style:name="ce8" style:family="table-cell" style:parent-style-name="Default">
  <style:table-cell-properties style:wrap-option="wrap" />
  <style:text-properties style:font-weight="bold" />
</style:style>
<style:style style:name="ce9" style:family="table-cell" style:parent-style-name="Default">
  <style:table-cell-properties style:data-style-name="N11" />
</style:style>
<style:style style:name="ce10" style:family="table-cell" style:parent-style-name="Default">
  <style:table-cell-properties style:data-style-name="N11" />
</style:style>
<style:style style:name="co1" style:family="table-column">
  <style:table-column-properties style:break-before="auto" style:column-width="0.8917in" />
</style:style>
<style:style style:name="co2" style:family="table-column">
  <style:table-column-properties style:break-before="auto" style:column-width="0.6665in" />
</style:style>
<style:style style:name="co_pct" style:family="table-column">
  <style:table-column-properties style:break-before="auto" style:column-width="0.6665in" style:data-style-name="N11" />
</style:style>
<style:style style:name="ta1" style:family="table" style:master-page-name="Standard">
  <table:table-properties table:display="true" table:writing-mode="lr-tb" />
</style:style>
<number:percentage-style style:name="N11">
  <number:number number:decimal-places="2" number:min-decimal-places="2" number:min-integer-digits="1" />
  <number:text>%</number:text>
</number:percentage-style>"""


# --- Main sheet ---

def _build_main_sheet(table: ET.Element, state: ODSState) -> None:
    O, T, X = NS_OFFICE, NS_TABLE, NS_TEXT
    baseline = state.baseline
    variants = state.variants
    max_quality = state.max_quality
    settings_list = state.settings_list

    base_fps = baseline["averageFps"] if baseline else 0

    # Row 1: BASE header
    row1 = el(table, "table-row", T)
    _add_text_cell(row1, "BASE", "ce1")
    if base_fps > 0:
        _add_num_cell(row1, str(int(base_fps)), base_fps, "ce1")
    else:
        _add_empty_cell(row1, "ce1")
    _add_empty_cell(row1, "ce1", 4)
    _add_empty_cell(row1)

    # Row 2: framesRendered (baseline)
    row2 = el(table, "table-row", T)
    _add_text_cell(row2, "framesRendered", "ce2")
    if baseline:
        fr = baseline.get("framesRendered", 0)
        _add_num_cell(row2, str(fr), float(fr), "ce1")
    else:
        _add_empty_cell(row2, "ce1")
    _add_empty_cell(row2, "ce1", 4)
    _add_empty_cell(row2)
    _add_empty_cell(row2)

    # Row 3: gpuFps avg (baseline)
    row3 = el(table, "table-row", T)
    _add_text_cell(row3, "gpuFps avg", "ce2")
    if baseline:
        ga = baseline.get("gpuFpsAvg", 0)
        _add_num_cell(row3, f"{ga:.1f}", float(ga), "ce1")
    else:
        _add_empty_cell(row3, "ce1")
    _add_empty_cell(row3, "ce1", 4)
    _add_empty_cell(row3)
    _add_empty_cell(row3)

    # Row 4: gpuFps p95 (baseline)
    row4 = el(table, "table-row", T)
    _add_text_cell(row4, "gpuFps p95", "ce2")
    if baseline:
        gp = baseline.get("gpuFpsP95", 0)
        _add_num_cell(row4, f"{gp:.1f}", float(gp), "ce1")
    else:
        _add_empty_cell(row4, "ce1")
    _add_empty_cell(row4, "ce1", 4)
    _add_empty_cell(row4)
    _add_empty_cell(row4)

    # Setting rows
    setting_row = 5
    for sd in settings_list:
        row = el(table, "table-row", T)
        _add_text_cell(row, sd["name"], "ce2")

        col_order = sd.get("col_order", ["HIGH", "MEDIUM", "LOW"])
        fps_data = variants.get(sd["name"], {})

        for variant in col_order:
            data = fps_data.get(variant)
            fps = _get_fps(data)
            if fps > 0:
                _add_num_cell(row, str(int(fps)), fps, "ce1")
            else:
                _add_empty_cell(row, "ce1")

        extra_cols = 5 - len(col_order)
        if extra_cols > 0:
            _add_empty_cell(row, "ce1", extra_cols)

        high_data = fps_data.get("HIGH")
        high_fps = _get_fps(high_data)

        if sd.get("custom_pct_col"):
            custom_data = fps_data.get("CUSTOM")
            custom_fps = _get_fps(custom_data)
            worst_fps = (
                min(high_fps, custom_fps)
                if custom_fps > 0 and high_fps > 0
                else (high_fps if high_fps > 0 else custom_fps)
            )
        else:
            worst_fps = high_fps

        if worst_fps > 0 and base_fps > 0:
            pct = (base_fps - worst_fps) / base_fps
            pct_display = f"{pct * 100:.2f}%"
            _add_pct_cell(row, pct_display, pct, f"=([.$B$1]-[.B{setting_row}])/[.$B$1]")
        else:
            _add_empty_cell(row)

        if sd.get("custom_pct_col"):
            custom_fps = _get_fps(fps_data.get("CUSTOM"))
            if custom_fps > 0 and base_fps > 0:
                custom_pct = (base_fps - custom_fps) / base_fps
                custom_pct_display = f"{custom_pct * 100:.2f}%"
                _add_pct_cell(row, custom_pct_display, custom_pct, f"=([.$B$1]-[.E{setting_row}])/[.$B$1]", "ce10")
            else:
                _add_empty_cell(row)
        else:
            _add_empty_cell(row)

        setting_row += 1

    # Separator row
    el(table, "table-row", T)

    # Label row
    row_label = el(table, "table-row", T)
    _add_text_cell(row_label, "Graphics settings impact (version 1.5.10f1) ", "ce8")
    _add_empty_cell(row_label, "ce1", 4)
    _add_empty_cell(row_label, repeat=2)

    # Another separator
    el(table, "table-row", T)

    # Max quality row
    max_fps = _get_fps(max_quality)
    row_rec = el(table, "table-row", T)
    _add_text_cell(row_rec, "Max quality", "ce1")
    if max_fps > 0:
        _add_num_cell(row_rec, str(int(max_fps)), max_fps, "ce1")
    else:
        _add_empty_cell(row_rec, "ce1")
    _add_empty_cell(row_rec, "ce1", 4)
    if max_fps > 0 and base_fps > 0:
        max_pct = (base_fps - max_fps) / base_fps
        _add_pct_cell(row_rec, f"{max_pct * 100:.2f}%", max_pct, f"=([.$B$1]-[.B{setting_row}])/[.$B$1]")
    else:
        _add_empty_cell(row_rec)

    # --- Baseline gpuFrameTimes data section ---
    if baseline and baseline.get("gpuFrameTimes"):
        base_ft = baseline["gpuFrameTimes"]
        r_hdr = el(table, "table-row", T)
        _add_text_cell(r_hdr, "Baseline gpuFrameTimes (ms)", "ce7")
        _add_text_cell(r_hdr, "Frame #", "ce7")
        _add_text_cell(r_hdr, "Value", "ce7")
        _add_empty_cell(r_hdr, "ce7", 4)
        _add_empty_cell(r_hdr, repeat=2)

        for i, val in enumerate(base_ft):
            r = el(table, "table-row", T)
            _add_empty_cell(r)
            _add_num_cell(r, str(i + 1), float(i + 1), "ce1")
            _add_num_cell(r, f"{val:.2f}", float(val), "ce1")
            _add_empty_cell(r, "ce1", 4)
            _add_empty_cell(r, repeat=2)


# --- Per-setting sheets ---

def _build_setting_sheet(spreadsheet: ET.Element, sd: dict, state: ODSState) -> None:
    O, T, X = NS_OFFICE, NS_TABLE, NS_TEXT
    baseline = state.baseline
    variants = state.variants

    name = sd["name"]
    col_order = sd.get("col_order", ["HIGH", "MEDIUM", "LOW"])
    labels = sd.get("labels", [])
    fps_data = variants.get(name, {})

    safe_name = name.replace(" ", "_").replace("-", "_")
    sheet_table = el(
        spreadsheet, "table", T,
        {ns("name", T): safe_name, ns("style-name", T): "ta1"},
    )

    el(sheet_table, "table-column", T, {ns("style-name", T): "co1", ns("number-columns-repeated", T): "8"})

    # Row 1: headers
    hdr = el(sheet_table, "table-row", T)
    _add_text_cell(hdr, "Metric", "ce7")
    _add_text_cell(hdr, "Baseline", "ce7")
    for v in col_order:
        label = labels[col_order.index(v)] if col_order.index(v) < len(labels) else v
        _add_text_cell(hdr, label, "ce7")
    extra = 5 - len(col_order)
    if extra > 0:
        _add_empty_cell(hdr, "ce7", extra)
    _add_empty_cell(hdr, repeat=2)

    # Helper to add a metric row
    def _add_metric_row(label: str, baseline_key: str, variant_key: str | None):
        r = el(sheet_table, "table-row", T)
        _add_text_cell(r, label, "ce2")
        if baseline:
            val = baseline.get(baseline_key, 0)
            if isinstance(val, (int, float)):
                _add_num_cell(r, f"{val:.1f}" if isinstance(val, float) else str(val), float(val), "ce1")
            else:
                _add_empty_cell(r, "ce1")
        else:
            _add_empty_cell(r, "ce1")
        for v in col_order:
            d = fps_data.get(v)
            if isinstance(d, dict):
                fv = d.get(variant_key, 0) if variant_key else 0
                if isinstance(fv, (int, float)):
                    _add_num_cell(r, f"{fv:.1f}" if isinstance(fv, float) else str(fv), float(fv), "ce1")
                else:
                    _add_empty_cell(r, "ce1")
            else:
                _add_empty_cell(r, "ce1")
        ex = 5 - len(col_order)
        if ex > 0:
            _add_empty_cell(r, "ce1", ex)
        _add_empty_cell(r, repeat=2)

    # Row 2: FPS
    _add_metric_row("FPS", "averageFps", "averageFps")
    # Row 3: framesRendered
    _add_metric_row("framesRendered", "framesRendered", "framesRendered")
    # Row 4: gpuFps avg
    _add_metric_row("gpuFps avg", "gpuFpsAvg", "gpuFpsAvg")
    # Row 5: gpuFps p95
    _add_metric_row("gpuFps p95", "gpuFpsP95", "gpuFpsP95")

    # --- gpuFrameTimes data section (horizontal layout) ---
    ft_series: list[tuple[str, list[float]]] = []
    if baseline and baseline.get("gpuFrameTimes"):
        ft_series.append(("Baseline", baseline["gpuFrameTimes"]))

    base_ft = baseline.get("gpuFrameTimes") if baseline else None
    for v in col_order:
        d = fps_data.get(v)
        if isinstance(d, dict) and d.get("gpuFrameTimes"):
            var_ft = d["gpuFrameTimes"]
            if base_ft is None or var_ft != base_ft:
                label = labels[col_order.index(v)] if col_order.index(v) < len(labels) else v
                ft_series.append((label, var_ft))

    if len(ft_series) > 1:
        r_ft_hdr = el(sheet_table, "table-row", T)
        _add_text_cell(r_ft_hdr, "gpuFrameTimes (ms)", "ce7")
        _add_text_cell(r_ft_hdr, "Frame #", "ce7")
        for sn, _ in ft_series:
            _add_text_cell(r_ft_hdr, sn, "ce7")
        remaining = 8 - (2 + len(ft_series))
        if remaining > 0:
            _add_empty_cell(r_ft_hdr, "ce7", remaining)
        _add_empty_cell(r_ft_hdr, repeat=2)

        num_points = min(len(arr) for _, arr in ft_series)
        for i in range(num_points):
            r = el(sheet_table, "table-row", T)
            _add_empty_cell(r)
            _add_num_cell(r, str(i + 1), float(i + 1), "ce1")
            for _, arr in ft_series:
                _add_num_cell(r, f"{arr[i]:.2f}", float(arr[i]), "ce1")
            remaining = 8 - (2 + len(ft_series))
            if remaining > 0:
                _add_empty_cell(r, "ce1", remaining)
            _add_empty_cell(r, repeat=2)


# --- Conditional formatting ---

def _add_conditional_formats(spreadsheet: ET.Element) -> None:
    T, CALC = NS_TABLE, NS_CALC

    cf_parent = ET.SubElement(spreadsheet, ns("conditional-formats", CALC))

    # Column G color scale
    cf1 = ET.SubElement(cf_parent, ns("conditional-format", CALC))
    cf1.set(ns("target-range-address", CALC), "Summary.G1:Summary.G1048576")
    cs1 = ET.SubElement(cf1, ns("color-scale", CALC))
    _color_entry(cs1, "0", "minimum", "#ffffff")
    _color_entry(cs1, "50", "percentile", "#dedce6")
    _color_entry(cs1, "0", "maximum", "#bf0041")

    # H5 color scale (for custom AA impact)
    cf2 = ET.SubElement(cf_parent, ns("conditional-format", CALC))
    cf2.set(ns("target-range-address", CALC), "Summary.H5:Summary.H5")
    cs2 = ET.SubElement(cf2, ns("color-scale", CALC))
    _color_entry(cs2, "0", "minimum", "#ffffff")
    _color_entry(cs2, "50", "percentile", "#dedce6")
    _color_entry(cs2, "0", "maximum", "#bf0041")

    # Calculation settings
    cs = ET.SubElement(spreadsheet, ns("calculation-settings", T))
    cs.set(ns("automatic-find-labels", T), "false")
    cs.set(ns("use-regular-expressions", T), "false")
    cs.set(ns("use-wildcards", T), "true")


def _color_entry(parent: ET.Element, value: str, type_: str, color: str) -> None:
    CALC = NS_CALC
    e = ET.SubElement(parent, ns("color-scale-entry", CALC))
    e.set(ns("value", CALC), value)
    e.set(ns("type", CALC), type_)
    e.set(ns("color", CALC), color)


# --- FPS helper (local to avoid circular import) ---

def _get_fps(data: Any) -> float:
    if isinstance(data, dict):
        return data.get("averageFps", 0)
    return float(data) if data else 0


# --- Write ODS ---

def write_ods(state: ODSState, output_path: Path | None = None) -> None:
    """Generate the full ODS file from accumulated state."""
    if output_path is None:
        output_path = state.output_path
    O, T, X, S, N = NS_OFFICE, NS_TABLE, NS_TEXT, NS_STYLE, NS_NUMBER

    office_doc = ET.Element(ns("document-content", O))
    office_doc.set(ns("version", O), "1.4")
    office_body = el(office_doc, "body", O)
    office_spreadsheet = el(office_body, "spreadsheet", O)

    # Main sheet
    main_table = el(
        office_spreadsheet, "table", T,
        {ns("name", T): "Summary", ns("style-name", T): "ta1"},
    )
    el(main_table, "table-column", T, {ns("style-name", T): "co1", ns("number-columns-repeated", T): "6"})
    el(main_table, "table-column", T, {ns("style-name", T): "co_pct", ns("number-columns-repeated", T): "2"})

    _build_main_sheet(main_table, state)

    # Per-setting sheets
    for sd in state.settings_list:
        _build_setting_sheet(office_spreadsheet, sd, state)

    # Conditional formatting
    _add_conditional_formats(office_spreadsheet)

    content_xml = ET.tostring(office_doc, encoding="utf-8", xml_declaration=True)

    # styles.xml
    auto_styles_xml = _build_styles(None)
    styles_path = Path(__file__).parent.parent / "styles_template.xml"
    if styles_path.exists():
        styles_text = styles_path.read_text()
        styles_text = styles_text.replace(
            "</office:document-styles>",
            '<office:automatic-styles xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
            'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
            'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
            'xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0">\n'
            + auto_styles_xml
            + "\n</office:automatic-styles>\n</office:document-styles>",
        )
        styles_xml = styles_text.encode("utf-8")
    else:
        styles_xml = (
            b'<?xml version="1.0" encoding="UTF-8"?>\n'
            b'<office:document-styles xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" office:version="1.4" />'
        )

    # meta.xml
    meta_path = Path(__file__).parent.parent / "meta_template.xml"
    if meta_path.exists():
        meta_xml = meta_path.read_bytes()
    else:
        meta_xml = (
            b'<?xml version="1.0" encoding="UTF-8"?>\n'
            b'<office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
            b'office:version="1.4"><office:meta></office:meta></office:document-meta>'
        )

    # manifest.xml
    manifest_path = Path(__file__).parent.parent / "manifest_template.xml"
    if manifest_path.exists():
        manifest_xml = manifest_path.read_bytes()
    else:
        manifest_xml = (
            b'<?xml version="1.0" encoding="UTF-8"?>\n'
            b'<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" '
            b'manifest:version="1.4">'
            b'<manifest:file-entry manifest:full-path="/" manifest:version="1.4" '
            b'manifest:media-type="application/vnd.oasis.opendocument.spreadsheet"/>'
            b'<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
            b'<manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>'
            b'<manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/>'
            b'</manifest:manifest>'
        )

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/vnd.oasis.opendocument.spreadsheet", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/manifest.xml", manifest_xml)
        zf.writestr("content.xml", content_xml)
        zf.writestr("styles.xml", styles_xml)
        zf.writestr("meta.xml", meta_xml)

    print(f"  ODS written to {output_path}")
