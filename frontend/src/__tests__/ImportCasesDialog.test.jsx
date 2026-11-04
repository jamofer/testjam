import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { ImportCasesDialog } from "../components/project/ImportCasesDialog"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock("../api/testcases", () => ({
  suitesApi: {},
  casesApi: { importCsv: vi.fn() },
}))

import { casesApi } from "../api/testcases"

const CSV_FILE = new File(["name\nLogin\n"], "cases.csv", { type: "text/csv" })

describe("ImportCasesDialog", () => {
  beforeEach(() => {
    casesApi.importCsv.mockReset()
  })

  it("uploads the picked file to the project", async () => {
    casesApi.importCsv.mockResolvedValue({ created: 1, suites_created: 1, errors: [] })
    renderDialog()
    openAndPick(CSV_FILE)

    fireEvent.click(screen.getByRole("button", { name: "Import" }))

    expect(await screen.findByTestId("import-summary")).toHaveTextContent("Test cases created: 1 · New suites: 1")
    expect(casesApi.importCsv).toHaveBeenCalledWith("3", CSV_FILE)
  })

  it("lists the rows that could not be imported", async () => {
    casesApi.importCsv.mockResolvedValue({
      created: 0,
      suites_created: 0,
      errors: [{ row: 2, name: "Login", error: "A test case with this name already exists in the suite" }],
    })
    renderDialog()
    openAndPick(CSV_FILE)

    fireEvent.click(screen.getByRole("button", { name: "Import" }))

    expect(await screen.findByText("Row 2 (Login): A test case with this name already exists in the suite")).toBeInTheDocument()
  })

  it("keeps the import disabled until a file is picked", () => {
    renderDialog()

    fireEvent.click(screen.getByRole("button", { name: /import csv/i }))

    expect(screen.getByRole("button", { name: "Import" })).toBeDisabled()
  })
})

function renderDialog() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <ImportCasesDialog projectId="3" />
    </QueryClientProvider>,
  )
}

function openAndPick(file) {
  fireEvent.click(screen.getByRole("button", { name: /import csv/i }))
  fireEvent.change(screen.getByLabelText("CSV file"), { target: { files: [file] } })
}
