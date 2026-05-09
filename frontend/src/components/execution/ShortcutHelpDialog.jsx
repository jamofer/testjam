import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "../ui/dialog"
import { STATUS_CONFIG } from "../../lib/statusConfig"

export const SHORTCUT_TO_STATUS = { p: "passed", f: "failed", b: "blocked", n: "not_run" }

function ShortcutRow({ keys, description }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex gap-1">
        {keys.map(k => (
          <kbd key={k} className="px-2 py-0.5 text-xs font-mono bg-gray-100 border border-gray-300 rounded">{k}</kbd>
        ))}
      </div>
      <span className="text-gray-600">{description}</span>
    </div>
  )
}

export function ShortcutHelpDialog({ open, onOpenChange, isAutomated }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Keyboard shortcuts</DialogTitle>
          <DialogDescription>Navigate and update results without the mouse.</DialogDescription>
        </DialogHeader>
        <div className="space-y-2 text-sm">
          <ShortcutRow keys={["j", "↓"]} description="Focus next result" />
          <ShortcutRow keys={["k", "↑"]} description="Focus previous result" />
          {!isAutomated && Object.entries(SHORTCUT_TO_STATUS).map(([key, status]) => (
            <ShortcutRow key={key} keys={[key]} description={`Mark as ${STATUS_CONFIG[status].label}`} />
          ))}
          <ShortcutRow keys={["?"]} description="Toggle this help" />
          <ShortcutRow keys={["Esc"]} description="Close this help" />
        </div>
      </DialogContent>
    </Dialog>
  )
}
