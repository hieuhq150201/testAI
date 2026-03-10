export function ProgressBar({ value, color = "emerald" }: { value: number; color?: string }) {
  const colors: Record<string, string> = {
    emerald: "bg-emerald-500", rose: "bg-rose-500", blue: "bg-blue-500",
  };
  return (
    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden">
      <div
        className={`h-2.5 rounded-full transition-all duration-700 ${colors[color] ?? colors.emerald}`}
        style={{ width: `${Math.round(value * 100)}%` }}
      />
    </div>
  );
}
