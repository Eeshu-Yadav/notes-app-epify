export const NOTE_COLORS = [
  "default",
  "yellow",
  "green",
  "blue",
  "pink",
  "purple",
  "orange",
  "gray",
]

const SWATCH = {
  default: "bg-white",
  yellow: "bg-note-yellow",
  green: "bg-note-green",
  blue: "bg-note-blue",
  pink: "bg-note-pink",
  purple: "bg-note-purple",
  orange: "bg-note-orange",
  gray: "bg-note-gray",
}

export function colorBgClass(color) {
  return SWATCH[color] ?? SWATCH.default
}

export const COLOR_LABEL = {
  default: "Default",
  yellow: "Yellow",
  green: "Green",
  blue: "Blue",
  pink: "Pink",
  purple: "Purple",
  orange: "Orange",
  gray: "Gray",
}
