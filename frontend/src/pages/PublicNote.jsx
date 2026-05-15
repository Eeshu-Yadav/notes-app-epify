import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { StickyNote } from "lucide-react"
import { getPublicNote } from "@/lib/api"
import { cn } from "@/lib/utils"
import { colorBgClass } from "@/lib/noteColors"

export default function PublicNote() {
  const { token } = useParams()
  const [note, setNote] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function run() {
      if (!token) return
      setLoading(true)
      try {
        const data = await getPublicNote(token)
        if (!cancelled) setNote(data)
      } catch {
        if (!cancelled)
          setError("This link is unavailable or has expired.")
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    run()
    return () => {
      cancelled = true
    }
  }, [token])

  return (
    <div className="min-h-full flex flex-col">
      <header className="border-b border-zinc-200 bg-background">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center gap-2">
          <StickyNote className="h-5 w-5" />
          <span className="font-semibold">Notes</span>
          <span className="text-xs text-muted-foreground ml-2">
            Shared note
          </span>
        </div>
      </header>
      <main className="flex-1 max-w-3xl mx-auto w-full px-4 py-8">
        {loading ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : error ? (
          <p className="text-sm text-muted-foreground">{error}</p>
        ) : note ? (
          <article
            className={cn(
              "rounded-lg border border-zinc-200 shadow-sm p-6",
              colorBgClass(note.color),
            )}
          >
            <h1 className="text-2xl font-semibold mb-2 break-words">
              {note.title || "Untitled"}
            </h1>
            <p className="text-xs text-muted-foreground mb-4">
              Shared by {note.owner_email} ·{" "}
              {new Date(note.updated_at).toLocaleString()}
            </p>
            <div className="text-[15px] whitespace-pre-wrap break-words">
              {note.content}
            </div>
          </article>
        ) : null}
      </main>
    </div>
  )
}
