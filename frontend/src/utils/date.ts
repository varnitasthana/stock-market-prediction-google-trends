export const toISODate = (value: Date): string => {
  const localDate = new Date(value.getTime() - value.getTimezoneOffset() * 60_000);
  return localDate.toISOString().slice(0, 10);
};

export const getTodayISO = (): string => toISODate(new Date());

export const formatDisplayDate = (value?: string | null): string => {
  if (!value) return 'N/A';
  const [year, month, day] = value.split('-');
  if (!year || !month || !day) return value;
  return `${day}-${month}-${year}`;
};

export const formatDisplayDateRange = (value?: string | null): string => {
  if (!value) return 'N/A';
  const [start, end] = value.split(' to ');
  if (!end) return formatDisplayDate(start);
  return `${formatDisplayDate(start)} to ${formatDisplayDate(end)}`;
};
