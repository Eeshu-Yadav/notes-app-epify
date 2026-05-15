import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { toast } from "sonner"
import { getApiErrorMessage, shareNote, unshareNote } from "@/lib/api"

export function ShareDialog({ open, onOpenChange, note, onChanged }) {
  const [email, setEmail] = useState("")
  const [canEdit, setCanEdit] = useState(false)
  const [busy, setBusy] = useState(false)

  if (!note) return null

  async function add(e) {
    e.preventDefault()
    if (!email.trim() || !note) return
    setBusy(true)
    try {
      await shareNote(note.id, email.trim(), canEdit)
      toast.success(`Shared with ${email.trim()}`)
      setEmail("")
      setCanEdit(false)
      onChanged()
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Failed to share"))
    } finally {
      setBusy(false)
    }
  }

  async function revoke(targetEmail) {
    if (!note) return
    setBusy(true)
    try {
      await unshareNote(note.id, targetEmail)
      toast.success(`Revoked ${targetEmail}`)
      onChanged()
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Failed to revoke"))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Share note</DialogTitle>
        </DialogHeader>

        <form onSubmit={add} className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor="share-email">Email</Label>
            <Input
              id="share-email"
              type="email"
              placeholder="person@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={canEdit}
              onChange={(e) => setCanEdit(e.target.checked)}
            />
            Can edit
          </label>
          <Button type="submit" disabled={busy}>
            {busy ? "Sharing..." : "Share"}
          </Button>
        </form>

        <div className="space-y-2 mt-2">
          <p className="text-sm font-medium">Shared with</p>
          {note.shared_with.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Not shared with anyone yet.
            </p>
          ) : (
            <ul className="space-y-2">
              {note.shared_with.map((e) => (
                <li
                  key={e}
                  className="flex items-center justify-between rounded-md border border-zinc-200 px-3 py-2"
                >
                  <span className="text-sm">{e}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={busy}
                    onClick={() => revoke(e)}
                  >
                    Revoke
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
