import { Hero } from "./components/Hero";
import { Marquee } from "./components/Marquee";

export default function App() {
  return (
    <div className="min-h-screen bg-[#f9fafb] p-4 md:p-8">
      <Hero />
      <Marquee />
    </div>
  );
}
