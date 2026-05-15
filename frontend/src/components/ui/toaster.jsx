import { Toaster as SonnerToaster } from "sonner"

export function Toaster() {
  return (
    <SonnerToaster
      position="top-right"
      theme="light"
      richColors={false}
      closeButton
      toastOptions={{
        classNames: {
          toast:
            "rounded-md border border-zinc-200 bg-white text-zinc-900 shadow-sm",
          description: "text-zinc-500",
        },
      }}
    />
  )
}
