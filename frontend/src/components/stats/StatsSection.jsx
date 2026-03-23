const stats = [
  { value: '6', label: 'Турниров проведено' },
  { value: '100+', label: 'Участников' },
  { value: '100+', label: 'Команд' },
  { value: '18', label: 'Победителей' },
]

export default function StatsSection() {
  return (
    <section className="py-10">
      <div className="w-full max-w-[1920px] mx-auto px-16">

        {/* Header */}
        <div className="flex items-center gap-2 mb-4">
          <span className="font-heading text-[#2EECC0] text-[14px]">📊</span>
          <span className="font-heading text-[13px] tracking-[0.2em] uppercase text-[#2EECC0]">
            Stats
          </span>
        </div>

        {/* Stats row */}
        <div className="border border-[rgba(46,236,192,0.25)] rounded-md">
          <div className="grid grid-cols-4 divide-x divide-[rgba(46,236,192,0.15)]">
            {stats.map((stat, index) => (
              <div key={index} className="py-8 text-center">
                <div className="font-stats text-[3.5rem] text-[#2EECC0] mb-2 leading-none">
                  {stat.value}
                </div>
                <div className="font-heading text-[11px] tracking-[0.2em] uppercase text-[#6B7280]">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}