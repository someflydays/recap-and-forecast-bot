import ChatForm from "../components/ChatForm";

export default function HomePage() {
  return (
    <main className="min-h-screen p-4 sm:p-6 lg:p-8">
      <div className="max-w-2xl mx-auto pt-8 sm:pt-16">
        <div className="text-center mb-10">
          <h1 className="text-3xl sm:text-4xl font-bold text-white tracking-tight mb-3">
            Recap & Forecast
          </h1>
          <p className="text-[var(--text-secondary)] text-sm sm:text-base">
            AI-powered insights on any topic — past events or future predictions
          </p>
        </div>
        <ChatForm />
      </div>
    </main>
  );
}
