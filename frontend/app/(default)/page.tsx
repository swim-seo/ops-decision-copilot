export const metadata = {
  title: "Ops Copilot — AI-powered Operations Decision Support",
  description: "Upload your CSV, PDF, or Excel files. Ops Copilot builds a knowledge graph, detects problems, and tells you exactly what to do — before your next standup.",
};

import Hero from "@/components/hero-home";
import BusinessCategories from "@/components/business-categories";
import FeaturesPlanet from "@/components/features-planet";
import LargeTestimonial from "@/components/large-testimonial";
import Cta from "@/components/cta";

export default function Home() {
  return (
    <>
      <Hero />
      <BusinessCategories />
      <FeaturesPlanet />
      <LargeTestimonial />
      <Cta />
    </>
  );
}
