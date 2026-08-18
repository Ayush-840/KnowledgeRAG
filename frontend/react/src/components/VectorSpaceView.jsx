import { useEffect, useMemo, useRef, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Line } from '@react-three/drei'
import * as THREE from 'three'
import { docColor } from '../utils/docColors'

const QUERY_COLOR = '#22d3ee' // cyan: the query marker + promoted links
const SELECTED_COLOR = '#0f172a'

/**
 * 3D point cloud of the session's chunk embeddings (UMAP projection from the
 * backend). Points are colored by source document; the query drops in as a
 * distinct tetrahedron; retrieved chunks stay full color; non-retrieved chunks
 * recede; promoted (reranked top-k) chunks are enlarged and linked to the query.
 *
 * reducedMotion: disables idle auto-rotation (prefers-reduced-motion).
 * selected: the keyboard-selected point, shown with a white wireframe ring.
 */
export default function VectorSpaceView({ points, query, promotedIds, retrievedIds, onSelectPoint, selected, reducedMotion }) {
  const byId = useMemo(() => new Map(points.map((p) => [p.id, p])), [points])

  return (
    <Canvas
      camera={{ position: [0, 0, 18], fov: 50 }}
      dpr={[1, 2]}
      className="space-canvas"
      // `flat` disables ACESFilmic tone mapping — R3F applies it
      // unconditionally AFTER creating the renderer, so a gl={{ toneMapping }}
      // prop is silently ignored. With tone mapping off (and sRGB output
      // kept), the cyan query marker renders as the exact #22d3ee instead of
      // a tone-mapped pale blue, and every other color is unchanged.
      flat
    >
      <ambientLight intensity={0.7} />
      <PointCloud points={points} promotedIds={promotedIds} retrievedIds={retrievedIds} onSelectPoint={onSelectPoint} />
      {query && <QueryMarker position={[query.x, query.y, query.z]} />}
      {query &&
        (promotedIds || [])
          .map((id) => byId.get(id))
          .filter(Boolean)
          .map((p) => (
            <Line
              key={p.id}
              points={[
                [query.x, query.y, query.z],
                [p.x, p.y, p.z],
              ]}
              color={QUERY_COLOR}
              lineWidth={1}
              transparent
              opacity={0.5}
            />
          ))}
      {selected && <SelectionRing position={[selected.x, selected.y, selected.z]} />}
      <OrbitControls makeDefault enableDamping dampingFactor={0.08} autoRotate={!reducedMotion} autoRotateSpeed={0.6} />
    </Canvas>
  )
}

function PointCloud({ points, promotedIds, retrievedIds, onSelectPoint }) {
  const mesh = useRef(null)
  const [hovered, setHovered] = useState(null)
  const promoted = useMemo(() => new Set(promotedIds || []), [promotedIds])
  const retrieved = useMemo(() => new Set(retrievedIds || []), [retrievedIds])

  useEffect(() => {
    const m = mesh.current
    if (!m) return
    const dummy = new THREE.Object3D()
    const color = new THREE.Color()
    points.forEach((p, i) => {
      dummy.position.set(p.x, p.y, p.z)
      const isPromoted = promoted.has(p.id)
      const scale = (p.count ? 1 + Math.log2(p.count) : 1) * (isPromoted ? 2.2 : 1)
      dummy.scale.setScalar(scale)
      dummy.updateMatrix()
      m.setMatrixAt(i, dummy.matrix)
      color.set(docColor(p.filename))
      if (isPromoted) color.offsetHSL(0, 0, -0.12)
      else if (!retrieved.has(p.id)) color.lerp(new THREE.Color('#ffffff'), 0.6) // non-retrieved recede toward the light background
      m.setColorAt(i, color)
    })
    m.instanceMatrix.needsUpdate = true
    if (m.instanceColor) m.instanceColor.needsUpdate = true
  }, [points, promoted, retrieved])

  const hoveredPoint = hovered != null ? points[hovered] : null

  return (
    <>
      <instancedMesh
        ref={mesh}
        args={[undefined, undefined, points.length]}
        onClick={(e) => {
          e.stopPropagation()
          if (e.instanceId != null) onSelectPoint(points[e.instanceId].id)
        }}
        onPointerOver={(e) => {
          e.stopPropagation()
          if (e.instanceId != null) {
            setHovered(e.instanceId)
            document.body.style.cursor = 'pointer'
          }
        }}
        onPointerOut={() => {
          setHovered(null)
          document.body.style.cursor = 'auto'
        }}
      >
        <sphereGeometry args={[0.13, 12, 12]} />
        <meshBasicMaterial />
      </instancedMesh>
      {hoveredPoint && <SelectionRing position={[hoveredPoint.x, hoveredPoint.y, hoveredPoint.z]} dim />}
    </>
  )
}

/** The query lands as a tetrahedron — distinct SHAPE, not just color (colorblind-safe). */
function QueryMarker({ position }) {
  return (
    <group position={position}>
      <mesh>
        <tetrahedronGeometry args={[0.34]} />
        <meshBasicMaterial color={QUERY_COLOR} />
      </mesh>
      <pointLight color={QUERY_COLOR} intensity={1.2} distance={6} />
    </group>
  )
}

/** Selection ring (keyboard nav / hover). */
function SelectionRing({ position, dim }) {
  return (
    <mesh position={position}>
      <sphereGeometry args={[0.42, 16, 16]} />
      <meshBasicMaterial color={SELECTED_COLOR} wireframe transparent opacity={dim ? 0.4 : 0.8} />
    </mesh>
  )
}
