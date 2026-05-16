import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "./dialog"

function ShortcutRow({ keys, description }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div className="flex gap-1 shrink-0">
        {keys.map((k, i) => (
          <kbd key={i} className="px-2 py-0.5 text-xs font-mono bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded">{k}</kbd>
        ))}
      </div>
      <span className="text-gray-600 dark:text-gray-300 text-right">{description}</span>
    </div>
  )
}

export function ShortcutsDialog({ open, onOpenChange, title = "Keyboard shortcuts", description, sections }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          {description && <DialogDescription>{description}</DialogDescription>}
        </DialogHeader>
        <div className="space-y-4 text-sm">
          {sections.map((section, i) => (
            <div key={i} className="space-y-2">
              {section.title && (
                <p className="text-[11px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500">
                  {section.title}
                </p>
              )}
              <div className="space-y-1.5">
                {section.rows.map((row, j) => (
                  <ShortcutRow key={j} keys={row.keys} description={row.description} />
                ))}
              </div>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  )
}
