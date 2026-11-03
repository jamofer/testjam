import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"

import "../i18n"
import { ResultCounts } from "../components/execution/ResultCounts"

describe("ResultCounts", () => {
  it("shows each status tally with its label", () => {
    render(<ResultCounts counts={{ passed: 3, failed: 1, blocked: 2, not_run: 4 }} />)

    expect(screen.getByTitle("Pass")).toHaveTextContent("3")
    expect(screen.getByTitle("Fail")).toHaveTextContent("1")
    expect(screen.getByTitle("Blocked")).toHaveTextContent("2")
    expect(screen.getByTitle("Not run")).toHaveTextContent("4")
  })

  it("treats missing counts as zero", () => {
    render(<ResultCounts counts={undefined} />)

    expect(screen.getByTitle("Fail")).toHaveTextContent("0")
  })
})
