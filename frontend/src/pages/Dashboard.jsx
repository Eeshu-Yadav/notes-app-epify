import { useCallback, useEffect, useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { LogOut, Plus, Search, StickyNote } from "lucide-react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { NoteCard } from "@/components/NoteCard"
import { NoteEditorDialog } from "@/components/NoteEditorDialog"
import { ShareDialog } from "@/components/ShareDialog"
import { PublicLinkDialog } from "@/components/PublicLinkDialog"
import {
  createNote,
  deleteNote,
  getApiErrorMessage,
  getNote,
  listNotes,
  searchNotes,
  togglePin,
  updateNote,
} from "@/lib/api"
import { clearAuth, getUser } from "@/lib/auth"
import { cn } from "@/lib/utils"
import { colorBgClass, COLOR_LABEL, NOTE_COLORS } from "@/lib/noteColors"

const PAGE_SIZE = 24

export default function Dashboard() {
  const navigate = useNavigate()
  const user = getUser()

  const [notes, setNotes] = useState([])
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState("all")
  const [colorFilter, setColorFilter] = useState(null)
  const [search, setSearch] = useState("")
  const [activeSearch, setActiveSearch] = useState("")

  const [editorOpen, setEditorOpen] = useState(false)
  const [editingNote, setEditingNote] = useState(null)

  const [shareOpen, setShareOpen] = useState(false)
  const [shareNoteState, setShareNoteState] = useState(null)

  const [publicOpen, setPublicOpen] = useState(false)
  const [publicNoteState, setPublicNoteState] = useState(null)

  const fetchNotes = useCallback(
    async (opts) => {
      setLoading(true)
      try {
        if (activeSearch.trim()) {
          const res = await searchNotes(activeSearch.trim())
          setNotes(res.results)
          setHasMore(false)
          setPage(1)
          return
        }
        const params = {
          page: opts.page,
          page_size: PAGE_SIZE,
        }
        if (filter === "pinned") params.pinned = true
        if (filter === "archived") params.archived = true
        else params.archived = false
        if (colorFilter) params.color = colorFilter
        const data = await listNotes(params)
        setNotes((prev) =>
          opts.append ? [...prev, ...data.results] : data.results,
        )
        setHasMore(!!data.next)
        setPage(opts.page)
      } catch (err) {
        toast.error(getApiErrorMessage(err, "Failed to load notes"))
      } finally {
        setLoading(false)
      }
    },
    [filter, colorFilter, activeSearch],
  )

  useEffect(() => {
    fetchNotes({ page: 1, append: false })
  }, [fetchNotes])

  function refresh() {
    fetchNotes({ page: 1, append: false })
  }

  function loadMore() {
    fetchNotes({ page: page + 1, append: true })
  }

  function logout() {
    clearAuth()
    navigate("/login", { replace: true })
  }

  function openNew() {
    setEditingNote(null)
    setEditorOpen(true)
  }

  function openEdit(note) {
    setEditingNote(note)
    setEditorOpen(true)
  }

  async function handleSave(data, noteId) {
    try {
      if (noteId) {
        await updateNote(noteId, data)
        toast.success("Note updated")
      } else {
        await createNote(data)
        toast.success("Note created")
      }
      refresh()
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Failed to save note"))
      throw err
    }
  }

  async function handleTogglePin(note) {
    try {
      await togglePin(note.id)
      refresh()
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Failed to toggle pin"))
    }
  }

  async function handleChangeColor(note, color) {
    try {
      await updateNote(note.id, { color })
      refresh()
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Failed to update color"))
    }
  }

  async function handleDelete(note) {
    if (!window.confirm("Delete this note?")) return
    try {
      await deleteNote(note.id)
      toast.success("Note deleted")
      refresh()
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Failed to delete"))
    }
  }

  async function openShare(note) {
    try {
      const fresh = await getNote(note.id)
      setShareNoteState(fresh)
      setShareOpen(true)
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Failed to load note"))
    }
  }

  async function refreshShareNote() {
    if (!shareNoteState) return
    try {
      const fresh = await getNote(shareNoteState.id)
      setShareNoteState(fresh)
      refresh()
    } catch {
      // ignore
    }
  }

  async function openPublic(note) {
    try {
      const fresh = await getNote(note.id)
      setPublicNoteState(fresh)
      setPublicOpen(true)
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Failed to load note"))
    }
  }

  async function refreshPublicNote() {
    if (!publicNoteState) return
    try {
      const fresh = await getNote(publicNoteState.id)
      setPublicNoteState(fresh)
      refresh()
    } catch {
      // ignore
    }
  }

  const { pinned, others } = useMemo(() => {
    const p = []
    const o = []
    for (const n of notes) {
      if (n.is_pinned) p.push(n)
      else o.push(n)
    }
    return { pinned: p, others: o }
  }, [notes])

  function onSearchSubmit(e) {
    e.preventDefault()
    setActiveSearch(search)
  }

  function clearSearch() {
    setSearch("")
    setActiveSearch("")
  }

  const showPinnedSection = filter !== "pinned" && pinned.length > 0 && !activeSearch

  return (
    <div className="min-h-full flex flex-col">
      <header className="sticky top-0 z-30 bg-background/95 backdrop-blur border-b border-zinc-200">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-3">
          <div className="flex items-center gap-2 shrink-0">
            <StickyNote className="h-5 w-5" />
            <span className="font-semibold text-base">Notes</span>
          </div>
          <form
            onSubmit={onSearchSubmit}
            className="flex-1 max-w-xl mx-auto relative"
          >
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search notes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 bg-white"
            />
            {activeSearch && (
              <button
                type="button"
                onClick={clearSearch}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground hover:text-foreground"
              >
                Clear
              </button>
            )}
          </form>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                {user?.email ?? "Account"}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuLabel className="text-xs text-muted-foreground">
                {user?.email}
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={logout}>
                <LogOut className="h-4 w-4" /> Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        <div className="max-w-6xl mx-auto px-4 pb-3 flex flex-wrap items-center gap-3">
          <div className="inline-flex rounded-md border border-zinc-200 bg-white p-0.5">
            {(["all", "pinned", "archived"]).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={cn(
                  "px-3 py-1 text-sm rounded-sm capitalize",
                  filter === f
                    ? "bg-zinc-900 text-white"
                    : "text-zinc-600 hover:text-zinc-900",
                )}
              >
                {f}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Color:</span>
            <button
              onClick={() => setColorFilter(null)}
              className={cn(
                "h-5 w-5 rounded-full border border-zinc-300 bg-white",
                colorFilter === null && "ring-2 ring-zinc-900 ring-offset-1",
              )}
              title="All colors"
            />
            {NOTE_COLORS.filter((c) => c !== "default").map((c) => (
              <button
                key={c}
                onClick={() => setColorFilter(c)}
                title={COLOR_LABEL[c]}
                className={cn(
                  "h-5 w-5 rounded-full border border-zinc-300",
                  colorBgClass(c),
                  colorFilter === c && "ring-2 ring-zinc-900 ring-offset-1",
                )}
              />
            ))}
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto px-4 py-6 w-full">
        {loading && notes.length === 0 ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : notes.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <StickyNote className="h-8 w-8 text-zinc-400 mb-3" />
            <p className="text-sm text-muted-foreground">
              {activeSearch
                ? "No notes match your search."
                : "No notes yet. Hit + to create your first."}
            </p>
          </div>
        ) : (
          <>
            {showPinnedSection && (
              <>
                <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
                  Pinned
                </h2>
                <NoteGrid
                  notes={pinned}
                  onOpen={openEdit}
                  onTogglePin={handleTogglePin}
                  onChangeColor={handleChangeColor}
                  onShare={openShare}
                  onPublicLink={openPublic}
                  onDelete={handleDelete}
                />
                {others.length > 0 && (
                  <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mt-8 mb-3">
                    Others
                  </h2>
                )}
                <NoteGrid
                  notes={others}
                  onOpen={openEdit}
                  onTogglePin={handleTogglePin}
                  onChangeColor={handleChangeColor}
                  onShare={openShare}
                  onPublicLink={openPublic}
                  onDelete={handleDelete}
                />
              </>
            )}
            {!showPinnedSection && (
              <NoteGrid
                notes={notes}
                onOpen={openEdit}
                onTogglePin={handleTogglePin}
                onChangeColor={handleChangeColor}
                onShare={openShare}
                onPublicLink={openPublic}
                onDelete={handleDelete}
              />
            )}

            {hasMore && (
              <div className="flex justify-center mt-8">
                <Button
                  variant="outline"
                  onClick={loadMore}
                  disabled={loading}
                >
                  {loading ? "Loading..." : "Load more"}
                </Button>
              </div>
            )}
          </>
        )}
      </main>

      <button
        onClick={openNew}
        title="New note"
        className="fixed bottom-6 right-6 h-14 w-14 rounded-full bg-zinc-900 text-white shadow-lg hover:bg-zinc-800 flex items-center justify-center transition-colors"
      >
        <Plus className="h-6 w-6" />
      </button>

      <NoteEditorDialog
        open={editorOpen}
        onOpenChange={setEditorOpen}
        note={editingNote}
        onSave={handleSave}
      />
      <ShareDialog
        open={shareOpen}
        onOpenChange={setShareOpen}
        note={shareNoteState}
        onChanged={refreshShareNote}
      />
      <PublicLinkDialog
        open={publicOpen}
        onOpenChange={setPublicOpen}
        note={publicNoteState}
        onChanged={refreshPublicNote}
      />
    </div>
  )
}

function NoteGrid({
  notes,
  onOpen,
  onTogglePin,
  onChangeColor,
  onShare,
  onPublicLink,
  onDelete,
}) {
  return (
    <div
      className="grid gap-4"
      style={{ gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))" }}
    >
      {notes.map((n) => (
        <NoteCard
          key={n.id}
          note={n}
          onOpen={onOpen}
          onTogglePin={onTogglePin}
          onChangeColor={onChangeColor}
          onShare={onShare}
          onPublicLink={onPublicLink}
          onDelete={onDelete}
        />
      ))}
    </div>
  )
}
