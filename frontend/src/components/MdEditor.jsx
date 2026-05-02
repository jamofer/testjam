import MDEditor from "@uiw/react-md-editor"

export function MdEditor({ value, onChange, height = 200 }) {
  return (
    <div data-color-mode="light">
      <MDEditor value={value} onChange={onChange} height={height} preview="edit" />
    </div>
  )
}

export function MdViewer({ value }) {
  if (!value) return null
  return (
    <div data-color-mode="light" className="md">
      <MDEditor.Markdown source={value} />
    </div>
  )
}
