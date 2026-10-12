/**
 * Markdown utilities for cleaning and preparing artifact document content.
 */

/**
 * Cleans and prepares markdown content for rendering:
 * 1. Strips duplicate leading title heading matching artifact.title (or leading H1) to avoid displaying title twice.
 * 2. Strips any decorative underline (e.g. repeated === or ---) immediately under the stripped title.
 * 3. Normalizes any standalone repeated equals signs (===...) elsewhere in the document into markdown horizontal rules (---).
 */
export function cleanMarkdownContent(rawContent: string, title?: string): string {
  if (!rawContent) return '';

  const lines = rawContent.split(/\r?\n/);
  const normalizedTitle = (title || '').replace(/[*_`#]/g, '').trim().toLowerCase();

  // 1. Check and strip duplicate leading title
  if (lines.length > 0) {
    let firstNonEmptyIdx = -1;
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].trim().length > 0) {
        firstNonEmptyIdx = i;
        break;
      }
    }

    if (firstNonEmptyIdx !== -1) {
      const firstLine = lines[firstNonEmptyIdx].trim();
      const isAtxHeading = /^#+\s+(.+)$/.test(firstLine);

      if (isAtxHeading) {
        const headingText = firstLine.replace(/^#+\s+/, '').replace(/[*_`]/g, '').trim().toLowerCase();
        const isH1 = /^#\s+/.test(firstLine);
        const matchesTitle = Boolean(
          normalizedTitle &&
          (headingText === normalizedTitle ||
            headingText.includes(normalizedTitle) ||
            normalizedTitle.includes(headingText))
        );

        if (isH1 || matchesTitle) {
          lines.splice(0, firstNonEmptyIdx + 1);

          // If the next non-empty line is an ASCII underline/divider (=== or ---), strip it too
          while (lines.length > 0 && lines[0].trim() === '') {
            lines.shift();
          }
          if (lines.length > 0 && (/^={3,}\s*$/.test(lines[0].trim()) || /^-{3,}\s*$/.test(lines[0].trim()))) {
            lines.shift();
          }
        }
      } else {
        // Check for setext heading style: Line 0 is title text, Line 1 is === or ---
        if (firstNonEmptyIdx + 1 < lines.length) {
          const nextLine = lines[firstNonEmptyIdx + 1].trim();
          const isUnderline = /^={3,}\s*$/.test(nextLine) || /^-{3,}\s*$/.test(nextLine);
          const lineText = firstLine.replace(/[*_`]/g, '').trim().toLowerCase();
          const matchesTitle = Boolean(
            normalizedTitle &&
            (lineText === normalizedTitle ||
              lineText.includes(normalizedTitle) ||
              normalizedTitle.includes(lineText))
          );

          if (isUnderline && (matchesTitle || Boolean(title))) {
            lines.splice(0, firstNonEmptyIdx + 2);
          }
        }
      }

      // Trim any remaining leading blank lines
      while (lines.length > 0 && lines[0].trim() === '') {
        lines.shift();
      }
    }
  }

  // 2. Convert any remaining standalone repeated equals lines (===...) into markdown horizontal rules (---)
  const converted = lines.map((line) => {
    if (/^\s*={3,}\s*$/.test(line)) {
      return '---';
    }
    return line;
  });

  return converted.join('\n');
}
