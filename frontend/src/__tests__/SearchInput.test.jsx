import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { SearchInput } from "../components/ui/search-input"

describe("SearchInput", () => {
  it("calls onChange with the new value when typing", () => {
    const onChange = vi.fn()
    render(<SearchInput value="" onChange={onChange} placeholder="Find" />)
    fireEvent.change(screen.getByPlaceholderText("Find"), { target: { value: "abc" } })
    expect(onChange).toHaveBeenCalledWith("abc")
  })

  it("hides the clear button when value is empty", () => {
    render(<SearchInput value="" onChange={() => {}} />)
    expect(screen.queryByLabelText("Clear search")).toBeNull()
  })

  it("shows the clear button when value is non-empty", () => {
    render(<SearchInput value="hello" onChange={() => {}} />)
    expect(screen.getByLabelText("Clear search")).toBeInTheDocument()
  })

  it("clears the value when the clear button is clicked", () => {
    const onChange = vi.fn()
    render(<SearchInput value="x" onChange={onChange} />)
    fireEvent.click(screen.getByLabelText("Clear search"))
    expect(onChange).toHaveBeenCalledWith("")
  })
})
