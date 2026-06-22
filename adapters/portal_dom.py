# Owns: portal DOM vocabulary — timing constants, grid positions, selectors, inline JS snippets.
# Must not: import anything outside stdlib; must not contain wizard flow logic or browser calls.
# May import: (nothing — pure data module).
#
# These constants describe one portal's UI structure. A future per-portal profile system would
# let PortalReceiver select a vocabulary module at construction time.

# Timing constants (seconds) — require live validation against the portal.
NAV_SETTLE_SECS = 2.0
LOCATION_SETTLE_SECS = 3.0
WHSE_SETTLE_SECS = 1.5
QTY_SETTLE_SECS = 0.5
SERIAL_SETTLE_SECS = 0.5
REVIEW_SETTLE_SECS = 2.0
FINALIZE_SETTLE_SECS = 3.0
GRID_PAGE_SETTLE_SECS = 1.5

# Grid column positions (confirmed from live screenshots, June 2026).
MODEL_COL = 3
TBR_COL = 7
QTY_COL = 8

GRID_ROW_TIMEOUT_MS = 8_000
RECEIVE_URL_TIMEOUT_MS = 15_000
MAX_GRID_PAGES = 10

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
NEXT_BTN_SELECTOR = (
    ".k-pager-wrap a.k-next-button, "
    ".k-grid-pager a[aria-label*='next' i], "
    ".k-grid-pager .k-i-arrow-e"
)

# Inline JS — portal-specific; none are domain names or credentials.
READ_OPTIONS_JS = (
    "(sel) => { const s=document.querySelector(sel); if(!s) return [];"
    " return Array.from(s.options).map(o=>({value:o.value,text:o.text})); }"
)
KENDO_SET_JS = (
    "(a) => { const s=document.querySelector(a.selector); if(!s) return; s.value=a.value;"
    " if(typeof $!=='undefined'){const w=$(s).data('kendoDropDownList');"
    " if(w){w.value(a.value);w.trigger('change');return;}}"
    " s.dispatchEvent(new Event('change',{bubbles:true})); }"
)
QTY_SET_JS = "el=>{el.value='1';el.dispatchEvent(new Event('change',{bubbles:true}));}"
FINALIZE_CHECK_JS = (
    "()=>{const as=document.querySelectorAll('.alert-danger,.alert.alert-error');"
    " for(const a of as) if(a.offsetParent!==null&&(a.textContent||'').trim().length>0)"
    " return a.textContent.trim(); return '';}"
)
