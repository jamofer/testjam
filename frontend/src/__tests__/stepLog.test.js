import { describe, expect, it } from "vitest"
import { formatStepLogLine, parseStepLog } from "../lib/stepLog"

describe("parseStepLog", () => {
  it("reads timestamp, level and message of the current format", () => {
    expect(parseStepLog("2026-11-18T09:15:02.123Z [INFO] logged in\n\n2026-11-18T09:15:03.000Z [FAIL] boom")).toEqual([
      { ts: "2026-11-18T09:15:02.123Z", level: "INFO", message: "logged in" },
      { ts: "2026-11-18T09:15:03.000Z", level: "FAIL", message: "boom" },
    ])
  })

  it("still reads rows stored before timestamps existed", () => {
    expect(parseStepLog("**[INFO]** first\n\n**[WARN]** second")).toEqual([
      { ts: null, level: "INFO", message: "first" },
      { ts: null, level: "WARN", message: "second" },
    ])
  })

  it("reads the old listener batch format", () => {
    expect(parseStepLog("2026-11-18 09:15:02.123 [DEBUG] x")).toEqual([
      { ts: "2026-11-18T09:15:02.123", level: "DEBUG", message: "x" },
    ])
  })

  it("keeps the lines of a multi-line message together", () => {
    expect(parseStepLog("2026-11-18T09:15:02.123Z [FAIL] Traceback:\n  File x\n\n  line 2\n\n[INFO] next")).toEqual([
      { ts: "2026-11-18T09:15:02.123Z", level: "FAIL", message: "Traceback:\n  File x\n\n  line 2" },
      { ts: null, level: "INFO", message: "next" },
    ])
  })

  it("keeps free text that has no level", () => {
    expect(parseStepLog("plain text")).toEqual([{ ts: null, level: null, message: "plain text" }])
  })
})

describe("formatStepLogLine", () => {
  it("normalises the timestamp to UTC milliseconds", () => {
    expect(formatStepLogLine("INFO", "hi", "2026-11-18T10:15:02.123456+01:00")).toBe("2026-11-18T09:15:02.123Z [INFO] hi")
  })

  it("leaves the timestamp out when there is none", () => {
    expect(formatStepLogLine("INFO", "hi", null)).toBe("[INFO] hi")
  })
})
