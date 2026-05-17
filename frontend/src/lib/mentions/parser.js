// Recognized sigils inside a markdown body:
//
//   @username         user
//   #42               bug
//   !17               execution
//   !17/91            test result inside execution 17
//   !17/91/3          step result inside that result
//   ~91               test case (definition)
//
// Output schema mirrors backend/testjam/services/mentions.py so the
// notification fan-out and the MdViewer renderer see the same tokens.

const USER_PATTERN = /(?<!\S)@([a-zA-Z0-9_.\-]+)/g
const BUG_PATTERN = /(?<!\S)#(\d+)\b/g
const EXECUTION_PATTERN = /(?<!\S)!(\d+)(?:\/(\d+)(?:\/(\d+))?)?\b/g
const CASE_PATTERN = /(?<!\S)~(\d+)\b/g

const FENCED_CODE = /```[\s\S]*?```/gm
const INLINE_CODE = /`[^`\n]+`/g

export function parse(text) {
  if (!text) return []
  const masked = maskCode(text)
  const tokens = [
    ...matchAll(masked, USER_PATTERN, ([raw, slug], start, end) => ({
      kind: "user", raw, slug, start, end,
    })),
    ...matchAll(masked, BUG_PATTERN, ([raw, id], start, end) => ({
      kind: "bug", raw, id: Number(id), start, end,
    })),
    ...matchAll(masked, EXECUTION_PATTERN, ([raw, exec, result, step], start, end) => {
      const executionId = Number(exec)
      if (step !== undefined) {
        return {
          kind: "step_result", raw, id: executionId,
          sub_ids: [Number(result), Number(step)], start, end,
        }
      }
      if (result !== undefined) {
        return {
          kind: "result", raw, id: executionId,
          sub_ids: [Number(result)], start, end,
        }
      }
      return { kind: "execution", raw, id: executionId, start, end }
    }),
    ...matchAll(masked, CASE_PATTERN, ([raw, id], start, end) => ({
      kind: "case", raw, id: Number(id), start, end,
    })),
  ]
  tokens.sort((left, right) => left.start - right.start)
  return dedupe(tokens)
}

export function usernames(text) {
  return parse(text).filter(t => t.kind === "user").map(t => t.slug)
}

function matchAll(text, pattern, build) {
  const out = []
  for (const match of text.matchAll(pattern)) {
    out.push(build(match, match.index, match.index + match[0].length))
  }
  return out
}

function maskCode(text) {
  return text
    .replace(FENCED_CODE, match => " ".repeat(match.length))
    .replace(INLINE_CODE, match => " ".repeat(match.length))
}

function dedupe(tokens) {
  const seen = new Set()
  const unique = []
  for (const token of tokens) {
    const key = [
      token.kind,
      token.slug ?? "",
      token.id ?? "",
      (token.sub_ids ?? []).join(","),
    ].join("|")
    if (seen.has(key)) continue
    seen.add(key)
    unique.push(token)
  }
  return unique
}
