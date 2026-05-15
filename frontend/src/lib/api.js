import axios from "axios"
import { clearAuth, getToken } from "./auth"

const baseURL = import.meta.env.VITE_API_BASE_URL

export const http = axios.create({ baseURL })

http.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (res) => res,
  (error) => {
    const status = error.response?.status
    const path = window.location.pathname
    const onPublicRoute =
      path.startsWith("/p/") ||
      path === "/login" ||
      path === "/register"
    if (status === 401 && !onPublicRoute) {
      clearAuth()
      window.location.assign("/login")
    }
    return Promise.reject(error)
  },
)

export async function register(
  email,
  password,
) {
  const res = await http.post("/register", { email, password })
  return res.data
}

export async function login(
  email,
  password,
) {
  const res = await http.post("/login", { email, password })
  return res.data
}

export async function me() {
  const res = await http.get("/me")
  return res.data
}

export async function listNotes(
  params = {},
) {
  const res = await http.get("/notes", { params })
  return res.data
}

export async function getNote(id) {
  const res = await http.get(`/notes/${id}`)
  return res.data
}

export async function createNote(input) {
  const res = await http.post("/notes", input)
  return res.data
}

export async function updateNote(
  id,
  input,
) {
  const res = await http.patch(`/notes/${id}`, input)
  return res.data
}

export async function deleteNote(id) {
  await http.delete(`/notes/${id}`)
}

export async function shareNote(
  id,
  share_with_email,
  can_edit = false,
) {
  await http.post(`/notes/${id}/share`, { share_with_email, can_edit })
}

export async function unshareNote(
  id,
  share_with_email,
) {
  await http.post(`/notes/${id}/unshare`, { share_with_email })
}

export async function togglePin(id) {
  const res = await http.post(`/notes/${id}/toggle-pin`)
  return res.data
}

export async function createPublicLink(
  id,
  expires_at,
) {
  const body = expires_at ? { expires_at } : {}
  const res = await http.post(`/notes/${id}/public-link`, body)
  return res.data
}

export async function revokePublicLink(id) {
  await http.delete(`/notes/${id}/public-link`)
}

export async function getPublicNote(token) {
  const res = await http.get(`/public/notes/${token}`)
  return res.data
}

export async function searchNotes(
  q,
) {
  const res = await http.get("/search", { params: { q } })
  return res.data
}

export async function listTags() {
  const res = await http.get("/tags")
  return res.data
}

export function getApiErrorMessage(err, fallback = "Something went wrong") {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data
    if (data && typeof data === "object") {
      const d = data
      if (typeof d.message === "string") return d.message
      if (typeof d.detail === "string") return d.detail
      for (const v of Object.values(d)) {
        if (Array.isArray(v) && v.length > 0 && typeof v[0] === "string") {
          return v[0]
        }
        if (typeof v === "string") return v
      }
    }
    if (err.message) return err.message
  }
  return fallback
}
