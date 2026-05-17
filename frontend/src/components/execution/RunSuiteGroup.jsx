import { ChevronRight, FolderOpen } from "lucide-react"
import { ResultCard } from "./ResultCard"

export function RunSuiteGroup({ suiteId, groups, childrenOf, orderedResults, focusedResultId, setFocusedResultId, id, isAutomated, focusedStepId = null, followLive = false }) {
  const { suite, items } = groups[suiteId]
  const children = childrenOf[suiteId] ?? []

  return (
    <div className="border rounded-lg overflow-hidden">
      <details open className="group/suite">
        <summary className="flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-gray-900 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer list-none font-medium text-sm text-gray-800 dark:text-gray-100">
          <ChevronRight size={14} className="transition-transform shrink-0 group-open/suite:rotate-90" />
          <FolderOpen size={14} className="text-yellow-500 shrink-0" />
          <span className="truncate flex-1">{suite.name}</span>
          <span className="text-xs text-gray-400 dark:text-gray-500 shrink-0">({items.length})</span>
        </summary>
        <div className="px-2 py-2 space-y-2">
          {children.length > 0 && (
            <div className="pl-4 space-y-2 border-l-2 border-gray-100 dark:border-gray-800">
              {children.map(childId => (
                <RunSuiteGroup key={childId} suiteId={childId} groups={groups} childrenOf={childrenOf}
                  orderedResults={orderedResults} focusedResultId={focusedResultId} setFocusedResultId={setFocusedResultId}
                  id={id} isAutomated={isAutomated} focusedStepId={focusedStepId} followLive={followLive} />
              ))}
            </div>
          )}
          {items.map(result => {
            const treeIdx = orderedResults.findIndex(r => r.id === result.id)
            return (
              <ResultCard key={result.id} result={result} executionId={id} index={treeIdx} total={orderedResults.length}
                isAutomated={isAutomated}
                focused={result.id === focusedResultId}
                focusedStepId={result.id === focusedResultId ? focusedStepId : null}
                onFocus={() => setFocusedResultId(result.id)}
                followLive={followLive} />
            )
          })}
        </div>
      </details>
    </div>
  )
}
