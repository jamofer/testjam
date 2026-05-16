import { jsPDF } from "jspdf"
import autoTable from "jspdf-autotable"

// Brand palette — matches Tailwind primary (rose-700) + neutral grays
const C = {
  brand:      [190,  18,  60],   // primary-700 rose
  brandLight: [255, 228, 230],   // primary-100
  headerBg:   [ 31,  41,  55],   // gray-800
  headerFg:   [255, 255, 255],
  rowAlt:     [249, 250, 251],   // gray-50
  border:     [229, 231, 235],   // gray-200
  muted:      [107, 114, 128],   // gray-500
  text:       [ 17,  24,  39],   // gray-900

  passed:     [209, 250, 229],   // green-100
  passedText: [ 22, 101,  52],   // green-800
  failed:     [254, 226, 226],   // red-100
  failedText: [153,  27,  27],   // red-800
  blocked:    [254, 243, 199],   // yellow-100
  blockedText:[146,  64,  14],   // yellow-800
  notrun:     [243, 244, 246],   // gray-100
  notrunText: [ 75,  85,  99],   // gray-600
}

const STATUS_COLORS = {
  passed:   { bg: C.passed,   fg: C.passedText },
  failed:   { bg: C.failed,   fg: C.failedText },
  blocked:  { bg: C.blocked,  fg: C.blockedText },
  not_run:  { bg: C.notrun,   fg: C.notrunText },
}

const STATUS_LABEL = {
  passed: "Passed", failed: "Failed", blocked: "Blocked", not_run: "Not run",
}

function fmtDate(iso, timezone) {
  if (!iso) return "—"
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium", timeStyle: "short",
    timeZone: timezone || undefined,
  })
}

function fmtTimezoneAbbreviation(timezone) {
  try {
    const parts = new Intl.DateTimeFormat(undefined, {
      timeZone: timezone, timeZoneName: "short",
    }).formatToParts(new Date())
    return parts.find(part => part.type === "timeZoneName")?.value || timezone
  } catch {
    return timezone || "UTC"
  }
}

