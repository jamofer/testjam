import { describe, it, expect, beforeEach } from "vitest"
import { loadRecents, pushRecent, clearRecents } from "../lib/commandPaletteRecents"


beforeEach(() => {
  window.localStorage.clear()
})


describe("commandPaletteRecents", () => {
  it("returns an empty list when nothing has been stored", () => {
    expect(loadRecents()).toEqual([])
  })

  it("returns an empty list when the stored value is corrupted", () => {
    window.localStorage.setItem("testjam.command-palette.recents", "{not json")

    expect(loadRecents()).toEqual([])
  })

  it("persists a new entry at the top", () => {
    const next = pushRecent({ kind: "project", url: "/projects/7", title: "Acme" })

    expect(next[0]).toMatchObject({ kind: "project", url: "/projects/7", title: "Acme" })
    expect(loadRecents()).toHaveLength(1)
  })

  it("deduplicates by kind + url, keeping the newest occurrence first", () => {
    pushRecent({ kind: "project", url: "/projects/7", title: "Acme" })
    pushRecent({ kind: "exec", url: "/executions/42/run", title: "Smoke" })
    const next = pushRecent({ kind: "project", url: "/projects/7", title: "Acme renamed" })

    expect(next).toHaveLength(2)
    expect(next[0]).toMatchObject({ kind: "project", title: "Acme renamed" })
    expect(next[1].kind).toBe("exec")
  })

  it("caps the stored list at 10 entries", () => {
    for (let i = 0; i < 15; i++) {
      pushRecent({ kind: "project", url: `/projects/${i}`, title: `P${i}` })
    }

    expect(loadRecents()).toHaveLength(10)
    expect(loadRecents()[0]).toMatchObject({ url: "/projects/14" })
  })

  it("ignores malformed entries on push", () => {
    pushRecent({ kind: "project", url: "/projects/1", title: "ok" })
    pushRecent({ kind: "project", url: "/projects/2" }) // missing title

    expect(loadRecents()).toHaveLength(1)
  })

  it("clears everything", () => {
    pushRecent({ kind: "project", url: "/projects/7", title: "Acme" })

    clearRecents()

    expect(loadRecents()).toEqual([])
  })
})
