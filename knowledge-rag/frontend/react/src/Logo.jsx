export default function Logo({ size = 36 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <linearGradient
          id="kr-brand-grad"
          x1="7"
          y1="3"
          x2="25"
          y2="29"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="var(--brand-amber)" />
          <stop offset="1" stopColor="var(--brand-orange)" />
        </linearGradient>
      </defs>
      {/* document */}
      <path
        d="M9 3h10.5L24 7.5V27a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"
        fill="url(#kr-brand-grad)"
      />
      {/* folded corner */}
      <path d="M19.5 3v4.5H24" fill="var(--brand-orange-light)" opacity="0.85" />
      {/* embedded node/path motif */}
      <g stroke="#0f172a" strokeWidth="1.5" strokeLinecap="round">
        <path d="M12 13.5l3.5 4.5M15.5 18l4-3.5M12 13.5l7.5-.5" />
      </g>
      <circle cx="12" cy="13.5" r="2" fill="#0f172a" />
      <circle cx="15.5" cy="18" r="2" fill="#0f172a" />
      <circle cx="19.5" cy="13" r="2" fill="#0f172a" />
    </svg>
  )
}
