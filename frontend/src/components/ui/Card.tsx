interface CardProps {
  title: string;
  value: string;
  icon?: string;
}

export default function Card({ title, value, icon }: CardProps) {
  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-xl p-5 transition-colors hover:bg-[#282828]">
      <div className="flex items-center gap-3">
        {icon && (
          <div className="w-10 h-10 rounded-lg bg-[rgba(99,102,241,0.15)] flex items-center justify-center text-xl">
            {icon}
          </div>
        )}
        <div className="flex-1">
          <h3 className="font-medium text-gray-300">{title}</h3>
          <div className="text-2xl font-bold text-white mt-1">{value}</div>
        </div>
      </div>
    </div>
  );
}
