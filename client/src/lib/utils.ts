import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export type ApiResult<T = unknown> = {
  ok: boolean
  status: number
  data?: T
  errorText?: string
}

export async function apiFetch<T = any>(input: RequestInfo | URL, init?: RequestInit): Promise<ApiResult<T>> {
  try {
    const res = await fetch(input, init)
    const contentType = res.headers.get('content-type') || ''
    const isJson = contentType.includes('application/json')
    if (res.ok) {
      const data = isJson ? await res.json() : await res.text()
      return { ok: true, status: res.status, data: data as T }
    } else {
      const msg = isJson ? JSON.stringify(await res.json()).slice(0, 500) : (await res.text()).slice(0, 500)
      return { ok: false, status: res.status, errorText: msg || `${res.status}` }
    }
  } catch (e: any) {
    return { ok: false, status: 0, errorText: e?.message ?? String(e) }
  }
}