function fmtDuration(ms) {
  if (ms == null) return "—"
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

function launchedBy(execution) {
  if (execution.token_name) return `via ${execution.token_name}`
  if (execution.created_by?.username) return execution.created_by.username
  return execution.triggered_by || "—"
}

export function exportExecutionPdf(execution, results, projectName = "", options = {}) {
  const { timezone = "UTC", username = "" } = options
  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" })
  const pageW = doc.internal.pageSize.getWidth()
  const margin = 14

  // ── Brand header bar ──────────────────────────────────────────────────────
  doc.setFillColor(...C.brand)
  doc.rect(0, 0, pageW, 18, "F")

  doc.setTextColor(...C.headerFg)
  doc.setFont("helvetica", "bold")
  doc.setFontSize(11)
  doc.text("Testjam", margin, 11)

  doc.setFont("helvetica", "normal")
  doc.setFontSize(9)
  doc.text("Execution Report", pageW - margin, 11, { align: "right" })

  // ── Title ─────────────────────────────────────────────────────────────────
  let y = 28
  doc.setTextColor(...C.text)
  doc.setFont("helvetica", "bold")
  doc.setFontSize(16)
  doc.text(execution.title, margin, y)

  // ── Meta info grid (3 columns, 2 rows) ───────────────────────────────────
  y += 9
  const meta = [
    ["Project",     projectName || "—"],
    ["Environment", execution.environment || "—"],
    ["Version",     execution.version_name || "—"],
    ["Launched by", launchedBy(execution)],
    ["Started",     fmtDate(execution.started_at, timezone)],
    ["Finished",    fmtDate(execution.finished_at, timezone)],
  ]

  doc.setFontSize(7)
  const colW = (pageW - margin * 2) / 3
  const ROW_H = 11  // mm per meta row: 4 label + 5 value + 2 gap
  meta.forEach(([label, value], i) => {
    const col = i % 3
    const row = Math.floor(i / 3)
    const x = margin + col * colW
    const baseY = y + row * ROW_H
    doc.setFont("helvetica", "bold")
    doc.setTextColor(...C.muted)
    doc.text(label.toUpperCase(), x, baseY)
    doc.setFont("helvetica", "normal")
    doc.setTextColor(...C.text)
    doc.setFontSize(9)
    doc.text(value, x, baseY + 5)
    doc.setFontSize(7)
  })

  // ── Summary boxes ─────────────────────────────────────────────────────────
  y += ROW_H * 2 + 6
  const s = execution.summary ?? {}
  const stats = [
    { label: "Passed",  value: s.passed  ?? 0, ...STATUS_COLORS.passed  },
    { label: "Failed",  value: s.failed  ?? 0, ...STATUS_COLORS.failed  },
    { label: "Blocked", value: s.blocked ?? 0, ...STATUS_COLORS.blocked },
    { label: "Not run", value: s.not_run ?? 0, ...STATUS_COLORS.not_run },
  ]

  const boxW = (pageW - margin * 2 - 9) / 4
  stats.forEach((stat, i) => {
    const x = margin + i * (boxW + 3)
    doc.setFillColor(...stat.bg)
    doc.roundedRect(x, y, boxW, 16, 2, 2, "F")
    doc.setFont("helvetica", "bold")
    doc.setFontSize(18)
    doc.setTextColor(...stat.fg)
    doc.text(String(stat.value), x + boxW / 2, y + 9, { align: "center" })
    doc.setFontSize(7)
    doc.setFont("helvetica", "normal")
    doc.text(stat.label, x + boxW / 2, y + 14, { align: "center" })
  })

  // ── Results table ─────────────────────────────────────────────────────────
  y += 22

  const rows = results.map(r => [
    r.test_case_title || "—",
    STATUS_LABEL[r.status] ?? r.status,
    r.executed_by || "—",
    fmtDuration(r.duration_ms),
    fmtDate(r.executed_at, timezone),
    r.comment || "",
  ])

  autoTable(doc, {
    startY: y,
    head: [["Test Case", "Status", "Executed by", "Time", "Date", "Comment"]],
    body: rows,
    margin: { left: margin, right: margin },
    styles: {
      fontSize: 8,
      cellPadding: { top: 3, bottom: 3, left: 4, right: 4 },
      textColor: C.text,
      lineColor: C.border,
      lineWidth: 0.1,
    },
    headStyles: {
      fillColor: C.headerBg,
      textColor: C.headerFg,
      fontStyle: "bold",
      fontSize: 8,
    },
    alternateRowStyles: { fillColor: C.rowAlt },
    tableWidth: pageW - margin * 2,
    columnStyles: {
      0: { cellWidth: 62 },
      1: { cellWidth: 20, halign: "center" },
      2: { cellWidth: 26 },
      3: { cellWidth: 20, halign: "right", cellPadding: { top: 3, bottom: 3, left: 2, right: 2 } },
      4: { cellWidth: 30 },
      5: { cellWidth: 24 },
    },
    didParseCell(data) {
      if (data.section === "body" && data.column.index === 1) {
        const status = results[data.row.index]?.status
        const colors = STATUS_COLORS[status]
        if (colors) {
          data.cell.styles.fillColor = colors.bg
          data.cell.styles.textColor = colors.fg
          data.cell.styles.fontStyle = "bold"
        }
      }
    },
    showHead: "everyPage",
    rowPageBreak: "avoid",
  })

  // Draw footers after autoTable so total page count is known
  const totalPages = doc.internal.getNumberOfPages()
  const pageH = doc.internal.pageSize.getHeight()
  const generatedAt = new Date().toLocaleString(undefined, {
    dateStyle: "medium", timeStyle: "short", timeZone: timezone,
  })
  const tzAbbreviation = fmtTimezoneAbbreviation(timezone)
  const byClause = username ? ` by ${username}` : ""
  const generated = `${generatedAt} ${tzAbbreviation}${byClause}`
  for (let p = 1; p <= totalPages; p++) {
    doc.setPage(p)
    doc.setFontSize(7)
    doc.setTextColor(...C.muted)
    doc.text(`Page ${p} of ${totalPages}  ·  Generated ${generated}`, pageW / 2, pageH - 8, { align: "center" })
  }

  doc.save(`execution_${execution.id}_${execution.title.replace(/\s+/g, "_")}.pdf`)
}
