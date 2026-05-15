import { useEffect, useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"
import { colorBgClass, COLOR_LABEL, NOTE_COLORS } from "@/lib/noteColors"

export function NoteEditorDialog({ open, onOpenChange, note, onSave }) {
  const [title, setTitle] = useState("")
  const [content, setContent] = useState("")
  const [color, setColor] = useState("default")
  const [tags, setTags] = useState([])
  const [tagInput, setTagInput] = useState("")
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open) {
      setTitle(note?.title ?? "")
      setContent(note?.content ?? "")
      setColor(note?.color ?? "default")
      setTags(note?.tags_detail.map((t) => t.name) ?? [])
      setTagInput("")
    }
  }, [open, note])

  function commitTagInput() {
    const parts = tagInput
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)
    if (parts.length === 0) return
    setTags((prev) => Array.from(new Set([...prev, ...parts])))
    setTagInput("")
  }

  function removeTag(t) {
    setTags((prev) => prev.filter((x) => x !== t))
  }

  async function save() {
    setSaving(true)
    try {
      await onSave(
        {
          title: title.trim(),
          content,
          color,
          tags,
        },
        note?.id ?? null,
      )
      onOpenChange(false)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={cn("max-w-xl", colorBgClass(color))}>
        <DialogHeader>
          <DialogTitle>{note ? "Edit note" : "New note"}</DialogTitle>
        </DialogHeader>

        <div className="space-y-3">
          <Input
            placeholder="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="bg-white/70 border-zinc-200"
          />
          <Textarea
            placeholder="Take a note..."
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={Math.min(16, Math.max(6, content.split("\n").length + 1))}
            className="bg-white/70 border-zinc-200 resize-none"
          />

          <div>
            <div className="flex items-center gap-2 flex-wrap">
              {NOTE_COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setColor(c)}
                  title={COLOR_LABEL[c]}
                  className={cn(
                    "h-6 w-6 rounded-full border border-zinc-300",
                    colorBgClass(c),
                    color === c && "ring-2 ring-zinc-900 ring-offset-2",
                  )}
                />
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2 flex-wrap mb-2">
              {tags.map((t) => (
                <Badge key={t} variant="secondary" className="gap-1 bg-white/70">
                  {t}
                  <button
                    type="button"
                    onClick={() => removeTag(t)}
                    className="ml-0.5"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
            <Input
              placeholder="Add tags (comma-separated). Press Enter."
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === ",") {
                  e.preventDefault()
                  commitTagInput()
                }
              }}
              onBlur={commitTagInput}
              className="bg-white/70 border-zinc-200"
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={saving}
          >
            Cancel
          </Button>
          <Button onClick={save} disabled={saving}>
            {saving ? "Saving..." : "Save"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
