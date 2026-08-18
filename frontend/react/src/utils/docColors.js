// One deterministic color per document, so a document means the same color in
// the vector space view, the file list, and the source drawer.
const HUE_CACHE = {}

function docHue(filename) {
  if (HUE_CACHE[filename]) return HUE_CACHE[filename]
  let h = 0
  for (let i = 0; i < filename.length; i++) {
    h = (h * 31 + filename.charCodeAt(i)) >>> 0
  }
  HUE_CACHE[filename] = h % 360
  return HUE_CACHE[filename]
}

/** CSS color string, e.g. "hsl(210, 70%, 62%)". */
export function docColor(filename) {
  return `hsl(${docHue(filename)}, 70%, 62%)`
}

/** [r, g, b] in 0..1 for three.js materials. */
export function docRgb(filename) {
  const h = docHue(filename) / 360
  const s = 0.7
  const l = 0.62
  const q = l < 0.5 ? l * (1 + s) : l + s - l * s
  const p = 2 * l - q
  const hue2rgb = (t) => {
    if (t < 0) t += 1
    if (t > 1) t -= 1
    if (t < 1 / 6) return p + (q - p) * 6 * t
    if (t < 1 / 2) return q
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6
    return p
  }
  return [hue2rgb(h + 1 / 3), hue2rgb(h), hue2rgb(h - 1 / 3)]
}
