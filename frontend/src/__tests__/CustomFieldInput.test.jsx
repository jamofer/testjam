import { useState } from "react"
import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"

import "../i18n"
import { CustomFieldsForm } from "../components/customField/CustomFieldInput"

function StatefulForm({ definitions, initial = {}, onChange }) {
  const [values, setValues] = useState(initial)
  const handleChange = next => {
    setValues(next)
    onChange(next)
  }
  return <CustomFieldsForm definitions={definitions} values={values} onChange={handleChange} />
}

function buildDefinition(overrides = {}) {
  return {
    id: 1,
    project_id: 1,
    entity_type: "bug",
    key: "priority",
    label: "Priority",
    type: "text",
    options: null,
    required: false,
    position: 0,
    archived_at: null,
    ...overrides,
  }
}

describe("CustomFieldsForm", () => {
  it("renders nothing when no definitions are provided", () => {
    const { container } = render(
      <CustomFieldsForm definitions={[]} values={{}} onChange={vi.fn()} />,
    )

    expect(container.firstChild).toBeNull()
  })

  it("emits a string value for text fields", async () => {
    const onChange = vi.fn()
    const definitions = [buildDefinition()]

    render(<StatefulForm definitions={definitions} onChange={onChange} />)
    await userEvent.type(screen.getByRole("textbox"), "P0")

    expect(onChange).toHaveBeenLastCalledWith({ priority: "P0" })
  })

  it("toggles boolean fields via checkbox", async () => {
    const onChange = vi.fn()
    const definitions = [buildDefinition({ key: "is_blocker", label: "Blocker", type: "bool" })]

    render(<CustomFieldsForm definitions={definitions} values={{}} onChange={onChange} />)
    await userEvent.click(screen.getByRole("checkbox"))

    expect(onChange).toHaveBeenLastCalledWith({ is_blocker: true })
  })

  it("removes the key when the value becomes empty", async () => {
    const onChange = vi.fn()
    const definitions = [buildDefinition()]

    render(
      <StatefulForm
        definitions={definitions}
        initial={{ priority: "P0" }}
        onChange={onChange}
      />,
    )
    await userEvent.clear(screen.getByRole("textbox"))

    expect(onChange).toHaveBeenLastCalledWith({})
  })

  it("marks required fields with a badge", () => {
    const definitions = [buildDefinition({ required: true })]

    render(<CustomFieldsForm definitions={definitions} values={{}} onChange={vi.fn()} />)

    expect(screen.getByText(/required/i)).toBeInTheDocument()
  })
})
