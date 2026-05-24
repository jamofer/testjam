"""Reusable malicious payload batteries.

Each constant is iterated by tests that touch a user-string boundary —
filenames, markdown bodies, link URLs. Add to a list here once and every
endpoint test picks it up; never bake payload strings into individual
tests, otherwise the coverage rots independently per file.
"""

PATH_TRAVERSAL_FILENAMES = [
    "../../etc/passwd",
    "..\\..\\windows\\system32\\config\\sam",
    "/etc/shadow",
    "C:\\Windows\\System32\\drivers\\etc\\hosts",
    "../../../../../../../../tmp/escape.txt",
    "....//....//etc/passwd",
    "/../../../../absolute.txt",
    ".",
    "..",
    "",
]

XSS_HTML_BODIES = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "<svg/onload=alert(1)>",
    "<iframe src=javascript:alert(1)></iframe>",
    "<a href=\"javascript:alert(1)\">click</a>",
    "<body onload=alert(1)>",
    "<<SCRIPT>alert(1)//<</SCRIPT>",
    "\"><script>alert(1)</script>",
]

UNSAFE_URL_SCHEMES = [
    "javascript:alert(1)",
    "JaVaScRiPt:alert(1)",
    "data:text/html,<script>alert(1)</script>",
    "vbscript:msgbox(1)",
    "file:///etc/passwd",
    " javascript:alert(1)",
]

SAFE_URL_SCHEMES = [
    "http://example.com/path",
    "https://example.com/path?q=1",
    "mailto:user@example.com",
    "/relative/path",
    "#anchor",
]
