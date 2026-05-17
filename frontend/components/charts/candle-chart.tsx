'use client';

import {
  ColorType,
  createChart,
  CrosshairMode,
  type IChartApi,
  type ISeriesApi,
  type SeriesMarker,
  type Time,
} from 'lightweight-charts';
import { memo, useEffect, useRef } from 'react';

import type { Candle } from '@/lib/types';

export interface ChartMarker {
  /** ISO timestamp */
  time: string;
  position: 'aboveBar' | 'belowBar' | 'inBar';
  color: string;
  shape: 'arrowUp' | 'arrowDown' | 'circle' | 'square';
  text?: string;
}

export interface PriceLine {
  price: number;
  color: string;
  title: string;
  style?: 'solid' | 'dashed' | 'dotted';
}

interface Props {
  candles: Candle[];
  markers?: ChartMarker[];
  priceLines?: PriceLine[];
  height?: number;
}

function CandleChartImpl({ candles, markers = [], priceLines = [], height = 360 }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  // Track whether we've already done the initial fitContent so we don't
  // jam the timescale back to "show all" on every candle update (which
  // wrecks the user's scroll/zoom).
  const fittedRef = useRef(false);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0a0a0a' },
        textColor: '#a1a1aa',
        fontSize: 11,
      },
      grid: {
        vertLines: { color: '#27272a' },
        horzLines: { color: '#27272a' },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: '#3f3f46' },
      timeScale: {
        borderColor: '#3f3f46',
        timeVisible: true,
        secondsVisible: false,
      },
      width: containerRef.current.clientWidth,
      height,
    });
    const series = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });
    chartRef.current = chart;
    seriesRef.current = series;
    fittedRef.current = false;

    const onResize = () => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', onResize);

    return () => {
      window.removeEventListener('resize', onResize);
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
      fittedRef.current = false;
    };
  }, [height]);

  useEffect(() => {
    if (!seriesRef.current) return;
    const data = candles.map((c) => ({
      time: (Math.floor(new Date(c.timestamp).getTime() / 1000) as unknown) as Time,
      open: Number(c.open),
      high: Number(c.high),
      low: Number(c.low),
      close: Number(c.close),
    }));
    seriesRef.current.setData(data);
    // Only fit once on the first non-empty load; later updates respect the
    // user's current scroll/zoom.
    if (data.length > 0 && !fittedRef.current) {
      chartRef.current?.timeScale().fitContent();
      fittedRef.current = true;
    }
  }, [candles]);

  useEffect(() => {
    if (!seriesRef.current) return;
    const ms: SeriesMarker<Time>[] = markers.map((m) => ({
      time: (Math.floor(new Date(m.time).getTime() / 1000) as unknown) as Time,
      position: m.position,
      color: m.color,
      shape: m.shape,
      text: m.text,
    }));
    seriesRef.current.setMarkers(ms);
  }, [markers]);

  useEffect(() => {
    if (!seriesRef.current) return;
    // Remove and re-add (lightweight-charts has no diff API for price lines)
    const series = seriesRef.current;
    const lines: ReturnType<typeof series.createPriceLine>[] = priceLines.map((pl) =>
      series.createPriceLine({
        price: pl.price,
        color: pl.color,
        lineWidth: 1,
        lineStyle: pl.style === 'dashed' ? 1 : pl.style === 'dotted' ? 2 : 0,
        axisLabelVisible: true,
        title: pl.title,
      }),
    );
    return () => {
      lines.forEach((l) => series.removePriceLine(l));
    };
  }, [priceLines]);

  return <div ref={containerRef} style={{ width: '100%', height }} />;
}

/**
 * Memoised so that parent re-renders (which happen every 30-60s due to SWR
 * polling) don't re-create the chart's internal state. Parents must pass
 * stable references for `candles` / `markers` / `priceLines` (use useMemo).
 */
export const CandleChart = memo(CandleChartImpl);
