import type { IndicatorDefinition, IndicatorSelection } from "@/types/api";

export const INDICATOR_COLORS = ["#ffd43b", "#e649a7", "#a97ee8", "#54c6df", "#50b46a", "#ff7a2f"];

export interface IndicatorPlotStyle {
  color: string;
  lineStyle: "solid" | "dashed" | "dotted";
}

export interface IndicatorPeriodLine {
  enabled: boolean;
  value: number;
  source?: string;
}

export interface ConfiguredIndicator extends IndicatorSelection {
  enabled: boolean;
  periodLines?: IndicatorPeriodLine[];
  styles: Record<string, IndicatorPlotStyle>;
}

export function defaultParameters(definition: IndicatorDefinition): Record<string, unknown> {
  return Object.fromEntries(definition.parameters.map((parameter) => [
    parameter.key,
    Array.isArray(parameter.default) ? [...parameter.default] : parameter.default,
  ]));
}

function periodParameter(definition: IndicatorDefinition) {
  return definition.parameters.find((parameter) => parameter.type === "integer_list");
}

export function periodLineKey(config: Pick<ConfiguredIndicator, "indicator_id">, index: number): string {
  if (config.indicator_id === "vol") return `mavol_${index + 1}`;
  return `${config.indicator_id}_${index + 1}`;
}

export function plotKeys(config: ConfiguredIndicator, includeDisabled = false): string[] {
  if (config.periodLines) {
    const lineKeys = config.periodLines.flatMap((line, index) =>
      includeDisabled || line.enabled ? [periodLineKey(config, index)] : [],
    );
    return config.indicator_id === "vol" ? ["volume", ...lineKeys] : lineKeys;
  }

  const periods = Array.isArray(config.parameters.periods)
    ? config.parameters.periods.map((value) => Number(value)).filter(Number.isFinite)
    : [];
  const periodKeys = periods.map((period) => `${config.indicator_id}_${period}`);
  switch (config.indicator_id) {
    case "ma": case "ema": case "wma": case "rsi": return periodKeys;
    case "vol": return ["volume", ...periods.map((period) => `mavol_${period}`)];
    case "boll": return ["upper", "middle", "lower"];
    case "super": return ["up", "down"];
    case "macd": return ["histogram", "macd", "signal"];
    case "kdj": return ["k", "d", "j"];
    case "stochrsi": return ["k", "d"];
    case "trix": return ["trix", "signal"];
    default: return [config.indicator_id];
  }
}

export function normalizeStyles(config: ConfiguredIndicator): ConfiguredIndicator {
  const styles = Object.fromEntries(plotKeys(config, true).map((key, index) => [
    key,
    config.styles?.[key] || { color: INDICATOR_COLORS[index % INDICATOR_COLORS.length], lineStyle: "solid" },
  ]));
  return { ...config, styles };
}

export function createIndicator(definition: IndicatorDefinition, enabled = false): ConfiguredIndicator {
  const parameters = defaultParameters(definition);
  const period = periodParameter(definition);
  const defaults = Array.isArray(period?.default) ? period.default.map(Number) : [];
  const slots = period?.max_items || defaults.length;
  const source = String(parameters.source || "close");
  const periodLines = period ? Array.from({ length: slots }, (_, index) => ({
    enabled: index < defaults.length,
    value: defaults[index] || 0,
    ...(definition.parameters.some((item) => item.key === "source") ? { source } : {}),
  })) : undefined;

  return normalizeStyles({
    instance_id: `${definition.id}-default`,
    indicator_id: definition.id,
    placement: definition.placement,
    parameters,
    enabled,
    periodLines,
    styles: {},
  });
}

export function hydrateIndicator(
  definition: IndicatorDefinition,
  saved?: Partial<ConfiguredIndicator>,
): ConfiguredIndicator {
  const fresh = createIndicator(definition, saved?.enabled ?? Boolean(saved));
  if (!saved) return fresh;

  const parameters = { ...fresh.parameters, ...saved.parameters };
  const storedPeriods = Array.isArray(saved.parameters?.periods)
    ? saved.parameters.periods.map(Number).filter((value) => Number.isFinite(value) && value > 0)
    : [];
  const periodLines = fresh.periodLines?.map((line, index) => {
    const savedLine = saved.periodLines?.[index];
    return savedLine ? { ...line, ...savedLine } : {
      ...line,
      enabled: index < storedPeriods.length,
      value: storedPeriods[index] || line.value,
    };
  });
  const styles = { ...(saved.styles || {}) };
  periodLines?.forEach((line, index) => {
    const slotKey = periodLineKey(fresh, index);
    const legacyKey = fresh.indicator_id === "vol"
      ? `mavol_${line.value}`
      : `${fresh.indicator_id}_${line.value}`;
    if (!styles[slotKey] && styles[legacyKey]) styles[slotKey] = styles[legacyKey];
  });

  return normalizeStyles({
    ...fresh,
    ...saved,
    enabled: saved.enabled ?? true,
    parameters,
    periodLines,
    styles,
  });
}

export function apiSelection(config: ConfiguredIndicator): IndicatorSelection {
  const parameters = { ...config.parameters };
  if (config.periodLines) {
    const lines = config.periodLines.flatMap((line, index) => line.enabled && line.value > 0 ? [{
      slot: index + 1,
      period: line.value,
      ...(line.source ? { source: line.source } : {}),
    }] : []);
    parameters.periods = lines.map((line) => line.period);
    parameters.lines = lines;
  }
  return {
    instance_id: config.instance_id,
    indicator_id: config.indicator_id,
    placement: config.placement,
    parameters,
  };
}
