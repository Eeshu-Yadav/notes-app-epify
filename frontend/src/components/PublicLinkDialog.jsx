import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { toast } from "sonner"
import { Copy, RefreshCw, Trash2 } from "lucide-react"
import { createPublicLink, getApiErrorMessage, revokePublicLink } from "@/lib/api"

export function PublicLinkDialog({ open, onOpenChange, note, onChanged }) {
  const [busy, setBusy] = useState(false)

  if (!note) return null

  const link = note.public_link
  const fullUrl = link
    ? `${window.location.origin}/p/${link.token}`
    : ""

  async function create() {
    if (!note) return
    setBusy(true)
    try {
      await createPublicLink(note.id)
      toast.success("Public link created")
      onChanged()
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Failed to create link"))
    } finally {
      setBusy(false)
    }
  }

  async function rotate() {
    if (!note) return
    setBusy(true)
    try {
      await revokePublicLink(note.id)
      await createPublicLink(note.id)
      toast.success("Link rotated")
      onChanged()
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Failed to rotate"))
    } finally {
      setBusy(false)
    }
  }

  async function revoke() {
    if (!note) return
    setBusy(true)
    try {
      await revokePublicLink(note.id)
      toast.success("Link revoked")
      onChanged()
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Failed to revoke"))
    } finally {
      setBusy(false)
    }
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(fullUrl)
      toast.success("Copied to clipboard")
    } catch {
      toast.error("Copy failed")
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Public link</DialogTitle>
        </DialogHeader>

        {link ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Input readOnly value={fullUrl} />
              <Button
                variant="outline"
                size="icon"
                onClick={copy}
                title="Copy"
              >
                <Copy className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              Views: {link.view_count}
              {link.expires_at && ` · Expires ${new Date(link.expires_at).toLocaleString()}`}
            </p>
            <div className="flex gap-2">
              <Button variant="outline" onClick={rotate} disabled={busy}>
                <RefreshCw className="h-4 w-4" /> Rotate
              </Button>
              <Button variant="destructive" onClick={revoke} disabled={busy}>
                <Trash2 className="h-4 w-4" /> Revoke
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Anyone with the link will be able to view this note.
            </p>
            <Button onClick={create} disabled={busy}>
              {busy ? "Creating..." : "Create public link"}
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
