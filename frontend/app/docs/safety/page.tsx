export default function SafetyPage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-3xl flex-col gap-6 px-6 py-10 text-slate-200">
      <header className="space-y-2">
        <h1 className="text-3xl font-bold">Safety Guidance</h1>
        <p className="text-sm text-slate-400">
          Research use only. Follow medical guidance for individuals with neurological conditions or photosensitivity. These
          notes summarize internal guardrails and public standards such as WCAG 2.3.1 for flashing content.
        </p>
      </header>
      <section className="space-y-3 text-sm leading-relaxed">
        <p>
          • Keep audio levels below 70% of device volume. Encourage users to adjust to comfortable SPL before starting longer
          blocks.
        </p>
        <p>
          • Provide a visible stop/escape interaction at all times. Remind participants to stop immediately if they experience
          discomfort, dizziness, or headaches.
        </p>
        <p>
          • For visual stimuli between 3–60 Hz, apply low-contrast defaults, follow WCAG 2.3.1 guidance, and display the
          photosensitivity banner shown on the landing page.
        </p>
        <p>
          • Clearly label experimental presets and avoid therapeutic claims. Reference peer-reviewed citations in preset
          descriptions to maintain transparency.
        </p>
      </section>
    </main>
  );
}
