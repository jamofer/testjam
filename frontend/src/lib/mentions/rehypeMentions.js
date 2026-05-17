import { visit, SKIP } from "unist-util-visit"

import { parse } from "./parser"

const SKIPPABLE_PARENTS = new Set(["code", "pre"])

// Rehype plugin: walks text nodes (skipping <code> / <pre>) and rewrites any
// mention token into a <span data-mention="true" data-...> element so the
// react-markdown `components` map can render it as a MentionChip.
export function rehypeMentions() {
  return (tree) => {
    visit(tree, "text", (node, index, parent) => {
      if (!parent || index === null) return undefined
      if (SKIPPABLE_PARENTS.has(parent.tagName)) return SKIP
      const tokens = parse(node.value)
      if (tokens.length === 0) return undefined
      const replacement = splitTextByTokens(node.value, tokens)
      parent.children.splice(index, 1, ...replacement)
      return [SKIP, index + replacement.length]
    })
  }
}

function splitTextByTokens(value, tokens) {
  const out = []
  let cursor = 0
  for (const token of tokens) {
    if (token.start > cursor) {
      out.push(textNode(value.slice(cursor, token.start)))
    }
    out.push(mentionNode(token))
    cursor = token.end
  }
  if (cursor < value.length) {
    out.push(textNode(value.slice(cursor)))
  }
  return out
}

function textNode(value) {
  return { type: "text", value }
}

function mentionNode(token) {
  const properties = {
    "data-mention": "true",
    "data-mention-kind": token.kind,
    "data-mention-raw": token.raw,
  }
  if (token.slug) properties["data-mention-slug"] = token.slug
  if (token.id !== undefined) properties["data-mention-id"] = String(token.id)
  if (token.sub_ids && token.sub_ids.length > 0) {
    properties["data-mention-sub-ids"] = token.sub_ids.join(",")
  }
  return {
    type: "element",
    tagName: "span",
    properties,
    children: [textNode(token.raw)],
  }
}
