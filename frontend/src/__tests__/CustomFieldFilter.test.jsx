import { describe, it, expect, vi } from "vitest"
import { fireEvent, render, screen } from "@testing-library/react"

import "../i18n"
import { CustomFieldFilter } from "../components/customField/CustomFieldFilter"

const TEXT_FIELD = { id: 1, key: "component", label: "Component", type: "text" }
const BOOL_FIELD = { id: 2, key: "is_blocker", label: "Blocker", type: "bool" }

describe("CustomFieldFilter", () => {
  it("tells the user an empty text value matches any value", () => {
    renderFilter(TEXT_FIELD, "any")

    expect(screen.getByLabelText("Value")).toHaveAttribute("placeholder", "Any value")
    expect(screen.getByLabelText("Value")).toHaveValue("")
  })

  it("goes back to any value when the text is cleared", () => {
    const onFieldValueChange = vi.fn()
    renderFilter(TEXT_FIELD, "api", onFieldValueChange)

    fireEvent.change(screen.getByLabelText("Value"), { target: { value: "" } })

    expect(onFieldValueChange).toHaveBeenLastCalledWith("any")
  })

  it("offers translated yes and no for boolean fields", () => {
    renderFilter(BOOL_FIELD, "any")

    fireEvent.click(screen.getAllByRole("combobox")[1])

    expect(screen.getByRole("option", { name: "Yes" })).toBeInTheDocument()
    expect(screen.getByRole("option", { name: "No" })).toBeInTheDocument()
  })
})

function renderFilter(definition, fieldValue, onFieldValueChange = vi.fn()) {
  return render(
    <CustomFieldFilter
      definitions={[definition]}
      fieldKey={definition.key}
      fieldValue={fieldValue}
      onFieldKeyChange={vi.fn()}
      onFieldValueChange={onFieldValueChange}
      selectedDefinition={definition}
    />,
  )
}
