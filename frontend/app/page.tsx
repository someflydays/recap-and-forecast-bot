import ChatForm from "../components/ChatForm";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-white p-6">
      <h1 className="text-2xl font-bold text-center mb-6">
        Recap & Forecast Bot
      </h1>
      <ChatForm />
    </main>
  );
}