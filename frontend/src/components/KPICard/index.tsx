import { useEffect, useRef } from 'react';
import { motion, useMotionValue, useTransform, animate } from 'framer-motion';

interface KPICardProps {
  label: string;
  value: string;
  sub?: string;
  statusColor: string;
  statusBadge?: string;
}

function parseNumeric(value: string): number {
  const cleaned = value.replace(/[万亿,]/g, '');
  const num = parseFloat(cleaned);
  return Number.isNaN(num) ? 0 : num;
}

function getBadgeColor(badge: string): { dot: string; text: string } {
  switch (badge) {
    case 'NORMAL':
      return { dot: 'bg-aims-up', text: 'text-aims-up' };
    case 'HIGH':
      return { dot: 'bg-aims-down', text: 'text-aims-down' };
    case 'WARN':
      return { dot: 'bg-aims-warn', text: 'text-aims-warn' };
    default:
      return { dot: 'bg-aims-up', text: 'text-aims-up' };
  }
}

function AnimatedValue({ value }: { value: string }) {
  const isNumeric = /\d/.test(value);
  const count = useMotionValue(0);
  const target = parseNumeric(value);
  const nodeRef = useRef<HTMLSpanElement>(null);
  const hasSuffix = /[万亿]/.test(value);
  const suffix = hasSuffix ? value.replace(/[\d.,]/g, '') : '';
  const decimals = (value.match(/\.(\d+)/)?.[1] || '').length;

  const rounded = useTransform(count, (latest) => {
    if (target >= 10000) {
      return (latest / 10000).toFixed(2) + '万亿';
    }
    return latest.toFixed(decimals);
  });

  useEffect(() => {
    if (!isNumeric) {
      return undefined;
    }

    const controls = animate(count, target, {
      duration: 1.2,
      ease: 'easeOut',
    });
    return controls.stop;
  }, [count, isNumeric, target]);

  if (!isNumeric) {
    return <span className="font-mono tabular-nums">{value}</span>;
  }

  return (
    <motion.span ref={nodeRef} className="font-mono tabular-nums">
      {rounded}
    </motion.span>
  );
}

export default function KPICard({
  label,
  value,
  sub,
  statusColor,
  statusBadge,
}: KPICardProps) {
  const badgeStyle = statusBadge ? getBadgeColor(statusBadge) : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="card flex min-h-[112px] w-full min-w-0 flex-col justify-center gap-2 rounded-lg border border-aims-border bg-aims-card px-4 py-4"
    >
      {/* Label */}
      <span className="text-aims-amber text-xs font-medium leading-none">
        {label}
      </span>

      {/* Value */}
      <span
        className="text-[clamp(28px,3.2vw,42px)] font-bold font-mono tabular-nums leading-none"
        style={{ color: statusColor }}
      >
        <AnimatedValue value={value} />
      </span>

      {/* Sub + Badge */}
      <div className="flex items-center gap-2 -mt-1">
        {sub && (
          <span className="text-aims-amber/80 text-[11px] font-mono tabular-nums leading-none">
            {sub}
          </span>
        )}
        {statusBadge && badgeStyle && (
          <span className="inline-flex items-center gap-1 text-[11px] font-mono font-semibold leading-none">
            <span className={`inline-block w-[5px] h-[5px] rounded-full ${badgeStyle.dot}`} />
            <span className={badgeStyle.text}>{statusBadge}</span>
          </span>
        )}
      </div>
    </motion.div>
  );
}
