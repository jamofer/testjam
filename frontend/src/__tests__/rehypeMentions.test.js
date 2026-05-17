import { describe, it, expect } from "vitest"
import { unified } from "unified"
import rehypeParse from "rehype-parse"
import rehypeStringify from "rehype-stringify"

import { rehypeMentions } from "../lib/mentions/rehypeMentions"

function transform(html) {
  return unified()
    .use(rehypeParse, { fragment: true })
    .use(rehypeMentions)
    .use(rehypeStringify)
    .processSync(html)
    .toString()
}

describe("rehypeMentions", () => {
  it("wraps a @user token in a span", () => {
    const out = transform("<p>hello @alice</p>")
    expect(out).toContain('data-mention-kind="user"')
    expect(out).toContain('data-mention-slug="alice"')
    expect(out).toContain("@alice")
  })

  it("wraps #bug with id attribute", () => {
    const out = transform("<p>see #42</p>")
    expect(out).toContain('data-mention-kind="bug"')
    expect(out).toContain('data-mention-id="42"')
  })

  it("emits sub-ids for composite tokens", () => {
    const out = transform("<p>step !17/91/3 broke</p>")
    expect(out).toContain('data-mention-kind="step_result"')
    expect(out).toContain('data-mention-sub-ids="91,3"')
  })

  it("skips tokens inside <code>", () => {
    const out = transform("<p>real @alice and <code>@bob</code></p>")
    expect(out).toContain('data-mention-slug="alice"')
    expect(out).not.toContain('data-mention-slug="bob"')
  })

  it("skips tokens inside <pre>", () => {
    const out = transform("<pre>see #42 here</pre>")
    expect(out).not.toContain("data-mention-id")
  })
})
