import { motion } from "motion/react";
import { ChevronRight } from "lucide-react";

const VIDEO_SRC =
  "https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260505_101331_74f9b798-3f00-4e86-8a01-377aa16ffeaa.mp4";

export function Hero() {
  return (
    <section className="relative w-full max-w-[1400px] mx-auto rounded-[48px] bg-white border border-slate-200/50 shadow-[0_40px_100px_-20px_rgba(0,0,0,0.03)] overflow-hidden h-[600px] flex flex-col">
      {/* Video layer */}
      <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden select-none">
        <video
          src={VIDEO_SRC}
          autoPlay
          loop
          muted
          playsInline
          className="w-full h-full object-cover scale-105 transition-transform duration-1000"
        />
      </div>

      {/* Content layer */}
      <div className="relative z-20 flex-1 px-8 md:px-16 pt-12 md:pt-16 flex flex-col items-start">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          <h1 className="font-display font-medium text-[42px] md:text-[56px] tracking-tight text-[#0a1b33] leading-[1.1]">
            Foundation of the
            <br />
            new digital epoch
          </h1>

          <p className="mt-5 font-sans text-[14px] md:text-[15px] text-[#64748b] max-w-md leading-relaxed">
            Designing products, powering ecosystems and laying the foundation
            of a decentralized web for enterprises, builders and communities
            alike.
          </p>

          <motion.a
            href="/"
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.97 }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
            className="mt-8 inline-block bg-[#0a152d] text-white font-semibold text-[13px] px-7 py-3 rounded-full shadow-[0_12px_30px_rgba(10,21,45,0.25)] cursor-pointer"
          >
            Contact Us
          </motion.a>
        </motion.div>
      </div>

      {/* Floating bottom navbar */}
      <FloatingNavbar />
    </section>
  );
}

function FloatingNavbar() {
  return (
    <div className="absolute bottom-10 left-1/2 -translate-x-1/2 z-30">
      <motion.nav
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.7, ease: "easeOut" }}
        className="flex items-center bg-white/90 backdrop-blur-2xl px-1.5 py-1.5 rounded-full shadow-[0_12px_40px_rgba(0,0,0,0.08)] border border-slate-200/40"
      >
        {/* Logo */}
        <div className="w-9 h-9 rounded-full bg-white border border-slate-100 shadow-sm flex items-center justify-center text-[#0a1b33] text-[14px] mr-1">
          ✦
        </div>

        <button className="px-4 py-2 rounded-full text-[12px] font-semibold text-slate-500 hover:text-[#0a1b33] transition-colors cursor-pointer">
          Products
        </button>
        <button className="px-4 py-2 rounded-full text-[12px] font-semibold text-slate-500 hover:text-[#0a1b33] transition-colors cursor-pointer">
          Docs
        </button>

        <a
          href="/"
          className="flex items-center gap-1 ml-1 bg-white px-5 py-2 rounded-full text-[12px] font-semibold text-[#0a1b33] border border-slate-200/60 shadow-sm hover:border-slate-300 transition-all cursor-pointer"
        >
          Get in touch
          <ChevronRight className="w-3.5 h-3.5" strokeWidth={2} />
        </a>
      </motion.nav>
    </div>
  );
}
