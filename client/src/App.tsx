import { useEffect, useMemo, useRef, useState } from 'react'
import { Button } from './components/ui/button'
import { Input } from './components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card'
import { Separator } from './components/ui/separator'
import { Badge } from './components/ui/badge'
import { Upload, ChevronLeft, ChevronRight, Maximize2, X, Trash2 } from 'lucide-react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'
import { Hands, Results } from '@mediapipe/hands'
import { Camera } from '@mediapipe/camera_utils'

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${(pdfjs as any).version}/build/pdf.worker.min.js`

const API_BASE = 'http://localhost:8000'

interface PdfItem {
  id: number
  filename: string
  original_name: string
  topic?: string | null
  path: string
  num_pages: number
  is_open: boolean
  current_page: number
}

export default function App() {
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const [allItems, setAllItems] = useState<PdfItem[]>([])
  const [filter, setFilter] = useState('')
  const [selected, setSelected] = useState<PdfItem | null>(null)
  const [numPages, setNumPages] = useState<number | null>(null)
  const [page, setPage] = useState(1)
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const camRef = useRef<Camera | null>(null)
  const handsRef = useRef<Hands | null>(null)
  const [gesturesEnabled, setGesturesEnabled] = useState(false)

  const fetchList = async () => {
    const res = await fetch(`${API_BASE}/api/pdfs/`)
    const data = await res.json()
    setAllItems(data.items)
  }

  useEffect(() => {
    fetchList()
  }, [])

  const normalize = (s: string) => s
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase()

  const filteredItems = useMemo(() => {
    const needle = normalize(filter || '')
    if (!needle) return allItems
    return allItems.filter(doc => {
      const topic = normalize(doc.topic || '')
      const name = normalize(doc.original_name || '')
      return topic.includes(needle) || name.includes(needle)
    })
  }, [allItems, filter])

  const onUpload = async (file: File) => {
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await fetch(`${API_BASE}/api/pdfs/upload`, { method: 'POST', body: fd })
      if (!res.ok) {
        const txt = await res.text().catch(() => '')
        alert(`Error al subir PDF: ${res.status} ${txt}`)
        return
      }
      const created: PdfItem = await res.json()
      setFilter('')
      await fetchList()
      // Abrir automáticamente el documento subido
      await openDoc(created)
    } catch (e: any) {
      alert(`Error al subir PDF: ${e?.message ?? e}`)
    }
  }

  const openDoc = async (doc: PdfItem) => {
    const res = await fetch(`${API_BASE}/api/pdfs/${doc.id}/open`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })
    const data = await res.json()
    setSelected(data)
    setPage(data.current_page ?? 1)
  }

  const closeDoc = async () => {
    if (!selected) return
    const res = await fetch(`${API_BASE}/api/pdfs/${selected.id}/close`, { method: 'POST' })
    const data = await res.json()
    setSelected(data)
    setSelected(null)
  }

  const changePage = async (mode: 'next' | 'prev' | 'set', val?: number) => {
    if (!selected) return
    const res = await fetch(`${API_BASE}/api/pdfs/${selected.id}/page`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode, page: val })
    })
    const data = await res.json()
    setSelected(data)
    setPage(data.current_page)
  }

  const classify = async (topic: string) => {
    if (!selected) return
    const res = await fetch(`${API_BASE}/api/pdfs/${selected.id}/classify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic })
    })
    const data = await res.json()
    setSelected(data)
    await fetchList()
  }

  const deleteDoc = async (id: number) => {
    await fetch(`${API_BASE}/api/pdfs/${id}`, { method: 'DELETE' })
    if (selected?.id === id) setSelected(null)
    await fetchList()
  }

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
  }

  // MediaPipe Hands: detección de dedos levantados
  useEffect(() => {
    if (!gesturesEnabled) return

    const video = videoRef.current
    if (!video) return

    const hands = new Hands({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
    })
    hands.setOptions({
      maxNumHands: 1,
      modelComplexity: 0,
      minDetectionConfidence: 0.6,
      minTrackingConfidence: 0.6
    })

    const isFingerUp = (landmarks: any, tipIdx: number, pipIdx: number) => {
      // Dedo levantado si la punta está más arriba (menor y) que la articulación PIP
      return landmarks[tipIdx].y < landmarks[pipIdx].y
    }
    let lastTime = 0

    hands.onResults((results: Results) => {
      const now = performance.now()
      if (!results.multiHandLandmarks || results.multiHandLandmarks.length === 0) return
      const lm = results.multiHandLandmarks[0]
      const indexUp = isFingerUp(lm, 8, 6)
      const middleUp = isFingerUp(lm, 12, 10)
      // Prioridad: dos dedos (siguiente) > un dedo (anterior)
      if (now - lastTime > 800) {
        if (indexUp && middleUp) {
          changePage('next')
          lastTime = now
        } else if (indexUp && !middleUp) {
          changePage('prev')
          lastTime = now
        }
      }
    })

    const cam = new Camera(video, {
      onFrame: async () => {
        await hands.send({ image: video })
      },
      width: 640,
      height: 480
    })

    cam.start()
    camRef.current = cam
    handsRef.current = hands

    return () => {
      cam.stop()
      hands.close()
      camRef.current = null
      handsRef.current = null
    }
  }, [gesturesEnabled, selected])

  return (
    <div className="h-screen flex flex-col">
      <header className="border-b">
        <div className="container mx-auto px-4 h-14 flex items-center justify-between">
          <h1 className="font-semibold">PDF Gesture Reader</h1>
          <div className="inline-flex items-center">
            <Button variant="outline" onClick={() => fileInputRef.current?.click()} className="inline-flex items-center gap-2">
              <Upload className="h-4 w-4" /> Subir PDF
            </Button>
            <input ref={fileInputRef} type="file" className="hidden" accept="application/pdf" onChange={(e) => {
              const f = e.target.files?.[0]
              if (f) onUpload(f)
              if (e.target) e.target.value = ''
            }} />
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-4 flex-1 flex gap-4 overflow-hidden">
        <Card className="w-80 flex-shrink-0">
          <CardHeader>
            <CardTitle>Biblioteca</CardTitle>
          </CardHeader>
          <CardContent>
            <Input placeholder="Filtrar por nombre o categoría" value={filter} onChange={(e) => setFilter(e.target.value)} />
            <Separator className="my-3" />
            <div className="space-y-2 overflow-auto max-h-[calc(100vh-220px)] pr-1">
              {filteredItems.map(doc => (
                <div key={doc.id} className={`rounded-md border p-2 ${selected?.id === doc.id ? 'border-primary' : ''}`}>
                  <div className="flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <div className="text-sm font-medium truncate" title={doc.original_name}>{doc.original_name}</div>
                      <div className="text-xs text-muted-foreground">{doc.num_pages} páginas</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button size="sm" variant="secondary" onClick={() => openDoc(doc)} className="inline-flex items-center gap-1">
                        <Maximize2 className="h-4 w-4" /> Abrir
                      </Button>
                      <Button size="icon" variant="destructive" onClick={() => deleteDoc(doc.id)} aria-label="Borrar">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  {doc.topic && <div className="mt-2"><Badge>{doc.topic}</Badge></div>}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="flex-1 min-w-0 flex flex-col">
          <CardHeader className="py-3">
            <div className="flex items-center justify-between">
              <CardTitle>Visor</CardTitle>
              <div className="flex items-center gap-2">
                <Button variant={gesturesEnabled ? 'default' : 'outline'} onClick={() => setGesturesEnabled(v => !v)}>
                  {gesturesEnabled ? 'Gestos ON' : 'Gestos OFF'}
                </Button>
                {selected ? (
                  <Button variant="secondary" onClick={closeDoc} className="inline-flex items-center gap-1">
                    <X className="h-4 w-4" /> Cerrar
                  </Button>
                ) : null}
              </div>
            </div>
          </CardHeader>
          <CardContent className="flex-1 flex gap-4 overflow-hidden">
            <div className="flex-1 min-w-0 flex flex-col items-center overflow-auto">
              {selected ? (
                <>
                  <Document file={`${API_BASE}/api/pdfs/${selected.id}/file`} onLoadSuccess={onDocumentLoadSuccess} loading={<div className="text-sm">Cargando PDF...</div>}>
                    <Page pageNumber={page} width={900} renderTextLayer renderAnnotationLayer />
                  </Document>
                  <div className="flex items-center gap-2 mt-2">
                    <Button variant="outline" size="icon" onClick={() => changePage('prev')} disabled={page <= 1}><ChevronLeft className="h-4 w-4" /></Button>
                    <span className="text-sm">{page}/{numPages ?? selected.num_pages}</span>
                    <Button variant="outline" size="icon" onClick={() => changePage('next')} disabled={numPages ? page >= numPages : page >= selected.num_pages}><ChevronRight className="h-4 w-4" /></Button>
                  </div>
                  <div className="flex items-center gap-2 mt-2">
                    {['deporte', 'política', 'economía', 'tecnología'].map(t => (
                      <Button key={t} variant={selected.topic === t ? 'default' : 'outline'} size="sm" onClick={() => classify(t)}>{t}</Button>
                    ))}
                  </div>
                </>
              ) : (
                <div className="text-sm text-muted-foreground">Selecciona un PDF para visualizar</div>
              )}
            </div>

            <div className="w-80 flex flex-col gap-2">
              <div className="text-sm font-medium">Webcam (Gestos)</div>
              <video ref={videoRef} className="w-full rounded-lg" playsInline />
              <div className="text-xs text-muted-foreground">Gestos: índice levantado = página anterior; índice + medio levantados = página siguiente.</div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
