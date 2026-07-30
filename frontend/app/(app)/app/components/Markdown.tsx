"use client";

import React from "react";

/**
 * Minimal markdown renderer for Claude-generated text.
 *
 * Claude returns markdown (**bold**, bullet lists, headings) but the app used to
 * print it as raw text, so emphasis markers leaked into the UI. A full markdown
 * library would require a dependency + pnpm lockfile update, so this covers the
 * subset Claude actually emits: bold / italic / inline code / lists / headings.
 * Output is built as React elements — no dangerouslySetInnerHTML.
 */

type Block =
  | { type: "heading"; level: number; text: string }
  | { type: "ul"; items: string[] }
  | { type: "ol"; items: string[] }
  | { type: "p"; text: string };

const HEADING_RE = /^(#{1,6})\s+(.*)$/;
const BULLET_RE = /^\s*[-*•]\s+(.*)$/;
const ORDERED_RE = /^\s*\d+[.)]\s+(.*)$/;
// **bold** first, then `code`, then *italic* — order matters so ** is not eaten by *.
const INLINE_RE = /\*\*([^*]+)\*\*|`([^`]+)`|\*([^*\n]+)\*/g;

function renderInline(text: string, keyPrefix: string): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  let cursor = 0;
  let n = 0;
  INLINE_RE.lastIndex = 0;

  let match = INLINE_RE.exec(text);
  while (match !== null) {
    if (match.index > cursor) nodes.push(text.slice(cursor, match.index));
    const key = `${keyPrefix}-i${n++}`;

    if (match[1] !== undefined) {
      nodes.push(
        <strong key={key} className="font-semibold text-slate-100">
          {match[1]}
        </strong>
      );
    } else if (match[2] !== undefined) {
      nodes.push(
        <code
          key={key}
          className="rounded bg-white/10 px-1 py-0.5 font-mono text-[0.85em] text-amber-200"
        >
          {match[2]}
        </code>
      );
    } else {
      nodes.push(
        <em key={key} className="italic">
          {match[3]}
        </em>
      );
    }

    cursor = match.index + match[0].length;
    match = INLINE_RE.exec(text);
  }

  if (cursor < text.length) nodes.push(text.slice(cursor));
  return nodes;
}

function parseBlocks(src: string): Block[] {
  const blocks: Block[] = [];
  const lines = src.split("\n");
  let paragraph: string[] = [];

  const flushParagraph = () => {
    if (paragraph.length === 0) return;
    blocks.push({ type: "p", text: paragraph.join("\n") });
    paragraph = [];
  };

  for (const line of lines) {
    if (line.trim() === "") {
      flushParagraph();
      continue;
    }

    const heading = HEADING_RE.exec(line);
    if (heading) {
      flushParagraph();
      blocks.push({ type: "heading", level: heading[1].length, text: heading[2] });
      continue;
    }

    const bullet = BULLET_RE.exec(line);
    if (bullet) {
      flushParagraph();
      const last = blocks[blocks.length - 1];
      if (last?.type === "ul") last.items.push(bullet[1]);
      else blocks.push({ type: "ul", items: [bullet[1]] });
      continue;
    }

    const ordered = ORDERED_RE.exec(line);
    if (ordered) {
      flushParagraph();
      const last = blocks[blocks.length - 1];
      if (last?.type === "ol") last.items.push(ordered[1]);
      else blocks.push({ type: "ol", items: [ordered[1]] });
      continue;
    }

    paragraph.push(line);
  }

  flushParagraph();
  return blocks;
}

const HEADING_SIZE: Record<number, string> = {
  1: "text-base font-semibold text-slate-100",
  2: "text-sm font-semibold text-slate-100",
  3: "text-sm font-semibold text-slate-200",
};

interface Props {
  text: string;
  className?: string;
}

export default function Markdown({ text, className = "" }: Props) {
  const blocks = React.useMemo(() => parseBlocks(text), [text]);

  return (
    <div className={`space-y-2 ${className}`}>
      {blocks.map((block, i) => {
        const key = `b${i}`;

        if (block.type === "heading") {
          return (
            <p key={key} className={HEADING_SIZE[block.level] ?? HEADING_SIZE[3]}>
              {renderInline(block.text, key)}
            </p>
          );
        }

        if (block.type === "ul") {
          return (
            <ul key={key} className="list-disc space-y-1 pl-5 marker:text-slate-500">
              {block.items.map((item, j) => (
                <li key={`${key}-${j}`}>{renderInline(item, `${key}-${j}`)}</li>
              ))}
            </ul>
          );
        }

        if (block.type === "ol") {
          return (
            <ol key={key} className="list-decimal space-y-1 pl-5 marker:text-slate-500">
              {block.items.map((item, j) => (
                <li key={`${key}-${j}`}>{renderInline(item, `${key}-${j}`)}</li>
              ))}
            </ol>
          );
        }

        return (
          <p key={key} className="whitespace-pre-wrap">
            {renderInline(block.text, key)}
          </p>
        );
      })}
    </div>
  );
}
