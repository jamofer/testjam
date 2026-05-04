import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { Skeleton, SkeletonText, SkeletonList } from "../components/ui/skeleton"

describe("Skeleton", () => {
  it("renders with status role and aria-busy", () => {
    render(<Skeleton />)
    const el = screen.getByRole("status")
    expect(el.getAttribute("aria-busy")).toBe("true")
  })

  it("applies the custom className", () => {
    const { container } = render(<Skeleton className="h-7 w-1/2" />)
    expect(container.firstChild.className).toContain("h-7")
    expect(container.firstChild.className).toContain("w-1/2")
  })
})

describe("SkeletonText", () => {
  it("renders the requested number of lines", () => {
    const { container } = render(<SkeletonText lines={4} />)
    expect(container.firstChild.children).toHaveLength(4)
  })

  it("makes the last line shorter than the others", () => {
    const { container } = render(<SkeletonText lines={3} />)
    const lines = container.firstChild.children
    expect(lines[2].className).toContain("w-2/3")
    expect(lines[0].className).toContain("w-full")
  })
})

describe("SkeletonList", () => {
  it("renders the requested number of items", () => {
    const { container } = render(<SkeletonList count={5} />)
    expect(container.firstChild.children).toHaveLength(5)
  })
})
