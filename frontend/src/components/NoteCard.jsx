import { MoreVertical, Pin, PinOff, Palette, Share2, Link as LinkIcon, Trash2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"
import { colorBgClass, COLOR_LABEL, NOTE_COLORS } from "@/lib/noteColors"

export function NoteCard({
  note,
  onOpen,
  onTogglePin,
  onChangeColor,
  onShare,
  onPublicLink,
  onDelete,
}) {
  return (
    <div
      className={cn(
        "group relative flex flex-col rounded-lg border border-zinc-200 shadow-sm p-4 min-h-[140px] cursor-pointer hover:shadow-md transition-shadow",
        colorBgClass(note.color),
      )}
      onClick={() => onOpen(note)}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="text-[15px] font-semibold leading-tight break-words flex-1">
          {note.title || "Untitled"}
        </h3>
        <div className="flex items-center gap-1 shrink-0">
          {note.is_pinned && (
            <Pin className="h-3.5 w-3.5 text-zinc-500" />
          )}
          <div onClick={(e) => e.stopPropagation()}>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 opacity-60 group-hover:opacity-100"
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-44">
                <DropdownMenuItem onSelect={() => onTogglePin(note)}>
                  {note.is_pinned ? (
                    <>
                      <PinOff className="h-4 w-4" /> Unpin
                    </>
                  ) : (
                    <>
                      <Pin className="h-4 w-4" /> Pin
                    </>
                  )}
                </DropdownMenuItem>
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger>
                    <Palette className="h-4 w-4" /> Change color
                  </DropdownMenuSubTrigger>
                  <DropdownMenuSubContent className="w-40">
                    {NOTE_COLORS.map((c) => (
                      <DropdownMenuItem
                        key={c}
                        onSelect={() => onChangeColor(note, c)}
                      >
                        <span
                          className={cn(
                            "h-4 w-4 rounded-full border border-zinc-200",
                            colorBgClass(c),
                          )}
                        />
                        <span>{COLOR_LABEL[c]}</span>
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuSubContent>
                </DropdownMenuSub>
                <DropdownMenuItem onSelect={() => onShare(note)}>
                  <Share2 className="h-4 w-4" /> Share
                </DropdownMenuItem>
                <DropdownMenuItem onSelect={() => onPublicLink(note)}>
                  <LinkIcon className="h-4 w-4" /> Public link
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onSelect={() => onDelete(note)}
                  className="text-destructive focus:text-destructive"
                >
                  <Trash2 className="h-4 w-4" /> Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
      <p className="text-sm text-zinc-700 whitespace-pre-wrap line-clamp-5 break-words flex-1">
        {note.content}
      </p>
      {note.tags_detail.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-3">
          {note.tags_detail.map((t) => (
            <Badge key={t.id} variant="outline" className="bg-white/60">
              {t.name}
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}
