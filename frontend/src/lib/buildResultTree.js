import { sortSuitesHierarchically } from "../hooks/useSuites"

/**
 * Group results by suite, fill in missing ancestors so the tree is connected,
 * and return top-level ids + children adjacency.
 */
export function buildResultTree(groups, allSuites) {
  const order = sortSuitesHierarchically(allSuites).map(s => s.id)
  const suiteMap = Object.fromEntries(allSuites.map(s => [s.id, s]))

  const full = { ...groups }
  Object.values(groups).forEach(({ suite }) => {
    if (!suite) return
    let pid = suite.parent_suite_id
    while (pid && !full[pid]) {
      const ancestor = suiteMap[pid]
      if (!ancestor) break
      full[pid] = { suite: ancestor, items: [] }
      pid = ancestor.parent_suite_id
    }
  })

  const topLevelIds = []
  const childrenOf = {}

  Object.values(full).forEach(({ suite }) => {
    if (!suite) return
    const parentId = suite.parent_suite_id
    if (parentId && full[parentId]) {
      if (!childrenOf[parentId]) childrenOf[parentId] = []
      childrenOf[parentId].push(suite.id)
    } else {
      topLevelIds.push(suite.id)
    }
  })

  const sort = (ids) => ids.sort((a, b) => order.indexOf(a) - order.indexOf(b))
  sort(topLevelIds)
  Object.keys(childrenOf).forEach(pid => sort(childrenOf[pid]))

  return { topLevelIds, childrenOf, full }
}
