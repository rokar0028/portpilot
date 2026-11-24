import type { Evidence } from "@/types/checker";

export function groupEvidence(evidence: Evidence[]): [string, Evidence[]][] {
  return Array.from(
    evidence.reduce((groups, item) => {
      const group = groups.get(item.url) ?? [];
      group.push(item);
      groups.set(item.url, group);
      return groups;
    }, new Map<string, Evidence[]>()),
  );
}

export function sourceCount(evidence: Evidence[]): number {
  return new Set(evidence.map((source) => source.url)).size;
}
