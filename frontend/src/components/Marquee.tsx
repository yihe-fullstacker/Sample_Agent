interface LogoItem {
  name: string;
  src: string;
  /** Brand gradient used for the hover glow layer */
  gradient: string;
}

const LOGOS: LogoItem[] = [
  {
    name: "Procure",
    src: "https://svgl.app/library/procure.svg",
    gradient: "radial-gradient(circle, #3b82f6 0%, #1d4ed8 55%, transparent 70%)",
  },
  {
    name: "Shopify",
    src: "https://svgl.app/library/shopify.svg",
    gradient: "radial-gradient(circle, #facc15 0%, #eab308 55%, transparent 70%)",
  },
  {
    name: "Blender",
    src: "https://svgl.app/library/blender.svg",
    gradient: "radial-gradient(circle, #60a5fa 0%, #2563eb 55%, transparent 70%)",
  },
  {
    name: "Figma",
    src: "https://svgl.app/library/figma.svg",
    gradient: "radial-gradient(circle, #c084fc 0%, #7c3aed 55%, transparent 70%)",
  },
  {
    name: "Spotify",
    src: "https://svgl.app/library/spotify.svg",
    gradient: "radial-gradient(circle, #fb7185 0%, #e11d48 55%, transparent 70%)",
  },
  {
    name: "Lottielab",
    src: "https://svgl.app/library/lottielab.svg",
    gradient: "radial-gradient(circle, #fde047 0%, #22c55e 55%, transparent 70%)",
  },
  {
    name: "Google Cloud",
    src: "https://svgl.app/library/google-cloud.svg",
    gradient: "radial-gradient(circle, #93c5fd 0%, #38bdf8 55%, transparent 70%)",
  },
  {
    name: "Bing",
    src: "https://svgl.app/library/bing.svg",
    gradient: "radial-gradient(circle, #22d3ee 0%, #0d9488 55%, transparent 70%)",
  },
];

export function Marquee() {
  return (
    <div className="marquee mt-10 max-w-[1400px] mx-auto overflow-hidden">
      <div className="marquee-track flex w-max">
        {[0, 1].map((copy) => (
          <div
            key={copy}
            aria-hidden={copy === 1}
            className="flex gap-4 pr-4"
          >
            {LOGOS.map((logo) => (
              <LogoCard key={`${copy}-${logo.name}`} logo={logo} />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

function LogoCard({ logo }: { logo: LogoItem }) {
  return (
    <div className="group relative h-24 w-40 shrink-0 flex items-center justify-center rounded-full bg-white border border-slate-200/60 shadow-sm hover:border-slate-300 transition-all overflow-hidden">
      {/* Hover gradient layer */}
      <div
        className="absolute inset-0 scale-150 opacity-0 group-hover:scale-100 group-hover:opacity-100 transition-all duration-500 ease-out"
        style={{ background: logo.gradient }}
      />

      {/* Logo */}
      <img
        src={logo.src}
        alt={logo.name}
        loading="lazy"
        draggable={false}
        className="relative h-8 w-auto object-contain transition-all duration-500 group-hover:brightness-0 group-hover:invert"
      />
    </div>
  );
}
