export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-paper font-ui text-ink">
      {children}
    </div>
  );
}
